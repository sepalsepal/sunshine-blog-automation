import os
import logging
import json
import time
import urllib.request
import urllib.parse
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ALLOWED_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
STREAMLIT_APP_URL = os.getenv("STREAMLIT_APP_URL", "https://sunshine-blog.streamlit.app")

# Logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def trigger_streamlit(action, topic=None):
    """Streamlit 앱에 HTTP 요청으로 워크플로우 트리거"""
    try:
        url = f"{STREAMLIT_APP_URL}?action={action}"
        if topic:
            url += f"&topic={urllib.parse.quote(topic)}"
        
        print(f"🌐 Streamlit 앱 호출: {url}")
        
        # 간단한 GET 요청 (Streamlit은 URL 파라미터로 처리)
        req = urllib.request.Request(url, headers={'User-Agent': 'TelegramBot/1.0'})
        urllib.request.urlopen(req, timeout=10)
        return True
    except Exception as e:
        print(f"⚠️ Streamlit 호출 실패 (정상일 수 있음): {e}")
        return True  # Streamlit은 리다이렉트할 수 있어서 에러여도 OK

# Fallback: 로컬 파일 기반 (로컬 테스트용)
STATE_FILE = "bot_command.json"

def save_command(command, data=None):
    """Save command to shared file for Streamlit to pick up (fallback)"""
    with open(STATE_FILE, "w") as f:
        json.dump({"command": command, "data": data, "timestamp": time.time()}, f)
    print(f"💾 Command saved: {command}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    if str(update.effective_chat.id) != ALLOWED_CHAT_ID:
        return
    
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="👋 안녕하세요! **Sunshine Blog Manager**입니다.\n\n"
             "1️⃣ **'1'**을 입력하면 키워드로 글쓰기를 시작합니다.\n"
             "2️⃣ 진행 상황은 실시간으로 알림이 옵니다.\n"
             "3️⃣ 승인 요청 시 **[승인]** 버튼을 누르면 업로드됩니다."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages"""
    if str(update.effective_chat.id) != ALLOWED_CHAT_ID:
        return

    text = update.message.text.strip()

    if text == "1":
        await update.message.reply_text("💡 **주제(키워드)**를 입력해주세요.")
        context.user_data['awaiting_keyword'] = True
        
    elif context.user_data.get('awaiting_keyword'):
        keyword = text
        context.user_data['awaiting_keyword'] = False
        
        # HTTP로 Streamlit 앱에 워크플로우 시작 요청
        trigger_streamlit("start", topic=keyword)
        save_command("START_WORKFLOW", {"topic": keyword})  # 로컬 백업
        
        await update.message.reply_text(f"🚀 **'{keyword}'** 주제로 워크플로우를 시작합니다!\n\n📧 승인 요청이 이메일로 전송됩니다.")
    else:
        await update.message.reply_text("❓ 알 수 없는 명령어입니다. '1'을 입력하여 시작하세요.")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button clicks"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "APPROVE_UPLOAD":
        # HTTP로 Streamlit 앱에 승인 요청
        trigger_streamlit("approve")
        save_command("APPROVE_UPLOAD")  # 로컬 백업
        await query.edit_message_text(text="✅ **승인 완료!** 워드프레스 업로드를 시작합니다.")
        
    elif data == "REJECT_UPLOAD":
        trigger_streamlit("reject")
        save_command("REJECT_UPLOAD")
        await query.edit_message_text(text="❌ **거절됨.** 워크플로우를 종료합니다.")

# --- [NEW] 스케줄러 설정 ---
def scheduled_auto_post():
    """스케줄된 자동 포스팅"""
    from datetime import datetime
    print(f"⏰ [{datetime.now()}] 스케줄러 자동 실행!")
    trigger_streamlit("start", topic="auto")
    print("📧 승인 요청이 텔레그램/이메일로 전송됩니다.")

if __name__ == '__main__':
    if not TOKEN:
        print("❌ Error: TELEGRAM_BOT_TOKEN not found in .env")
        exit(1)
    
    # APScheduler 설정 (8am, 7pm KST)
    from apscheduler.schedulers.background import BackgroundScheduler
    import pytz
    
    scheduler = BackgroundScheduler(timezone=pytz.timezone('Asia/Seoul'))
    
    # 오전 8시 실행
    scheduler.add_job(scheduled_auto_post, 'cron', hour=8, minute=0)
    # 오후 7시 실행
    scheduler.add_job(scheduled_auto_post, 'cron', hour=19, minute=0)
    
    scheduler.start()
    print("⏰ 스케줄러 설정 완료: 오전 8시, 오후 7시 (KST)")
    
    # 텔레그램 봇 시작
    application = ApplicationBuilder().token(TOKEN).build()
    
    application.add_handler(CommandHandler('start', start))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    application.add_handler(CallbackQueryHandler(button_callback))
    
    print("🤖 Telegram Bot is running...")
    application.run_polling()

