import os
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# دریافت توکن‌ها از متغیرهای محیطی
BOT_TOKEN = os.environ.get('BOT_TOKEN')
HF_TOKEN = os.environ.get('HF_TOKEN')

if not BOT_TOKEN:
    raise ValueError("لطفاً توکن ربات را تنظیم کنید")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('سلام! من با Hugging Face کار می‌کنم.')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not HF_TOKEN:
        await update.message.reply_text("توکن Hugging Face تنظیم نشده است")
        return
    
    try:
        # در اینجا کد هوش مصنوعی اضافه خواهد شد
        await update.message.reply_text("هوش مصنوعی به زودی اضافه می‌شود...")
    except Exception as e:
        await update.message.reply_text(f"خطا: {str(e)}")

def main():
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("✅ ربات شروع به کار کرد...")
    application.run_polling()

if __name__ == '__main__':
    main()
