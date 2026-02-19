"""
Crews for Project Sunshine
Phase 2: 6개 Crew 정의 완료

CrewAI 인터페이스 호환 (kickoff 메서드)
기존 agents/ 코드를 재사용

Pipeline:
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ 1.Storyboard │───▶│  2.Content   │───▶│3.TextOverlay │
│    Crew      │    │    Crew      │    │    Crew      │
└──────────────┘    └──────────────┘    └──────────────┘
       │                                       │
       ▼                                       ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   PD 승인    │    │5.Creative    │◀───│ 4.TechReview │
│  (수동)      │    │ ReviewCrew   │    │    Crew      │
└──────────────┘    └──────────────┘    └──────────────┘
                           │
                           ▼
                    ┌──────────────┐
                    │6.Publishing  │
                    │    Crew      │
                    └──────────────┘
"""

from .storyboard_crew import StoryboardCrew
from .content_crew import ContentCrew
from .text_overlay_crew import TextOverlayCrew
from .tech_review_crew import TechReviewCrew
from .creative_review_crew import CreativeReviewCrew
from .publishing_crew import PublishingCrew

# Legacy (deprecated)
from .review_crew import ReviewCrew

__all__ = [
    # Phase 2 - 6 Crews
    "StoryboardCrew",      # 1. 스토리보드 자동 생성
    "ContentCrew",         # 2. 이미지 생성
    "TextOverlayCrew",     # 3. 텍스트 오버레이
    "TechReviewCrew",      # 4. 기술 검수 (자동)
    "CreativeReviewCrew",  # 5. 크리에이티브 검수 (VLM)
    "PublishingCrew",      # 6. 게시
    # Legacy
    "ReviewCrew",
]
