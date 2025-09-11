import os
import time
import requests
from openai import OpenAI

TOKEN = os.getenv("TELEGRAM_TOKEN")
BASE_URL = f"https://api.telegram.org/bot{TOKEN}"

# کلاینت OpenAI با huggingface
client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=os.environ["HF_TOKEN"],
)

def get_updates(offset=None):
    url = BASE_URL + "/getUpdates"
    params = {"timeout": 100, "offset": offset}
    resp = requests.get(url, params=params)
    return resp.json()

def send_message(chat_id, text):
    url = BASE_URL + "/sendMessage"
    data = {"chat_id": chat_id, "text": text}
    requests.post(url, data=data)

def ask_openai(question):
    # پیام رو به مدل می‌فرستیم و جوابش رو می‌گیریم
    completion = client.chat.completions.create(
        model="moonshotai/Kimi-K2-Instruct-0905:together",
        messages=[
            {
                "role": "user",
                "content": question
            }
        ],
    )
    # متن پاسخ رو برمی‌گردونیم
    return completion.choices[0].message.content

def main():
    offset = None
    print("Bot started...")
    while True:
        updates = get_updates(offset)
        if updates["ok"]:
            for update in updates["result"]:
                offset = update["update_id"] + 1
                message = update.get("message")
                if message:
                    chat_id = message["chat"]["id"]
                    text = message.get("text", "")
                    if text:
                        # پرسیدن سوال به مدل OpenAI
                        reply = ask_openai(text)
                        send_message(chat_id, reply)
        time.sleep(1)

if __name__ == "__main__":
    main()
