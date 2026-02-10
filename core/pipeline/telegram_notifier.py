"""
Telegram 알림 모듈
Project Sunshine - PD 승인 요청 및 상태 알림

Bot: JunTrans_bot
Chat ID: 5360443525
"""

import os
import requests
from typing import Optional
from pathlib import Path


class TelegramNotifier:
    """텔레그램 알림 전송 클래스"""

    def __init__(self):
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID", "5360443525")
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}" if self.bot_token else None

    def is_configured(self) -> bool:
        """텔레그램 설정 여부 확인"""
        return bool(self.bot_token)

    def send_approval_request(
        self,
        topic: str,
        score: int,
        preview_url: str,
        pipeline_id: str,
        image_count: int = 7
    ) -> bool:
        """PD님께 파이널 승인 요청"""
        if not self.is_configured():
            print("   [텔레그램] 토큰 미설정, 알림 스킵")
            return False

        message = f"""
🎬 <b>파이널 승인 요청</b>

📁 콘텐츠: <b>{topic.upper()}</b>
📊 최종 점수: <b>{score}점</b>
🖼️ 이미지: {image_count}장

🔗 미리보기: {preview_url}

✅ 승인하시려면 위 링크에서 승인 버튼을 클릭해주세요.
        """

        return self._send_message(message.strip())

    def send_completion_notice(self, topic: str, instagram_url: str = None) -> bool:
        """게시 완료 알림"""
        if not self.is_configured():
            return False

        message = f"""
✅ <b>게시 완료!</b>

📁 콘텐츠: <b>{topic.upper()}</b>
📱 Instagram에 게시되었습니다.
        """

        if instagram_url:
            message += f"\n🔗 {instagram_url}"

        return self._send_message(message.strip())

    def send_failure_notice(self, topic: str, step: str, error: str) -> bool:
        """실패 알림"""
        if not self.is_configured():
            return False

        message = f"""
❌ <b>파이프라인 실패</b>

📁 콘텐츠: <b>{topic.upper()}</b>
📍 실패 단계: {step}
💬 오류: {error}

확인이 필요합니다.
        """

        return self._send_message(message.strip())

    def send_progress_update(self, topic: str, stage: str, status: str, score: int = None) -> bool:
        """진행 상황 알림 (선택적)"""
        if not self.is_configured():
            return False

        emoji = {
            "running": "🔄",
            "completed": "✅",
            "failed": "❌"
        }.get(status, "📌")

        message = f"{emoji} {topic.upper()}: {stage}"
        if score:
            message += f" ({score}점)"

        return self._send_message(message)

    def send_image(self, image_path: str, caption: str = "") -> bool:
        """이미지 전송"""
        if not self.is_configured():
            return False

        if not Path(image_path).exists():
            print(f"   [텔레그램] 이미지 파일 없음: {image_path}")
            return False

        try:
            url = f"{self.base_url}/sendPhoto"

            with open(image_path, 'rb') as photo:
                response = requests.post(
                    url,
                    data={
                        "chat_id": self.chat_id,
                        "caption": caption,
                        "parse_mode": "HTML"
                    },
                    files={"photo": photo},
                    timeout=30
                )

            if response.status_code == 200:
                return True
            elif response.status_code == 413:
                print(f"   [텔레그램] 이미지가 너무 큽니다 (최대 10MB)")
            else:
                print(f"   [텔레그램] 이미지 전송 HTTP {response.status_code}")

            return False

        except requests.exceptions.Timeout:
            print(f"   [텔레그램] 이미지 전송 타임아웃 (30초)")
            return False

        except IOError as e:
            print(f"   [텔레그램] 이미지 파일 읽기 실패: {e}")
            return False

        except Exception as e:
            print(f"   [텔레그램] 이미지 전송 실패: {type(e).__name__}: {e}")
            return False

    def send_images_album(self, image_paths: list, caption: str = "") -> bool:
        """여러 이미지 앨범으로 전송 (최대 10장)"""
        if not self.is_configured():
            return False

        if not image_paths:
            return False

        # P0 fix: 파일 핸들 누수 방지를 위해 try/finally 패턴 적용
        files = {}
        try:
            url = f"{self.base_url}/sendMediaGroup"

            # 최대 10장까지
            paths = image_paths[:10]
            media = []

            for i, path in enumerate(paths):
                if Path(path).exists():
                    file_key = f"photo{i}"
                    files[file_key] = open(path, 'rb')
                    media.append({
                        "type": "photo",
                        "media": f"attach://{file_key}",
                        "caption": caption if i == 0 else "",
                        "parse_mode": "HTML"
                    })

            if not media:
                return False

            import json
            response = requests.post(
                url,
                data={
                    "chat_id": self.chat_id,
                    "media": json.dumps(media)
                },
                files=files,
                timeout=60
            )

            return response.status_code == 200

        except Exception as e:
            print(f"   [텔레그램] 앨범 전송 실패: {e}")
            return False
        finally:
            # P0 fix: 예외 발생 여부와 관계없이 파일 핸들 정리
            for f in files.values():
                try:
                    f.close()
                except Exception:
                    pass

    def _send_message(self, text: str, max_retries: int = 3) -> bool:
        """메시지 전송 (내부용)

        P1 fix: 재시도 로직 추가 (exponential backoff)
        """
        if not self.base_url:
            return False

        import time as time_module

        for attempt in range(max_retries):
            try:
                url = f"{self.base_url}/sendMessage"
                response = requests.post(
                    url,
                    json={
                        "chat_id": self.chat_id,
                        "text": text,
                        "parse_mode": "HTML"
                    },
                    timeout=10
                )

                if response.status_code == 200:
                    return True
                elif response.status_code == 401:
                    print(f"   [텔레그램] 인증 실패: 토큰이 유효하지 않습니다")
                    return False  # 인증 실패는 재시도 불가
                elif response.status_code == 400:
                    error_data = response.json() if response.content else {}
                    error_desc = error_data.get("description", "Bad Request")
                    print(f"   [텔레그램] 요청 오류: {error_desc}")
                    return False  # 잘못된 요청은 재시도 불가
                elif response.status_code == 429:
                    # P1 fix: Rate limit 시 재시도
                    retry_after = int(response.headers.get("Retry-After", 5))
                    print(f"   [텔레그램] 레이트 제한, {retry_after}초 후 재시도...")
                    time_module.sleep(retry_after)
                    continue
                else:
                    print(f"   [텔레그램] HTTP {response.status_code}: {response.text[:100]}")

            except requests.exceptions.Timeout:
                print(f"   [텔레그램] 타임아웃 (시도 {attempt + 1}/{max_retries})")
            except requests.exceptions.ConnectionError:
                print(f"   [텔레그램] 연결 실패 (시도 {attempt + 1}/{max_retries})")
            except Exception as e:
                print(f"   [텔레그램] 오류: {type(e).__name__}: {e}")

            # P1 fix: exponential backoff
            if attempt < max_retries - 1:
                delay = 2 ** attempt  # 1, 2, 4초
                time_module.sleep(delay)

        print(f"   [텔레그램] 최대 재시도 횟수 초과 ({max_retries}회)")
        return False


# 테스트용
if __name__ == "__main__":
    notifier = TelegramNotifier()

    if notifier.is_configured():
        print("텔레그램 설정됨, 테스트 메시지 전송...")
        result = notifier._send_message("🧪 Project Sunshine 텔레그램 테스트")
        print(f"전송 결과: {'성공' if result else '실패'}")
    else:
        print("TELEGRAM_BOT_TOKEN 환경변수가 설정되지 않았습니다.")
        print("사용법: TELEGRAM_BOT_TOKEN=your_token python -m pipeline.telegram_notifier")
