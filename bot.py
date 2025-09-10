import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from supabase import create_client, Client
from openai import OpenAI
import json

# دریافت توکن‌ها
BOT_TOKEN = os.environ.get('BOT_TOKEN')
HF_TOKEN = os.environ.get('HF_TOKEN')
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')

# کلاینت‌ها
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
client = OpenAI(base_url="https://router.huggingface.co/v1", api_key=HF_TOKEN)

async def save_message(user_id: int, content: str, role: str = "user"):
    """ذخیره پیام در دیتابیس"""
    try:
        supabase.table("messages").insert({
            "user_id": user_id,
            "message_text": content,
            "role": role
        }).execute()
    except Exception as e:
        print(f"خطا در ذخیره پیام: {e}")

async def get_chat_history(user_id: int, limit: int = 10):
    """دریافت تاریخچه گفتگوی کاربر"""
    try:
        response = supabase.table("messages").select("*").eq("user_id", user_id).order("created_at", desc=True).limit(limit).execute()
        return response.data
    except Exception as e:
        print(f"خطا در دریافت تاریخچه: {e}")
        return []

async def build_conversation_context(user_id: int, new_message: str):
    """ساخت زمینه گفتگو با تاریخچه"""
    history = await get_chat_history(user_id)
    
    # مرتب کردن از قدیمی به جدید
    history.sort(key=lambda x: x['created_at'])
    
    messages = []
    
    # اضافه کردن پیام‌های تاریخی
    for msg in history:
        messages.append({
            "role": msg['role'],
            "content": msg['message_text']
        })
    
    # اضافه کردن پیام جدید کاربر
    messages.append({
        "role": "user",
        "content": new_message
    })
    
    return messages

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پردازش پیام با حافظه"""
    user = update.effective_user
    user_text = update.message.text
    
    await update.message.reply_chat_action("typing")
    
    try:
        # ساخت زمینه گفتگو با تاریخچه
        conversation_context = await build_conversation_context(user.id, user_text)
        
        # ارسال به هوش مصنوعی با تاریخچه
        completion = client.chat.completions.create(
            model="moonshotai/Kimi-K2-Instruct-0905:together",
            messages=conversation_context,
            max_tokens=500,
            temperature=0.7
        )
        
        bot_response = completion.choices[0].message.content
        
        # ذخیره پیام کاربر
        await save_message(user.id, user_text, "user")
        
        # ذخیره پاسخ ربات
        await save_message(user.id, bot_response, "assistant")
        
        await update.message.reply_text(bot_response[:4000])
        
    except Exception as e:
        error_msg = f"خطا: {str(e)}"
        await update.message.reply_text(error_msg)
        await save_message(user.id, user_text, "user")
        await save_message(user.id, error_msg, "system")

async def clear_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پاک کردن تاریخچه کاربر"""
    try:
        user_id = update.effective_user.id
        supabase.table("messages").delete().eq("user_id", user_id).execute()
        await update.message.reply_text("✅ تاریخچه گفتگوی شما پاک شد!")
    except Exception as e:
        await update.message.reply_text(f"خطا: {str(e)}")

async def show_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش تاریخچه کاربر"""
    try:
        user_id = update.effective_user.id
        history = await get_chat_history(user_id, 20)
        
        response = "📖 تاریخچه گفتگوی شما:\n\n"
        for msg in reversed(history):  # نمایش از قدیمی به جدید
            role_icon = "👤" if msg['role'] == 'user' else "🤖"
            response += f"{role_icon} {msg['message_text']}\n"
            response += f"⏰ {msg['created_at'][:16]}\n"
            response += "─" * 30 + "\n"
        
        await update.message.reply_text(response[:4000])
        
    except Exception as e:
        await update.message.reply_text(f"خطا: {str(e)}")

# تنظیمات ربات
def main():
    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("clearhistory", clear_history))
    application.add_handler(CommandHandler("history", show_history))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("✅ ربات با حافظه شروع به کار کرد...")
    application.run_polling()

if __name__ == '__main__':
    main()
