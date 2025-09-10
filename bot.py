import os
from openai import OpenAI
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# دریافت توکن‌ها از متغیرهای محیطی
BOT_TOKEN = os.environ.get('BOT_TOKEN')
HF_TOKEN = os.environ.get('HF_TOKEN')

if not BOT_TOKEN:
    raise ValueError("لطفاً توکن ربات را تنظیم کنید")

if not HF_TOKEN:
    raise ValueError("لطفاً توکن Hugging Face را تنظیم کنید")

# تنظیم کلاینت OpenAI برای Hugging Face
client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=HF_TOKEN,
)

def query_ai(prompt):
    try:
        completion = client.chat.completions.create(
            model="moonshotai/Kimi-K2-Instruct-0905:together",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=500,
            temperature=0.7
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"خطا در پردازش: {str(e)}"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('سلام! من با هوش مصنوعی پیشرفته کار می‌کنم. 🤖')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    
    # نشان دادن اینکه ربات در حال پردازش است
    await update.message.reply_chat_action("typing")
    
    # دریافت پاسخ از هوش مصنوعی
    response_text = query_ai(user_text)
    
    # ارسال پاسخ
    await update.message.reply_text(response_text[:4000])

def main():
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("✅ ربات با هوش مصنوعی پیشرفته شروع به کار کرد...")
    application.run_polling()

if __name__ == '__main__':
    main()
