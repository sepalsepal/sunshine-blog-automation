"""
Slack 이벤트 수신 서버
Phase 5: FastAPI 기반 웹훅 처리

Endpoints:
- POST /slack/interactions: 버튼 클릭 등 인터랙션 처리
- POST /slack/events: 이벤트 구독 (URL 검증 포함)
- POST /slack/commands: 슬래시 커맨드 처리
- GET /health: 헬스 체크
- GET /status: 파이프라인 상태 조회
"""

import os
import json
import hmac
import hashlib
import asyncio
from datetime import datetime
from typing import Optional
from pathlib import Path

try:
    from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
    from fastapi.responses import JSONResponse
    from fastapi.middleware.cors import CORSMiddleware
    import uvicorn
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    print("[Warning] FastAPI not installed. Run: pip install fastapi uvicorn")

import sys
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

if FASTAPI_AVAILABLE:
    from integrations.slack_handler import SlackApprovalHandler, ApprovalStatus

    app = FastAPI(
        title="Project Sunshine Approval Server",
        description="햇살이 콘텐츠 자동화 승인 서버",
        version="1.0.0"
    )

    # CORS 설정
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Slack 핸들러 (글로벌)
    slack_handler = SlackApprovalHandler()

    # 파이프라인 상태 저장소 참조
    try:
        from support.utils.state_store import StateStore
        state_store = StateStore()
    except ImportError:
        state_store = None

    @app.get("/")
    async def root():
        """루트 엔드포인트"""
        return {
            "name": "Project Sunshine Approval Server",
            "version": "1.0.0",
            "status": "running",
            "slack_enabled": slack_handler.enabled
        }

    @app.get("/health")
    async def health_check():
        """헬스 체크"""
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "slack_connected": slack_handler.enabled
        }

    @app.post("/slack/interactions")
    async def handle_slack_interactions(request: Request):
        """
        Slack 인터랙션 엔드포인트

        버튼 클릭, 모달 제출 등 처리
        """
        body = await request.body()

        # 서명 검증
        if not verify_slack_signature(request, body):
            raise HTTPException(status_code=401, detail="Invalid signature")

        # 페이로드 파싱
        form_data = await request.form()
        payload_str = form_data.get("payload", "{}")
        payload = json.loads(payload_str)

        interaction_type = payload.get("type")

        # 인터랙션 타입별 처리
        if interaction_type == "block_actions":
            # 버튼 클릭
            result = await slack_handler.handle_interaction(payload)
            return JSONResponse(result if result else {"ok": True})

        elif interaction_type == "view_submission":
            # 모달 제출 (반려 피드백)
            result = await slack_handler.handle_modal_submission(payload)
            return JSONResponse(result if result else {"ok": True})

        elif interaction_type == "view_closed":
            # 모달 닫힘
            return JSONResponse({"ok": True})

        return JSONResponse({"ok": True})

    @app.post("/slack/events")
    async def handle_slack_events(request: Request):
        """
        Slack 이벤트 엔드포인트

        URL 검증 및 이벤트 수신
        """
        body = await request.body()
        data = json.loads(body)

        # URL 검증 (Slack 앱 설정 시 필요)
        if data.get("type") == "url_verification":
            return JSONResponse({"challenge": data.get("challenge")})

        # 이벤트 처리
        event = data.get("event", {})
        event_type = event.get("type")

        if event_type == "message":
            # 메시지 이벤트 (필요시 처리)
            pass

        elif event_type == "reaction_added":
            # 리액션 추가 (이모지로 승인/반려 처리 가능)
            reaction = event.get("reaction")
            item = event.get("item", {})

            if reaction in ["white_check_mark", "heavy_check_mark", "+1"]:
                # 승인 이모지
                print(f"[Event] 승인 리액션: {reaction}")
            elif reaction in ["x", "no_entry", "-1"]:
                # 반려 이모지
                print(f"[Event] 반려 리액션: {reaction}")

        return JSONResponse({"ok": True})

    @app.post("/slack/commands")
    async def handle_slack_commands(request: Request):
        """
        Slack 슬래시 커맨드 엔드포인트

        /sunshine [action] [food_name]
        """
        form_data = await request.form()
        command = form_data.get("command")
        text = form_data.get("text", "").strip()
        user_id = form_data.get("user_id")
        user_name = form_data.get("user_name")

        if command == "/sunshine":
            return await handle_sunshine_command(text, user_id, user_name)

        return JSONResponse({
            "response_type": "ephemeral",
            "text": f"알 수 없는 명령어: {command}"
        })

    async def handle_sunshine_command(text: str, user_id: str, user_name: str) -> JSONResponse:
        """
        /sunshine 커맨드 처리

        사용법:
        - /sunshine status [food_name] - 상태 조회
        - /sunshine approve <approval_id> - 승인
        - /sunshine reject <approval_id> <reason> - 반려
        - /sunshine pending - 대기 중인 승인 목록
        - /sunshine help - 도움말
        """
        args = text.split(maxsplit=2)

        if not args:
            return JSONResponse({
                "response_type": "ephemeral",
                "text": get_help_text()
            })

        action = args[0].lower()

        if action == "help":
            return JSONResponse({
                "response_type": "ephemeral",
                "text": get_help_text()
            })

        elif action == "status":
            food_name = args[1] if len(args) > 1 else None
            return await get_status_response(food_name)

        elif action == "pending":
            pending = slack_handler.get_pending_approvals()
            if not pending:
                text = "대기 중인 승인 요청이 없습니다."
            else:
                text = f"*대기 중인 승인 요청 ({len(pending)}건):*\n"
                for approval in pending:
                    text += f"• `{approval.id}` - {approval.food_name_kr} ({approval.approval_type.value})\n"
            return JSONResponse({
                "response_type": "in_channel",
                "text": text
            })

        elif action == "approve":
            if len(args) < 2:
                return JSONResponse({
                    "response_type": "ephemeral",
                    "text": "사용법: /sunshine approve <approval_id>"
                })
            approval_id = args[1]
            success = slack_handler.manual_approve(approval_id, user_name)
            return JSONResponse({
                "response_type": "in_channel",
                "text": f"✅ 승인됨: `{approval_id}`" if success else f"⚠️ 승인 실패: `{approval_id}`"
            })

        elif action == "reject":
            if len(args) < 3:
                return JSONResponse({
                    "response_type": "ephemeral",
                    "text": "사용법: /sunshine reject <approval_id> <reason>"
                })
            approval_id = args[1]
            reason = args[2]
            success = slack_handler.manual_reject(approval_id, reason, user_name)
            return JSONResponse({
                "response_type": "in_channel",
                "text": f"❌ 반려됨: `{approval_id}`" if success else f"⚠️ 반려 실패: `{approval_id}`"
            })

        else:
            return JSONResponse({
                "response_type": "ephemeral",
                "text": f"알 수 없는 액션: {action}\n\n{get_help_text()}"
            })

    async def get_status_response(food_name: Optional[str]) -> JSONResponse:
        """파이프라인 상태 조회 응답"""
        if state_store is None:
            return JSONResponse({
                "response_type": "ephemeral",
                "text": "상태 저장소가 초기화되지 않았습니다."
            })

        if food_name:
            state = state_store.get_state(food_name)
            if state:
                text = f"*{food_name} 파이프라인 상태:*\n"
                text += f"• 상태: {state.get('status', 'unknown')}\n"
                text += f"• 기술 검수: {state.get('tech_review_score', 'N/A')}점\n"
                text += f"• 크리에이티브: {state.get('creative_review_score', 'N/A')}점\n"
                if state.get('instagram_url'):
                    text += f"• Instagram: {state['instagram_url']}"
            else:
                text = f"`{food_name}` 파이프라인을 찾을 수 없습니다."
        else:
            stats = state_store.get_statistics()
            text = f"*전체 파이프라인 현황:*\n"
            text += f"• 총: {stats.get('total', 0)}건\n"
            text += f"• 완료: {stats.get('completed', 0)}건\n"
            text += f"• 대기: {stats.get('pending', 0)}건\n"
            text += f"• 실패: {stats.get('failed', 0)}건\n"
            text += f"• 성공률: {stats.get('success_rate', 0):.1f}%"

        return JSONResponse({
            "response_type": "in_channel",
            "text": text
        })

    def get_help_text() -> str:
        """도움말 텍스트"""
        return """*🌻 Project Sunshine 명령어*

```
/sunshine status [food_name]  - 파이프라인 상태 조회
/sunshine pending             - 대기 중인 승인 목록
/sunshine approve <id>        - 승인
/sunshine reject <id> <사유>  - 반려
/sunshine help                - 도움말
```

*승인 ID 예시:*
• `sb_watermelon_1234567890` - 스토리보드 승인
• `final_watermelon_1234567890` - 최종 승인
"""

    def verify_slack_signature(request: Request, body: bytes) -> bool:
        """Slack 요청 서명 검증"""
        signing_secret = os.getenv("SLACK_SIGNING_SECRET")

        if not signing_secret:
            # 개발 모드: 서명 검증 스킵
            return True

        timestamp = request.headers.get("X-Slack-Request-Timestamp", "")
        signature = request.headers.get("X-Slack-Signature", "")

        if not timestamp or not signature:
            return False

        sig_basestring = f"v0:{timestamp}:{body.decode()}"
        my_signature = "v0=" + hmac.new(
            signing_secret.encode(),
            sig_basestring.encode(),
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(my_signature, signature)

    # API 엔드포인트: 승인 요청 생성 (외부에서 호출 가능)
    @app.post("/api/approval/storyboard")
    async def create_storyboard_approval(request: Request):
        """스토리보드 승인 요청 API"""
        data = await request.json()

        approval_id = await slack_handler.send_storyboard_approval_request(
            food_name=data["food_name"],
            food_name_kr=data["food_name_kr"],
            storyboard_path=data["storyboard_path"],
            storyboard_summary=data.get("storyboard_summary", {})
        )

        return JSONResponse({
            "approval_id": approval_id,
            "status": "pending"
        })

    @app.post("/api/approval/final")
    async def create_final_approval(request: Request):
        """최종 승인 요청 API"""
        data = await request.json()

        approval_id = await slack_handler.send_final_approval_request(
            food_name=data["food_name"],
            food_name_kr=data["food_name_kr"],
            images_dir=data["images_dir"],
            tech_score=data["tech_score"],
            creative_score=data["creative_score"],
            preview_urls=data.get("preview_urls", [])
        )

        return JSONResponse({
            "approval_id": approval_id,
            "status": "pending"
        })

    @app.get("/api/approval/{approval_id}")
    async def get_approval_status(approval_id: str):
        """승인 상태 조회 API"""
        approval = slack_handler.get_approval_status(approval_id)

        if not approval:
            raise HTTPException(status_code=404, detail="Approval not found")

        return JSONResponse(approval.to_dict())

    @app.get("/api/approvals/pending")
    async def get_pending_approvals():
        """대기 중인 승인 목록 API"""
        pending = slack_handler.get_pending_approvals()
        return JSONResponse({
            "count": len(pending),
            "approvals": [a.to_dict() for a in pending]
        })


def run_server(host: str = "0.0.0.0", port: int = 8000):
    """서버 실행"""
    if not FASTAPI_AVAILABLE:
        print("FastAPI가 설치되지 않았습니다.")
        print("설치: pip install fastapi uvicorn")
        return

    print(f"\n{'━'*50}")
    print(f"🌻 Project Sunshine Approval Server")
    print(f"{'━'*50}")
    print(f"   Host: {host}")
    print(f"   Port: {port}")
    print(f"   Slack: {'활성화' if slack_handler.enabled else '비활성화'}")
    print(f"{'━'*50}\n")

    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Project Sunshine Approval Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host")
    parser.add_argument("--port", type=int, default=8000, help="Port")

    args = parser.parse_args()

    run_server(host=args.host, port=args.port)
