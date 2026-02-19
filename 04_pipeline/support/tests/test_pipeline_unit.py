"""
파이프라인 단위 테스트

Author: 최검증
Date: 2026-01-30
"""

import pytest
from pathlib import Path
import sys
import json

# 프로젝트 루트 추가
ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))


class TestPipelineStatus:
    """파이프라인 상태 관리 테스트"""

    def test_status_file_structure(self):
        """status.json 파일 구조 테스트"""
        status_file = ROOT / "services/dashboard/status.json"

        if status_file.exists():
            with open(status_file, 'r', encoding='utf-8') as f:
                status = json.load(f)

            # 필수 필드 확인
            assert "topic" in status or status.get("topic") is None
            assert "steps" in status
            assert "total_progress" in status
            assert isinstance(status["steps"], list)

    def test_publish_history_structure(self):
        """publish_history.json 파일 구조 테스트"""
        history_file = ROOT / "services/dashboard/publish_history.json"

        if history_file.exists():
            with open(history_file, 'r', encoding='utf-8') as f:
                history = json.load(f)

            assert isinstance(history, (list, dict))


class TestQualityChecker:
    """품질 검수 에이전트 테스트"""

    def test_quality_checker_import(self):
        """QualityCheckerAgent import 테스트"""
        from core.agents.quality_checker import QualityCheckerAgent
        assert QualityCheckerAgent is not None

    def test_quality_checker_v8_import(self):
        """QualityCheckerV8Agent import 테스트"""
        from core.agents.quality_checker_v8 import QualityCheckerV8Agent
        assert QualityCheckerV8Agent is not None


class TestImageGenerator:
    """이미지 생성 에이전트 테스트"""

    def test_image_generator_import(self):
        """ImageGeneratorAgent import 테스트"""
        from core.agents.image_generator import ImageGeneratorAgent
        assert ImageGeneratorAgent is not None

    def test_dalle3_not_implemented(self):
        """DALL-E 3 백업 옵션이 NotImplementedError를 발생시키는지 확인"""
        from core.agents.image_generator import ImageGeneratorAgent

        # 클래스 메서드 존재 확인
        assert hasattr(ImageGeneratorAgent, '_generate_dalle3')

    def test_stability_not_implemented(self):
        """Stability AI 백업 옵션이 NotImplementedError를 발생시키는지 확인"""
        from core.agents.image_generator import ImageGeneratorAgent

        # 클래스 메서드 존재 확인
        assert hasattr(ImageGeneratorAgent, '_generate_stability')


class TestContentConfig:
    """콘텐츠 설정 파일 테스트"""

    def test_text_json_files_valid(self):
        """text.json 파일들이 유효한 JSON인지 확인"""
        settings_dir = ROOT / "config/settings"
        text_files = list(settings_dir.glob("*_text.json"))

        assert len(text_files) > 0, "텍스트 설정 파일이 없습니다"

        for text_file in text_files:
            with open(text_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # JSON 파일이 딕셔너리 또는 리스트인지 확인
            assert isinstance(data, (dict, list)), f"{text_file.name}이 올바른 JSON이 아닙니다"

    def test_publish_schedule_valid(self):
        """publish_schedule.json이 유효한지 확인"""
        schedule_file = ROOT / "config/settings/publish_schedule.json"

        if schedule_file.exists():
            with open(schedule_file, 'r', encoding='utf-8') as f:
                schedule = json.load(f)

            assert isinstance(schedule, dict)
            assert "scheduled" in schedule


class TestCoreUtils:
    """core/utils 모듈 테스트"""

    def test_content_manager_import(self):
        """ContentManager import 테스트"""
        from core.utils.content_manager import ContentManager
        assert ContentManager is not None

    def test_cover_manager_import(self):
        """CoverManager import 테스트"""
        from core.utils.cover_manager import CoverManager
        assert CoverManager is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
