import os
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from supabase import create_client, Client

# دریافت توکن‌ها از متغیرهای محیطی
BOT_TOKEN = os.environ.get('BOT_TOKEN')
HF_TOKEN = os.environ.get('HF_TOKEN')
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')

if not all([BOT_TOKEN, HF_TOKEN, SUPABASE_URL, SUPABASE_KEY]):
    raise ValueError("لطفاً همه متغیرهای محیطی را تنظیم کنید")

# ایجاد کلاینت Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def query_ai(prompt):
    try:
        url = "https://api-inference.huggingface.co/models/microsoft/DialoGPT-medium"
        headers = {"Authorization": f"Bearer {HF_TOKEN}"}
        data = {"inputs": prompt, "parameters": {"max_length": 100}}
        
        response = requests.post(url, headers=headers, json=data, timeout=30)
        if response.status_code != 200:
            return f"خطای سرور: {response.status_code}"
            
        result = response.json()
        return result[0].get('generated_text', 'پاسخ نامعلوم')
    except Exception as e:
        return f"خطا در پردازش: {str(e)}"

async def save_user(update: Update):
    """ذخیره اطلاعات کاربر در دیتابیس"""
    user = update.effective_user
    try:
        # چک کردن وجود کاربر
        existing_user = supabase.table("users").select("*").eq("user_id", user.id).execute()
        
        if len(existing_user.data) == 0:
            # کاربر جدید
            supabase.table("users").insert({
                "user_id": user.id,
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "message_count": 1
            }).execute()
        else:
            # آپدیت کاربر موجود
            supabase.table("users").update({
                "message_count": existing_user.data[0]["message_count"] + 1
            }).eq("user_id", user.id).execute()
            
    except Exception as e:
        print(f"خطا در ذخیره کاربر: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await save_user(update)
    await update.message.reply_text('سلام! خوش آمدید. اطلاعات شما ذخیره شد. 🤖')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await save_user(update)
    user_text = update.message.text
    await update.message.reply_chat_action("typing")
    response_text = query_ai(user_text)
    await update.message.reply_text(response_text[:4000])

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """آمار کاربران"""
    try:
        result = supabase.table("users").select("count").execute()
        total_users = len(result.data)
        await update.message.reply_text(f"تعداد کاربران: {total_users} نفر")
    except Exception as e:
        await update.message.reply_text(f"خطا در دریافت آمار: {e}")

def main():
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("stats", stats))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("✅ ربات با دیتابیس شروع به کار کرد...")
    application.run_polling()

if __name__ == '__main__':
    main()
