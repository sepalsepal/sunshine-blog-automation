"""
ReviewCrew - 품질 검수 Crew
기존 QualityCheckerAgent를 래핑 (CrewAI 인터페이스 호환)
"""

import asyncio
from pathlib import Path
import sys

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from core.agents.quality_checker import QualityCheckerAgent


class ReviewCrew:
    """
    품질 검수 Crew

    기존 QualityCheckerAgent(박과장)의 로직을 재사용
    85점 이상이면 통과

    CrewAI kickoff() 인터페이스 호환
    """

    def __init__(self):
        self.quality_checker = QualityCheckerAgent()

    def run(self, images: list, topic: str = "unknown") -> dict:
        """
        검수 실행

        Args:
            images: 이미지 경로 리스트 또는 {"path": "..."} 딕셔너리 리스트
            topic: 주제명

        Returns:
            {
                "passed": bool,
                "score": float,
                "grade": str,
                "issues": list,
                "report": dict
            }
        """
        # 기존 에이전트 실행 (async)
        result = asyncio.run(self.quality_checker.run({
            "images": images,
            "topic": topic
        }))

        if result.success:
            report = result.data.get("report", {})
            return {
                "passed": result.data.get("passed", False),
                "score": report.get("total_score", 0),
                "grade": report.get("grade", "D"),
                "issues": report.get("issues", []),
                "report": report
            }
        else:
            return {
                "passed": False,
                "score": 0,
                "grade": "F",
                "issues": [result.error],
                "report": {}
            }

    def kickoff(self, inputs: dict) -> dict:
        """
        CrewAI 스타일 실행

        Args:
            inputs: {"images": [...], "topic": "..."}
        """
        return self.run(
            images=inputs.get("images", []),
            topic=inputs.get("topic", "unknown")
        )


# 테스트용
if __name__ == "__main__":
    crew = ReviewCrew()

    # 테스트 데이터
    test_images = [
        str(ROOT / "outputs" / "banana_v8_final" / f"banana_0{i}_content.png")
        for i in range(5)
    ]
    test_images.insert(0, str(ROOT / "outputs" / "banana_v8_final" / "banana_00_cover.png"))

    result = crew.kickoff({
        "images": test_images,
        "topic": "banana"
    })

    print(f"점수: {result['score']}")
    print(f"등급: {result['grade']}")
    print(f"통과: {result['passed']}")
    if result['issues']:
        print(f"이슈: {result['issues']}")
