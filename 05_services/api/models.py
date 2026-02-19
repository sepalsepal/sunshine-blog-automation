"""
API Pydantic 모델 정의
Project Sunshine Backend API
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime


class PipelineStatus(str, Enum):
    """파이프라인 실행 상태"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    AWAITING_APPROVAL = "awaiting_approval"


class QualityGateType(str, Enum):
    """품질 게이트 타입"""
    G1 = "G1"  # 글 검수
    G2 = "G2"  # 이미지 검수
    G3 = "G3"  # 합성 검수


# ============================================================
# Request Models
# ============================================================

class PipelineStartRequest(BaseModel):
    """파이프라인 시작 요청"""
    topic: str = Field(..., description="콘텐츠 주제 (예: mango, cherry)")
    skip_publish: bool = Field(default=True, description="게시 스킵 여부")
    skip_approval: bool = Field(default=False, description="PD 승인 스킵 여부")
    force: bool = Field(default=False, description="기존 콘텐츠 덮어쓰기")
    dry_run: bool = Field(default=True, description="드라이런 모드")


class TopicExploreRequest(BaseModel):
    """주제 탐색 요청"""
    count: int = Field(default=5, description="추천 주제 개수", ge=1, le=20)
    exclude_existing: bool = Field(default=True, description="기제작 주제 제외")


class ApprovalRequest(BaseModel):
    """PD 승인 요청"""
    pipeline_id: str = Field(..., description="파이프라인 실행 ID")
    approved: bool = Field(..., description="승인 여부")
    feedback: Optional[str] = Field(None, description="피드백 (거절 시)")


# ============================================================
# Response Models
# ============================================================

class TopicInfo(BaseModel):
    """주제 정보"""
    name_en: str
    name_kr: str
    category: str
    safety: str
    already_created: bool = False


class TopicExploreResponse(BaseModel):
    """주제 탐색 응답"""
    existing_topics: List[str]
    recommended_topics: List[TopicInfo]
    total_available: int


class StageProgress(BaseModel):
    """단계별 진행 상황"""
    stage_number: int
    stage_name: str
    status: str  # pending, running, completed, failed
    score: Optional[int] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    retry_count: int = 0


class QualityGateResult(BaseModel):
    """품질 게이트 결과"""
    gate_type: QualityGateType
    score: int
    passed: bool
    criteria_scores: Dict[str, int]
    feedback: str
    issues: List[str]


class PipelineProgress(BaseModel):
    """파이프라인 진행 상황"""
    pipeline_id: str
    topic: str
    status: PipelineStatus
    current_stage: int
    total_stages: int
    stages: List[StageProgress]
    quality_gates: List[QualityGateResult]
    started_at: datetime
    estimated_completion: Optional[datetime] = None
    error: Optional[str] = None


class PipelineStartResponse(BaseModel):
    """파이프라인 시작 응답"""
    pipeline_id: str
    topic: str
    status: PipelineStatus
    message: str
    websocket_url: Optional[str] = None


class PipelineResultResponse(BaseModel):
    """파이프라인 결과 응답"""
    pipeline_id: str
    topic: str
    status: PipelineStatus
    total_time_seconds: float
    quality_scores: Dict[str, int]  # G1, G2, G3 점수
    output_images: List[str]
    caption: Optional[str] = None
    hashtags: List[str] = []
    preview_url: Optional[str] = None
    published: bool = False
    instagram_url: Optional[str] = None


class HealthResponse(BaseModel):
    """헬스체크 응답"""
    status: str
    version: str
    agents_loaded: int
    uptime_seconds: float
