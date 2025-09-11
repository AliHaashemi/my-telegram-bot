from fastapi import FastAPI, Request
import httpx
import os

app = FastAPI()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
BOT_API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

@app.post("/webhook")
async def telegram_webhook(request: Request):
    data = await request.json()

    chat_id = data.get("message", {}).get("chat", {}).get("id")
    message_text = data.get("message", {}).get("text", "")

    if chat_id and message_text:
        reply_text = f"شما گفتید: {message_text}"
        await send_message(chat_id, reply_text)

    return {"ok": True}

async def send_message(chat_id: int, text: str):
    url = f"{BOT_API_URL}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    async with httpx.AsyncClient() as client:
        await client.post(url, json=payload)

@app.get("/")
def read_root():
    return {"message": "Telegram bot is running!"}
