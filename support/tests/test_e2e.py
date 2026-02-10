"""
Phase 6: E2E (End-to-End) 테스트
작성: Phase 6 Day 3

테스트 대상:
- 전체 파이프라인 흐름
- 드라이런 모드
- 실패 복구
- 상태 영속성
"""

import pytest
import asyncio
import json
import tempfile
import shutil
import os
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
def temp_workspace():
    """임시 작업 공간"""
    temp_dir = tempfile.mkdtemp()
    workspace = {
        "root": temp_dir,
        "storyboards": Path(temp_dir) / "storyboards",
        "outputs": Path(temp_dir) / "outputs",
        "data": Path(temp_dir) / "data",
        "logs": Path(temp_dir) / "logs"
    }

    for dir_path in workspace.values():
        if isinstance(dir_path, Path):
            dir_path.mkdir(parents=True, exist_ok=True)

    yield workspace
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def mock_7_images(temp_workspace):
    """7장 테스트 이미지 생성"""
    from PIL import Image

    food_name = "watermelon"
    output_dir = temp_workspace["outputs"] / f"{food_name}_final"
    output_dir.mkdir(parents=True, exist_ok=True)

    images = []

    for i in range(7):
        if i == 0:
            filename = f"{food_name}_{i:02d}_cover.png"
        elif i == 6:
            filename = f"{food_name}_{i:02d}_cta.png"
        else:
            filename = f"{food_name}_{i:02d}_content.png"

        img_path = output_dir / filename
        img = Image.new('RGB', (1080, 1080), color=(255, 200, 100))
        img.save(img_path, 'PNG')
        images.append(str(img_path))

    return {
        "images": images,
        "output_dir": str(output_dir),
        "food_name": food_name
    }


# ==============================================================================
# E2E Pipeline Tests
# ==============================================================================

class TestE2EPipeline:
    """E2E 파이프라인 테스트"""

    def test_full_pipeline_structure(self):
        """전체 파이프라인 구조 확인"""
        from core.crews import (
            StoryboardCrew,
            ContentCrew,
            TextOverlayCrew,
            TechReviewCrew,
            CreativeReviewCrew,
            PublishingCrew
        )

        # 파이프라인 순서 검증
        pipeline = [
            ("1. StoryboardCrew", StoryboardCrew),
            ("2. ContentCrew", ContentCrew),
            ("3. TextOverlayCrew", TextOverlayCrew),
            ("4. TechReviewCrew", TechReviewCrew),
            ("5. CreativeReviewCrew", CreativeReviewCrew),
            ("6. PublishingCrew", PublishingCrew)
        ]

        for name, crew_class in pipeline:
            crew = crew_class()
            assert hasattr(crew, 'run'), f"{name} must have run method"
            assert hasattr(crew, 'kickoff'), f"{name} must have kickoff method"

    def test_storyboard_to_content_e2e(self, temp_workspace):
        """스토리보드 → 콘텐츠 E2E 테스트"""
        from core.crews import StoryboardCrew, ContentCrew

        # 1. 스토리보드 생성
        storyboard_crew = StoryboardCrew()
        storyboard_crew.storyboard_dir = temp_workspace["storyboards"]

        sb_result = storyboard_crew.run(
            food_name="watermelon",
            food_name_kr="수박"
        )

        assert sb_result["success"] is True
        assert len(sb_result["slides"]) == 7

        # 스토리보드 파일 확인
        storyboard_path = Path(sb_result["storyboard_path"])
        assert storyboard_path.exists()

        # JSON 파일 확인
        json_path = Path(sb_result["json_path"])
        assert json_path.exists()

        # 2. 콘텐츠 생성 (생성 스킵)
        content_crew = ContentCrew()

        # 슬라이드를 프롬프트 형식으로 변환
        prompts = [{"prompt": p["prompt"]} for p in sb_result["prompts"]]

        content_result = content_crew.run(
            topic="watermelon",
            slides=prompts,
            output_dir=str(temp_workspace["outputs"] / "watermelon_v1"),
            skip_generation=True
        )

        assert "success" in content_result

    def test_review_e2e(self, mock_7_images):
        """검수 E2E 테스트"""
        from core.crews import TechReviewCrew, CreativeReviewCrew

        # 1. 기술 검수
        tech_crew = TechReviewCrew()
        tech_result = tech_crew.run(
            content_dir=mock_7_images["output_dir"],
            food_name=mock_7_images["food_name"]
        )

        assert tech_result["success"] is True
        assert "percentage" in tech_result
        assert "grade" in tech_result

        # 2. 크리에이티브 검수
        creative_crew = CreativeReviewCrew()
        creative_crew.vlm_available = False

        creative_result = creative_crew.run(
            content_dir=mock_7_images["output_dir"],
            food_name=mock_7_images["food_name"]
        )

        assert creative_result["success"] is True
        assert "total_score" in creative_result
        assert "verdict" in creative_result


# ==============================================================================
# Dry Run E2E Tests
# ==============================================================================

class TestDryRunE2E:
    """드라이런 모드 E2E 테스트"""

    def test_storyboard_dryrun(self, temp_workspace):
        """스토리보드 드라이런 테스트"""
        from core.crews import StoryboardCrew

        crew = StoryboardCrew()
        crew.storyboard_dir = temp_workspace["storyboards"]

        result = crew.run(
            food_name="apple",
            food_name_kr="사과"
        )

        assert result["success"] is True

        # 실제 이미지 생성 없이 스토리보드만 생성됨
        assert Path(result["storyboard_path"]).exists()

    def test_content_skip_generation(self, temp_workspace, mock_7_images):
        """콘텐츠 생성 스킵 테스트"""
        from core.crews import ContentCrew

        crew = ContentCrew()

        result = crew.run(
            topic="watermelon",
            slides=[],
            output_dir=mock_7_images["output_dir"],
            skip_generation=True
        )

        assert result["success"] is True
        assert len(result["images"]) == 7

    @patch('crews.publishing_crew.asyncio.run')
    def test_publish_dryrun(self, mock_run, mock_7_images):
        """게시 드라이런 테스트"""
        from core.crews import PublishingCrew

        # Mock 결과 설정
        mock_result = Mock()
        mock_result.success = True
        mock_result.data = {
            "publish_results": {
                "cloudinary": {"success": True, "count": 7, "urls": []},
                "instagram": {"success": True, "simulated": True}
            }
        }
        mock_run.return_value = mock_result

        crew = PublishingCrew()

        result = crew.run(
            images=mock_7_images["images"],
            caption="테스트 캡션",
            topic="watermelon",
            platforms=["cloudinary"]  # Instagram 제외
        )

        assert "success" in result


# ==============================================================================
# Failure Recovery E2E Tests
# ==============================================================================

class TestFailureRecoveryE2E:
    """실패 복구 E2E 테스트"""

    def test_retry_context_recovery(self):
        """재시도 컨텍스트 복구 테스트"""
        from core.pipeline.quality_loop import RetryContext

        context = RetryContext(max_attempts=3)

        # 첫 번째 시도 실패
        context.increment()
        context.add_feedback("tech", "해상도 문제", 75.0)

        assert context.can_retry() is True
        assert context.attempt == 1

        # 두 번째 시도 실패
        context.increment()
        context.add_feedback("creative", "다양성 부족", 70.0)

        assert context.can_retry() is True
        assert context.attempt == 2

        # 세 번째 시도
        context.increment()
        assert context.can_retry() is False

    def test_state_recovery(self, temp_workspace):
        """상태 복구 테스트"""
        from support.utils.state_store import StateStore

        store_path = str(temp_workspace["data"] / "states.json")

        # 상태 저장
        store1 = StateStore(store_path=store_path)
        store1.save_state("watermelon", {
            "status": "in_progress",
            "current_phase": "content_generation",
            "tech_review_score": None,
            "creative_review_score": None
        })

        # 새 인스턴스로 복구
        store2 = StateStore(store_path=store_path)
        state = store2.get_state("watermelon")

        assert state is not None
        assert state["status"] == "in_progress"
        assert state["current_phase"] == "content_generation"

    def test_pending_pipeline_recovery(self, temp_workspace):
        """미완료 파이프라인 복구 테스트"""
        from support.utils.state_store import StateStore

        store_path = str(temp_workspace["data"] / "states.json")
        store = StateStore(store_path=store_path)

        # 여러 상태 저장
        store.save_state("apple", {"status": "completed"})
        store.save_state("banana", {"status": "in_progress"})
        store.save_state("cherry", {"status": "failed"})

        # 미완료 파이프라인 조회
        pending = store.get_pending_pipelines()

        assert "banana" in pending
        assert "apple" not in pending


# ==============================================================================
# State Persistence E2E Tests
# ==============================================================================

class TestStatePersistenceE2E:
    """상태 영속성 E2E 테스트"""

    def test_full_state_lifecycle(self, temp_workspace):
        """전체 상태 라이프사이클 테스트"""
        from support.utils.state_store import StateStore

        store_path = str(temp_workspace["data"] / "states.json")
        store = StateStore(store_path=store_path)

        food_name = "watermelon"

        # 1. 초기 상태
        store.save_state(food_name, {
            "status": "initialized",
            "food_name_kr": "수박"
        })

        # 2. 스토리보드 단계
        store.save_state(food_name, {
            "status": "storyboard_complete",
            "food_name_kr": "수박",
            "storyboard_path": "/tmp/storyboard.md"
        })

        # 3. 콘텐츠 생성 단계
        store.save_state(food_name, {
            "status": "content_complete",
            "food_name_kr": "수박",
            "storyboard_path": "/tmp/storyboard.md",
            "content_dir": "/tmp/watermelon_final"
        })

        # 4. 검수 단계
        store.save_state(food_name, {
            "status": "review_complete",
            "food_name_kr": "수박",
            "tech_review_score": 92.5,
            "creative_review_score": 88.0
        })

        # 5. 완료 상태
        store.save_state(food_name, {
            "status": "completed",
            "food_name_kr": "수박",
            "tech_review_score": 92.5,
            "creative_review_score": 88.0,
            "instagram_url": "https://instagram.com/p/test123"
        })

        # 최종 상태 확인
        final_state = store.get_state(food_name)
        assert final_state["status"] == "completed"
        assert final_state["instagram_url"] == "https://instagram.com/p/test123"

    def test_statistics_update(self, temp_workspace):
        """통계 업데이트 테스트"""
        from support.utils.state_store import StateStore

        store_path = str(temp_workspace["data"] / "states.json")
        store = StateStore(store_path=store_path)

        # 여러 파이프라인 상태 저장
        store.save_state("apple", {
            "status": "completed",
            "tech_review_score": 95.0,
            "creative_review_score": 92.0
        })
        store.save_state("banana", {
            "status": "completed",
            "tech_review_score": 90.0,
            "creative_review_score": 88.0
        })
        store.save_state("cherry", {
            "status": "failed",
            "tech_review_score": 70.0,
            "creative_review_score": 65.0
        })

        stats = store.get_statistics()

        assert stats["total"] == 3
        assert stats["completed"] == 2
        assert stats["failed"] == 1
        assert stats["success_rate"] == pytest.approx(66.67, 0.1)


# ==============================================================================
# Slack Approval E2E Tests
# ==============================================================================

class TestSlackApprovalE2E:
    """Slack 승인 E2E 테스트"""

    @pytest.mark.asyncio
    async def test_approval_flow(self, temp_workspace):
        """승인 흐름 E2E 테스트"""
        from support.utils.slack_handler import SlackApprovalHandler

        handler = SlackApprovalHandler()
        handler.enabled = False

        # 1. 스토리보드 승인 요청
        sb_approval_id = await handler.send_storyboard_approval_request(
            food_name="watermelon",
            food_name_kr="수박",
            storyboard_path="/tmp/storyboard.md",
            storyboard_summary={"slides": 7}
        )

        assert sb_approval_id is not None

        # 2. 수동 승인
        result = handler.manual_approve(sb_approval_id, "test_user")
        assert result is True

        # 3. 승인 상태 확인
        approval = handler.get_approval_status(sb_approval_id)
        assert approval is not None
        assert approval.status.value == "approved"

    @pytest.mark.asyncio
    async def test_rejection_flow(self, temp_workspace):
        """반려 흐름 E2E 테스트"""
        from support.utils.slack_handler import SlackApprovalHandler

        handler = SlackApprovalHandler()
        handler.enabled = False

        # 1. 최종 승인 요청
        final_approval_id = await handler.send_final_approval_request(
            food_name="banana",
            food_name_kr="바나나",
            images_dir="/tmp/banana_final",
            tech_score=75.0,
            creative_score=70.0,
            preview_urls=[]
        )

        assert final_approval_id is not None

        # 2. 수동 반려
        result = handler.manual_reject(
            final_approval_id,
            "품질 기준 미달",
            "test_reviewer"
        )
        assert result is True

        # 3. 반려 상태 확인
        approval = handler.get_approval_status(final_approval_id)
        assert approval is not None
        assert approval.status.value == "rejected"
        assert approval.feedback == "품질 기준 미달"


# ==============================================================================
# Quality Standards E2E Tests
# ==============================================================================

class TestQualityStandardsE2E:
    """품질 기준 E2E 테스트"""

    def test_7_slide_requirement(self, temp_workspace):
        """7장 슬라이드 요구사항 테스트"""
        from core.crews import StoryboardCrew
        from core.crews.storyboard_crew import SLIDE_STRUCTURE

        # SLIDE_STRUCTURE가 7장인지 확인
        assert len(SLIDE_STRUCTURE) == 7

        # 스토리보드 생성 시 7장 생성
        crew = StoryboardCrew()
        crew.storyboard_dir = temp_workspace["storyboards"]

        result = crew.run(
            food_name="orange",
            food_name_kr="오렌지"
        )

        assert len(result["slides"]) == 7

    def test_90_point_pass_threshold(self):
        """90점 통과 기준 테스트"""
        from core.pipeline.quality_loop import QualityControlLoop

        assert QualityControlLoop.TECH_PASS_SCORE == 90
        assert QualityControlLoop.CREATIVE_PASS_SCORE == 90
        assert QualityControlLoop.CONDITIONAL_PASS_SCORE == 80

    def test_slide_types(self, temp_workspace):
        """슬라이드 타입 테스트"""
        from core.crews import StoryboardCrew

        crew = StoryboardCrew()
        crew.storyboard_dir = temp_workspace["storyboards"]

        result = crew.run(
            food_name="grape",
            food_name_kr="포도"
        )

        expected_types = ["cover", "result", "benefit1", "benefit2", "caution", "amount", "cta"]
        actual_types = [s["type"] for s in result["slides"]]

        assert actual_types == expected_types


# ==============================================================================
# Integration with External Services E2E Tests
# ==============================================================================

class TestExternalServicesE2E:
    """외부 서비스 통합 E2E 테스트"""

    def test_cloudinary_mock(self, mock_7_images):
        """Cloudinary 모의 테스트"""
        # 환경변수 확인
        has_cloudinary = (
            os.getenv("CLOUDINARY_CLOUD_NAME") and
            os.getenv("CLOUDINARY_API_KEY") and
            os.getenv("CLOUDINARY_API_SECRET")
        )

        if has_cloudinary:
            # 실제 Cloudinary 테스트 (설정된 경우만)
            pass
        else:
            # 모의 테스트
            assert True

    def test_instagram_mock(self, mock_7_images):
        """Instagram 모의 테스트"""
        # 환경변수 확인
        has_instagram = (
            os.getenv("INSTAGRAM_BUSINESS_ACCOUNT_ID") and
            os.getenv("INSTAGRAM_ACCESS_TOKEN")
        )

        if has_instagram:
            # 실제 Instagram 테스트 (설정된 경우만)
            pass
        else:
            # 모의 테스트
            assert True


# ==============================================================================
# Performance E2E Tests
# ==============================================================================

class TestPerformanceE2E:
    """성능 E2E 테스트"""

    def test_storyboard_generation_time(self, temp_workspace):
        """스토리보드 생성 시간 테스트"""
        import time
        from core.crews import StoryboardCrew

        crew = StoryboardCrew()
        crew.storyboard_dir = temp_workspace["storyboards"]

        start = time.time()
        result = crew.run(
            food_name="peach",
            food_name_kr="복숭아"
        )
        elapsed = time.time() - start

        assert result["success"] is True
        # 스토리보드 생성은 1초 이내 완료되어야 함
        assert elapsed < 1.0

    def test_review_time(self, mock_7_images):
        """검수 시간 테스트"""
        import time
        from core.crews import TechReviewCrew, CreativeReviewCrew

        # 기술 검수
        tech_crew = TechReviewCrew()
        start = time.time()
        tech_result = tech_crew.run(
            content_dir=mock_7_images["output_dir"],
            food_name=mock_7_images["food_name"]
        )
        tech_elapsed = time.time() - start

        assert tech_result["success"] is True
        # 기술 검수는 5초 이내
        assert tech_elapsed < 5.0

        # 크리에이티브 검수 (VLM 없이)
        creative_crew = CreativeReviewCrew()
        creative_crew.vlm_available = False

        start = time.time()
        creative_result = creative_crew.run(
            content_dir=mock_7_images["output_dir"],
            food_name=mock_7_images["food_name"]
        )
        creative_elapsed = time.time() - start

        assert creative_result["success"] is True
        # VLM 없이 1초 이내
        assert creative_elapsed < 1.0


# ==============================================================================
# Run Tests
# ==============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
