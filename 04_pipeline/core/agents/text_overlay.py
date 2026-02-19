"""
TextOverlayAgent - 텍스트 오버레이 에이전트
이미지에 텍스트 오버레이 적용 (Puppeteer 활용)

Author: 최기술 대리
"""

import asyncio
import json
import os
from typing import Any, Dict, List, Optional
from pathlib import Path
from .base import BaseAgent, AgentResult


class TextOverlayAgent(BaseAgent):
    """
    텍스트 오버레이 에이전트 (Puppeteer 연동)

    입력 형식 1 (단순):
        {"topic": "apple"}
        → config/apple_text.json 로드
        → media_bank/instagram_ready/apple/ 이미지 사용

    입력 형식 2 (상세):
        {
            "images": ["path/to/image_00.png", ...],
            "text_data": [
                {"slide": 1, "type": "cover", "title": "APPLE"},
                ...
            ],
            "output_dir": "output/apple_final/"
        }
    """

    @property
    def name(self) -> str:
        return "TextOverlay"

    def validate_input(self, input_data: Any) -> bool:
        """입력 검증"""
        if isinstance(input_data, str):
            return len(input_data) > 0
        if isinstance(input_data, dict):
            # topic, plan.topic, 또는 (images + text_data) 필수
            if input_data.get("topic"):
                return True
            if input_data.get("plan", {}).get("topic"):
                return True
            if input_data.get("images") and input_data.get("text_data"):
                return True
        return False

    async def execute(self, input_data: Any) -> AgentResult:
        """
        텍스트 오버레이 실행

        Args:
            input_data: topic 문자열 또는 상세 설정 dict

        Returns:
            AgentResult with overlay results
        """
        # 입력 정규화
        if isinstance(input_data, str):
            config = {"topic": input_data}
        elif isinstance(input_data, dict):
            # 파이프라인에서 올 때: plan + images 포함
            if "plan" in input_data:
                topic = input_data["plan"].get("topic")
                config = {"topic": topic}
                # ImageGenerator에서 온 이미지 경로 → Puppeteer 입력 위치로 복사
                if "images" in input_data:
                    await self._prepare_images_for_puppeteer(topic, input_data["images"])
            else:
                config = input_data
        else:
            return AgentResult(success=False, error="Invalid input type")

        topic = config.get("topic")

        # 모드 결정: 단순 모드 vs 상세 모드
        if topic and not config.get("images"):
            # 단순 모드: Puppeteer 스크립트 직접 호출
            result = await self._run_simple_mode(topic)
        else:
            # 상세 모드: 커스텀 이미지/텍스트 사용
            result = await self._run_advanced_mode(config)

        if result["success"]:
            self.log(f"✓ {result['count']}개 이미지 오버레이 완료")
            return AgentResult(
                success=True,
                data={
                    "output_images": result.get("output_images", []),
                    "output_dir": result.get("output_dir"),
                    "count": result.get("count", 0),
                    "topic": topic
                },
                metadata={"mode": result.get("mode", "simple")}
            )
        else:
            self.log(f"✗ 오버레이 실패: {result['error']}", level="error")
            return AgentResult(
                success=False,
                error=result.get("error"),
                metadata={"mode": result.get("mode", "simple")}
            )

    async def _prepare_images_for_puppeteer(self, topic: str, images: List[Dict]):
        """
        fal.ai 생성 이미지를 Puppeteer가 읽는 위치로 복사

        ImageGenerator 출력 위치: outputs/{topic}/
        Puppeteer 입력 위치: media_bank/instagram_ready/{topic}/
        """
        import shutil

        target_dir = Path(__file__).parent.parent / "media_bank" / "instagram_ready" / topic
        target_dir.mkdir(parents=True, exist_ok=True)

        # 기존 파일 정리
        for f in target_dir.iterdir():
            if f.suffix.lower() in ('.png', '.jpg', '.jpeg'):
                f.unlink()

        # 이미지 복사 (인덱스 순서)
        copied = 0
        for img in sorted(images, key=lambda x: x.get("index", 0)):
            src = Path(img.get("path", ""))
            if src.exists():
                dst = target_dir / f"{topic}_{img['index']:02d}.png"
                shutil.copy2(str(src), str(dst))
                copied += 1

        self.log(f"이미지 {copied}개 → media_bank/instagram_ready/{topic}/ 복사 완료")

    async def _run_simple_mode(self, topic: str) -> Dict:
        """
        단순 모드: 기존 Puppeteer 스크립트 호출
        config/{topic}_text.json 사용
        """
        scripts_path = Path(__file__).parent.parent / "scripts"
        script_file = scripts_path / "add_text_overlay_puppeteer.js"

        if not script_file.exists():
            return {
                "success": False,
                "error": f"Puppeteer 스크립트 없음: {script_file}",
                "mode": "simple"
            }

        # 텍스트 데이터 존재 확인
        config_path = Path(__file__).parent.parent / "config" / f"{topic}_text.json"
        if not config_path.exists():
            return {
                "success": False,
                "error": f"텍스트 데이터 없음: {config_path}",
                "mode": "simple"
            }

        try:
            self.log(f"'{topic}' Puppeteer 오버레이 시작")

            process = await asyncio.create_subprocess_exec(
                "node",
                str(script_file),
                topic,
                cwd=str(scripts_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=120  # 2분 타임아웃
            )

            stdout_str = stdout.decode("utf-8")
            stderr_str = stderr.decode("utf-8")

            if process.returncode == 0:
                # 출력 이미지 목록 생성
                output_dir = Path(__file__).parent.parent / "images" / topic
                output_images = []

                if output_dir.exists():
                    output_images = sorted([
                        str(output_dir / f)
                        for f in os.listdir(output_dir)
                        if f.endswith('.png') and not f.startswith('.')
                    ])

                return {
                    "success": True,
                    "count": len(output_images) or stdout_str.count("✅"),
                    "output_dir": str(output_dir),
                    "output_images": output_images,
                    "mode": "simple",
                    "stdout": stdout_str
                }
            else:
                return {
                    "success": False,
                    "error": stderr_str or f"Exit code: {process.returncode}",
                    "mode": "simple"
                }

        except asyncio.TimeoutError:
            return {
                "success": False,
                "error": "Puppeteer 실행 타임아웃 (120초)",
                "mode": "simple"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "mode": "simple"
            }

    async def _run_advanced_mode(self, config: Dict) -> Dict:
        """
        상세 모드: 커스텀 이미지/텍스트로 오버레이

        Args:
            config: {
                "images": ["path/to/image_00.png", ...],
                "text_data": [{"slide": 1, "type": "cover", "title": "APPLE"}, ...],
                "output_dir": "output/apple_final/"
            }
        """
        images = config.get("images", [])
        text_data = config.get("text_data", [])
        output_dir = config.get("output_dir")
        topic = config.get("topic", "custom")

        if not images or not text_data:
            return {
                "success": False,
                "error": "images와 text_data 필수",
                "mode": "advanced"
            }

        # 출력 디렉토리 생성
        if output_dir:
            output_path = Path(output_dir)
        else:
            output_path = Path(__file__).parent.parent / "output" / f"{topic}_final"

        output_path.mkdir(parents=True, exist_ok=True)

        # 임시 텍스트 데이터 파일 생성
        temp_config_dir = Path(__file__).parent.parent / "config"
        temp_text_file = temp_config_dir / f"_temp_{topic}_text.json"

        try:
            # text_data를 JSON 파일로 저장
            with open(temp_text_file, 'w', encoding='utf-8') as f:
                json.dump(text_data, f, ensure_ascii=False, indent=2)

            # 이미지 심볼릭 링크 또는 복사 (임시)
            temp_image_dir = Path(__file__).parent.parent / "media_bank" / "instagram_ready" / f"_temp_{topic}"
            temp_image_dir.mkdir(parents=True, exist_ok=True)

            for i, img_path in enumerate(images):
                src = Path(img_path)
                if src.exists():
                    dst = temp_image_dir / f"{topic}_{i:02d}{src.suffix}"
                    if dst.exists():
                        dst.unlink()
                    # 심볼릭 링크 생성
                    dst.symlink_to(src.resolve())

            # Puppeteer 실행 (임시 topic 사용)
            result = await self._run_simple_mode(f"_temp_{topic}")

            if result["success"]:
                # 출력 파일을 최종 위치로 이동
                temp_output = Path(__file__).parent.parent / "images" / f"_temp_{topic}"
                final_images = []

                if temp_output.exists():
                    for i, f in enumerate(sorted(os.listdir(temp_output))):
                        if f.endswith('.png'):
                            src = temp_output / f
                            dst = output_path / f"{topic}_{i:02d}.png"
                            src.rename(dst)
                            final_images.append(str(dst))

                return {
                    "success": True,
                    "count": len(final_images),
                    "output_dir": str(output_path),
                    "output_images": final_images,
                    "mode": "advanced"
                }
            else:
                return result

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "mode": "advanced"
            }
        finally:
            # 임시 파일 정리
            if temp_text_file.exists():
                temp_text_file.unlink()
            if temp_image_dir.exists():
                import shutil
                shutil.rmtree(temp_image_dir, ignore_errors=True)
