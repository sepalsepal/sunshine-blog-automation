"""
Slack 인터랙션 핸들러
Phase 5: 승인 프로세스

- 승인 요청 메시지 전송
- 버튼 클릭 처리
- 승인/반려 상태 관리
- 피드백 수집

승인 포인트:
1. 스토리보드 승인 (김부장 검토 → PD님 승인)
2. 최종 승인 (PD님 최종 승인 → 게시)
"""

import os
import json
import hmac
import hashlib
import asyncio
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path

ROOT = Path(__file__).parent.parent

try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False


class ApprovalType(Enum):
    """승인 유형"""
    STORYBOARD = "storyboard"
    FINAL = "final"


class ApprovalStatus(Enum):
    """승인 상태"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    TIMEOUT = "timeout"


@dataclass
class ApprovalRequest:
    """승인 요청 데이터"""
    id: str
    food_name: str
    food_name_kr: str
    approval_type: ApprovalType
    status: ApprovalStatus = ApprovalStatus.PENDING
    requester: str = "system"
    reviewer: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    reviewed_at: Optional[datetime] = None
    feedback: Optional[str] = None
    message_ts: Optional[str] = None
    channel_id: Optional[str] = None

    # 추가 데이터
    tech_score: Optional[float] = None
    creative_score: Optional[float] = None
    storyboard_path: Optional[str] = None
    images_dir: Optional[str] = None

    def to_dict(self) -> Dict:
        """딕셔너리 변환"""
        data = {
            "id": self.id,
            "food_name": self.food_name,
            "food_name_kr": self.food_name_kr,
            "approval_type": self.approval_type.value,
            "status": self.status.value,
            "requester": self.requester,
            "reviewer": self.reviewer,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
            "feedback": self.feedback,
            "message_ts": self.message_ts,
            "channel_id": self.channel_id,
            "tech_score": self.tech_score,
            "creative_score": self.creative_score
        }
        return data


class SlackApprovalHandler:
    """
    Slack 승인 핸들러

    Features:
    - 스토리보드 승인 요청
    - 최종 게시 승인 요청
    - 버튼 인터랙션 처리
    - 반려 피드백 모달
    - 승인 대기 (폴링/콜백)
    """

    def __init__(self):
        self.bot_token = os.getenv("SLACK_BOT_TOKEN")
        self.signing_secret = os.getenv("SLACK_SIGNING_SECRET")
        self.approval_channel = os.getenv("SLACK_APPROVAL_CHANNEL", "#sunshine-approvals")

        self.enabled = bool(self.bot_token) and AIOHTTP_AVAILABLE

        # 승인 요청 저장소 (메모리, 실제로는 DB 사용 권장)
        self.pending_approvals: Dict[str, ApprovalRequest] = {}

        # 파일 기반 영구 저장 (간단한 구현)
        self.storage_path = ROOT / "data" / "approvals.json"
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self._load_approvals()

        # 콜백 함수
        self.on_approved: Optional[Callable] = None
        self.on_rejected: Optional[Callable] = None

    def _load_approvals(self):
        """저장된 승인 요청 로드"""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for approval_id, approval_data in data.items():
                        self.pending_approvals[approval_id] = ApprovalRequest(
                            id=approval_data["id"],
                            food_name=approval_data["food_name"],
                            food_name_kr=approval_data.get("food_name_kr", ""),
                            approval_type=ApprovalType(approval_data["approval_type"]),
                            status=ApprovalStatus(approval_data["status"]),
                            requester=approval_data.get("requester", "system"),
                            reviewer=approval_data.get("reviewer"),
                            feedback=approval_data.get("feedback"),
                            message_ts=approval_data.get("message_ts"),
                            channel_id=approval_data.get("channel_id")
                        )
            except (json.JSONDecodeError, KeyError):
                self.pending_approvals = {}

    def _save_approvals(self):
        """승인 요청 저장"""
        data = {
            approval_id: approval.to_dict()
            for approval_id, approval in self.pending_approvals.items()
        }
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    async def send_storyboard_approval_request(
        self,
        food_name: str,
        food_name_kr: str,
        storyboard_path: str,
        storyboard_summary: Dict[str, Any]
    ) -> str:
        """
        스토리보드 승인 요청 전송

        Args:
            food_name: 영문 음식명
            food_name_kr: 한글 음식명
            storyboard_path: 스토리보드 파일 경로
            storyboard_summary: 스토리보드 요약 정보

        Returns:
            approval_id: 승인 요청 ID
        """
        approval_id = f"sb_{food_name}_{int(datetime.now().timestamp())}"

        blocks = self._build_storyboard_approval_blocks(
            approval_id=approval_id,
            food_name=food_name,
            food_name_kr=food_name_kr,
            storyboard_summary=storyboard_summary
        )

        message_ts, channel_id = await self._send_message(blocks)

        # 승인 요청 저장
        approval = ApprovalRequest(
            id=approval_id,
            food_name=food_name,
            food_name_kr=food_name_kr,
            approval_type=ApprovalType.STORYBOARD,
            storyboard_path=storyboard_path,
            message_ts=message_ts,
            channel_id=channel_id
        )
        self.pending_approvals[approval_id] = approval
        self._save_approvals()

        print(f"\n📝 스토리보드 승인 요청 전송: {approval_id}")

        return approval_id

    async def send_final_approval_request(
        self,
        food_name: str,
        food_name_kr: str,
        images_dir: str,
        tech_score: float,
        creative_score: float,
        preview_urls: List[str] = None
    ) -> str:
        """
        최종 승인 요청 전송

        Args:
            food_name: 영문 음식명
            food_name_kr: 한글 음식명
            images_dir: 이미지 디렉토리
            tech_score: 기술 검수 점수
            creative_score: 크리에이티브 검수 점수
            preview_urls: 이미지 미리보기 URL 리스트

        Returns:
            approval_id: 승인 요청 ID
        """
        approval_id = f"final_{food_name}_{int(datetime.now().timestamp())}"

        blocks = self._build_final_approval_blocks(
            approval_id=approval_id,
            food_name=food_name,
            food_name_kr=food_name_kr,
            tech_score=tech_score,
            creative_score=creative_score,
            preview_urls=preview_urls or []
        )

        message_ts, channel_id = await self._send_message(blocks)

        # 승인 요청 저장
        approval = ApprovalRequest(
            id=approval_id,
            food_name=food_name,
            food_name_kr=food_name_kr,
            approval_type=ApprovalType.FINAL,
            images_dir=images_dir,
            tech_score=tech_score,
            creative_score=creative_score,
            message_ts=message_ts,
            channel_id=channel_id
        )
        self.pending_approvals[approval_id] = approval
        self._save_approvals()

        print(f"\n🎬 최종 승인 요청 전송: {approval_id}")

        return approval_id

    def _build_storyboard_approval_blocks(
        self,
        approval_id: str,
        food_name: str,
        food_name_kr: str,
        storyboard_summary: Dict[str, Any]
    ) -> List[Dict]:
        """스토리보드 승인 요청 블록 구성"""
        # 다양성 체크 이모지
        poses = storyboard_summary.get("poses", [])
        angles = storyboard_summary.get("angles", [])
        human_shots = storyboard_summary.get("human_shots", 0)

        pose_check = "✅" if len(poses) >= 4 else "⚠️"
        angle_check = "✅" if len(angles) >= 4 else "⚠️"
        human_check = "✅" if human_shots >= 2 else "⚠️"

        return [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"📝 스토리보드 승인 요청: {food_name_kr}",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*음식:*\n{food_name_kr} ({food_name})"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*슬라이드:*\n{storyboard_summary.get('slide_count', 8)}장"
                    }
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*다양성 검증:*\n"
                            f"{pose_check} 포즈: {', '.join(poses) if isinstance(poses, list) else poses}\n"
                            f"{angle_check} 앵글: {', '.join(angles) if isinstance(angles, list) else angles}\n"
                            f"{human_check} 사람 등장: {human_shots}장"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*슬라이드 요약:*\n```{storyboard_summary.get('summary', '...')}```"
                }
            },
            {
                "type": "divider"
            },
            {
                "type": "actions",
                "block_id": f"approval_{approval_id}",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "✅ 승인",
                            "emoji": True
                        },
                        "style": "primary",
                        "action_id": "approve",
                        "value": approval_id
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "❌ 반려",
                            "emoji": True
                        },
                        "style": "danger",
                        "action_id": "reject",
                        "value": approval_id
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "📄 상세 보기",
                            "emoji": True
                        },
                        "action_id": "view_details",
                        "value": approval_id
                    }
                ]
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"🆔 `{approval_id}` | 🕐 {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                    }
                ]
            }
        ]

    def _build_final_approval_blocks(
        self,
        approval_id: str,
        food_name: str,
        food_name_kr: str,
        tech_score: float,
        creative_score: float,
        preview_urls: List[str]
    ) -> List[Dict]:
        """최종 승인 요청 블록 구성"""
        # 점수 이모지
        tech_emoji = "🟢" if tech_score >= 90 else "🟡" if tech_score >= 80 else "🔴"
        creative_emoji = "🟢" if creative_score >= 90 else "🟡" if creative_score >= 80 else "🔴"

        # 전체 판정
        overall_pass = tech_score >= 80 and creative_score >= 80
        verdict = "✅ PASS" if overall_pass else "⚠️ CONDITIONAL"

        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"🎬 최종 승인 요청: {food_name_kr}",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*음식:*\n{food_name_kr} ({food_name})"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*판정:*\n{verdict}"
                    }
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*검수 결과:*\n"
                            f"{tech_emoji} 기술 검수: *{tech_score:.1f}점*\n"
                            f"{creative_emoji} 크리에이티브: *{creative_score:.1f}점*"
                }
            },
            {
                "type": "divider"
            }
        ]

        # 이미지 미리보기 (최대 3장)
        for i, url in enumerate(preview_urls[:3]):
            blocks.append({
                "type": "image",
                "image_url": url,
                "alt_text": f"Preview {i+1}: {food_name}"
            })

        blocks.extend([
            {
                "type": "divider"
            },
            {
                "type": "actions",
                "block_id": f"approval_{approval_id}",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "✅ 게시 승인",
                            "emoji": True
                        },
                        "style": "primary",
                        "action_id": "approve",
                        "value": approval_id
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "❌ 반려",
                            "emoji": True
                        },
                        "style": "danger",
                        "action_id": "reject",
                        "value": approval_id
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "🖼️ 전체 보기",
                            "emoji": True
                        },
                        "action_id": "view_all_images",
                        "value": approval_id
                    }
                ]
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"🆔 `{approval_id}` | 🕐 {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                    }
                ]
            }
        ])

        return blocks

    async def handle_interaction(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Slack 인터랙션 처리

        Args:
            payload: Slack interaction payload

        Returns:
            응답 데이터
        """
        action = payload["actions"][0]
        action_id = action["action_id"]
        approval_id = action["value"]
        user_id = payload["user"]["id"]
        user_name = payload["user"].get("username", user_id)

        approval = self.pending_approvals.get(approval_id)
        if not approval:
            return {"text": "⚠️ 승인 요청을 찾을 수 없습니다."}

        if approval.status != ApprovalStatus.PENDING:
            return {"text": f"⚠️ 이미 처리된 요청입니다: {approval.status.value}"}

        if action_id == "approve":
            return await self._handle_approve(approval, user_name, payload)
        elif action_id == "reject":
            return await self._handle_reject(approval, user_name, payload)
        elif action_id == "view_details":
            return await self._handle_view_details(approval)
        elif action_id == "view_all_images":
            return await self._handle_view_all_images(approval)

        return {"text": "알 수 없는 액션입니다."}

    async def _handle_approve(
        self,
        approval: ApprovalRequest,
        user_name: str,
        payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """승인 처리"""
        approval.status = ApprovalStatus.APPROVED
        approval.reviewer = user_name
        approval.reviewed_at = datetime.now()
        self._save_approvals()

        # 메시지 업데이트
        await self._update_message_with_result(
            channel=payload["channel"]["id"],
            ts=approval.message_ts,
            approval=approval,
            result_text=f"✅ *승인됨* by @{user_name}"
        )

        # 콜백 실행
        if self.on_approved:
            try:
                await self.on_approved(approval)
            except Exception as e:
                print(f"[Slack] 승인 콜백 오류: {e}")

        return {
            "response_type": "ephemeral",
            "text": f"✅ {approval.food_name_kr} ({approval.food_name}) 승인되었습니다."
        }

    async def _handle_reject(
        self,
        approval: ApprovalRequest,
        user_name: str,
        payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """반려 처리 - 피드백 모달 표시"""
        modal = {
            "type": "modal",
            "callback_id": f"reject_feedback_{approval.id}",
            "title": {
                "type": "plain_text",
                "text": "반려 사유 입력"
            },
            "submit": {
                "type": "plain_text",
                "text": "반려 확인"
            },
            "close": {
                "type": "plain_text",
                "text": "취소"
            },
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*{approval.food_name_kr}* ({approval.food_name}) 반려 사유를 입력해주세요."
                    }
                },
                {
                    "type": "input",
                    "block_id": "feedback_block",
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "feedback_input",
                        "multiline": True,
                        "placeholder": {
                            "type": "plain_text",
                            "text": "반려 사유를 상세히 입력하세요...\n예: 포즈 다양성 부족, 표지 레이아웃 수정 필요"
                        }
                    },
                    "label": {
                        "type": "plain_text",
                        "text": "피드백"
                    }
                },
                {
                    "type": "input",
                    "block_id": "priority_block",
                    "optional": True,
                    "element": {
                        "type": "static_select",
                        "action_id": "priority_input",
                        "placeholder": {
                            "type": "plain_text",
                            "text": "우선순위 선택"
                        },
                        "options": [
                            {"text": {"type": "plain_text", "text": "🔴 높음 (즉시 수정)"}, "value": "high"},
                            {"text": {"type": "plain_text", "text": "🟡 중간 (다음 작업 전)"}, "value": "medium"},
                            {"text": {"type": "plain_text", "text": "🟢 낮음 (시간 여유)"}, "value": "low"}
                        ]
                    },
                    "label": {
                        "type": "plain_text",
                        "text": "수정 우선순위"
                    }
                }
            ],
            "private_metadata": json.dumps({
                "approval_id": approval.id,
                "user_name": user_name,
                "channel_id": payload["channel"]["id"]
            })
        }

        await self._open_modal(payload["trigger_id"], modal)
        return {}

    async def _handle_view_details(self, approval: ApprovalRequest) -> Dict[str, Any]:
        """상세 보기"""
        if approval.approval_type == ApprovalType.STORYBOARD:
            text = f"📄 스토리보드 경로: `{approval.storyboard_path}`"
        else:
            text = f"🖼️ 이미지 폴더: `{approval.images_dir}`\n"
            text += f"📊 기술: {approval.tech_score}점, 크리에이티브: {approval.creative_score}점"

        return {
            "response_type": "ephemeral",
            "text": text
        }

    async def _handle_view_all_images(self, approval: ApprovalRequest) -> Dict[str, Any]:
        """전체 이미지 보기"""
        if approval.images_dir:
            images_path = Path(approval.images_dir)
            images = sorted(images_path.glob("*.png"))
            text = f"🖼️ 전체 이미지 ({len(images)}장):\n"
            for img in images:
                text += f"• `{img.name}`\n"
        else:
            text = "이미지 정보가 없습니다."

        return {
            "response_type": "ephemeral",
            "text": text
        }

    async def handle_modal_submission(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """모달 제출 처리 (반려 피드백)"""
        callback_id = payload["view"]["callback_id"]

        if callback_id.startswith("reject_feedback_"):
            metadata = json.loads(payload["view"]["private_metadata"])
            approval_id = metadata["approval_id"]
            user_name = metadata["user_name"]
            channel_id = metadata["channel_id"]

            # 피드백 추출
            values = payload["view"]["state"]["values"]
            feedback = values["feedback_block"]["feedback_input"]["value"]
            priority = values.get("priority_block", {}).get("priority_input", {}).get("selected_option", {}).get("value", "medium")

            approval = self.pending_approvals.get(approval_id)
            if approval:
                approval.status = ApprovalStatus.REJECTED
                approval.reviewer = user_name
                approval.reviewed_at = datetime.now()
                approval.feedback = f"[{priority}] {feedback}"
                self._save_approvals()

                # 메시지 업데이트
                await self._update_message_with_result(
                    channel=channel_id,
                    ts=approval.message_ts,
                    approval=approval,
                    result_text=f"❌ *반려됨* by @{user_name}\n```{feedback}```"
                )

                # 콜백 실행
                if self.on_rejected:
                    try:
                        await self.on_rejected(approval, feedback)
                    except Exception as e:
                        print(f"[Slack] 반려 콜백 오류: {e}")

            return {"response_action": "clear"}

        return {}

    async def wait_for_approval(
        self,
        approval_id: str,
        timeout: int = 3600,
        poll_interval: int = 5
    ) -> ApprovalRequest:
        """
        승인 대기 (폴링)

        Args:
            approval_id: 승인 요청 ID
            timeout: 타임아웃 (초)
            poll_interval: 폴링 간격 (초)

        Returns:
            ApprovalRequest

        Raises:
            TimeoutError: 타임아웃 시
        """
        start_time = datetime.now()

        while True:
            # 파일에서 최신 상태 로드
            self._load_approvals()

            approval = self.pending_approvals.get(approval_id)
            if approval and approval.status != ApprovalStatus.PENDING:
                return approval

            elapsed = (datetime.now() - start_time).total_seconds()
            if elapsed > timeout:
                # 타임아웃 처리
                if approval:
                    approval.status = ApprovalStatus.TIMEOUT
                    self._save_approvals()
                raise TimeoutError(f"승인 대기 시간 초과: {approval_id}")

            await asyncio.sleep(poll_interval)

    async def _send_message(self, blocks: List[Dict]) -> tuple:
        """Slack 메시지 전송"""
        if not self.enabled:
            self._save_local_notification(blocks)
            return ("local", "local")

        try:
            async with aiohttp.ClientSession() as session:
                response = await session.post(
                    "https://slack.com/api/chat.postMessage",
                    headers={
                        "Authorization": f"Bearer {self.bot_token}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "channel": self.approval_channel,
                        "blocks": blocks,
                        "text": "승인 요청이 도착했습니다."  # 폴백 텍스트
                    }
                )
                data = await response.json()
                if data.get("ok"):
                    return (data.get("ts", ""), data.get("channel", ""))
                else:
                    print(f"[Slack] 메시지 전송 실패: {data.get('error')}")
                    self._save_local_notification(blocks)
                    return ("local", "local")
        except Exception as e:
            print(f"[Slack] 메시지 전송 오류: {e}")
            self._save_local_notification(blocks)
            return ("local", "local")

    async def _update_message_with_result(
        self,
        channel: str,
        ts: str,
        approval: ApprovalRequest,
        result_text: str
    ):
        """메시지 업데이트 (결과 반영)"""
        if not self.enabled or channel == "local":
            print(f"\n📢 [로컬 알림] {result_text}")
            return

        # 결과 블록
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{approval.food_name_kr}* ({approval.food_name})\n{result_text}"
                }
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"🆔 `{approval.id}` | 처리 시간: {approval.reviewed_at.strftime('%Y-%m-%d %H:%M') if approval.reviewed_at else 'N/A'}"
                    }
                ]
            }
        ]

        try:
            async with aiohttp.ClientSession() as session:
                await session.post(
                    "https://slack.com/api/chat.update",
                    headers={
                        "Authorization": f"Bearer {self.bot_token}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "channel": channel,
                        "ts": ts,
                        "blocks": blocks,
                        "text": result_text
                    }
                )
        except Exception as e:
            print(f"[Slack] 메시지 업데이트 오류: {e}")

    async def _open_modal(self, trigger_id: str, modal: Dict):
        """Slack 모달 열기"""
        if not self.enabled:
            print(f"\n📢 [로컬] 모달 표시 (Slack 미연결)")
            return

        try:
            async with aiohttp.ClientSession() as session:
                await session.post(
                    "https://slack.com/api/views.open",
                    headers={
                        "Authorization": f"Bearer {self.bot_token}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "trigger_id": trigger_id,
                        "view": modal
                    }
                )
        except Exception as e:
            print(f"[Slack] 모달 열기 오류: {e}")

    def _save_local_notification(self, blocks: List[Dict]):
        """로컬에 알림 저장 (Slack 미연결 시)"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = ROOT / "data" / "notifications" / f"approval_{timestamp}.json"
        filename.parent.mkdir(parents=True, exist_ok=True)

        with open(filename, "w", encoding="utf-8") as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "blocks": blocks
            }, f, ensure_ascii=False, indent=2)

        # 콘솔 출력
        print(f"\n📢 [로컬 알림 저장됨] {filename}")

    def verify_signature(self, timestamp: str, signature: str, body: bytes) -> bool:
        """Slack 요청 서명 검증"""
        if not self.signing_secret:
            return True  # 테스트 모드

        sig_basestring = f"v0:{timestamp}:{body.decode()}"
        my_signature = "v0=" + hmac.new(
            self.signing_secret.encode(),
            sig_basestring.encode(),
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(my_signature, signature)

    def get_pending_approvals(self) -> List[ApprovalRequest]:
        """대기 중인 승인 요청 조회"""
        return [
            approval for approval in self.pending_approvals.values()
            if approval.status == ApprovalStatus.PENDING
        ]

    def get_approval_status(self, approval_id: str) -> Optional[ApprovalRequest]:
        """특정 승인 요청 상태 조회"""
        return self.pending_approvals.get(approval_id)

    # CLI용 수동 승인/반려 메서드
    def manual_approve(self, approval_id: str, reviewer: str = "cli") -> bool:
        """CLI에서 수동 승인"""
        approval = self.pending_approvals.get(approval_id)
        if approval and approval.status == ApprovalStatus.PENDING:
            approval.status = ApprovalStatus.APPROVED
            approval.reviewer = reviewer
            approval.reviewed_at = datetime.now()
            self._save_approvals()
            print(f"✅ 승인됨: {approval_id}")
            return True
        return False

    def manual_reject(self, approval_id: str, feedback: str, reviewer: str = "cli") -> bool:
        """CLI에서 수동 반려"""
        approval = self.pending_approvals.get(approval_id)
        if approval and approval.status == ApprovalStatus.PENDING:
            approval.status = ApprovalStatus.REJECTED
            approval.reviewer = reviewer
            approval.reviewed_at = datetime.now()
            approval.feedback = feedback
            self._save_approvals()
            print(f"❌ 반려됨: {approval_id}")
            return True
        return False


# 테스트
if __name__ == "__main__":
    import asyncio

    async def test():
        handler = SlackApprovalHandler()
        print(f"Slack 활성화: {handler.enabled}")

        # 스토리보드 승인 요청 테스트
        approval_id = await handler.send_storyboard_approval_request(
            food_name="watermelon",
            food_name_kr="수박",
            storyboard_path="storyboards/watermelon_storyboard.md",
            storyboard_summary={
                "slide_count": 8,
                "poses": ["sitting", "lying", "standing", "looking_up"],
                "angles": ["front", "side_45", "side_90", "top_down"],
                "human_shots": 2,
                "summary": "표지 → 효능1 → 효능2 → 급여량 → 조리법 → CTA"
            }
        )

        print(f"승인 요청 ID: {approval_id}")

        # 수동 승인 테스트
        handler.manual_approve(approval_id, "test_user")

        # 상태 확인
        status = handler.get_approval_status(approval_id)
        print(f"상태: {status.status.value if status else 'None'}")

    asyncio.run(test())
