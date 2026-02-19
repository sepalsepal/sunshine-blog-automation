"""
알림 시스템
- Slack 알림
- 승인 요청
- 완료/에러 알림

Phase 3: 알림 시스템
"""

import os
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

ROOT = Path(__file__).parent.parent

try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False


class SlackNotifier:
    """
    Slack 알림 시스템

    Features:
    - 승인 요청 알림
    - 완료 알림
    - 에러 알림
    - Block Kit 지원
    """

    def __init__(self):
        self.webhook_url = os.getenv("SLACK_WEBHOOK_URL")
        self.enabled = bool(self.webhook_url) and AIOHTTP_AVAILABLE
        self.channel = os.getenv("SLACK_CHANNEL", "#sunshine-pipeline")

        # 로컬 알림 저장 (Slack 미연결 시)
        self.notifications_dir = ROOT / "data" / "notifications"
        self.notifications_dir.mkdir(parents=True, exist_ok=True)

    async def _send(self, message: Dict[str, Any]) -> bool:
        """Slack 메시지 전송"""
        if not self.enabled:
            # Slack 미연결 시 로컬 저장
            self._save_local(message)
            return False

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url,
                    json=message,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    return response.status == 200
        except Exception as e:
            print(f"[Slack 전송 실패] {e}")
            self._save_local(message)
            return False

    def _save_local(self, message: Dict[str, Any]):
        """로컬에 알림 저장"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.notifications_dir / f"notification_{timestamp}.json"

        with open(filename, "w", encoding="utf-8") as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "message": message
            }, f, ensure_ascii=False, indent=2)

        # 콘솔 출력
        text = message.get("text", "")
        if text:
            print(f"\n📢 [알림] {text}\n")

    async def send_approval_request(
        self,
        phase: str,
        food_name: str,
        file_path: str,
        tech_score: float = None,
        creative_score: float = None
    ):
        """승인 요청 알림"""
        if phase == "storyboard":
            blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "📝 스토리보드 승인 요청"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"*음식:*\n{food_name}"},
                        {"type": "mrkdwn", "text": f"*파일:*\n`{file_path}`"}
                    ]
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "✅ 승인"},
                            "style": "primary",
                            "action_id": f"approve_storyboard_{food_name}"
                        },
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "❌ 반려"},
                            "style": "danger",
                            "action_id": f"reject_storyboard_{food_name}"
                        }
                    ]
                }
            ]
            text = f"📝 스토리보드 승인 요청: {food_name}"
        else:
            # 최종 승인
            score_color = "good" if (tech_score or 0) >= 80 and (creative_score or 0) >= 80 else "warning"

            blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "✅ 최종 승인 요청"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"*음식:*\n{food_name}"},
                        {"type": "mrkdwn", "text": f"*파일:*\n`{file_path}`"}
                    ]
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"*기술 검수:*\n{tech_score:.1f}점"},
                        {"type": "mrkdwn", "text": f"*크리에이티브:*\n{creative_score:.1f}점"}
                    ]
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "✅ 게시 승인"},
                            "style": "primary",
                            "action_id": f"approve_final_{food_name}"
                        },
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "❌ 반려"},
                            "style": "danger",
                            "action_id": f"reject_final_{food_name}"
                        }
                    ]
                }
            ]
            text = f"✅ 최종 승인 요청: {food_name} (기술: {tech_score:.1f}, 크리에이티브: {creative_score:.1f})"

        await self._send({
            "text": text,
            "blocks": blocks
        })

    async def send_completion(
        self,
        food_name: str,
        instagram_url: str,
        tech_score: float = None,
        creative_score: float = None
    ):
        """완료 알림"""
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "🎉 게시 완료!"
                }
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*음식:*\n{food_name}"},
                    {"type": "mrkdwn", "text": f"*Instagram:*\n<{instagram_url}|게시물 보기>"}
                ]
            }
        ]

        if tech_score and creative_score:
            blocks.append({
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*기술 검수:*\n{tech_score:.1f}점"},
                    {"type": "mrkdwn", "text": f"*크리에이티브:*\n{creative_score:.1f}점"}
                ]
            })

        await self._send({
            "text": f"🎉 게시 완료: {food_name} - {instagram_url}",
            "blocks": blocks
        })

    async def send_error(
        self,
        food_name: str,
        error: str,
        phase: str = None
    ):
        """에러 알림"""
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "❌ 파이프라인 오류"
                }
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*음식:*\n{food_name}"},
                    {"type": "mrkdwn", "text": f"*단계:*\n{phase or '알 수 없음'}"}
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*오류 내용:*\n```{error}```"
                }
            }
        ]

        await self._send({
            "text": f"❌ 파이프라인 오류: {food_name} - {error}",
            "blocks": blocks
        })

    async def send_review_alert(
        self,
        food_name: str,
        tech_score: float,
        creative_score: float,
        verdict: str
    ):
        """검수 결과 알림"""
        if verdict == "PASS":
            emoji = "✅"
            color = "good"
        elif verdict == "CONDITIONAL":
            emoji = "⚠️"
            color = "warning"
        else:
            emoji = "❌"
            color = "danger"

        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{emoji} 검수 결과: {verdict}"
                }
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*음식:*\n{food_name}"},
                    {"type": "mrkdwn", "text": f"*판정:*\n{verdict}"}
                ]
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*기술 검수:*\n{tech_score:.1f}점"},
                    {"type": "mrkdwn", "text": f"*크리에이티브:*\n{creative_score:.1f}점"}
                ]
            }
        ]

        await self._send({
            "text": f"{emoji} 검수 결과: {food_name} - {verdict}",
            "blocks": blocks
        })


# 테스트
if __name__ == "__main__":
    import asyncio

    async def test():
        notifier = SlackNotifier()
        print(f"Slack 활성화: {notifier.enabled}")

        await notifier.send_approval_request(
            phase="storyboard",
            food_name="watermelon",
            file_path="storyboards/watermelon_storyboard.md"
        )

        await notifier.send_completion(
            food_name="watermelon",
            instagram_url="https://instagram.com/p/test123",
            tech_score=95.0,
            creative_score=88.5
        )

    asyncio.run(test())
