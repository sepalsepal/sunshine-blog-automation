#!/usr/bin/env python3
"""
브로콜리 v1.0 품질 검수 실행
"""

import asyncio
import sys
from pathlib import Path
from glob import glob

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from core.agents.quality_checker_v8 import QualityCheckerV8Agent


async def main():
    print("━" * 60)
    print("🔍 브로콜리 v1.0 품질 검수")
    print("━" * 60)

    output_dir = ROOT / "outputs" / "broccoli_v8_final"

    # 최종 렌더링된 이미지 수집 (broccoli_XX_type.png)
    images = sorted(glob(str(output_dir / "broccoli_0*.png")))

    print(f"\n검수 대상: {len(images)}개 이미지")
    for img in images:
        print(f"  - {Path(img).name}")

    checker = QualityCheckerV8Agent()

    result = await checker.run({
        "images": images,
        "topic": "broccoli"
    })

    print("\n" + "━" * 60)
    print("📊 검수 결과")
    print("━" * 60)

    report = result.data.get("report", {})

    print(f"\n총점: {report.get('total_score', 0):.0f}점 / 등급: {report.get('grade', '-')}")
    print(f"판정: {'✅ PASS' if result.data.get('passed') else '❌ FAIL'}")

    print("\n카테고리별 점수:")
    for cat in report.get("details", []):
        status = "✅" if cat["score"] >= cat["max_score"] * 0.7 else "⚠️"
        print(f"  {status} {cat['category']}: {cat['score']:.0f}/{cat['max_score']}점")
        if cat.get("issues"):
            for issue in cat["issues"]:
                print(f"      - {issue}")

    print("\n" + "━" * 60)


if __name__ == "__main__":
    asyncio.run(main())
