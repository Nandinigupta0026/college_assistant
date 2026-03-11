import os
from dotenv import load_dotenv
from test_nova import ask_nova
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from calendar_tool import get_daily_summary
from deadline_detector import is_important_message, auto_save_deadlines_from_whatsapp


load_dotenv()
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("YOUR_CHAT_ID")

async def handle_message(update, context):
    message = update.message.text
    
    # Step 1 - is it worth attention?
    result = is_important_message(message)
    
    if result.get("important"):
        category = result.get("category")
        
        # Step 2 - alert you always
        await context.bot.send_message(
            chat_id=CHAT_ID,
            text=f"{category}: {result.get('summary')}"
        )
        
        # Step 3 - if deadline/exam, also save to calendar
        if category in ["deadline", "exam date", "new assignment"]:
            auto_save_deadlines_from_whatsapp([message])
    else:
        print(" Not important, ignoring")
        
        
async def send_summary(context):
    summary=get_daily_summary()
    
    await context.bot.send_message(
        chat_id=CHAT_ID,
        text=summary
    )   
if __name__ == "__main__":
    import datetime
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT, handle_message))
    app.job_queue.run_daily(
        send_summary,
        time=datetime.time(8, 0, 0)
    )
    
    # Test immediately - sends after 5 seconds
    app.job_queue.run_once(
        send_summary,
        when=5
    )
    print("🤖 Telegram Bot starting...")
    print("✅ Bot is running!")
    app.run_polling()