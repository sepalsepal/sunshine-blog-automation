"""
ContentCrew - 콘텐츠 생성 Crew
이미지 생성 + 텍스트 오버레이 래핑 (CrewAI 인터페이스 호환)
"""

import asyncio
import subprocess
from pathlib import Path
import sys
import json

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

from core.agents.image_generator import ImageGeneratorAgent
from core.agents.prompt_generator import PromptGeneratorAgent


def run_async(coro):
    """
    비동기 코루틴을 안전하게 실행하는 헬퍼 함수.
    이미 실행 중인 이벤트 루프가 있으면 해당 루프에서 실행하고,
    없으면 새 루프를 생성하여 실행한다.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        # 실행 중인 루프 없음 - 새로 생성
        return asyncio.run(coro)

    # 이미 루프가 실행 중인 경우
    import concurrent.futures
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(asyncio.run, coro)
        return future.result()


class ContentCrew:
    """
    콘텐츠 생성 Crew

    기존 에이전트 재사용:
    - PromptGeneratorAgent: 이미지 프롬프트 생성
    - ImageGeneratorAgent: AI 이미지 생성
    - Puppeteer 스크립트: 텍스트 오버레이

    CrewAI kickoff() 인터페이스 호환
    """

    def __init__(self):
        self.image_generator = ImageGeneratorAgent()
        self.prompt_generator = PromptGeneratorAgent()

    def run_text_overlay(self, script_name: str) -> bool:
        """Puppeteer로 텍스트 오버레이 실행"""
        script_path = ROOT / "scripts" / script_name

        if not script_path.exists():
            print(f"스크립트 없음: {script_path}")
            return False

        try:
            result = subprocess.run(
                ["node", str(script_path)],
                capture_output=True,
                text=True,
                cwd=str(ROOT)
            )
            return result.returncode == 0
        except Exception as e:
            print(f"오버레이 실패: {e}")
            return False

    def run(
        self,
        topic: str,
        slides: list = None,
        output_dir: str = None,
        skip_generation: bool = False
    ) -> dict:
        """
        콘텐츠 생성 실행

        Args:
            topic: 주제 (예: "banana")
            slides: 슬라이드 정보 리스트
                [{"title": "...", "subtitle": "...", "prompt": "..."}, ...]
            output_dir: 출력 디렉토리
            skip_generation: True면 이미지 생성 건너뛰고 기존 이미지 사용

        Returns:
            {
                "success": bool,
                "images": [...],
                "output_dir": str
            }
        """
        if output_dir is None:
            output_dir = str(ROOT / "outputs" / f"{topic}_v8_final")

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        generated_images = []

        if not skip_generation and slides:
            # 1. 슬라이드를 ImageGeneratorAgent 형식으로 변환
            prompts = []
            for i, slide in enumerate(slides):
                prompt = slide.get("prompt", "")
                if not prompt:
                    # 프롬프트가 없으면 기본 프롬프트 생성
                    prompt = f"A golden retriever dog with {topic}, Instagram post style, high quality photo"

                slide_type = slide.get("type", "content")
                if i == 0:
                    slide_type = "cover"
                elif i == len(slides) - 1:
                    slide_type = "cta"

                prompts.append({
                    "index": i,
                    "type": slide_type,
                    "prompt": prompt
                })
                print(f"[{i+1}/{len(slides)}] 이미지 생성 중...")

            # 2. ImageGeneratorAgent 배치 호출
            result = run_async(self.image_generator.run({
                "prompts": prompts,
                "plan": {"topic": topic}
            }))

            if result.success:
                images_data = result.data.get("images", [])
                for img in images_data:
                    if img.get("exists") and img.get("path"):
                        generated_images.append(img["path"])
                        print(f"  완료: {Path(img['path']).name}")
                    else:
                        print(f"  실패: {img.get('error', 'unknown error')}")
            else:
                print(f"  전체 실패: {result.error}")
        else:
            # 기존 이미지 사용
            for f in sorted(output_path.glob(f"{topic}_*.png")):
                generated_images.append(str(f))

        return {
            "success": len(generated_images) > 0,
            "images": generated_images,
            "output_dir": str(output_path),
            "count": len(generated_images)
        }

    def kickoff(self, inputs: dict) -> dict:
        """
        CrewAI 스타일 실행

        Args:
            inputs: {
                "topic": "banana",
                "slides": [...],
                "output_dir": "...",  # optional
                "skip_generation": False  # optional
            }
        """
        return self.run(
            topic=inputs.get("topic", "unknown"),
            slides=inputs.get("slides", []),
            output_dir=inputs.get("output_dir"),
            skip_generation=inputs.get("skip_generation", False)
        )


# 테스트용
if __name__ == "__main__":
    crew = ContentCrew()

    # 기존 이미지로 테스트 (생성 건너뛰기)
    result = crew.kickoff({
        "topic": "banana",
        "slides": [],
        "output_dir": str(ROOT / "outputs" / "banana_v8_final"),
        "skip_generation": True
    })

    print(f"성공: {result['success']}")
    print(f"이미지 수: {result['count']}")
    for img in result['images'][:3]:
        print(f"  - {Path(img).name}")
