import os
import asyncio
from dotenv import load_dotenv

from fastapi import FastAPI, Request, HTTPException
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, ContextTypes, Dispatcher
from telegram.constants import ParseMode

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

if not BOT_TOKEN or not WEBHOOK_URL:
    raise Exception("BOT_TOKEN یا WEBHOOK_URL در فایل .env تنظیم نشده‌اند.")

app = FastAPI()

bot = Bot(token=BOT_TOKEN)
application = Application.builder().bot(bot).build()

# تعریف هندلر start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سلام! ربات با وبهوک آماده است.")

application.add_handler(CommandHandler("start", start))

# تنظیم dispatcher برای دریافت آپدیت‌ها از وب‌هوک
dispatcher: Dispatcher = application.dispatcher

@app.post("/webhook")
async def telegram_webhook(request: Request):
    if request.headers.get("content-type") != "application/json":
        raise HTTPException(status_code=403, detail="Invalid content type")

    data = await request.json()
    update = Update.de_json(data, bot)
    await dispatcher.process_update(update)
    return {"status": "ok"}

# تابع تنظیم وبهوک (یکبار اجرا کن)
async def set_webhook():
    await bot.set_webhook(url=WEBHOOK_URL)
    print(f"Webhook set to {WEBHOOK_URL}")

# اجرای وبهوک روی Uvicorn
if __name__ == "__main__":
    import uvicorn

    loop = asyncio.get_event_loop()
    loop.run_until_complete(set_webhook())

    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
