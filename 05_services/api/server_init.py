"""
Server for Project Sunshine
Phase 5: Slack 웹훅 서버
"""

try:
    from .app import app, run_server
    __all__ = ["app", "run_server"]
except ImportError:
    # FastAPI 미설치 시
    __all__ = []
