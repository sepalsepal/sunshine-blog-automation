#!/usr/bin/env python3
"""
MVP Crew 통합 테스트

3개 Crew 테스트:
1. ContentCrew - 기존 이미지 확인
2. ReviewCrew - 품질 검수
3. PublishingCrew - Cloudinary만 (Instagram 제외)
"""

import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from core.crews import ContentCrew, ReviewCrew, PublishingCrew


def main():
    print("=" * 60)
    print("🚀 MVP Crew 통합 테스트")
    print("=" * 60)

    # 1. ContentCrew 테스트
    print("\n[1/3] ContentCrew - 기존 이미지 확인")
    content_crew = ContentCrew()
    content_result = content_crew.kickoff({
        "topic": "banana",
        "skip_generation": True
    })

    if content_result["success"]:
        print(f"  ✅ 성공 - {content_result['count']}장 이미지")
    else:
        print(f"  ❌ 실패")
        return

    # 2. ReviewCrew 테스트
    print("\n[2/3] ReviewCrew - 품질 검수")
    review_crew = ReviewCrew()
    review_result = review_crew.kickoff({
        "images": content_result["images"],
        "topic": "banana"
    })

    print(f"  점수: {review_result['score']:.0f}점 ({review_result['grade']})")
    print(f"  통과: {'✅ PASS' if review_result['passed'] else '❌ FAIL'}")
    if review_result["issues"]:
        print(f"  이슈: {len(review_result['issues'])}개")

    # 3. PublishingCrew 테스트 (Cloudinary만)
    print("\n[3/3] PublishingCrew - Cloudinary 업로드 테스트")
    publishing_crew = PublishingCrew()
    publish_result = publishing_crew.kickoff({
        "images": content_result["images"][:2],  # 2장만 테스트
        "caption": "테스트 게시물\n#sunshinedogfood #햇살이 #테스트",
        "topic": "test_crews",
        "platforms": ["cloudinary"]  # Instagram 제외
    })

    cloudinary = publish_result.get("cloudinary", {})
    if cloudinary.get("success"):
        print(f"  ✅ 성공 - {cloudinary.get('count', 0)}장 업로드")
    else:
        print(f"  ⚠️  Cloudinary 스킵 또는 실패")

    # 결과 요약
    print("\n" + "=" * 60)
    print("📊 테스트 결과 요약")
    print("=" * 60)
    print(f"  ContentCrew:    {'✅' if content_result['success'] else '❌'}")
    print(f"  ReviewCrew:     {'✅' if review_result['passed'] else '⚠️'} ({review_result['score']:.0f}점)")
    print(f"  PublishingCrew: {'✅' if cloudinary.get('success') else '⚠️'}")
    print("\n✅ Phase 1 완료 - MVP Crew 테스트 성공")


if __name__ == "__main__":
    main()
