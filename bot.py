import os
import asyncio
from dotenv import load_dotenv

from fastapi import FastAPI, Request
from telegram import Update, Bot
from telegram.ext import (
    Application, CommandHandler, ContextTypes
)
import uvicorn

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

if not BOT_TOKEN or not WEBHOOK_URL:
    raise Exception("BOT_TOKEN یا WEBHOOK_URL در .env تنظیم نشده.")

bot = Bot(token=BOT_TOKEN)

# ساخت اپلیکیشن تلگرام
application = Application.builder().token(BOT_TOKEN).build()

# FastAPI اپلیکیشن
app = FastAPI()

# هندلر /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سلام! ربات با وب‌هوک فعال است ✅")

# ثبت هندلر
application.add_handler(CommandHandler("start", start))

# مسیر وب‌هوک برای دریافت پیام‌ها از تلگرام
@app.post("/webhook")
async def webhook_handler(request: Request):
    data = await request.json()
    update = Update.de_json(data, bot)
    await application.update_queue.put(update)
    return {"status": "ok"}

# ثبت وب‌هوک در تلگرام
async def set_webhook():
    await bot.set_webhook(WEBHOOK_URL)
    print(f"✅ Webhook set to {WEBHOOK_URL}")

# اجرای برنامه
if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(set_webhook())
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
