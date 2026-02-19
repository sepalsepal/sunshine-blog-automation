"""
Project Sunshine Backend API Server
FastAPI 기반 파이프라인 제어 서버

실행: python -m uvicorn api.server:app --reload --port 8000
"""

# .env 파일 자동 로드
from dotenv import load_dotenv
load_dotenv()

import asyncio
import uuid
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import json

# 프로젝트 루트 추가
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.api.models import (
    PipelineStartRequest, PipelineStartResponse, PipelineProgress,
    PipelineResultResponse, PipelineStatus, StageProgress,
    TopicExploreRequest, TopicExploreResponse, TopicInfo,
    ApprovalRequest, QualityGateResult, QualityGateType,
    HealthResponse
)

# ============================================================
# 글로벌 상태 관리
# ============================================================

# 파이프라인 실행 상태 저장
pipeline_states: Dict[str, Dict] = {}

# WebSocket 연결 관리
websocket_connections: Dict[str, WebSocket] = {}

# 서버 시작 시간
SERVER_START_TIME = time.time()

# ============================================================
# 애플리케이션 설정
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 수명주기 관리"""
    # Startup
    print("🌟 Project Sunshine API Server 시작")
    print(f"   버전: v5.0")
    print(f"   시간: {datetime.now().isoformat()}")
    yield
    # Shutdown
    print("🌙 Project Sunshine API Server 종료")


app = FastAPI(
    title="Project Sunshine API",
    description="햇살이 강아지 음식 정보 Instagram 자동화 API",
    version="5.0.0",
    lifespan=lifespan
)

# CORS 설정 (프론트엔드 연동용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 개발용, 프로덕션에서는 제한 필요
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 템플릿 설정
WEB_DIR = Path(__file__).parent.parent / "web"
templates = Jinja2Templates(directory=str(WEB_DIR / "templates"))

# 정적 파일 설정 (CSS, JS)
if (WEB_DIR / "static").exists():
    app.mount("/static", StaticFiles(directory=str(WEB_DIR / "static")), name="static")


# ============================================================
# 웹 페이지 라우트
# ============================================================

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """대시보드 페이지"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/create", response_class=HTMLResponse)
async def create_page(request: Request):
    """콘텐츠 제작 페이지"""
    return templates.TemplateResponse("create.html", {"request": request})


@app.get("/history", response_class=HTMLResponse)
async def history_page(request: Request):
    """제작 이력 페이지"""
    # TODO: history.html 템플릿 구현
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/preview/{pipeline_id}", response_class=HTMLResponse)
async def preview_page(request: Request, pipeline_id: str):
    """파이널 승인 미리보기 페이지"""
    from fastapi.responses import RedirectResponse
    import traceback

    try:
        # 파이프라인 데이터 조회
        if pipeline_id not in pipeline_states:
            return RedirectResponse(url="/")

        state = pipeline_states[pipeline_id]
        result = state.get("result", {}) or {}

        # 이미지 파일 목록 가져오기
        topic = state.get("topic", "unknown")
        output_dir = Path(__file__).parent.parent / "outputs" / topic

        images = []
        if output_dir.exists():
            for f in sorted(output_dir.glob("*.png")):
                images.append(f.name)

        # 품질 점수 (기본값 설정으로 템플릿 에러 방지)
        quality_scores = {"G1": 0, "G2": 0, "G3": 0}
        quality_scores.update(result.get("quality_scores", {}) or {})

        # stages에서 점수 추출 시도
        for stage in state.get("stages", []):
            # StageProgress 객체 또는 딕셔너리 모두 처리
            stage_name = stage.stage_name if hasattr(stage, 'stage_name') else stage.get('stage_name', '')
            stage_score = stage.score if hasattr(stage, 'score') else stage.get('score')

            if stage_score and "기획" in stage_name:
                quality_scores["G1"] = stage_score
            elif stage_score and "이미지" in stage_name:
                quality_scores["G2"] = stage_score
            elif stage_score and "합성" in stage_name:
                quality_scores["G3"] = stage_score

        # 평균 점수 계산
        valid_scores = [v for v in quality_scores.values() if v and v > 0]
        avg_score = sum(valid_scores) // len(valid_scores) if valid_scores else 0

        return templates.TemplateResponse("preview.html", {
            "request": request,
            "pipeline_id": pipeline_id,
            "topic": topic,
            "score": avg_score,
            "images": images,
            "caption": result.get("caption", "") or "",
            "hashtags": result.get("hashtags", []) or [],
            "quality_scores": quality_scores
        })
    except Exception as e:
        print(f"[PREVIEW ERROR] {pipeline_id}: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/images/{topic}/{filename}")
async def serve_image(topic: str, filename: str):
    """이미지 파일 서빙"""
    from fastapi.responses import FileResponse

    # outputs 폴더에서 먼저 확인
    output_path = Path(__file__).parent.parent / "outputs" / topic / filename
    if output_path.exists():
        return FileResponse(output_path)

    # images 폴더에서 확인 (기존 콘텐츠)
    images_path = Path(__file__).parent.parent / "images"
    # 폴더명 패턴: NNN_topic
    for folder in images_path.iterdir():
        if folder.is_dir() and topic in folder.name:
            file_path = folder / filename
            if file_path.exists():
                return FileResponse(file_path)

    raise HTTPException(status_code=404, detail="이미지를 찾을 수 없습니다")


# ============================================================
# 헬스체크 엔드포인트
# ============================================================

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """서버 상태 확인 (k8s/docker 헬스체크용)"""
    return HealthResponse(
        status="healthy",
        version="5.0.0",
        agents_loaded=8,  # 8개 에이전트
        uptime_seconds=time.time() - SERVER_START_TIME
    )


# ============================================================
# 주제 탐색 엔드포인트
# ============================================================

@app.post("/api/topics/explore", response_model=TopicExploreResponse)
async def explore_topics(request: TopicExploreRequest):
    """
    주제 탐색 (1~2단계)
    - 기제작 목록 스캔
    - 추천 주제 생성
    """
    try:
        # 1. 기제작 목록 확인
        images_dir = Path(__file__).parent.parent / "images"
        existing = []

        if images_dir.exists():
            for folder in images_dir.iterdir():
                if folder.is_dir() and not folder.name.startswith('.'):
                    # 폴더명에서 주제 추출 (예: 012_mango -> mango)
                    parts = folder.name.split('_')
                    if len(parts) >= 2:
                        existing.append(parts[-1])
                    else:
                        existing.append(folder.name)

        # 2. topics_expanded.json에서 추천 주제 로드
        topics_file = Path(__file__).parent.parent / "config" / "topics_expanded.json"
        recommended = []
        total_available = 0

        if topics_file.exists():
            with open(topics_file) as f:
                topics_data = json.load(f)

            categories = topics_data.get("categories", {})

            for category_name, category_data in categories.items():
                # topics_expanded.json 구조: {label, count, topics: [...]}
                topics_list = category_data.get("topics", [])
                category_label = category_data.get("label", category_name)

                for item in topics_list:
                    total_available += 1
                    topic_name = item.get("id", "")  # id가 영문명

                    # 기제작 여부 확인
                    already_created = topic_name.lower() in [e.lower() for e in existing]

                    # 제외 옵션 적용
                    if request.exclude_existing and already_created:
                        continue

                    if len(recommended) < request.count:
                        recommended.append(TopicInfo(
                            name_en=topic_name,
                            name_kr=item.get("ko", topic_name),  # ko가 한글명
                            category=category_label,
                            safety=item.get("safety", "unknown"),
                            already_created=already_created
                        ))

        return TopicExploreResponse(
            existing_topics=existing,
            recommended_topics=recommended,
            total_available=total_available
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/topics/{topic}/validate")
async def validate_topic(topic: str):
    """
    주제 유효성 검증
    - 안전도 확인
    - 기제작 여부 확인
    """
    try:
        # topics_expanded.json에서 주제 검색
        topics_file = Path(__file__).parent.parent / "config" / "topics_expanded.json"

        if not topics_file.exists():
            raise HTTPException(status_code=404, detail="주제 데이터베이스 없음")

        with open(topics_file) as f:
            topics_data = json.load(f)

        # 주제 검색
        for category_name, category_data in topics_data.get("categories", {}).items():
            topics_list = category_data.get("topics", [])
            category_label = category_data.get("label", category_name)

            for item in topics_list:
                if item.get("id", "").lower() == topic.lower():
                    return {
                        "valid": True,
                        "topic": topic,
                        "name_kr": item.get("ko"),
                        "category": category_label,
                        "safety": item.get("safety", "unknown"),
                        "can_proceed": item.get("safety") == "safe"
                    }

        return {
            "valid": False,
            "topic": topic,
            "message": "주제를 찾을 수 없습니다",
            "can_proceed": False
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# 파이프라인 실행 엔드포인트
# ============================================================

@app.post("/api/pipeline/start", response_model=PipelineStartResponse)
async def start_pipeline(request: PipelineStartRequest, background_tasks: BackgroundTasks):
    """
    파이프라인 시작
    - 비동기 백그라운드 실행
    - WebSocket으로 진행 상황 전송
    """
    pipeline_id = str(uuid.uuid4())[:8]

    # 초기 상태 저장
    pipeline_states[pipeline_id] = {
        "id": pipeline_id,
        "topic": request.topic,
        "status": PipelineStatus.PENDING,
        "current_stage": 0,
        "total_stages": 12,
        "stages": [],
        "quality_gates": [],
        "started_at": datetime.now(),
        "config": request.model_dump(),
        "error": None,
        "result": None
    }

    # 백그라운드에서 파이프라인 실행
    background_tasks.add_task(run_pipeline_background, pipeline_id, request)

    return PipelineStartResponse(
        pipeline_id=pipeline_id,
        topic=request.topic,
        status=PipelineStatus.PENDING,
        message=f"파이프라인 시작됨: {request.topic}",
        websocket_url=f"/ws/pipeline/{pipeline_id}"
    )


async def run_pipeline_background(pipeline_id: str, request: PipelineStartRequest):
    """백그라운드 파이프라인 실행"""
    try:
        state = pipeline_states[pipeline_id]
        state["status"] = PipelineStatus.RUNNING

        # 실제 파이프라인 임포트 및 실행
        from core.pipeline.pipeline_v5 import SunshinePipelineV5

        pipeline = SunshinePipelineV5()

        # 진행 상황 콜백 설정
        async def progress_callback(stage: int, name: str, status: str, score: int = None):
            state["current_stage"] = stage
            state["stages"].append(StageProgress(
                stage_number=stage,
                stage_name=name,
                status=status,
                score=score,
                started_at=datetime.now() if status == "running" else None,
                completed_at=datetime.now() if status in ["completed", "failed"] else None
            ))

            # WebSocket으로 전송
            if pipeline_id in websocket_connections:
                try:
                    await websocket_connections[pipeline_id].send_json({
                        "type": "progress",
                        "stage": stage,
                        "name": name,
                        "status": status,
                        "score": score
                    })
                except:
                    pass

        # 파이프라인 실행 (콜백 및 ID 전달)
        result = await pipeline.run(
            topic=request.topic,
            skip_publish=request.skip_publish,
            skip_approval=request.skip_approval,
            force=request.force,
            pipeline_id=pipeline_id,
            progress_callback=progress_callback
        )

        if result.get("success"):
            # 파이프라인 결과에서 필요한 데이터 추출
            pipeline_results = result.get("results", {})

            # 품질 점수 추출
            quality_scores = {}
            if "gate_scores" in pipeline_results:
                gate_scores = pipeline_results["gate_scores"]
                quality_scores["G1"] = gate_scores.get("G1", {}).get("total_score", 0)
                quality_scores["G2"] = gate_scores.get("G2", {}).get("total_score", 0)
                quality_scores["G3"] = gate_scores.get("G3", {}).get("total_score", 0)

            # 출력 이미지 목록
            overlay_data = pipeline_results.get("overlay", {})
            output_images = overlay_data.get("output_images", [])

            # 캡션 데이터
            caption_data = pipeline_results.get("caption", {})
            caption_text = caption_data.get("caption", "")
            hashtags = caption_data.get("hashtags", [])

            state["result"] = {
                "success": True,
                "quality_scores": quality_scores,
                "output_images": output_images,
                "caption": caption_text,
                "hashtags": hashtags,
                "total_time": result.get("total_time", 0),
                "preview_url": result.get("preview_url"),
                "raw_results": pipeline_results  # 디버깅용
            }

            # 승인 대기 상태 확인
            if result.get("awaiting_approval"):
                state["status"] = PipelineStatus.AWAITING_APPROVAL
                print(f"[PIPELINE] {pipeline_id}: 승인 대기 상태로 전환")
            else:
                state["status"] = PipelineStatus.COMPLETED
        else:
            state["status"] = PipelineStatus.FAILED
            state["error"] = result.get("error", "Unknown error")

    except Exception as e:
        pipeline_states[pipeline_id]["status"] = PipelineStatus.FAILED
        pipeline_states[pipeline_id]["error"] = str(e)


@app.get("/api/pipeline/{pipeline_id}/status", response_model=PipelineProgress)
async def get_pipeline_status(pipeline_id: str):
    """파이프라인 진행 상황 조회"""
    if pipeline_id not in pipeline_states:
        raise HTTPException(status_code=404, detail="파이프라인을 찾을 수 없습니다")

    state = pipeline_states[pipeline_id]

    return PipelineProgress(
        pipeline_id=pipeline_id,
        topic=state["topic"],
        status=state["status"],
        current_stage=state["current_stage"],
        total_stages=state["total_stages"],
        stages=state.get("stages", []),
        quality_gates=state.get("quality_gates", []),
        started_at=state["started_at"],
        error=state.get("error")
    )


@app.get("/api/pipeline/{pipeline_id}/result", response_model=PipelineResultResponse)
async def get_pipeline_result(pipeline_id: str):
    """파이프라인 결과 조회"""
    if pipeline_id not in pipeline_states:
        raise HTTPException(status_code=404, detail="파이프라인을 찾을 수 없습니다")

    state = pipeline_states[pipeline_id]

    if state["status"] not in [PipelineStatus.COMPLETED, PipelineStatus.FAILED]:
        raise HTTPException(status_code=400, detail="파이프라인이 아직 완료되지 않았습니다")

    result = state.get("result", {})

    return PipelineResultResponse(
        pipeline_id=pipeline_id,
        topic=state["topic"],
        status=state["status"],
        total_time_seconds=(datetime.now() - state["started_at"]).total_seconds(),
        quality_scores=result.get("quality_scores", {}),
        output_images=result.get("output_images", []),
        caption=result.get("caption"),
        hashtags=result.get("hashtags", []),
        published=result.get("published", False)
    )


@app.post("/api/pipeline/{pipeline_id}/cancel")
async def cancel_pipeline(pipeline_id: str):
    """파이프라인 취소"""
    if pipeline_id not in pipeline_states:
        raise HTTPException(status_code=404, detail="파이프라인을 찾을 수 없습니다")

    state = pipeline_states[pipeline_id]

    if state["status"] == PipelineStatus.RUNNING:
        state["status"] = PipelineStatus.FAILED
        state["error"] = "사용자에 의해 취소됨"
        return {"message": "파이프라인 취소됨", "pipeline_id": pipeline_id}

    return {"message": "취소할 수 없는 상태", "status": state["status"]}


# ============================================================
# PD 승인 엔드포인트
# ============================================================

@app.post("/api/pipeline/{pipeline_id}/approve")
async def approve_pipeline(pipeline_id: str, request: ApprovalRequest, background_tasks: BackgroundTasks):
    """PD 승인 처리"""
    if pipeline_id not in pipeline_states:
        raise HTTPException(status_code=404, detail="파이프라인을 찾을 수 없습니다")

    state = pipeline_states[pipeline_id]

    if state["status"] != PipelineStatus.AWAITING_APPROVAL:
        raise HTTPException(status_code=400, detail="승인 대기 상태가 아닙니다")

    if request.approved:
        # 승인됨
        state["approval"] = {
            "approved": True,
            "approved_at": datetime.now().isoformat()
        }

        # 원래 요청에서 skip_publish 확인
        original_config = state.get("config", {})
        skip_publish = original_config.get("skip_publish", True)

        if skip_publish:
            # 드라이런 모드 - 게시 스킵, 바로 완료
            state["status"] = PipelineStatus.COMPLETED
            state["result"]["published"] = False
            return {
                "message": "승인 완료 (게시 스킵됨 - 드라이런 모드)",
                "pipeline_id": pipeline_id,
                "published": False
            }
        else:
            # 실제 게시 진행 (백그라운드)
            state["status"] = PipelineStatus.RUNNING
            background_tasks.add_task(run_publish_background, pipeline_id)
            return {
                "message": "승인됨, 게시 진행 중",
                "pipeline_id": pipeline_id
            }
    else:
        # 거절됨
        state["status"] = PipelineStatus.FAILED
        state["error"] = f"PD 거절: {request.feedback}"
        return {"message": "거절됨", "feedback": request.feedback}


async def run_publish_background(pipeline_id: str):
    """백그라운드 게시 실행"""
    try:
        state = pipeline_states[pipeline_id]
        topic = state.get("topic", "unknown")
        result = state.get("result", {})
        raw_results = result.get("raw_results", {})

        # 게시 에이전트 실행
        from core.agents import PublisherAgent
        publisher = PublisherAgent()

        publish_input = {
            **raw_results.get("overlay", {}),
            "topic": topic,
            "passed": True
        }
        publish_result = await publisher.run(publish_input)

        if publish_result.success:
            state["status"] = PipelineStatus.COMPLETED
            state["result"]["published"] = True
            state["result"]["instagram_url"] = publish_result.data.get("publish_results", {}).get("instagram", {}).get("permalink", "")
            print(f"[PUBLISH] {pipeline_id}: 게시 완료")
        else:
            state["status"] = PipelineStatus.FAILED
            state["error"] = f"게시 실패: {publish_result.error}"
            print(f"[PUBLISH] {pipeline_id}: 게시 실패 - {publish_result.error}")

    except Exception as e:
        pipeline_states[pipeline_id]["status"] = PipelineStatus.FAILED
        pipeline_states[pipeline_id]["error"] = f"게시 오류: {str(e)}"
        print(f"[PUBLISH] {pipeline_id}: 오류 - {e}")


# ============================================================
# WebSocket 엔드포인트 (실시간 진행 상황)
# ============================================================

@app.websocket("/ws/pipeline/{pipeline_id}")
async def pipeline_websocket(websocket: WebSocket, pipeline_id: str):
    """파이프라인 진행 상황 실시간 스트리밍"""
    await websocket.accept()
    websocket_connections[pipeline_id] = websocket

    try:
        while True:
            # 클라이언트로부터 메시지 대기 (ping/pong)
            data = await websocket.receive_text()

            if data == "ping":
                await websocket.send_text("pong")
            elif data == "status":
                if pipeline_id in pipeline_states:
                    state = pipeline_states[pipeline_id]
                    await websocket.send_json({
                        "type": "status",
                        "status": state["status"],
                        "current_stage": state["current_stage"]
                    })

    except WebSocketDisconnect:
        if pipeline_id in websocket_connections:
            del websocket_connections[pipeline_id]


# ============================================================
# 기타 유틸리티 엔드포인트
# ============================================================

@app.get("/api/agents")
async def list_agents():
    """에이전트 목록 조회"""
    return {
        "agents": [
            {"name": "김차장", "role": "기획", "type": "PlannerAgent"},
            {"name": "최검증", "role": "팩트체크", "type": "FactCheckerAgent"},
            {"name": "김작가", "role": "텍스트", "type": "TextAgent"},
            {"name": "이작가", "role": "이미지", "type": "ImageGeneratorAgent"},
            {"name": "박편집", "role": "편집", "type": "TextOverlayAgent"},
            {"name": "박과장", "role": "검수", "type": "QualityCheckerAgent"},
            {"name": "이카피", "role": "캡션", "type": "CaptionAgent"},
            {"name": "김대리", "role": "게시", "type": "PublisherAgent"},
        ],
        "total": 8
    }


@app.get("/api/pipelines")
async def list_pipelines():
    """실행 중/완료된 파이프라인 목록"""
    return {
        "pipelines": [
            {
                "id": pid,
                "topic": state["topic"],
                "status": state["status"],
                "started_at": state["started_at"].isoformat()
            }
            for pid, state in pipeline_states.items()
        ],
        "total": len(pipeline_states)
    }


# ============================================================
# 실행
# ============================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.server:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
