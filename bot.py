import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from supabase import create_client, Client
from openai import OpenAI
from datetime import datetime

# دریافت توکن‌ها
BOT_TOKEN = os.environ.get('BOT_TOKEN')
HF_TOKEN = os.environ.get('HF_TOKEN')
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')

# کلاینت‌ها
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
client = OpenAI(base_url="https://router.huggingface.co/v1", api_key=HF_TOKEN)

async def save_message(user_id: int, message_text: str, bot_response: str = None):
    """ذخیره پیام در دیتابیس"""
    try:
        supabase.table("messages").insert({
            "user_id": user_id,
            "message_text": message_text,
            "bot_response": bot_response
        }).execute()
    except Exception as e:
        print(f"خطا در ذخیره پیام: {e}")

async def save_user(update: Update):
    """ذخیره کاربر"""
    user = update.effective_user
    try:
        existing_user = supabase.table("users").select("*").eq("user_id", user.id).execute()
        
        if not existing_user.data:
            supabase.table("users").insert({
                "user_id": user.id,
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name
            }).execute()
    except Exception as e:
        print(f"خطا در ذخیره کاربر: {e}")

def query_ai(prompt: str) -> str:
    """پرسش از هوش مصنوعی"""
    try:
        completion = client.chat.completions.create(
            model="moonshotai/Kimi-K2-Instruct-0905:together",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"خطا: {str(e)}"

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پردازش پیام کاربر"""
    user = update.effective_user
    user_text = update.message.text
    
    await save_user(update)
    await update.message.reply_chat_action("typing")
    
    # دریافت پاسخ از هوش مصنوعی
    bot_response = query_ai(user_text)
    
    # ذخیره پیام کاربر و پاسخ ربات
    await save_message(user.id, user_text, bot_response)
    
    await update.message.reply_text(bot_response[:4000])

async def all_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """مشاهده تمام پیام‌ها (فقط برای ادمین)"""
    try:
        # دریافت تمام پیام‌ها
        messages = supabase.table("messages").select("*, users(username)").execute()
        
        response = "📋 لیست پیام‌ها:\n\n"
        for msg in messages.data:
            response += f"👤 @{msg['users']['username']}\n"
            response += f"💬 {msg['message_text']}\n"
            response += f"🤖 {msg['bot_response']}\n"
            response += f"⏰ {msg['created_at']}\n"
            response += "─" * 30 + "\n"
        
        await update.message.reply_text(response[:4000])
        
    except Exception as e:
        await update.message.reply_text(f"خطا: {str(e)}")

async def user_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """مشاهده پیام‌های کاربر خاص"""
    try:
        user_id = update.effective_user.id
        messages = supabase.table("messages").select("*").eq("user_id", user_id).execute()
        
        response = f"📋 پیام‌های شما:\n\n"
        for msg in messages.data:
            response += f"💬 {msg['message_text']}\n"
            response += f"🤖 {msg['bot_response']}\n"
            response += f"⏰ {msg['created_at']}\n"
            response += "─" * 20 + "\n"
        
        await update.message.reply_text(response[:4000])
        
    except Exception as e:
        await update.message.reply_text(f"خطا: {str(e)}")

# تنظیمات ربات
def main():
    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", save_user))
    application.add_handler(CommandHandler("mymessages", user_messages))
    application.add_handler(CommandHandler("allmessages", all_messages))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    application.run_polling()

if __name__ == '__main__':
    main()
