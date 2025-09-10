import os
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# توکن‌ها را از متغیرهای محیطی بگیر
BOT_TOKEN = os.environ.get("8352301516:AAFu5U234zRh6XIfeE5h9hlxf3jEecne7aQ")  # توکن ربات تلگرام
HF_TOKEN = os.environ.get("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")    # توکن Hugging Face
API_URL = "https://api-inference.huggingface.co/models/google/gemma-2b-it"

headers = {"Authorization": f"Bearer {HF_TOKEN}"}

def query_huggingface(prompt):
    payload = {"inputs": prompt}
    response = requests.post(API_URL, headers=headers, json=payload)
    return response.json()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('سلام! من با هوش مصنوعی Hugging Face کار می‌کنم.')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    try:
        output = query_huggingface(user_text)
        
        # پردازش پاسخ Hugging Face
        if isinstance(output, list) and len(output) > 0:
            response_text = output[0].get('generated_text', 'پاسخ نامعلوم')
        elif isinstance(output, dict) and 'generated_text' in output:
            response_text = output['generated_text']
        else:
            response_text = str(output)
        
        # محدودیت طول پیام تلگرام (4096 کاراکتر)
        await update.message.reply_text(response_text[:4000])
    except Exception as e:
        await update.message.reply_text(f"خطا در پردازش: {str(e)}")

def main():
    # ایجاد ربات تلگرام
    application = Application.builder().token(BOT_TOKEN).build()
    
    # اضافه کردن دستورات
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # اجرای ربات
    print("ربات در حال اجرا...")
    application.run_polling()

if __name__ == '__main__':
    main()
