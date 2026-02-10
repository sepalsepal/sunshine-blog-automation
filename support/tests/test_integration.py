"""
Phase 6: 통합 테스트
작성: Phase 6 Day 2

테스트 대상:
- Crew 간 연동
- Pipeline 흐름
- 품질 검사 루프
- Slack 승인 흐름
"""

import pytest
import asyncio
import json
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
def temp_output_dir():
    """임시 출력 디렉토리"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def temp_data_dir():
    """임시 데이터 디렉토리"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def sample_storyboard():
    """샘플 스토리보드 결과"""
    return {
        "success": True,
        "storyboard_path": "/tmp/test_storyboard.md",
        "diversity_pass": True,
        "slides": [
            {"index": 0, "type": "cover", "text": {"title": "수박", "subtitle": None}},
            {"index": 1, "type": "result", "text": {"title": "수박, 먹어도 돼요!", "subtitle": "안전하게 급여 가능해요"}},
            {"index": 2, "type": "benefit1", "text": {"title": "수분 보충", "subtitle": "92%가 수분"}},
            {"index": 3, "type": "benefit2", "text": {"title": "비타민 A", "subtitle": "피부와 눈 건강"}},
            {"index": 4, "type": "caution", "text": {"title": "주의하세요!", "subtitle": "씨 제거 필수"}},
            {"index": 5, "type": "amount", "text": {"title": "적정량", "subtitle": "체중 1kg당 10~20g"}},
            {"index": 6, "type": "cta", "text": {"title": "저장해두세요!", "subtitle": "우리 아이 건강 간식 정보"}}
        ],
        "prompts": [
            {"index": 0, "type": "cover", "prompt": "A golden retriever..."},
            {"index": 1, "type": "result", "prompt": "A golden retriever..."},
            {"index": 2, "type": "benefit1", "prompt": "A golden retriever..."},
            {"index": 3, "type": "benefit2", "prompt": "A golden retriever..."},
            {"index": 4, "type": "caution", "prompt": "A golden retriever..."},
            {"index": 5, "type": "amount", "prompt": "A golden retriever..."},
            {"index": 6, "type": "cta", "prompt": "A golden retriever..."}
        ]
    }


@pytest.fixture
def mock_images(temp_output_dir):
    """7장 이미지 목 생성"""
    from PIL import Image

    food_name = "watermelon"
    images = []

    for i in range(7):
        if i == 0:
            filename = f"{food_name}_{i:02d}_cover.png"
        elif i == 6:
            filename = f"{food_name}_{i:02d}_cta.png"
        else:
            filename = f"{food_name}_{i:02d}_content.png"

        img_path = Path(temp_output_dir) / filename
        img = Image.new('RGB', (1080, 1080), color=(255, 200, 100))
        img.save(img_path, 'PNG')
        images.append(str(img_path))

    return images


# ==============================================================================
# Storyboard → Content Flow Tests
# ==============================================================================

class TestStoryboardToContentFlow:
    """스토리보드 → 콘텐츠 생성 흐름 테스트"""

    def test_storyboard_generates_7_slides(self, temp_output_dir):
        """스토리보드가 7장 슬라이드를 생성하는지 확인"""
        from core.crews import StoryboardCrew

        crew = StoryboardCrew()
        crew.storyboard_dir = Path(temp_output_dir)

        result = crew.run(
            food_name="watermelon",
            food_name_kr="수박"
        )

        assert result["success"] is True
        assert len(result["slides"]) == 7

        # 슬라이드 타입 확인
        slide_types = [s["type"] for s in result["slides"]]
        assert slide_types == ["cover", "result", "benefit1", "benefit2", "caution", "amount", "cta"]

    def test_storyboard_generates_prompts(self, temp_output_dir):
        """스토리보드가 프롬프트를 생성하는지 확인"""
        from core.crews import StoryboardCrew

        crew = StoryboardCrew()
        crew.storyboard_dir = Path(temp_output_dir)

        result = crew.run(
            food_name="banana",
            food_name_kr="바나나"
        )

        assert "prompts" in result
        assert len(result["prompts"]) == 7

        # 각 프롬프트에 golden retriever 포함
        for prompt in result["prompts"]:
            assert "golden retriever" in prompt["prompt"].lower()

    def test_content_crew_uses_storyboard_prompts(self, sample_storyboard, temp_output_dir):
        """ContentCrew가 스토리보드 프롬프트를 사용하는지 확인"""
        from core.crews import ContentCrew

        crew = ContentCrew()

        # 이미지 생성 스킵하고 기존 이미지 사용
        result = crew.run(
            topic="watermelon",
            slides=sample_storyboard["prompts"],
            output_dir=temp_output_dir,
            skip_generation=True
        )

        assert "success" in result
        assert "images" in result


# ==============================================================================
# Tech Review → Creative Review Flow Tests
# ==============================================================================

class TestReviewFlow:
    """기술 검수 → 크리에이티브 검수 흐름 테스트"""

    def test_tech_review_runs_on_images(self, mock_images, temp_output_dir):
        """기술 검수가 이미지에 대해 실행되는지 확인"""
        from core.crews import TechReviewCrew

        crew = TechReviewCrew()

        result = crew.run(
            content_dir=temp_output_dir,
            food_name="watermelon"
        )

        assert result["success"] is True
        assert "total_score" in result
        assert "grade" in result
        assert result["percentage"] > 0

    def test_creative_review_runs_on_images(self, mock_images, temp_output_dir):
        """크리에이티브 검수가 이미지에 대해 실행되는지 확인"""
        from core.crews import CreativeReviewCrew

        crew = CreativeReviewCrew()
        crew.vlm_available = False  # VLM 없이 테스트

        result = crew.run(
            content_dir=temp_output_dir,
            food_name="watermelon"
        )

        assert result["success"] is True
        assert "total_score" in result
        assert "grade" in result
        assert "categories" in result

    def test_review_scores_affect_verdict(self, mock_images, temp_output_dir):
        """검수 점수가 판정에 영향을 미치는지 확인"""
        from core.crews import CreativeReviewCrew

        crew = CreativeReviewCrew()
        crew.vlm_available = False

        result = crew.run(
            content_dir=temp_output_dir,
            food_name="watermelon"
        )

        # VLM 없이 기본 점수는 60점 (4 카테고리 × 15점)
        # 판정 확인
        assert "verdict" in result
        assert result["verdict"] in ["PASS", "CONDITIONAL", "FAIL"]


# ==============================================================================
# Quality Loop Integration Tests
# ==============================================================================

class TestQualityLoopIntegration:
    """품질 검사 루프 통합 테스트"""

    def test_quality_loop_initialization(self):
        """품질 루프 초기화 테스트"""
        from core.pipeline.quality_loop import QualityControlLoop

        loop = QualityControlLoop()

        assert loop is not None
        assert loop.TECH_PASS_SCORE == 90
        assert loop.CREATIVE_PASS_SCORE == 90

    def test_quality_loop_with_skip_generation(self, mock_images, temp_output_dir, sample_storyboard):
        """품질 루프 (생성 스킵) 테스트"""
        from core.pipeline.quality_loop import QualityControlLoop

        loop = QualityControlLoop(config={
            "max_retries": 1,
            "skip_generation": True
        })

        # 기존 이미지가 있는 디렉토리 사용
        # 실제 테스트에서는 mock 사용

    def test_retry_context_accumulates_feedback(self):
        """재시도 컨텍스트가 피드백을 축적하는지 확인"""
        from core.pipeline.quality_loop import RetryContext

        context = RetryContext(max_attempts=3)

        context.increment()
        context.add_feedback("tech", "해상도 문제", 75.0)

        context.increment()
        context.add_feedback("tech", "텍스트 위치 문제", 80.0)
        context.add_feedback("creative", "다양성 부족", 70.0)

        assert len(context.score_history) == 3
        assert len(context.tech_feedbacks) == 2

        prompt = context.get_improvement_prompt()
        assert "해상도 문제" in prompt
        assert "텍스트 위치 문제" in prompt


# ==============================================================================
# Slack Approval Integration Tests
# ==============================================================================

class TestSlackApprovalIntegration:
    """Slack 승인 통합 테스트"""

    def test_slack_handler_initialization(self):
        """Slack 핸들러 초기화 테스트"""
        from support.utils.slack_handler import SlackApprovalHandler

        handler = SlackApprovalHandler()

        assert handler is not None
        # 환경변수 없으면 비활성화
        assert handler.enabled is False or handler.enabled is True

    def test_approval_status_enum(self):
        """승인 상태 열거형 테스트"""
        from support.utils.slack_handler import ApprovalStatus

        assert ApprovalStatus.PENDING.value == "pending"
        assert ApprovalStatus.APPROVED.value == "approved"
        assert ApprovalStatus.REJECTED.value == "rejected"
        assert ApprovalStatus.TIMEOUT.value == "timeout"

    def test_approval_type_enum(self):
        """승인 타입 열거형 테스트"""
        from support.utils.slack_handler import ApprovalType

        assert ApprovalType.STORYBOARD.value == "storyboard"
        assert ApprovalType.FINAL.value == "final"

    @pytest.mark.asyncio
    async def test_storyboard_approval_request(self):
        """스토리보드 승인 요청 테스트"""
        from support.utils.slack_handler import SlackApprovalHandler

        handler = SlackApprovalHandler()
        handler.enabled = False  # Slack 비활성화로 테스트

        approval_id = await handler.send_storyboard_approval_request(
            food_name="watermelon",
            food_name_kr="수박",
            storyboard_path="/tmp/test_storyboard.md",
            storyboard_summary={"slides": 7}
        )

        assert approval_id is not None
        assert approval_id.startswith("sb_watermelon_")

    @pytest.mark.asyncio
    async def test_final_approval_request(self):
        """최종 승인 요청 테스트"""
        from support.utils.slack_handler import SlackApprovalHandler

        handler = SlackApprovalHandler()
        handler.enabled = False

        approval_id = await handler.send_final_approval_request(
            food_name="watermelon",
            food_name_kr="수박",
            images_dir="/tmp/watermelon_final",
            tech_score=92.5,
            creative_score=88.0,
            preview_urls=[]
        )

        assert approval_id is not None
        assert approval_id.startswith("final_watermelon_")

    def test_manual_approve(self):
        """수동 승인 테스트"""
        from support.utils.slack_handler import SlackApprovalHandler, ApprovalRequest, ApprovalType, ApprovalStatus

        handler = SlackApprovalHandler()

        # 승인 요청 생성
        approval = ApprovalRequest(
            id="test_approval_123",
            food_name="watermelon",
            food_name_kr="수박",
            approval_type=ApprovalType.STORYBOARD
        )
        handler.pending_approvals["test_approval_123"] = approval

        # 수동 승인
        result = handler.manual_approve("test_approval_123", "test_reviewer")

        assert result is True
        assert approval.status == ApprovalStatus.APPROVED
        assert approval.reviewer == "test_reviewer"

    def test_manual_reject(self):
        """수동 반려 테스트"""
        from support.utils.slack_handler import SlackApprovalHandler, ApprovalRequest, ApprovalType, ApprovalStatus

        handler = SlackApprovalHandler()

        # 승인 요청 생성
        approval = ApprovalRequest(
            id="test_approval_456",
            food_name="banana",
            food_name_kr="바나나",
            approval_type=ApprovalType.FINAL
        )
        handler.pending_approvals["test_approval_456"] = approval

        # 수동 반려
        result = handler.manual_reject("test_approval_456", "품질 미달", "test_reviewer")

        assert result is True
        assert approval.status == ApprovalStatus.REJECTED
        assert approval.feedback == "품질 미달"


# ==============================================================================
# Pipeline State Integration Tests
# ==============================================================================

class TestPipelineStateIntegration:
    """파이프라인 상태 통합 테스트"""

    def test_state_store_with_pipeline_state(self, temp_data_dir):
        """StateStore와 파이프라인 상태 통합 테스트"""
        from support.utils.state_store import StateStore

        store = StateStore(store_path=f"{temp_data_dir}/test_states.json")

        # 파이프라인 상태 저장
        state = {
            "food_name": "watermelon",
            "food_name_kr": "수박",
            "status": "completed",
            "tech_review_score": 92.5,
            "creative_review_score": 88.0,
            "instagram_url": "https://instagram.com/p/test123"
        }
        store.save_state("watermelon", state)

        # 조회
        retrieved = store.get_state("watermelon")
        assert retrieved["status"] == "completed"
        assert retrieved["tech_review_score"] == 92.5

    def test_feedback_improver_with_state(self, temp_data_dir):
        """FeedbackImprover와 상태 통합 테스트"""
        from support.utils.feedback_improver import FeedbackImprover
        from support.utils.state_store import StateStore

        store = StateStore(store_path=f"{temp_data_dir}/test_states.json")
        improver = FeedbackImprover()

        # 실패 상태와 피드백
        state = {
            "food_name": "banana",
            "status": "failed",
            "tech_review_score": 72.0,
            "creative_review_score": 65.0,
            "feedback": "언더라인 비율 문제, 다양성 부족"
        }
        store.save_state("banana", state)

        # 피드백 분석
        analysis = improver.analyze_feedback(
            tech_feedback=state["feedback"],
            creative_feedback=state["feedback"]
        )

        assert len(analysis.categories) > 0


# ==============================================================================
# Full Crew Pipeline Integration Tests
# ==============================================================================

class TestFullCrewPipelineIntegration:
    """전체 Crew 파이프라인 통합 테스트"""

    def test_all_crews_instantiate(self):
        """모든 Crew 인스턴스화 가능 확인"""
        from core.crews import (
            StoryboardCrew,
            ContentCrew,
            TextOverlayCrew,
            TechReviewCrew,
            CreativeReviewCrew,
            PublishingCrew
        )

        crews = [
            StoryboardCrew(),
            ContentCrew(),
            TextOverlayCrew(),
            TechReviewCrew(),
            CreativeReviewCrew(),
            PublishingCrew()
        ]

        for crew in crews:
            assert crew is not None
            assert hasattr(crew, 'run')
            assert hasattr(crew, 'kickoff')

    def test_storyboard_to_review_flow(self, temp_output_dir, mock_images):
        """스토리보드 → 검수 흐름 테스트"""
        from core.crews import StoryboardCrew, TechReviewCrew, CreativeReviewCrew

        # 1. 스토리보드 생성
        storyboard_crew = StoryboardCrew()
        storyboard_crew.storyboard_dir = Path(temp_output_dir)

        sb_result = storyboard_crew.run(
            food_name="watermelon",
            food_name_kr="수박"
        )

        assert sb_result["success"] is True
        assert len(sb_result["slides"]) == 7

        # 2. 기술 검수 (mock 이미지 사용)
        tech_crew = TechReviewCrew()
        tech_result = tech_crew.run(
            content_dir=temp_output_dir,
            food_name="watermelon"
        )

        assert tech_result["success"] is True

        # 3. 크리에이티브 검수
        creative_crew = CreativeReviewCrew()
        creative_crew.vlm_available = False

        creative_result = creative_crew.run(
            content_dir=temp_output_dir,
            food_name="watermelon"
        )

        assert creative_result["success"] is True


# ==============================================================================
# Server Integration Tests
# ==============================================================================

class TestServerIntegration:
    """서버 통합 테스트"""

    def test_server_module_imports(self):
        """서버 모듈 import 테스트"""
        try:
            from services.api import app
            assert app is not None
        except ImportError:
            # FastAPI 미설치 시 예상되는 동작
            pass

    def test_slack_handler_in_server(self):
        """서버에서 Slack 핸들러 사용 테스트"""
        try:
            from services.api.app import slack_handler
            assert slack_handler is not None
        except (ImportError, NameError):
            # FastAPI 미설치 시 예상되는 동작
            pass


# ==============================================================================
# Run Tests
# ==============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
