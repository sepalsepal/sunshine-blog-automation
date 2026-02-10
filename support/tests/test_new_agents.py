"""
Test Suite for New Agents
Project Sunshine Test System

테스트 대상:
- SchedulerAgent
- MultiPlatformAgent
- RetryAgent
- TrendAgent
- TemplateAgent
"""

import asyncio
import json
import pytest
from datetime import datetime, timedelta
from pathlib import Path
import sys

# 프로젝트 루트 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.agents.scheduler import SchedulerAgent
from core.agents.multi_platform import MultiPlatformAgent, Platform
from core.agents.retry import RetryAgent, FailureType, RetryStrategy
from core.agents.trend import TrendAgent
from core.agents.template import TemplateAgent


class TestSchedulerAgent:
    """SchedulerAgent 테스트"""

    @pytest.fixture
    def agent(self):
        return SchedulerAgent()

    def test_name(self, agent):
        """에이전트 이름 확인"""
        assert agent.name == "SchedulerAgent"

    def test_get_optimal_time(self, agent):
        """최적 포스팅 시간 계산 테스트"""
        optimal_time = agent.get_optimal_time(category="fruit")
        assert isinstance(optimal_time, datetime)
        assert optimal_time >= datetime.now(optimal_time.tzinfo)

    def test_generate_weekly_schedule(self, agent):
        """주간 스케줄 생성 테스트"""
        topics = ["banana", "cherry", "apple"]
        schedule = agent.generate_weekly_schedule(topics, posts_per_day=1)

        assert len(schedule) >= len(topics)
        for item in schedule:
            assert "topic" in item
            assert "scheduled_time" in item
            assert "status" in item

    @pytest.mark.asyncio
    async def test_execute_generate_schedule(self, agent):
        """스케줄 생성 실행 테스트"""
        result = await agent.run({
            "action": "generate_schedule",
            "topics": ["banana", "watermelon"],
            "posts_per_day": 1
        })

        assert result.success
        assert "schedule" in result.data

    @pytest.mark.asyncio
    async def test_execute_add_to_queue(self, agent):
        """큐 추가 테스트"""
        result = await agent.run({
            "action": "add_to_queue",
            "topic": "test_topic",
            "category": "fruit"
        })

        assert result.success
        assert result.data["topic"] == "test_topic"

    @pytest.mark.asyncio
    async def test_execute_get_status(self, agent):
        """상태 조회 테스트"""
        result = await agent.run({"action": "get_status"})

        assert result.success
        assert "total" in result.data


class TestMultiPlatformAgent:
    """MultiPlatformAgent 테스트"""

    @pytest.fixture
    def agent(self):
        return MultiPlatformAgent()

    def test_name(self, agent):
        """에이전트 이름 확인"""
        assert agent.name == "MultiPlatformAgent"

    def test_platform_limits(self, agent):
        """플랫폼 제한 확인"""
        assert Platform.INSTAGRAM in agent.PLATFORM_LIMITS
        assert Platform.TWITTER in agent.PLATFORM_LIMITS

        instagram_limits = agent.PLATFORM_LIMITS[Platform.INSTAGRAM]
        assert instagram_limits["max_caption_length"] == 2200
        assert instagram_limits["max_hashtags"] == 30

    def test_adapt_content_for_twitter(self, agent):
        """트위터 콘텐츠 적응 테스트"""
        adapted = agent.adapt_content_for_platform(
            platform=Platform.TWITTER,
            caption="Test caption " * 50,  # 긴 캡션
            hashtags=["tag1", "tag2", "tag3", "tag4", "tag5", "tag6"],
            images=["img1.jpg", "img2.jpg", "img3.jpg", "img4.jpg", "img5.jpg"]
        )

        assert adapted["platform"] == "twitter"
        assert len(adapted["images"]) <= 4  # 트위터 이미지 제한
        assert adapted["optimized"] is True

    def test_validate_platform_requirements(self, agent):
        """플랫폼 요구사항 검증 테스트"""
        content = {
            "caption": "Short caption",
            "hashtags": ["tag1", "tag2"],
            "images": ["img1.jpg"]
        }

        validation = agent.validate_platform_requirements(Platform.INSTAGRAM, content)
        assert validation["valid"] is True

    @pytest.mark.asyncio
    async def test_execute_status(self, agent):
        """플랫폼 상태 조회 테스트"""
        result = await agent.run({"action": "status"})

        assert result.success
        assert "instagram" in result.data

    @pytest.mark.asyncio
    async def test_execute_adapt(self, agent):
        """콘텐츠 적응 테스트"""
        result = await agent.run({
            "action": "adapt",
            "platform": "instagram",
            "content": {
                "caption": "Test",
                "hashtags": ["test"],
                "images": ["test.jpg"]
            }
        })

        assert result.success
        assert result.data["platform"] == "instagram"


class TestRetryAgent:
    """RetryAgent 테스트"""

    @pytest.fixture
    def agent(self):
        return RetryAgent()

    def test_name(self, agent):
        """에이전트 이름 확인"""
        assert agent.name == "RetryAgent"

    def test_classify_failure_network(self, agent):
        """네트워크 에러 분류 테스트"""
        failure = agent.classify_failure("Connection refused: network unreachable")
        assert failure == FailureType.NETWORK

    def test_classify_failure_rate_limit(self, agent):
        """Rate limit 에러 분류 테스트"""
        failure = agent.classify_failure("429 Too Many Requests")
        assert failure == FailureType.API_RATE_LIMIT

    def test_classify_failure_auth(self, agent):
        """인증 에러 분류 테스트"""
        failure = agent.classify_failure("401 Unauthorized")
        assert failure == FailureType.AUTH

    def test_calculate_delay_exponential(self, agent):
        """지수 백오프 계산 테스트"""
        delay1 = agent.calculate_delay(RetryStrategy.EXPONENTIAL, 1, 1.0, 60.0)
        delay2 = agent.calculate_delay(RetryStrategy.EXPONENTIAL, 2, 1.0, 60.0)
        delay3 = agent.calculate_delay(RetryStrategy.EXPONENTIAL, 3, 1.0, 60.0)

        assert delay1 == 1.0
        assert delay2 == 2.0
        assert delay3 == 4.0

    def test_is_recoverable(self, agent):
        """복구 가능 여부 테스트"""
        assert agent.is_recoverable(FailureType.NETWORK) is True
        assert agent.is_recoverable(FailureType.AUTH) is False
        assert agent.is_recoverable(FailureType.VALIDATION) is False

    @pytest.mark.asyncio
    async def test_execute_add_failure(self, agent):
        """실패 작업 등록 테스트"""
        result = await agent.run({
            "action": "add",
            "task_id": "test_001",
            "task_type": "post",
            "error": "Connection timeout"
        })

        assert result.success
        assert result.data["failure_type"] == "network"

    @pytest.mark.asyncio
    async def test_execute_stats(self, agent):
        """통계 조회 테스트"""
        result = await agent.run({"action": "stats"})

        assert result.success
        assert "total_failures" in result.data


class TestTrendAgent:
    """TrendAgent 테스트"""

    @pytest.fixture
    def agent(self):
        return TrendAgent()

    def test_name(self, agent):
        """에이전트 이름 확인"""
        assert agent.name == "TrendAgent"

    def test_get_current_season(self, agent):
        """현재 계절 확인"""
        season = agent.get_current_season()
        assert season in ["spring", "summer", "autumn", "winter"]

    def test_get_seasonal_recommendations(self, agent):
        """계절 추천 테스트"""
        recs = agent.get_seasonal_recommendations()

        assert "season" in recs
        assert "theme" in recs
        assert "recommended_foods" in recs

    def test_get_upcoming_events(self, agent):
        """다가오는 이벤트 테스트"""
        events = agent.get_upcoming_events(days_ahead=365)
        # 1년 안에 적어도 몇 개의 이벤트가 있어야 함
        assert len(events) > 0

    def test_calculate_topic_score(self, agent):
        """주제 점수 계산 테스트"""
        score = agent.calculate_topic_score("banana")

        assert "topic" in score
        assert "score" in score
        assert "factors" in score
        assert 0 <= score["score"] <= 100

    def test_get_trending_hashtags(self, agent):
        """트렌딩 해시태그 테스트"""
        hashtags = agent.get_trending_hashtags("food", limit=5)

        assert len(hashtags) <= 5
        assert all(isinstance(tag, str) for tag in hashtags)

    @pytest.mark.asyncio
    async def test_execute_seasonal(self, agent):
        """계절 추천 실행 테스트"""
        result = await agent.run({"action": "seasonal"})

        assert result.success
        assert "season" in result.data

    @pytest.mark.asyncio
    async def test_execute_recommend(self, agent):
        """콘텐츠 추천 실행 테스트"""
        result = await agent.run({
            "action": "recommend",
            "topics": ["banana", "cherry", "watermelon"],
            "count": 3
        })

        assert result.success
        assert "recommendations" in result.data

    @pytest.mark.asyncio
    async def test_execute_plan(self, agent):
        """주간 계획 실행 테스트"""
        result = await agent.run({
            "action": "plan",
            "topics": ["banana", "cherry", "apple", "carrot", "chicken", "salmon", "egg"]
        })

        assert result.success
        assert "weekly_plan" in result.data
        assert len(result.data["weekly_plan"]) == 7


class TestTemplateAgent:
    """TemplateAgent 테스트"""

    @pytest.fixture
    def agent(self):
        return TemplateAgent()

    def test_name(self, agent):
        """에이전트 이름 확인"""
        assert agent.name == "TemplateAgent"

    def test_get_base_template(self, agent):
        """기본 템플릿 조회 테스트"""
        template = agent.get_base_template()

        assert template["slide_count"] == 10
        assert len(template["structure"]) == 10

    def test_get_category_style(self, agent):
        """카테고리 스타일 테스트"""
        style = agent.get_category_style("fruit")

        assert "emoji_style" in style
        assert "color_theme" in style
        assert "tone" in style

    def test_create_text_data_template(self, agent):
        """텍스트 데이터 템플릿 생성 테스트"""
        template = agent.create_text_data_template(
            topic="banana",
            topic_kr="바나나",
            category="fruit",
            is_safe=True
        )

        assert len(template) == 10
        assert template[0]["type"] == "cover"
        assert template[-1]["type"] == "cta"

    def test_validate_text_data(self, agent):
        """텍스트 데이터 검증 테스트"""
        valid_data = [
            {"slide": i, "type": "content_bottom", "title": f"Title {i}", "subtitle": f"Sub {i}"}
            for i in range(1, 11)
        ]
        valid_data[0]["type"] = "cover"
        valid_data[-1]["type"] = "cta"

        validation = agent.validate_text_data(valid_data)
        assert validation["valid"] is True

    def test_validate_text_data_invalid(self, agent):
        """잘못된 텍스트 데이터 검증 테스트"""
        invalid_data = [{"slide": 1, "type": "cover"}]  # 9장 부족

        validation = agent.validate_text_data(invalid_data)
        assert validation["valid"] is False
        assert len(validation["issues"]) > 0

    @pytest.mark.asyncio
    async def test_execute_list(self, agent):
        """템플릿 목록 조회 테스트"""
        result = await agent.run({"action": "list"})

        assert result.success
        assert "base_template" in result.data
        assert "category_variations" in result.data

    @pytest.mark.asyncio
    async def test_execute_generate(self, agent):
        """템플릿 생성 테스트"""
        result = await agent.run({
            "action": "generate",
            "topic": "apple",
            "topic_kr": "사과",
            "category": "fruit",
            "is_safe": True
        })

        assert result.success
        assert "template" in result.data
        assert len(result.data["template"]) == 10

    @pytest.mark.asyncio
    async def test_execute_get_style(self, agent):
        """스타일 가이드 조회 테스트"""
        result = await agent.run({
            "action": "get_style",
            "category": "dangerous"
        })

        assert result.success
        assert result.data["category"] == "dangerous"
        assert "경고" in result.data["style"]["emoji_style"]


# 통합 테스트
class TestAgentIntegration:
    """에이전트 통합 테스트"""

    @pytest.mark.asyncio
    async def test_full_workflow(self):
        """전체 워크플로우 테스트"""
        # 1. 트렌드 분석
        trend_agent = TrendAgent()
        trend_result = await trend_agent.run({
            "action": "recommend",
            "topics": ["banana", "cherry", "watermelon", "carrot", "chicken"],
            "count": 3
        })
        assert trend_result.success

        # 2. 스케줄링
        scheduler = SchedulerAgent()
        top_topics = [r["topic"] for r in trend_result.data["recommendations"]]
        schedule_result = await scheduler.run({
            "action": "generate_schedule",
            "topics": top_topics
        })
        assert schedule_result.success

        # 3. 템플릿 생성
        template_agent = TemplateAgent()
        template_result = await template_agent.run({
            "action": "generate",
            "topic": top_topics[0],
            "topic_kr": "테스트",
            "category": "fruit"
        })
        assert template_result.success

    @pytest.mark.asyncio
    async def test_error_handling_flow(self):
        """에러 핸들링 플로우 테스트"""
        retry_agent = RetryAgent()

        # 실패 등록
        add_result = await retry_agent.run({
            "action": "add",
            "task_id": "integration_test_001",
            "task_type": "posting",
            "error": "Network connection timeout",
            "agent_name": "PublisherAgent"
        })
        assert add_result.success
        assert add_result.data["is_recoverable"] is True

        # 통계 확인
        stats_result = await retry_agent.run({"action": "stats"})
        assert stats_result.success
        assert stats_result.data["total_failures"] >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
