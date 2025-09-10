import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# دریافت توکن از متغیر محیطی
BOT_TOKEN = os.environ.get('BOT_TOKEN')

# بررسی اینکه توکن وجود دارد
if not BOT_TOKEN:
    raise ValueError("لطفاً توکن ربات را در متغیر محیطی BOT_TOKEN تنظیم کنید")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('سلام! ربات با موفقیت راه‌اندازی شد.')

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f'شما گفتید: {update.message.text}')

def main():
    # ایجاد برنامه ربات
    application = Application.builder().token(BOT_TOKEN).build()
    
    # اضافه کردن دستورات
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    
    # شروع ربات
    print("✅ ربات شروع به کار کرد...")
    application.run_polling()

if __name__ == '__main__':
    main()
