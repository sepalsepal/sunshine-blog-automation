"""
PublishingCrew - 게시 Crew
기존 PublisherAgent를 래핑 (CrewAI 인터페이스 호환)
"""

import asyncio
from pathlib import Path
import sys

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

from core.agents.publisher import PublisherAgent


class PublishingCrew:
    """
    게시 Crew

    기존 PublisherAgent(김대리)의 로직을 재사용
    Cloudinary 업로드 + Instagram 게시

    CrewAI kickoff() 인터페이스 호환
    """

    def __init__(self):
        self.publisher = PublisherAgent()

    def run(
        self,
        images: list,
        caption: str,
        topic: str = "unknown",
        platforms: list = None
    ) -> dict:
        """
        게시 실행

        Args:
            images: 이미지 경로 리스트
            caption: 게시물 캡션
            topic: 주제명
            platforms: 게시할 플랫폼 리스트 (기본: cloudinary, instagram)

        Returns:
            {
                "success": bool,
                "post_id": str,
                "permalink": str,
                "error": str (실패시)
            }
        """
        if platforms is None:
            platforms = ["cloudinary", "instagram"]

        # config 설정
        self.publisher.config["instagram"] = {"caption_template": caption}
        self.publisher.config["platforms"] = platforms

        # 이미지 형식 변환
        if images and isinstance(images[0], str):
            images_with_paths = [{"path": p, "type": "content"} for p in images]
            # 첫 번째는 커버로 표시
            if images_with_paths:
                images_with_paths[0]["type"] = "cover"
        else:
            images_with_paths = images

        # 기존 에이전트 실행 (async)
        result = asyncio.run(self.publisher.run({
            "images": images_with_paths,
            "topic": topic,
            "passed": True  # 검수 통과 가정
        }))

        if result.success:
            publish_results = result.data.get("publish_results", {})
            ig_result = publish_results.get("instagram", {})

            return {
                "success": ig_result.get("success", False),
                "post_id": ig_result.get("post_id", ""),
                "permalink": ig_result.get("permalink", ""),
                "cloudinary": publish_results.get("cloudinary", {}),
                "simulated": ig_result.get("simulated", False)
            }
        else:
            return {
                "success": False,
                "post_id": "",
                "permalink": "",
                "error": result.error
            }

    def kickoff(self, inputs: dict) -> dict:
        """
        CrewAI 스타일 실행

        Args:
            inputs: {
                "images": [...],
                "caption": "...",
                "topic": "...",
                "platforms": [...]  # optional
            }
        """
        return self.run(
            images=inputs.get("images", []),
            caption=inputs.get("caption", ""),
            topic=inputs.get("topic", "unknown"),
            platforms=inputs.get("platforms")
        )


# 테스트용
if __name__ == "__main__":
    crew = PublishingCrew()

    # 테스트 (dry-run용)
    test_images = [
        str(ROOT / "outputs" / "banana_v8_final" / "banana_00_cover.png"),
        str(ROOT / "outputs" / "banana_v8_final" / "banana_01_content.png"),
    ]

    test_caption = """테스트 게시물

#sunshinedogfood #햇살이 #테스트"""

    # Cloudinary만 테스트 (Instagram 실제 게시 안 함)
    result = crew.kickoff({
        "images": test_images,
        "caption": test_caption,
        "topic": "test",
        "platforms": ["cloudinary"]  # Instagram 제외
    })

    print(f"성공: {result['success']}")
    if result.get('cloudinary', {}).get('success'):
        print(f"Cloudinary 업로드: {result['cloudinary'].get('count')}장")
