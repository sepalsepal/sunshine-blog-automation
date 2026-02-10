"""
Phase 6: Utils 단위 테스트
작성: Phase 6 Day 1

테스트 대상:
- StateStore
- SlackNotifier
- FeedbackImprover
- SelectiveRegenerator
- PipelineLogger
"""

import pytest
import json
import asyncio
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, AsyncMock
import sys

# 프로젝트 루트 경로 추가
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))


# ==============================================================================
# Fixtures
# ==============================================================================

@pytest.fixture
def temp_data_dir():
    """임시 데이터 디렉토리"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def sample_pipeline_state():
    """샘플 파이프라인 상태"""
    return {
        "food_name": "watermelon",
        "food_name_kr": "수박",
        "status": "completed",
        "tech_review_score": 92.5,
        "creative_review_score": 88.0,
        "instagram_url": "https://instagram.com/p/test123",
        "created_at": "2026-01-26T10:00:00"
    }


@pytest.fixture
def sample_tech_result():
    """샘플 기술 검수 결과"""
    return {
        "score": 75,
        "feedback": "언더라인 비율 문제, 슬라이드 0 텍스트 위치 조정 필요",
        "details": {
            "text_position": {"pass": False},
            "underline": {"pass": False},
            "resolution": {"pass": True}
        }
    }


@pytest.fixture
def sample_creative_result():
    """샘플 크리에이티브 검수 결과"""
    return {
        "score": 65,
        "feedback": "포즈 다양성 부족, 사람 등장 없음, AI 느낌이 남",
        "details": {
            "diversity": {
                "total": 12,
                "scores": {
                    "pose_variety": 2,
                    "angle_variety": 3,
                    "background_variety": 4,
                    "human_appearance": 1,
                    "food_form_variety": 2
                }
            },
            "emotion": {
                "total": 14,
                "scores": {"authenticity": 2}
            }
        }
    }


# ==============================================================================
# StateStore Tests
# ==============================================================================

class TestStateStore:
    """StateStore 단위 테스트"""

    def test_instantiation(self, temp_data_dir):
        """인스턴스화 테스트"""
        from support.utils.state_store import StateStore

        store = StateStore(store_path=f"{temp_data_dir}/test_states.json")
        assert store is not None
        assert store.states == {}

    def test_save_and_get_state(self, temp_data_dir, sample_pipeline_state):
        """상태 저장 및 조회 테스트"""
        from support.utils.state_store import StateStore

        store = StateStore(store_path=f"{temp_data_dir}/test_states.json")

        store.save_state("watermelon", sample_pipeline_state)

        retrieved = store.get_state("watermelon")
        assert retrieved is not None
        assert retrieved["food_name"] == "watermelon"
        assert retrieved["status"] == "completed"

    def test_state_persistence(self, temp_data_dir, sample_pipeline_state):
        """상태 영속성 테스트"""
        from support.utils.state_store import StateStore

        store_path = f"{temp_data_dir}/test_states.json"

        # 저장
        store1 = StateStore(store_path=store_path)
        store1.save_state("watermelon", sample_pipeline_state)

        # 새 인스턴스로 로드
        store2 = StateStore(store_path=store_path)
        retrieved = store2.get_state("watermelon")

        assert retrieved is not None
        assert retrieved["food_name"] == "watermelon"

    def test_get_pending_pipelines(self, temp_data_dir):
        """미완료 파이프라인 조회 테스트"""
        from support.utils.state_store import StateStore

        store = StateStore(store_path=f"{temp_data_dir}/test_states.json")

        store.save_state("apple", {"status": "completed"})
        store.save_state("banana", {"status": "pending"})
        store.save_state("cherry", {"status": "in_progress"})

        pending = store.get_pending_pipelines()

        assert "apple" not in pending
        assert "banana" in pending
        assert "cherry" in pending

    def test_get_completed_pipelines(self, temp_data_dir):
        """완료된 파이프라인 조회 테스트"""
        from support.utils.state_store import StateStore

        store = StateStore(store_path=f"{temp_data_dir}/test_states.json")

        store.save_state("apple", {"status": "completed"})
        store.save_state("banana", {"status": "pending"})

        completed = store.get_completed_pipelines()

        assert "apple" in completed
        assert "banana" not in completed

    def test_get_failed_pipelines(self, temp_data_dir):
        """실패한 파이프라인 조회 테스트"""
        from support.utils.state_store import StateStore

        store = StateStore(store_path=f"{temp_data_dir}/test_states.json")

        store.save_state("apple", {"status": "completed"})
        store.save_state("banana", {"status": "failed"})

        failed = store.get_failed_pipelines()

        assert "apple" not in failed
        assert "banana" in failed

    def test_delete_state(self, temp_data_dir, sample_pipeline_state):
        """상태 삭제 테스트"""
        from support.utils.state_store import StateStore

        store = StateStore(store_path=f"{temp_data_dir}/test_states.json")

        store.save_state("watermelon", sample_pipeline_state)
        assert store.get_state("watermelon") is not None

        result = store.delete_state("watermelon")
        assert result is True
        assert store.get_state("watermelon") is None

    def test_statistics(self, temp_data_dir):
        """통계 테스트"""
        from support.utils.state_store import StateStore

        store = StateStore(store_path=f"{temp_data_dir}/test_states.json")

        store.save_state("apple", {"status": "completed", "tech_review_score": 90})
        store.save_state("banana", {"status": "completed", "tech_review_score": 85})
        store.save_state("cherry", {"status": "failed"})

        stats = store.get_statistics()

        assert stats["total"] == 3
        assert stats["completed"] == 2
        assert stats["failed"] == 1
        assert stats["avg_tech_score"] == 87.5

    def test_history(self, temp_data_dir):
        """히스토리 테스트"""
        from support.utils.state_store import StateStore

        store = StateStore(store_path=f"{temp_data_dir}/test_states.json")

        for i in range(5):
            store.save_state(f"food_{i}", {"status": "completed", "updated_at": f"2026-01-{20+i:02d}"})

        history = store.get_history(limit=3)

        assert len(history) == 3


# ==============================================================================
# SlackNotifier Tests
# ==============================================================================

class TestSlackNotifier:
    """SlackNotifier 단위 테스트"""

    def test_instantiation(self):
        """인스턴스화 테스트"""
        from support.utils.notifier import SlackNotifier

        notifier = SlackNotifier()
        assert notifier is not None

    def test_local_save_when_disabled(self, temp_data_dir):
        """Slack 비활성화 시 로컬 저장 테스트"""
        from support.utils.notifier import SlackNotifier

        notifier = SlackNotifier()
        notifier.enabled = False
        notifier.notifications_dir = Path(temp_data_dir) / "notifications"
        notifier.notifications_dir.mkdir(parents=True, exist_ok=True)

        message = {"text": "테스트 메시지"}
        notifier._save_local(message)

        # 파일 생성 확인
        files = list(notifier.notifications_dir.glob("notification_*.json"))
        assert len(files) == 1

        # 내용 확인
        with open(files[0], 'r', encoding='utf-8') as f:
            saved = json.load(f)
            assert saved["message"]["text"] == "테스트 메시지"

    @pytest.mark.asyncio
    async def test_send_without_webhook(self, temp_data_dir):
        """Webhook 없이 send 테스트"""
        from support.utils.notifier import SlackNotifier

        notifier = SlackNotifier()
        notifier.enabled = False
        notifier.notifications_dir = Path(temp_data_dir) / "notifications"
        notifier.notifications_dir.mkdir(parents=True, exist_ok=True)

        result = await notifier._send({"text": "test"})

        assert result is False

    @pytest.mark.asyncio
    async def test_send_approval_request_storyboard(self, temp_data_dir):
        """스토리보드 승인 요청 테스트"""
        from support.utils.notifier import SlackNotifier

        notifier = SlackNotifier()
        notifier.enabled = False
        notifier.notifications_dir = Path(temp_data_dir) / "notifications"
        notifier.notifications_dir.mkdir(parents=True, exist_ok=True)

        await notifier.send_approval_request(
            phase="storyboard",
            food_name="watermelon",
            file_path="storyboards/watermelon_storyboard.md"
        )

        files = list(notifier.notifications_dir.glob("notification_*.json"))
        assert len(files) == 1

    @pytest.mark.asyncio
    async def test_send_completion(self, temp_data_dir):
        """완료 알림 테스트"""
        from support.utils.notifier import SlackNotifier

        notifier = SlackNotifier()
        notifier.enabled = False
        notifier.notifications_dir = Path(temp_data_dir) / "notifications"
        notifier.notifications_dir.mkdir(parents=True, exist_ok=True)

        await notifier.send_completion(
            food_name="watermelon",
            instagram_url="https://instagram.com/p/test123",
            tech_score=92.5,
            creative_score=88.0
        )

        files = list(notifier.notifications_dir.glob("notification_*.json"))
        assert len(files) == 1

    @pytest.mark.asyncio
    async def test_send_error(self, temp_data_dir):
        """에러 알림 테스트"""
        from support.utils.notifier import SlackNotifier

        notifier = SlackNotifier()
        notifier.enabled = False
        notifier.notifications_dir = Path(temp_data_dir) / "notifications"
        notifier.notifications_dir.mkdir(parents=True, exist_ok=True)

        await notifier.send_error(
            food_name="watermelon",
            error="이미지 생성 실패",
            phase="content_generation"
        )

        files = list(notifier.notifications_dir.glob("notification_*.json"))
        assert len(files) == 1


# ==============================================================================
# FeedbackImprover Tests
# ==============================================================================

class TestFeedbackImprover:
    """FeedbackImprover 단위 테스트"""

    def test_instantiation(self):
        """인스턴스화 테스트"""
        from support.utils.feedback_improver import FeedbackImprover

        improver = FeedbackImprover()
        assert improver is not None

    def test_keyword_mapping_exists(self):
        """키워드 매핑 존재 확인"""
        from support.utils.feedback_improver import FeedbackImprover

        improver = FeedbackImprover()
        assert len(improver.KEYWORD_MAPPING) > 0

    def test_analyze_tech_feedback(self, sample_tech_result):
        """기술 피드백 분석 테스트"""
        from support.utils.feedback_improver import FeedbackImprover, ProblemCategory

        improver = FeedbackImprover()

        analysis = improver.analyze_feedback(
            tech_feedback=sample_tech_result["feedback"],
            tech_details=sample_tech_result["details"]
        )

        assert ProblemCategory.TEXT_POSITION in analysis.categories
        assert ProblemCategory.UNDERLINE in analysis.categories

    def test_analyze_creative_feedback(self, sample_creative_result):
        """크리에이티브 피드백 분석 테스트"""
        from support.utils.feedback_improver import FeedbackImprover, ProblemCategory

        improver = FeedbackImprover()

        analysis = improver.analyze_feedback(
            creative_feedback=sample_creative_result["feedback"],
            creative_details=sample_creative_result["details"]
        )

        assert ProblemCategory.POSE_DIVERSITY in analysis.categories or \
               ProblemCategory.AUTHENTICITY in analysis.categories

    def test_analyze_combined_feedback(self, sample_tech_result, sample_creative_result):
        """통합 피드백 분석 테스트"""
        from support.utils.feedback_improver import FeedbackImprover

        improver = FeedbackImprover()

        analysis = improver.analyze_feedback(
            tech_feedback=sample_tech_result["feedback"],
            creative_feedback=sample_creative_result["feedback"],
            tech_details=sample_tech_result["details"],
            creative_details=sample_creative_result["details"]
        )

        assert len(analysis.categories) > 0
        assert analysis.priority in ["high", "medium", "low"]
        assert analysis.regeneration_scope in ["full", "selective", "minor"]

    def test_generate_improvement_prompt(self, sample_tech_result, sample_creative_result):
        """개선 프롬프트 생성 테스트"""
        from support.utils.feedback_improver import FeedbackImprover

        improver = FeedbackImprover()

        analysis = improver.analyze_feedback(
            tech_feedback=sample_tech_result["feedback"],
            creative_feedback=sample_creative_result["feedback"]
        )

        prompt = improver.generate_improvement_prompt(analysis)

        assert "IMPROVEMENT REQUIREMENTS" in prompt
        assert "Priority:" in prompt

    def test_slide_specific_improvements(self):
        """슬라이드별 개선사항 테스트"""
        from support.utils.feedback_improver import FeedbackImprover, FeedbackAnalysis, ProblemCategory

        improver = FeedbackImprover()

        analysis = FeedbackAnalysis(
            categories=[ProblemCategory.POSE_DIVERSITY],
            problem_slides=[2, 4],
            improvement_suggestions=["포즈 다양화 필요"],
            priority="medium",
            regeneration_scope="selective"
        )

        improvements = improver.get_slide_specific_improvements(analysis, 2)

        assert len(improvements) > 0

    def test_priority_determination(self):
        """우선순위 결정 테스트"""
        from support.utils.feedback_improver import FeedbackImprover, ProblemCategory

        improver = FeedbackImprover()

        # 기술 문제 → 높은 우선순위
        tech_categories = {ProblemCategory.RESOLUTION}
        priority = improver._determine_priority(tech_categories)
        assert priority == "high"

        # 여러 문제 → 높은 우선순위
        many_categories = {
            ProblemCategory.POSE_DIVERSITY,
            ProblemCategory.EMOTION,
            ProblemCategory.BACKGROUND
        }
        priority = improver._determine_priority(many_categories)
        assert priority == "high"


# ==============================================================================
# SelectiveRegenerator Tests
# ==============================================================================

class TestSelectiveRegenerator:
    """SelectiveRegenerator 단위 테스트"""

    def test_instantiation(self):
        """인스턴스화 테스트"""
        from support.utils.selective_regenerator import SelectiveRegenerator

        regenerator = SelectiveRegenerator()
        assert regenerator is not None

    def test_analyze_and_plan(self, sample_tech_result, sample_creative_result):
        """분석 및 계획 수립 테스트"""
        from support.utils.selective_regenerator import SelectiveRegenerator

        regenerator = SelectiveRegenerator()

        plan = regenerator.analyze_and_plan(
            tech_result=sample_tech_result,
            creative_result=sample_creative_result,
            total_slides=7  # Phase 6: 7장
        )

        assert plan is not None
        assert len(plan.slides_to_regenerate) + len(plan.slides_to_keep) == 7
        assert plan.strategy in ["full", "selective", "patch"]

    def test_strategy_determination(self):
        """전략 결정 테스트"""
        from support.utils.selective_regenerator import SelectiveRegenerator
        from support.utils.feedback_improver import FeedbackAnalysis

        regenerator = SelectiveRegenerator()

        # 70% 이상 → full
        strategy = regenerator._determine_strategy(
            analysis=Mock(),
            num_to_regenerate=6,
            total_slides=7
        )
        assert strategy == "full"

        # 30-70% → selective
        strategy = regenerator._determine_strategy(
            analysis=Mock(),
            num_to_regenerate=3,
            total_slides=7
        )
        assert strategy == "selective"

        # 30% 미만 → patch
        strategy = regenerator._determine_strategy(
            analysis=Mock(),
            num_to_regenerate=1,
            total_slides=7
        )
        assert strategy == "patch"

    def test_extract_index_from_filename(self):
        """파일명에서 인덱스 추출 테스트"""
        from support.utils.selective_regenerator import SelectiveRegenerator

        regenerator = SelectiveRegenerator()

        # slide_XX 패턴
        idx = regenerator._extract_index_from_filename("slide_02_content.png")
        assert idx == 2

        # _XX_ 패턴
        idx = regenerator._extract_index_from_filename("watermelon_04_content.png")
        assert idx == 4

    def test_regeneration_report(self, sample_tech_result, sample_creative_result):
        """재생성 리포트 테스트"""
        from support.utils.selective_regenerator import SelectiveRegenerator

        regenerator = SelectiveRegenerator()

        plan = regenerator.analyze_and_plan(
            tech_result=sample_tech_result,
            creative_result=sample_creative_result,
            total_slides=7
        )

        report = regenerator.get_regeneration_report(plan)

        assert "선택적 재생성 계획" in report
        assert "전략:" in report


# ==============================================================================
# QualityControlLoop Tests
# ==============================================================================

class TestQualityControlLoop:
    """QualityControlLoop 단위 테스트"""

    def test_pass_scores_are_90(self):
        """통과 점수가 90점인지 확인 (Phase 6)"""
        from core.pipeline.quality_loop import QualityControlLoop

        assert QualityControlLoop.TECH_PASS_SCORE == 90
        assert QualityControlLoop.CREATIVE_PASS_SCORE == 90
        assert QualityControlLoop.CONDITIONAL_PASS_SCORE == 80

    def test_retry_context(self):
        """RetryContext 테스트"""
        from core.pipeline.quality_loop import RetryContext

        context = RetryContext(max_attempts=3)

        assert context.can_retry() is True
        assert context.attempt == 0

        context.increment()
        assert context.attempt == 1
        assert context.can_retry() is True

        context.increment()
        context.increment()
        assert context.attempt == 3
        assert context.can_retry() is False

    def test_retry_context_feedback(self):
        """RetryContext 피드백 테스트"""
        from core.pipeline.quality_loop import RetryContext

        context = RetryContext()

        context.add_feedback("tech", "해상도 문제", 75.0)
        context.add_feedback("creative", "다양성 부족", 65.0)

        assert len(context.tech_feedbacks) == 1
        assert len(context.creative_feedbacks) == 1
        assert len(context.score_history) == 2

    def test_retry_context_improvement_prompt(self):
        """RetryContext 개선 프롬프트 테스트"""
        from core.pipeline.quality_loop import RetryContext

        context = RetryContext()

        context.add_feedback("tech", "해상도 문제", 75.0)
        context.add_feedback("creative", "다양성 부족", 65.0)

        prompt = context.get_improvement_prompt()

        assert "기술 검수 개선 필요" in prompt
        assert "크리에이티브 개선 필요" in prompt

    def test_retry_strategy(self):
        """재시도 전략 테스트"""
        from core.pipeline.quality_loop import RetryContext

        context = RetryContext()

        # 첫 시도
        context.increment()
        assert context.get_retry_strategy() == "full_regeneration"

        # 두 번째 시도
        context.increment()
        assert context.get_retry_strategy() == "selective_regeneration"

        # 세 번째 시도
        context.increment()
        assert context.get_retry_strategy() == "manual_intervention"


# ==============================================================================
# Integration Tests (Utils)
# ==============================================================================

class TestUtilsIntegration:
    """Utils 간 통합 테스트"""

    def test_all_utils_can_be_imported(self):
        """모든 유틸리티 import 가능 확인"""
        from support.utils import (
            PipelineLogger,
            SlackNotifier,
            StateStore,
            FeedbackImprover,
            FeedbackAnalysis,
            ProblemCategory,
            SelectiveRegenerator,
            RegenerationPlan
        )

        assert PipelineLogger is not None
        assert SlackNotifier is not None
        assert StateStore is not None
        assert FeedbackImprover is not None
        assert SelectiveRegenerator is not None

    def test_feedback_to_regeneration_flow(self, sample_tech_result, sample_creative_result):
        """피드백 → 재생성 계획 흐름 테스트"""
        from support.utils import FeedbackImprover, SelectiveRegenerator

        # 피드백 분석
        improver = FeedbackImprover()
        analysis = improver.analyze_feedback(
            tech_feedback=sample_tech_result["feedback"],
            creative_feedback=sample_creative_result["feedback"]
        )

        # 재생성 계획
        regenerator = SelectiveRegenerator()
        plan = regenerator.analyze_and_plan(
            tech_result=sample_tech_result,
            creative_result=sample_creative_result,
            total_slides=7
        )

        # 개선 프롬프트 생성
        prompt = improver.generate_improvement_prompt(analysis)

        assert len(analysis.categories) > 0
        assert plan is not None
        assert len(prompt) > 0


# ==============================================================================
# Run Tests
# ==============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
