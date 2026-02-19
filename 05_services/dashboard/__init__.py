"""
Project Sunshine - Dashboard Module

대시보드 및 상태 업데이트 모듈

사용법:
    # 상태 업데이트
    from services.dashboard import status_updater as dashboard

    dashboard.start_pipeline("cherry")
    dashboard.start_step("김차장")
    dashboard.complete_step("김차장", duration=5.0)
    dashboard.finish_pipeline()

    # 터미널 대시보드 실행
    python -m dashboard.cli_dashboard

    # 웹 대시보드 실행
    streamlit run dashboard/streamlit_app.py
"""

from . import status_updater

__all__ = ["status_updater"]
