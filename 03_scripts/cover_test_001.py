#!/usr/bin/env python3
"""
WO-COVER-TEST-001 표지 제작 테스트
대상: 감자, 멜론, 양파
스펙: 골든 샘플 v1.1
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from pipeline.cover_overlay_golden import create_cover_golden
from pipeline.cover_inspector import inspect_cover, generate_inspection_report

# 경로 정의
CONTENTS_ROOT = PROJECT_ROOT / "01_contents" / "3_approved"
REPORT_DIR = PROJECT_ROOT / "logs" / "cover_test" / "20260212"

# 대상 콘텐츠
TARGETS = [
    {
        "folder": "035_potato_감자",
        "korean": "감자",
        "english": "Potato",
        "clean_file": "hf_20260211_041041_56e27027-c4ab-4c9f-a10e-129e63e1f725.png",
        "output_name": "potato_cover.png"
    },
    {
        "folder": "043_melon_멜론",
        "korean": "멜론",
        "english": "Melon",
        "clean_file": "hf_20260211_041520_dd6de7bb-fad2-4aec-ba19-38c04539d0ce.png",
        "output_name": "melon_cover.png"
    },
    {
        "folder": "051_onion_양파",
        "korean": "양파",
        "english": "Onion",
        "clean_file": "hf_20260211_041524_2ece4ab5-6942-45fe-8f8c-a1d8c44ddcdf.png",
        "output_name": "onion_cover.png"
    }
]


def main():
    print("=" * 60)
    print("WO-COVER-TEST-001 표지 제작 테스트")
    print("스펙: 골든 샘플 v1.1")
    print("=" * 60)

    inspection_results = []

    for target in TARGETS:
        print(f"\n[STEP 1] 제작: {target['korean']} ({target['english']})")

        # 경로 설정
        source_path = CONTENTS_ROOT / target["folder"] / "00_Clean" / target["clean_file"]
        output_path = CONTENTS_ROOT / target["folder"] / target["output_name"]

        # 소스 파일 확인
        if not source_path.exists():
            print(f"  [ERROR] 소스 파일 없음: {source_path}")
            continue

        try:
            # 표지 생성
            create_cover_golden(
                source_path=str(source_path),
                korean_text=target["korean"],
                english_text=target["english"],
                output_path=str(output_path)
            )
            print(f"  → 제작 완료: {output_path.name}")

            # [STEP 2] 검수
            print(f"\n[STEP 2] 검수: cover_inspector.py 실행")
            result = inspect_cover(
                cover_path=str(output_path),
                english_name=target["english"],
                korean_name=target["korean"]
            )
            inspection_results.append(result)

            verdict = result["final_verdict"]
            similarity = result["checks"]["similarity"]["percent"]
            print(f"  → 유사도: {similarity}%, 판정: {verdict}")

        except Exception as e:
            print(f"  [ERROR] {e}")
            inspection_results.append({
                "cover_path": str(output_path),
                "english_name": target["english"].upper(),
                "korean_name": target["korean"],
                "error": str(e),
                "final_verdict": "FAIL"
            })

    # [STEP 3] 검수 리포트 생성
    print("\n" + "=" * 60)
    print("[STEP 3] 검수 리포트 생성")
    print("=" * 60)

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report_path = REPORT_DIR / "inspection_report.txt"
    report = generate_inspection_report(inspection_results, str(report_path))
    print(report)
    print(f"\n리포트 저장: {report_path}")

    # 결과 요약
    pass_count = sum(1 for r in inspection_results if r.get("final_verdict") == "PASS")
    fail_count = len(inspection_results) - pass_count

    print("\n" + "=" * 60)
    print(f"결과: {pass_count}건 PASS / {fail_count}건 FAIL")
    print("=" * 60)

    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    exit(main())
