"""
Dashboard Modules v1.0

대시보드 확장 모듈 패키지
- gallery_view: 이미지 갤러리 뷰
- calendar_view: 게시 스케줄 캘린더
"""

from .gallery_view import render_gallery_page, render_gallery_grid
from .calendar_view import render_calendar_page, render_month_calendar

__all__ = [
    'render_gallery_page',
    'render_gallery_grid',
    'render_calendar_page',
    'render_month_calendar',
]
