import os
import requests
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_message(text):
    """일반 텍스트 메시지 전송"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return False
    
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": text,
            "parse_mode": "Markdown"
        }
        requests.post(url, json=data)
        return True
    except:
        return False

def send_telegram_notification(title, topic, images):
    """텔레그램으로 제작 완료 알림 전송 (버튼 포함)"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return False
    
    try:
        message = f"""
🎨 **콘텐츠 제작 완료!**

📝 제목: {title}
🔍 주제: {topic}
🖼️ 이미지: {len(images)}개 생성

아래 버튼을 눌러 승인하거나 거절하세요.
        """
        
        # 인라인 키보드 (버튼) 추가
        reply_markup = {
            "inline_keyboard": [
                [
                    {"text": "✅ 승인 (Upload)", "callback_data": "APPROVE_UPLOAD"},
                    {"text": "❌ 거절 (Stop)", "callback_data": "REJECT_UPLOAD"}
                ]
            ]
        }
        
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "Markdown",
            "reply_markup": reply_markup
        }
        
        response = requests.post(url, json=data)
        return response.status_code == 200
            
    except Exception as e:
        print(f"❌ [Telegram] 에러: {e}")
        return False

def send_telegram_image(image_path, caption=""):
    """텔레그램으로 이미지 전송"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return False
    
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
        
        with open(image_path, 'rb') as photo:
            files = {'photo': photo}
            data = {
                'chat_id': TELEGRAM_CHAT_ID,
                'caption': caption
            }
            response = requests.post(url, files=files, data=data)
        
        return response.status_code == 200
    except Exception as e:
        print(f"❌ [Telegram] 이미지 전송 에러: {e}")
        return False
