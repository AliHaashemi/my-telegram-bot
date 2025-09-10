import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from supabase import create_client, Client
from openai import OpenAI

# دریافت توکن‌ها
BOT_TOKEN = os.environ.get('BOT_TOKEN')
HF_TOKEN = os.environ.get('HF_TOKEN')
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')

print("✅ توکن‌ها دریافت شدند")

# کلاینت‌ها
try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("✅ Supabase متصل شد")
except Exception as e:
    print(f"❌ خطا در اتصال به Supabase: {e}")

client = OpenAI(base_url="https://router.huggingface.co/v1", api_key=HF_TOKEN)

async def save_user(update: Update):
    """ذخیره کاربر در دیتابیس"""
    user = update.effective_user
    try:
        existing_user = supabase.table("users").select("*").eq("user_id", user.id).execute()
        
        if len(existing_user.data) == 0:
            supabase.table("users").insert({
                "user_id": user.id,
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "message_count": 0
            }).execute()
            print(f"✅ کاربر جدید ذخیره شد: {user.id}")
            
    except Exception as e:
        print(f"❌ خطا در ذخیره کاربر: {e}")

async def save_message(user_id: int, content: str, role: str = "user", bot_response: str = None):
    """ذخیره پیام در دیتابیس"""
    try:
        message_data = {
            "user_id": user_id,
            "message_text": content,
            "role": role,
            "bot_response": bot_response
        }
        supabase.table("messages").insert(message_data).execute()
        
        # آپدیت تعداد پیام‌های کاربر
        supabase.table("users").update({
            "message_count": supabase.table("users")
                .select("message_count")
                .eq("user_id", user_id)
                .execute().data[0]["message_count"] + 1
        }).eq("user_id", user_id).execute()
        
    except Exception as e:
        print(f"❌ خطا در ذخیره پیام: {e}")

async def get_chat_history(user_id: int, limit: int = 6):
    """دریافت تاریخچه گفتگوی کاربر"""
    try:
        response = supabase.table("messages").select("*").eq("user_id", user_id).order("created_at", desc=False).limit(limit).execute()
        return response.data
    except Exception as e:
        print(f"❌ خطا در دریافت تاریخچه: {e}")
        return []

async def build_conversation_context(user_id: int, new_message: str):
    """ساخت زمینه گفتگو با تاریخچه"""
    history = await get_chat_history(user_id)
    
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
    
    print(f"📩 پیام از کاربر {user.id}: {user_text}")
    
    # ذخیره کاربر
    await save_user(update)
    
    await update.message.reply_chat_action("typing")
    
    try:
        # ساخت زمینه گفتگو با تاریخچه
        conversation_context = await build_conversation_context(user.id, user_text)
        print(f"🧠 Context length: {len(conversation_context)} messages")
        
        # ارسال به هوش مصنوعی
        completion = client.chat.completions.create(
            model="moonshotai/Kimi-K2-Instruct-0905:together",
            messages=conversation_context,
            max_tokens=500,
            temperature=0.7
        )
        
        bot_response = completion.choices[0].message.content
        
        # ذخیره پیام کاربر
        await save_message(user.id, user_text, "user", bot_response)
        
        # ذخیره پاسخ ربات
        await save_message(user.id, bot_response, "assistant", user_text)
        
        print(f"🤖 پاسخ: {bot_response[:100]}...")
        await update.message.reply_text(bot_response[:4000])
        
    except Exception as e:
        error_msg = f"خطا در پردازش: {str(e)}"
        print(f"🚨 خطا: {error_msg}")
        await update.message.reply_text("⚡ مشکلی پیش اومده. دوباره تلاش کن.")

async def my_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش تاریخچه کاربر"""
    try:
        user_id = update.effective_user.id
        history = await get_chat_history(user_id, 10)
        
        response = "📖 تاریخچه گفتگوی شما:\n\n"
        for msg in history:
            role_icon = "👤" if msg['role'] == 'user' else "🤖"
            response += f"{role_icon} {msg['message_text']}\n"
            response += f"⏰ {msg['created_at'][:16]}\n"
            response += "─" * 30 + "\n"
        
        await update.message.reply_text(response[:4000])
        
    except Exception as e:
        await update.message.reply_text(f"❌ خطا: {str(e)}")

async def clear_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پاک کردن تاریخچه کاربر"""
    try:
        user_id = update.effective_user.id
        supabase.table("messages").delete().eq("user_id", user_id).execute()
        await update.message.reply_text("✅ تاریخچه شما پاک شد!")
    except Exception as e:
        await update.message.reply_text(f"❌ خطا: {str(e)}")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """آمار کاربر"""
    try:
        user_id = update.effective_user.id
        user_data = supabase.table("users").select("*").eq("user_id", user_id).execute()
        message_count = user_data.data[0]["message_count"] if user_data.data else 0
        
        await update.message.reply_text(f"📊 شما {message_count} پیام فرستادید!")
    except Exception as e:
        await update.message.reply_text(f"❌ خطا: {str(e)}")

# تنظیمات ربات
def main():
    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("history", my_history))
    application.add_handler(CommandHandler("clear", clear_history))
    application.add_handler(CommandHandler("stats", stats))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("🚀 ربات با حافظه شروع به کار کرد...")
    application.run_polling()

if __name__ == '__main__':
    main()
