import os
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from supabase import create_client, Client

# ==================== تنظیمات توکن‌ها ====================
BOT_TOKEN = os.environ.get('BOT_TOKEN')
HF_TOKEN = os.environ.get('HF_TOKEN')
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')

if not all([BOT_TOKEN, HF_TOKEN, SUPABASE_URL, SUPABASE_KEY]):
    raise ValueError("لطفاً همه متغیرهای محیطی را تنظیم کنید")

# ==================== راه‌اندازی کلاینت‌ها ====================
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
print("✅ سوپابیس متصل شد")

# ==================== توابع دیتابیس ====================
async def save_user(user_id: int, username: str, first_name: str, last_name: str):
    """ذخیره کاربر جدید در دیتابیس"""
    try:
        existing_user = supabase.table("users").select("*").eq("user_id", user_id).execute()
        
        if not existing_user.data:
            supabase.table("users").insert({
                "user_id": user_id,
                "username": username,
                "first_name": first_name,
                "last_name": last_name or "",
                "message_count": 0
            }).execute()
            print(f"✅ کاربر جدید ذخیره شد: {user_id}")
    except Exception as e:
        print(f"❌ خطا در ذخیره کاربر: {e}")

async def save_message(user_id: int, message_text: str, role: str = "user"):
    """ذخیره پیام در دیتابیس"""
    try:
        supabase.table("messages").insert({
            "user_id": user_id,
            "message_text": message_text,
            "role": role
        }).execute()
        
        # آپدیت تعداد پیام‌های کاربر
        supabase.table("users").update({
            "message_count": supabase.table("users")
                .select("message_count")
                .eq("user_id", user_id)
                .execute().data[0]["message_count"] + 1
        }).eq("user_id", user_id).execute()
        
        print(f"💾 پیام ذخیره شد برای کاربر {user_id}")
    except Exception as e:
        print(f"❌ خطا در ذخیره پیام: {e}")

async def get_user_history(user_id: int, limit: int = 6):
    """دریافت تاریخچه کاربر"""
    try:
        response = supabase.table("messages").select("*").eq("user_id", user_id).order("created_at", desc=False).limit(limit).execute()
        return response.data
    except Exception as e:
        print(f"❌ خطا در دریافت تاریخچه: {e}")
        return []

# ==================== توابع هوش مصنوعی ====================
def generate_ai_response(prompt: str, history: list = None):
    """تولید پاسخ با هوش مصنوعی"""
    try:
        # استفاده از Hugging Face API
        url = "https://api-inference.huggingface.co/models/microsoft/DialoGPT-medium"
        headers = {"Authorization": f"Bearer {HF_TOKEN}"}
        
        # ساخت prompt با تاریخچه
        if history:
            conversation = "\n".join([f"{msg['message_text']}" for msg in history])
            full_prompt = f"{conversation}\n{prompt}"
        else:
            full_prompt = prompt
            
        data = {"inputs": full_prompt, "parameters": {"max_length": 150}}
        
        response = requests.post(url, headers=headers, json=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if isinstance(result, list) and len(result) > 0:
                return result[0].get('generated_text', 'پاسخ نامعلوم').split('\n')[-1]
        return "پاسخ نامعلوم"
        
    except Exception as e:
        print(f"❌ خطا در تولید پاسخ: {e}")
        return "متأسفم، در پردازش مشکلی پیش آمد"

# ==================== دستورات ربات ====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دستور شروع"""
    user = update.effective_user
    await save_user(user.id, user.username, user.first_name, user.last_name)
    
    welcome_text = (
        "👋 سلام! به ربات هوشمند خوش آمدید!\n\n"
        "من با هوش مصنوعی کار می‌کنم و حافظه دارم!\n"
        "هر پیامی بفرستید با توجه به تاریخچه گفتگو پاسخ می‌دم."
    )
    await update.message.reply_text(welcome_text)
    await save_message(user.id, "/start", "command")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پردازش پیام‌های کاربر"""
    user = update.effective_user
    user_text = update.message.text
    
    print(f"📩 پیام از {user.id}: {user_text}")
    
    # ذخیره کاربر اگر وجود ندارد
    await save_user(user.id, user.username, user.first_name, user.last_name)
    
    await update.message.reply_chat_action("typing")
    
    try:
        # دریافت تاریخچه کاربر
        history = await get_user_history(user.id)
        print(f"📖 تاریخچه کاربر: {len(history)} پیام")
        
        # تولید پاسخ
        bot_response = generate_ai_response(user_text, history)
        
        # ذخیره پیام کاربر و پاسخ ربات
        await save_message(user.id, user_text, "user")
        await save_message(user.id, bot_response, "assistant")
        
        await update.message.reply_text(bot_response[:4000])
        
    except Exception as e:
        error_msg = f"خطا: {str(e)}"
        print(f"🚨 خطا: {error_msg}")
        await update.message.reply_text("⚡ مشکلی پیش آمد. لطفاً دوباره تلاش کنید.")

async def history_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """مشاهده تاریخچه"""
    user = update.effective_user
    history = await get_user_history(user.id, 10)
    
    response = "📖 آخرین گفتگوهای شما:\n\n"
    for msg in history[-5:]:
        role_icon = "👤" if msg['role'] == 'user' else "🤖"
        response += f"{role_icon} {msg['message_text']}\n"
        response += "─" * 30 + "\n"
    
    await update.message.reply_text(response[:4000])

async def stats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """آمار کاربر"""
    user = update.effective_user
    try:
        user_data = supabase.table("users").select("*").eq("user_id", user.id).execute()
        if user_data.data:
            msg_count = user_data.data[0]["message_count"]
            await update.message.reply_text(f"📊 شما {msg_count} پیام فرستادید!")
    except Exception as e:
        await update.message.reply_text(f"❌ خطا: {str(e)}")

# ==================== راه‌اندازی ربات ====================
def main():
    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("history", history_cmd))
    application.add_handler(CommandHandler("stats", stats_cmd))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("🚀 ربات هوشمند با حافظه شروع به کار کرد!")
    application.run_polling()

if __name__ == '__main__':
    main()
