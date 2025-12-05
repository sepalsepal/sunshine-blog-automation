import os
import logging
import json
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ALLOWED_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Shared State File (Communication with Streamlit)
STATE_FILE = "bot_command.json"

def save_command(command, data=None):
    """Save command to shared file for Streamlit to pick up"""
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
        
        # Save command to trigger Streamlit
        save_command("START_WORKFLOW", {"topic": keyword})
        
        await update.message.reply_text(f"🚀 **'{keyword}'** 주제로 워크플로우를 시작합니다!")
    else:
        await update.message.reply_text("❓ 알 수 없는 명령어입니다. '1'을 입력하여 시작하세요.")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button clicks"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "APPROVE_UPLOAD":
        save_command("APPROVE_UPLOAD")
        await query.edit_message_text(text="✅ **승인 완료!** 워드프레스 업로드를 시작합니다.")
        
    elif data == "REJECT_UPLOAD":
        save_command("REJECT_UPLOAD")
        await query.edit_message_text(text="❌ **거절됨.** 워크플로우를 종료합니다.")

if __name__ == '__main__':
    if not TOKEN:
        print("❌ Error: TELEGRAM_BOT_TOKEN not found in .env")
        exit(1)
        
    application = ApplicationBuilder().token(TOKEN).build()
    
    application.add_handler(CommandHandler('start', start))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    application.add_handler(CallbackQueryHandler(button_callback))
    
    print("🤖 Telegram Bot is running...")
    application.run_polling()
