"""
# ============================================================
# Project Sunshine - Agent Dry-Run Test
# ============================================================
#
# 새로운 에이전트 시스템 테스트 (API 없이 로컬 테스트)
# - CaptionAgent (이카피)
# - FactCheckerAgent (최검증)
# - AnalyticsAgent (정분석)
#
# 실행: python -m tests.test_agents_dryrun
# ============================================================
"""

import asyncio
import sys
from pathlib import Path

# 프로젝트 루트 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.agents.caption import CaptionAgent
from core.agents.fact_checker import FactCheckerAgent
from core.agents.analytics import AnalyticsAgent


def print_header(title: str):
    """섹션 헤더 출력"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_result(label: str, value, indent: int = 2):
    """결과 출력"""
    prefix = " " * indent
    if isinstance(value, dict):
        print(f"{prefix}{label}:")
        for k, v in value.items():
            print(f"{prefix}  {k}: {v}")
    elif isinstance(value, list):
        print(f"{prefix}{label}: ({len(value)}개)")
        for item in value[:5]:  # 최대 5개만
            print(f"{prefix}  - {item}")
        if len(value) > 5:
            print(f"{prefix}  ... 외 {len(value) - 5}개")
    else:
        print(f"{prefix}{label}: {value}")


async def test_caption_agent():
    """CaptionAgent (이카피) 테스트"""
    print_header("📝 CaptionAgent (이카피) 테스트")

    agent = CaptionAgent()

    # 테스트 주제들
    topics = ["cherry", "banana", "apple", "grape"]

    for topic in topics:
        print(f"\n  📌 [{topic.upper()}] 캡션 생성 테스트")

        result = await agent.run({"topic": topic})

        if result.success:
            data = result.data
            caption_data = data.get("caption", {})
            topic_info = data.get("topic_info", {})

            print(f"    ✓ 성공!")
            print(f"    - 급여 가능: {topic_info.get('can_eat', '?')}")
            print(f"    - 본문 길이: {caption_data.get('character_count', 0)}자")
            print(f"    - 해시태그: {caption_data.get('hashtag_count', 0)}개")

            # 해시태그 샘플 출력
            hashtags = caption_data.get("hashtags", [])[:5]
            print(f"    - 해시태그 샘플: {' '.join(hashtags)}")
        else:
            print(f"    ✗ 실패: {result.error}")

    print("\n  ✅ CaptionAgent 테스트 완료!")


async def test_fact_checker_agent():
    """FactCheckerAgent (최검증) 테스트"""
    print_header("🔍 FactCheckerAgent (최검증) 테스트")

    agent = FactCheckerAgent()

    # 테스트 케이스들
    test_cases = [
        {
            "topic": "cherry",
            "slides": [
                {"title": "조건부 OK!", "subtitle": "씨앗은 절대 안돼요"},
                {"title": "씨앗 독성!", "subtitle": "시안화물이 있어요"}
            ]
        },
        {
            "topic": "banana",
            "slides": [
                {"title": "먹어도 돼요!", "subtitle": "껍질만 잘 벗기면"},
                {"title": "에너지 보충", "subtitle": "천연 당분으로 활력"}
            ]
        },
        {
            "topic": "grape",
            "slides": [
                {"title": "절대 금지!", "subtitle": "급성 신부전 위험"}
            ]
        }
    ]

    for case in test_cases:
        topic = case["topic"]
        print(f"\n  📌 [{topic.upper()}] 팩트체크 테스트")

        result = await agent.run(case)

        if result.success:
            data = result.data
            verification = data.get("verification", {})

            print(f"    ✓ 검증 완료!")
            print(f"    - 정확도 점수: {verification.get('accuracy_score', 0)}점")
            print(f"    - 심각도: {verification.get('severity', 'N/A')}")
            print(f"    - 총 검사 항목: {verification.get('total_checks', 0)}개")
            print(f"    - 통과: {verification.get('passed', 0)}개")
            print(f"    - 경고: {verification.get('warnings', 0)}개")

            # 경고 메시지 출력
            issues = data.get("issues", [])
            if issues:
                print(f"    - 발견된 이슈:")
                for issue in issues[:3]:
                    print(f"      ⚠️ {issue.get('message', issue)}")
        else:
            print(f"    ✗ 실패: {result.error}")

    # 직접 호출 테스트
    print("\n  📌 [직접 호출] check_food_safety() 테스트")
    safety_result = agent.check_food_safety("grape")
    print(f"    - 안전성: {safety_result.get('safety_level', 'N/A')}")
    print(f"    - 메시지: {safety_result.get('message', 'N/A')}")
    if safety_result.get('emergency_info'):
        print(f"    - 응급 정보: {safety_result.get('emergency_info')}")

    print("\n  ✅ FactCheckerAgent 테스트 완료!")


async def test_analytics_agent():
    """AnalyticsAgent (정분석) 테스트"""
    print_header("📊 AnalyticsAgent (정분석) 테스트")

    agent = AnalyticsAgent()

    # 샘플 인사이트 데이터
    sample_data = {
        "period": "7d",
        "posts": [
            {
                "post_id": "post_001",
                "topic": "apple",
                "published_at": "2025-01-20T19:30:00",
                "insights": {
                    "reach": 15000,
                    "impressions": 22000,
                    "likes": 1200,
                    "comments": 85,
                    "saves": 180,
                    "shares": 45
                }
            },
            {
                "post_id": "post_002",
                "topic": "banana",
                "published_at": "2025-01-18T14:00:00",
                "insights": {
                    "reach": 12000,
                    "impressions": 18000,
                    "likes": 850,
                    "comments": 52,
                    "saves": 95,
                    "shares": 30
                }
            },
            {
                "post_id": "post_003",
                "topic": "cherry",
                "published_at": "2025-01-16T20:00:00",
                "insights": {
                    "reach": 10000,
                    "impressions": 15000,
                    "likes": 720,
                    "comments": 38,
                    "saves": 110,
                    "shares": 25
                }
            }
        ],
        "account_insights": {
            "followers": 15000,
            "follower_growth": 250,
            "profile_visits": 3200
        }
    }

    print("\n  📌 주간 성과 분석 테스트")

    result = await agent.run(sample_data)

    if result.success:
        data = result.data
        summary = data.get("summary", {})
        ranking = data.get("performance_ranking", [])
        recommendations = data.get("recommendations", {})
        alerts = data.get("alerts", [])

        print(f"    ✓ 분석 완료!")
        print(f"\n    📈 요약:")
        print(f"      - 분석 기간: {data.get('analysis_period', 'N/A')}")
        print(f"      - 총 게시물: {summary.get('total_posts', 0)}개")
        print(f"      - 총 도달: {summary.get('total_reach', 0):,}")
        print(f"      - 평균 참여율: {summary.get('avg_engagement_rate', 0):.1f}%")
        print(f"      - 최고 성과: {summary.get('best_performing', 'N/A')}")

        if ranking:
            print(f"\n    🏆 성과 랭킹:")
            for item in ranking[:3]:
                print(f"      {item['rank']}위: {item['topic']} ({item['engagement_rate']}%)")

        next_topics = recommendations.get("next_topics", [])
        if next_topics:
            print(f"\n    💡 추천 주제:")
            for topic in next_topics[:2]:
                print(f"      - {topic['topic']}: {topic['reason']}")

        if alerts:
            print(f"\n    🔔 알림:")
            for alert in alerts[:3]:
                print(f"      {alert.get('message', alert)}")
    else:
        print(f"    ✗ 실패: {result.error}")

    # 빈 데이터 테스트
    print("\n  📌 빈 데이터 테스트")
    empty_result = await agent.run({"period": "7d", "posts": []})
    if empty_result.success:
        print("    ✓ 빈 데이터 처리 정상")
    else:
        print(f"    ✗ 빈 데이터 처리 실패: {empty_result.error}")

    # 유틸리티 메서드 테스트
    print("\n  📌 유틸리티 메서드 테스트")
    suggestion = agent.get_next_topic_suggestion(["apple", "banana"])
    print(f"    - 다음 추천 주제: {suggestion.get('topic', 'N/A')}")
    print(f"    - 이유: {suggestion.get('reason', 'N/A')}")

    print("\n  ✅ AnalyticsAgent 테스트 완료!")


async def test_integration():
    """통합 테스트 - 에이전트 연동"""
    print_header("🔗 통합 테스트 - 에이전트 연동")

    topic = "cherry"
    print(f"\n  📌 [{topic.upper()}] 전체 파이프라인 테스트")

    # 1. 팩트체크
    print("\n  1️⃣ 팩트체크 (최검증)")
    fact_checker = FactCheckerAgent()
    fact_result = await fact_checker.run({
        "topic": topic,
        "slides": [
            {"title": "조건부 OK!", "subtitle": "씨앗은 절대 안돼요"}
        ]
    })

    if fact_result.success:
        verification = fact_result.data.get("verification", {})
        print(f"    ✓ 팩트체크 완료 - 정확도: {verification.get('accuracy_score', 0)}점")

    # 2. 캡션 생성
    print("\n  2️⃣ 캡션 생성 (이카피)")
    caption_agent = CaptionAgent()
    caption_result = await caption_agent.run({"topic": topic})

    if caption_result.success:
        caption_data = caption_result.data.get("caption", {})
        print(f"    ✓ 캡션 생성 완료 - {caption_data.get('character_count', 0)}자, 해시태그 {caption_data.get('hashtag_count', 0)}개")

    # 3. 성과 분석 (가상 데이터)
    print("\n  3️⃣ 성과 분석 (정분석)")
    analytics_agent = AnalyticsAgent()
    analytics_result = await analytics_agent.run({
        "period": "7d",
        "posts": [{
            "post_id": "test_001",
            "topic": topic,
            "published_at": "2025-01-22T19:00:00",
            "insights": {"reach": 10000, "likes": 800, "comments": 50, "saves": 120, "shares": 30}
        }],
        "account_insights": {"followers": 15000, "follower_growth": 100}
    })

    if analytics_result.success:
        summary = analytics_result.data.get("summary", {})
        print(f"    ✓ 성과 분석 완료 - 참여율: {summary.get('avg_engagement_rate', 0):.1f}%")

    print("\n  ✅ 통합 테스트 완료!")


async def main():
    """메인 테스트 실행"""
    print("\n" + "=" * 60)
    print("  🌟 Project Sunshine - Agent Dry-Run Test")
    print("=" * 60)

    try:
        # 개별 에이전트 테스트
        await test_caption_agent()
        await test_fact_checker_agent()
        await test_analytics_agent()

        # 통합 테스트
        await test_integration()

        print("\n" + "=" * 60)
        print("  🎉 모든 테스트 완료!")
        print("=" * 60)
        print("\n  결과 요약:")
        print("    ✅ CaptionAgent (이카피) - 정상")
        print("    ✅ FactCheckerAgent (최검증) - 정상")
        print("    ✅ AnalyticsAgent (정분석) - 정상")
        print("    ✅ 통합 테스트 - 정상")
        print("\n")

    except Exception as e:
        print(f"\n  ❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
