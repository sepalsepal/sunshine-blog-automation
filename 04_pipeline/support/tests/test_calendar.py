"""
캘린더 모듈 테스트

Author: 최검증
Date: 2026-01-30
"""

import pytest
from datetime import datetime
from pathlib import Path
import sys

# 프로젝트 루트 추가
ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))


class TestCalendarView:
    """캘린더 뷰 모듈 테스트"""

    def test_status_colors_defined(self):
        """상태별 색상이 정의되어 있는지 확인"""
        from services.dashboard._modules.calendar_view import STATUS_COLORS

        assert "pending" in STATUS_COLORS
        assert "scheduled" in STATUS_COLORS
        assert "completed" in STATUS_COLORS
        assert "published" in STATUS_COLORS

    def test_status_emoji_defined(self):
        """상태별 이모지가 정의되어 있는지 확인"""
        from services.dashboard._modules.calendar_view import STATUS_EMOJI

        assert "pending" in STATUS_EMOJI
        assert "scheduled" in STATUS_EMOJI
        assert "completed" in STATUS_EMOJI

    def test_load_schedule_returns_dict(self):
        """스케줄 로드가 딕셔너리를 반환하는지 확인"""
        from services.dashboard._modules.calendar_view import load_schedule

        schedule = load_schedule()
        assert isinstance(schedule, dict)
        assert "scheduled" in schedule or schedule == {"scheduled": [], "completed": [], "failed": [], "settings": {}}

    def test_load_history_returns_dict(self):
        """히스토리 로드가 딕셔너리를 반환하는지 확인"""
        from services.dashboard._modules.calendar_view import load_history

        history = load_history()
        assert isinstance(history, dict)

    def test_get_month_data_returns_dict(self):
        """월간 데이터가 딕셔너리를 반환하는지 확인"""
        from services.dashboard._modules.calendar_view import get_month_data

        data = get_month_data(2026, 1)
        assert isinstance(data, dict)


class TestGalleryView:
    """갤러리 뷰 모듈 테스트"""

    def test_thumbnail_path_generation(self):
        """썸네일 경로 생성 테스트"""
        from services.dashboard._modules.gallery_view import get_thumbnail_path

        test_path = Path("/test/image.jpg")
        thumb_path = get_thumbnail_path(test_path, (200, 200))

        assert "200x200" in thumb_path.name
        assert thumb_path.suffix == ".jpg"

    def test_get_images_by_category_returns_list(self):
        """카테고리별 이미지 조회가 리스트를 반환하는지 확인"""
        from services.dashboard._modules.gallery_view import get_images_by_category

        images = get_images_by_category("best_cta")
        assert isinstance(images, list)


class TestApiCosts:
    """API 비용 모듈 테스트"""

    def test_module_imports(self):
        """모듈 import 테스트"""
        from services.dashboard._modules.api_costs import (
            format_currency,
            format_krw
        )
        assert callable(format_currency)
        assert callable(format_krw)

    def test_format_currency(self):
        """통화 포맷 테스트"""
        from services.dashboard._modules.api_costs import format_currency
        result = format_currency(1.5)
        assert "$" in result

    def test_format_krw(self):
        """원화 변환 테스트"""
        from services.dashboard._modules.api_costs import format_krw
        result = format_krw(1.0, 1400)
        assert "₩" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
