import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from openai import OpenAI
import requests

# ==================== تنظیمات توکن‌ها ====================
BOT_TOKEN = os.environ.get('BOT_TOKEN')  # توکن ربات تلگرام
HF_TOKEN = os.environ.get('HF_TOKEN')    # توکن Hugging Face
SUPABASE_URL = os.environ.get('SUPABASE_URL')  # URL سوپابیس
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')  # توکن API سوپابیس

# بررسی وجود همه توکن‌ها
if not all([BOT_TOKEN, HF_TOKEN, SUPABASE_URL, SUPABASE_KEY]):
    raise ValueError("❌ لطفاً همه متغیرهای محیطی را تنظیم کنید")

print("✅ همه توکن‌ها دریافت شدند")

# ==================== راه‌اندازی کلاینت‌ها ====================
# کلاینت OpenAI برای Hugging Face
client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key="HF_TOKEN",
)

# ==================== توابع Supabase ====================
def supabase_request(table: str, method: str = "POST", data: dict = None, params: dict = None):
    """ارسال درخواست مستقیم به Supabase"""
    try:
        url = f"{SUPABASE_URL}/rest/v1/{table}"
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal"
        }
        
        if method == "GET":
            response = requests.get(url, headers=headers, params=params, timeout=10)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=data, timeout=10)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers, timeout=10)
        else:
            return None
            
        if response.status_code in [200, 201]:
            return response.json() if response.content else True
        return None
        
    except Exception as e:
        print(f"❌ خطا در Supabase: {e}")
        return None

async def save_user(user_id: int, username: str, first_name: str, last_name: str):
    """ذخیره کاربر جدید در دیتابیس"""
    user_data = {
        "user_id": user_id,
        "username": username or "",
        "first_name": first_name or "",
        "last_name": last_name or "",
        "message_count": 0
    }
    result = supabase_request("users", "POST", user_data)
    if result:
        print(f"✅ کاربر ذخیره شد: {user_id}")
    else:
        print(f"⚠️ کاربر از قبل وجود دارد: {user_id}")

async def save_message(user_id: int, message_text: str, role: str = "user"):
    """ذخیره پیام در دیتابیس"""
    message_data = {
        "user_id": user_id,
        "message_text": message_text,
        "role": role
    }
    if supabase_request("messages", "POST", message_data):
        print(f"💾 پیام ذخیره شد برای کاربر {user_id}")
        
        # آپدیت تعداد پیام‌های کاربر
        user_data = supabase_request("users", "GET", params={"user_id": f"eq.{user_id}"})
        if user_data:
            current_count = user_data[0].get("message_count", 0)
            update_data = {"message_count": current_count + 1}
            supabase_request("users", "POST", update_data, params={"user_id": f"eq.{user_id}"})

async def get_user_history(user_id: int, limit: int = 6):
    """دریافت تاریخچه گفتگوی کاربر"""
    try:
        params = {
            "user_id": f"eq.{user_id}",
            "order": "created_at.desc",
            "limit": str(limit)
        }
        history = supabase_request("messages", "GET", params=params) or []
        return history[::-1]  # برگرداندن از قدیمی به جدید
    except Exception as e:
        print(f"❌ خطا در دریافت تاریخچه: {e}")
        return []

# ==================== توابع هوش مصنوعی ====================
def generate_ai_response(user_text: str, history: list = None):
    """تولید پاسخ با هوش مصنوعی Gemma"""
    try:
        # ساخت messages با تاریخچه
        messages = []
        
        # اضافه کردن تاریخچه گفتگو
        if history:
            for msg in history:
                messages.append({
                    "role": msg['role'],
                    "content": msg['message_text']
                })
        
        # اضافه کردن پیام جدید کاربر
        messages.append({
            "role": "user",
            "content": user_text
        })
        
        # ارسال به هوش مصنوعی
       completion = client.chat.completions.create(
    model="moonshotai/Kimi-K2-Instruct-0905:together",
    messages=[
        {
            "role": "user",
            "content": "What is the capital of France?"
        }
    ],
 
        return completion.choices[0].message.content
        
    except Exception as e:
        print(f"❌ خطا در تولید پاسخ: {e}")
        return "متأسفم، در پردازش مشکلی پیش آمد"
)

# ==================== دستورات ربات ====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دستور شروع ربات"""
    user = update.effective_user
    await save_user(user.id, user.username, user.first_name, user.last_name)
    
    welcome_text = (
        "👋 سلام! به ربات هوشمند خوش آمدید!\n\n"
        "من با هوش مصنوعی Gemma-3 کار می‌کنم و حافظه دارم! 🧠\n"
        "هر پیامی بفرستید با توجه به تاریخچه گفتگو پاسخ می‌دم.\n\n"
        "✨ ویژگی‌ها:\n"
        "• ذخیره تمام گفتگوها در دیتابیس\n"
        "• حافظه هوش مصنوعی برای هر کاربر\n"
        "• پشتیبانی از چندین کاربر\n"
        "• استفاده از مدل پیشرفته Gemma-3"
    )
    await update.message.reply_text(welcome_text)
    await save_message(user.id, "/start", "command")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پردازش پیام‌های کاربر"""
    user = update.effective_user
    user_text = update.message.text
    
    print(f"📩 پیام از کاربر {user.id}: {user_text}")
    
    # ذخیره کاربر اگر وجود ندارد
    await save_user(user.id, user.username, user.first_name, user.last_name)
    
    await update.message.reply_chat_action("typing")
    
    try:
        # دریافت تاریخچه کاربر
        history = await get_user_history(user.id)
        print(f"📖 تاریخچه کاربر: {len(history)} پیام")
        
        # تولید پاسخ با هوش مصنوعی
        bot_response = generate_ai_response(user_text, history)
        
        # ذخیره پیام کاربر و پاسخ ربات
        await save_message(user.id, user_text, "user")
        await save_message(user.id, bot_response, "assistant")
        
        await update.message.reply_text(bot_response[:4000])
        
    except Exception as e:
        error_msg = f"خطا: {str(e)}"
        print(f"🚨 خطا: {error_msg}")
        await update.message.reply_text("⚡ مشکلی پیش آمد. لطفاً دوباره تلاش کنید.")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """آمار کاربر"""
    user = update.effective_user
    try:
        user_data = supabase_request("users", "GET", params={"user_id": f"eq.{user.id}"})
        if user_data:
            msg_count = user_data[0].get("message_count", 0)
            await update.message.reply_text(f"📊 شما {msg_count} پیام فرستادید!")
        else:
            await update.message.reply_text("❌ اطلاعات شما یافت نشد")
    except Exception as e:
        await update.message.reply_text(f"❌ خطا: {str(e)}")

async def my_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """مشاهده تاریخچه کاربر"""
    user = update.effective_user
    try:
        history = await get_user_history(user.id, 8)
        
        if not history:
            await update.message.reply_text("📝 تاریخچه‌ای یافت نشد")
            return
            
        response = "📖 آخرین گفتگوهای شما:\n\n"
        for msg in history:
            role_icon = "👤" if msg['role'] == 'user' else "🤖"
            response += f"{role_icon} {msg['message_text']}\n"
            response += "─" * 30 + "\n"
        
        await update.message.reply_text(response[:4000])
        
    except Exception as e:
        await update.message.reply_text(f"❌ خطا: {str(e)}")

# ==================== راه‌اندازی ربات ====================
def main():
    """تابع اصلی اجرای ربات"""
    # ایجاد برنامه ربات
    application = Application.builder().token(BOT_TOKEN).build()
    
    # اضافه کردن دستورات
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("stats", stats))
    application.add_handler(CommandHandler("history", my_history))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("🚀 ربات هوشمند با ویژگی‌های زیر شروع به کار کرد:")
    print("   ✅ ذخیره کاربران و پیام‌ها در Supabase")
    print("   ✅ حافظه هوش مصنوعی برای هر کاربر")
    print("   ✅ استفاده از مدل Gemma-3-27B")
    print("   ✅ پشتیبانی از چندین کاربر")
    
    # اجرای ربات
    application.run_polling()

if __name__ == '__main__':
    main()
