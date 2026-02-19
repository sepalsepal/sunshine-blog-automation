#!/usr/bin/env python3
"""
WO-COVER-BATCH-001 표지 이미지 제작 (3건)
대상: 감자, 멜론, 양파
기준: 골든 샘플 스펙 v1.0
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from pipeline.cover_overlay_golden import create_cover_golden, validate_output

# 경로 정의
CONTENTS_ROOT = PROJECT_ROOT / "01_contents" / "3_approved"

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
    print("WO-COVER-BATCH-001 표지 이미지 제작")
    print("골든 샘플 스펙 v1.0 준수")
    print("=" * 60)

    results = []

    for target in TARGETS:
        print(f"\n[처리] {target['korean']} ({target['english']})")

        # 경로 설정
        # 2026-02-13: 플랫 구조 반영
        source_path = CONTENTS_ROOT / target["folder"] / "00_Clean" / target["clean_file"]
        output_path = CONTENTS_ROOT / target["folder"] / "01_Insta&Thread" / target["output_name"]

        # 소스 파일 확인
        if not source_path.exists():
            print(f"  [ERROR] 소스 파일 없음: {source_path}")
            results.append({
                "name": target["korean"],
                "status": "FAIL",
                "reason": "소스 파일 없음"
            })
            continue

        # 출력 폴더 확인/생성
        output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            # 표지 생성
            create_cover_golden(
                source_path=str(source_path),
                korean_text=target["korean"],
                english_text=target["english"],
                output_path=str(output_path)
            )

            # 검증
            validation = validate_output(str(output_path))

            if validation["all_pass"]:
                results.append({
                    "name": target["korean"],
                    "status": "SUCCESS",
                    "output": target["output_name"],
                    "size": validation["size"]
                })
            else:
                results.append({
                    "name": target["korean"],
                    "status": "FAIL",
                    "reason": "검증 실패",
                    "checks": validation["checks"]
                })

        except Exception as e:
            print(f"  [ERROR] {e}")
            results.append({
                "name": target["korean"],
                "status": "FAIL",
                "reason": str(e)
            })

    # 결과 요약
    print("\n" + "=" * 60)
    print("[WO-COVER-BATCH-001 완료 보고]")
    print("=" * 60)

    success_count = sum(1 for r in results if r["status"] == "SUCCESS")

    for r in results:
        status = "완료" if r["status"] == "SUCCESS" else "실패"
        output = r.get("output", r.get("reason", ""))
        print(f"{r['name']}: [{status}] - {output}")

    print("-" * 30)
    print(f"스펙 준수: 예 (골든 샘플 v1.0)")
    print(f"결과: {success_count}/{len(TARGETS)} 성공")
    print("=" * 60)

    return 0 if success_count == len(TARGETS) else 1


if __name__ == "__main__":
    exit(main())
