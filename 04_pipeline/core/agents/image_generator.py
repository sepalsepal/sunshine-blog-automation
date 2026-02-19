"""
ImageGeneratorAgent - 이미지 생성 에이전트
프롬프트를 받아 AI 이미지 생성 (fal.ai Flux 2 Pro 기본)

Author: 최기술 대리
"""

import os
import asyncio
import httpx
from typing import Any, Dict, List
from pathlib import Path
from dotenv import load_dotenv
from PIL import Image
import io
from .base import BaseAgent, AgentResult, retry

# Instagram 표준 이미지 크기
INSTAGRAM_SIZE = (1080, 1080)

# 커스텀 예외 임포트
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from core.pipeline.exceptions import (
    ImageGenerationError,
    ImageDownloadError,
    AuthenticationError,
    RateLimitError,
    APIError,
)

# .env에서 환경변수 로드
load_dotenv()


class ImageGeneratorAgent(BaseAgent):
    """이미지 생성 에이전트 (fal.ai Flux 2 Pro 기본)"""

    @property
    def name(self) -> str:
        return "ImageGenerator"

    def validate_input(self, input_data: Any) -> bool:
        """프롬프트 리스트 검증"""
        if not input_data:
            return False
        prompts = input_data.get("prompts", [])
        return len(prompts) > 0

    async def execute(self, input_data: Any) -> AgentResult:
        """
        이미지 배치 생성

        Args:
            input_data: PromptGeneratorAgent의 출력

        Returns:
            AgentResult with generated image paths
        """
        prompts = input_data.get("prompts", [])
        plan = input_data.get("plan", {})
        topic = plan.get("topic", "unknown")

        self.log(f"{len(prompts)}개 이미지 생성 시작")

        # provider 우선순위: fal > dalle3 > stability > placeholder
        provider = self.config.get("provider", "fal")

        if provider == "fal":
            images = await self._generate_fal_flux(prompts, topic)
        elif provider == "dalle3":
            images = await self._generate_dalle3(prompts, topic)
        elif provider == "stability":
            images = await self._generate_stability(prompts, topic)
        else:
            images = await self._generate_placeholder(prompts, topic)

        return AgentResult(
            success=True,
            data={"images": images, "plan": plan},
            metadata={"image_count": len(images), "provider": provider}
        )

    @retry(max_attempts=3, delay=2.0)
    async def _generate_fal_flux(self, prompts: List, topic: str) -> List[Dict]:
        """
        fal.ai Flux 2 Pro API로 이미지 생성

        - 모델: fal-ai/flux-2-pro
        - 크기: 1080x1080 (Instagram 정사각형)
        - 인증: FAL_KEY 환경변수
        """
        import fal_client

        fal_key = os.getenv("FAL_KEY")
        if not fal_key:
            self.log("FAL_KEY가 .env에 설정되지 않음, placeholder로 대체", level="warning")
            return await self._generate_placeholder(prompts, topic)

        # FAL_KEY를 환경변수로 설정 (fal_client가 자동으로 읽음)
        os.environ["FAL_KEY"] = fal_key

        # 출력 폴더 생성
        output_dir = Path(__file__).parent.parent / "outputs" / topic
        output_dir.mkdir(parents=True, exist_ok=True)

        images = []

        for p in prompts:
            prompt_text = p.get("prompt", p.get("text", f"{topic} dog food image"))
            self.log(f"  [{p['index']}/{len(prompts)}] 생성 중: {prompt_text[:50]}...")

            try:
                # fal.ai Flux 2 Pro 호출 (비동기를 동기 래핑)
                result = await asyncio.to_thread(
                    fal_client.subscribe,
                    "fal-ai/flux-2-pro",
                    arguments={
                        "prompt": prompt_text,
                        "image_size": {"width": 1080, "height": 1080},
                        "num_images": 1,
                        "output_format": "png",
                        "safety_tolerance": "5",
                    }
                )

                # 결과에서 이미지 URL 추출
                image_url = result["images"][0]["url"]

                # 이미지 다운로드 후 로컬 저장 (타임아웃 30초)
                image_path = output_dir / f"{topic}_{p['index']:02d}_{p.get('type', 'content')}.png"
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.get(image_url)
                    response.raise_for_status()

                    # PIL로 이미지 로드 및 1080x1080 리사이즈
                    img = Image.open(io.BytesIO(response.content))
                    if img.size != INSTAGRAM_SIZE:
                        img = img.resize(INSTAGRAM_SIZE, Image.Resampling.LANCZOS)
                    img.save(image_path, "PNG", optimize=True)

                self.log(f"  [{p['index']}/{len(prompts)}] 완료: {image_path.name} ({INSTAGRAM_SIZE[0]}x{INSTAGRAM_SIZE[1]})")

                images.append({
                    "index": p["index"],
                    "type": p.get("type", "content"),
                    "path": str(image_path),
                    "exists": True,
                    "url": image_url,
                    "provider": "fal-flux-2-pro"
                })

            except httpx.HTTPStatusError as e:
                # HTTP 에러 (다운로드 실패)
                error_msg = f"이미지 다운로드 실패 (HTTP {e.response.status_code})"
                self.log(f"  [{p['index']}/{len(prompts)}] {error_msg}", level="error")
                images.append({
                    "index": p["index"],
                    "type": p.get("type", "content"),
                    "path": "",
                    "exists": False,
                    "error": error_msg,
                    "error_type": "download_error"
                })

            except httpx.TimeoutException as e:
                # 타임아웃
                error_msg = "이미지 다운로드 타임아웃"
                self.log(f"  [{p['index']}/{len(prompts)}] {error_msg}", level="error")
                images.append({
                    "index": p["index"],
                    "type": p.get("type", "content"),
                    "path": "",
                    "exists": False,
                    "error": error_msg,
                    "error_type": "timeout"
                })

            except KeyError as e:
                # API 응답 구조 오류
                error_msg = f"API 응답 파싱 실패: {str(e)}"
                self.log(f"  [{p['index']}/{len(prompts)}] {error_msg}", level="error")
                images.append({
                    "index": p["index"],
                    "type": p.get("type", "content"),
                    "path": "",
                    "exists": False,
                    "error": error_msg,
                    "error_type": "api_response_error"
                })

            except Exception as e:
                # 기타 에러
                error_type = type(e).__name__
                error_msg = f"{error_type}: {str(e)}"
                self.log(f"  [{p['index']}/{len(prompts)}] 실패: {error_msg}", level="error")
                images.append({
                    "index": p["index"],
                    "type": p.get("type", "content"),
                    "path": "",
                    "exists": False,
                    "error": error_msg,
                    "error_type": error_type.lower()
                })

        # 성공/실패 통계
        success_count = sum(1 for img in images if img["exists"])
        self.log(f"생성 완료: {success_count}/{len(images)}개 성공")

        return images

    async def _generate_placeholder(self, prompts: List, topic: str) -> List[Dict]:
        """플레이스홀더 이미지 (실제 생성 없이 경로만 반환)"""
        base_path = Path(self.config.get("_global", {}).get("paths", {}).get("images", "."))
        images = []

        for p in prompts:
            image_path = base_path / topic / f"{topic}_{p['index']:02d}_{p['type']}.png"
            images.append({
                "index": p["index"],
                "type": p["type"],
                "path": str(image_path),
                "exists": image_path.exists()
            })

        return images

    @retry(max_attempts=3, delay=2.0)
    async def _generate_dalle3(self, prompts: List, topic: str) -> List[Dict]:
        """DALL-E 3 API로 이미지 생성 (백업 옵션).

        Note:
            현재 fal.ai FLUX.2 Pro를 주력으로 사용 중.
            DALL-E 3는 비용 대비 효과가 낮아 백업으로만 유지.
            필요시 OpenAI API 키 설정 후 구현 예정.
        """
        self.log("DALL-E 3: 백업 옵션 (fal.ai 사용 권장)", level="info")
        raise NotImplementedError("DALL-E 3는 백업 옵션입니다. fal.ai를 사용하세요.")

    @retry(max_attempts=3, delay=2.0)
    async def _generate_stability(self, prompts: List, topic: str) -> List[Dict]:
        """Stability AI API로 이미지 생성 (백업 옵션).

        Note:
            현재 fal.ai FLUX.2 Pro를 주력으로 사용 중.
            Stability AI는 비용 대비 효과가 낮아 백업으로만 유지.
            필요시 Stability API 키 설정 후 구현 예정.
        """
        self.log("Stability AI: 백업 옵션 (fal.ai 사용 권장)", level="info")
        raise NotImplementedError("Stability AI는 백업 옵션입니다. fal.ai를 사용하세요.")
