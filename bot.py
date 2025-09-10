import os
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# دریافت توکن‌ها از متغیرهای محیطی
BOT_TOKEN = os.environ.get('BOT_TOKEN')
HF_TOKEN = os.environ.get('HF_TOKEN')
API_URL = "https://api-inference.huggingface.co/models/google/gemma-2b-it"

if not BOT_TOKEN:
    raise ValueError("لطفاً توکن ربات را تنظیم کنید")

if not HF_TOKEN:
    raise ValueError("لطفاً توکن Hugging Face را تنظیم کنید")

headers = {"Authorization": f"Bearer {HF_TOKEN}"}

def query_huggingface(prompt):
    try:
        payload = {"inputs": prompt}
        response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()  # بررسی خطای HTTP
        return response.json()
    except requests.exceptions.RequestException as e:
        return f"خطا در اتصال به Hugging Face: {str(e)}"
    except Exception as e:
        return f"خطای ناشناخته: {str(e)}"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('سلام! من با هوش مصنوعی Hugging Face کار می‌کنم.')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    
    # نشان دادن اینکه ربات در حال پردازش است
    await update.message.reply_chat_action("typing")
    
    # دریافت پاسخ از هوش مصنوعی
    output = query_huggingface(user_text)
    
    # پردازش پاسخ
    if isinstance(output, list) and len(output) > 0:
        if 'generated_text' in output[0]:
            response_text = output[0]['generated_text']
        else:
            response_text = str(output[0])
    elif isinstance(output, dict) and 'generated_text' in output:
        response_text = output['generated_text']
    elif isinstance(output, str):
        response_text = output
    else:
        response_text = f"پاسخ نامعلوم: {str(output)}"
    
    # ارسال پاسخ (با محدودیت طول تلگرام)
    await update.message.reply_text(response_text[:4000])

def main():
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("✅ ربات با هوش مصنوعی شروع به کار کرد...")
    print(f"توکن Hugging Face: {'موجود' if HF_TOKEN else 'مفقود'}")
    application.run_polling()

if __name__ == '__main__':
    main()
