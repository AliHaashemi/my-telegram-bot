import os
import requests
import json
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ==================== تنظیمات توکن‌ها ====================
BOT_TOKEN = os.environ.get('BOT_TOKEN')
HF_TOKEN = os.environ.get('HF_TOKEN')
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')

print("✅ توکن‌ها دریافت شدند")

# ==================== توابع Supabase مستقیم ====================
def supabase_request(table: str, method: str = "GET", data: dict = None):
    """درخواست مستقیم به Supabase"""
    try:
        url = f"{SUPABASE_URL}/rest/v1/{table}"
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json"
        }
        
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=10)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=data, timeout=10)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers, timeout=10)
        else:
            return None
            
        return response.json() if response.status_code == 200 else None
        
    except Exception as e:
        print(f"❌ خطا در Supabase: {e}")
        return None

async def save_user(user_id: int, username: str, first_name: str, last_name: str):
    """ذخیره کاربر جدید"""
    user_data = {
        "user_id": user_id,
        "username": username,
        "first_name": first_name,
        "last_name": last_name or "",
        "message_count": 0
    }
    result = supabase_request("users", "POST", user_data)
    if result:
        print(f"✅ کاربر ذخیره شد: {user_id}")

async def save_message(user_id: int, message_text: str, role: str = "user"):
    """ذخیره پیام"""
    message_data = {
        "user_id": user_id,
        "message_text": message_text,
        "role": role
    }
    result = supabase_request("messages", "POST", message_data)
    if result:
        print(f"💾 پیام ذخیره شد: {user_id}")

async def get_user_history(user_id: int, limit: int = 6):
    """دریافت تاریخچه کاربر"""
    try:
        url = f"{SUPABASE_URL}/rest/v1/messages?user_id=eq.{user_id}&order=created_at.desc&limit={limit}"
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}"
        }
        response = requests.get(url, headers=headers, timeout=10)
        return response.json() if response.status_code == 200 else []
    except Exception as e:
        print(f"❌ خطا در دریافت تاریخچه: {e}")
        return []

# ==================== توابع هوش مصنوعی ====================
def generate_ai_response(prompt: str, history: list = None):
    """تولید پاسخ با هوش مصنوعی"""
    try:
        url = "https://api-inference.huggingface.co/models/microsoft/DialoGPT-medium"
        headers = {"Authorization": f"Bearer {HF_TOKEN}"}
        
        full_prompt = prompt
        if history:
            conversation = "\n".join([msg['message_text'] for msg in history])
            full_prompt = f"{conversation}\n{prompt}"
            
        data = {"inputs": full_prompt, "parameters": {"max_length": 150}}
        
        response = requests.post(url, headers=headers, json=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if isinstance(result, list) and len(result) > 0:
                return result[0].get('generated_text', 'پاسخ نامعلوم')
        return "پاسخ نامعلوم"
        
    except Exception as e:
        print(f"❌ خطا در تولید پاسخ: {e}")
        return "متأسفم، در پردازش مشکلی پیش آمد"

# ==================== دستورات ربات ====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دستور شروع"""
    user = update.effective_user
    await save_user(user.id, user.username, user.first_name, user.last_name)
    
    welcome_text = "👋 سلام! به ربات هوشمند خوش آمدید!"
    await update.message.reply_text(welcome_text)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پردازش پیام‌های کاربر"""
    user = update.effective_user
    user_text = update.message.text
    
    print(f"📩 پیام از {user.id}: {user_text}")
    
    await save_user(user.id, user.username, user.first_name, user.last_name)
    await update.message.reply_chat_action("typing")
    
    try:
        history = await get_user_history(user.id)
        bot_response = generate_ai_response(user_text, history)
        
        await save_message(user.id, user_text, "user")
        await save_message(user.id, bot_response, "assistant")
        
        await update.message.reply_text(bot_response[:4000])
        
    except Exception as e:
        error_msg = f"خطا: {str(e)}"
        print(f"🚨 خطا: {error_msg}")
        await update.message.reply_text("⚡ مشکلی پیش آمد. لطفاً دوباره تلاش کنید.")

# ==================== راه‌اندازی ربات ====================
def main():
    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("🚀 ربات هوشمند شروع به کار کرد!")
    application.run_polling()

if __name__ == '__main__':
    main()
