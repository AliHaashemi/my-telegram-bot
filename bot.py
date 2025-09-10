import os
import requests
import torch
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from supabase import create_client, Client
from transformers import AutoModelForCausalLM, AutoTokenizer

# ==================== تنظیمات توکن‌ها ====================
BOT_TOKEN = os.environ.get('BOT_TOKEN')  # توکن ربات تلگرام
HF_TOKEN = os.environ.get('HF_TOKEN')    # توکن Hugging Face
SUPABASE_URL = os.environ.get('SUPABASE_URL')  # URL سوپابیس
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')  # توکن API سوپابیس

# ==================== بررسی توکن‌ها ====================
if not all([BOT_TOKEN, HF_TOKEN, SUPABASE_URL, SUPABASE_KEY]):
    raise ValueError("لطفاً همه متغیرهای محیطی را تنظیم کنید")

# ==================== راه‌اندازی کلاینت‌ها ====================
# سوپابیس
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# هوش مصنوعی StepFun
try:
    print("🌀 در حال بارگذاری مدل StepFun...")
    model = AutoModelForCausalLM.from_pretrained(
        "stepfun-ai/Step-Audio-2-mini", 
        trust_remote_code=True, 
        torch_dtype="auto"
    )
    tokenizer = AutoTokenizer.from_pretrained("stepfun-ai/Step-Audio-2-mini")
    print("✅ مدل StepFun بارگذاری شد")
except Exception as e:
    print(f"❌ خطا در بارگذاری مدل: {e}")
    model = None
    tokenizer = None

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
                "message_count": 0,
                "created_at": "now()"
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
            "role": role,
            "created_at": "now()"
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
def generate_stepfun_response(prompt: str, history: list = None):
    """تولید پاسخ با StepFun AI"""
    try:
        if model is None or tokenizer is None:
            return "مدل هوش مصنوعی در دسترس نیست"
        
        # ساخت متن ورودی با تاریخچه
        if history:
            conversation = "\n".join([f"{'User' if msg['role'] == 'user' else 'Assistant'}: {msg['message_text']}" for msg in history])
            full_prompt = f"{conversation}\nUser: {prompt}\nAssistant:"
        else:
            full_prompt = f"User: {prompt}\nAssistant:"
        
        # توکنایز و تولید پاسخ
        inputs = tokenizer.encode(full_prompt, return_tensors="pt")
        
        with torch.no_grad():
            outputs = model.generate(
                inputs,
                max_length=500,
                temperature=0.7,
                do_sample=True,
                pad_token_id=tokenizer.eos_token_id
            )
        
        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # استخراج فقط پاسخ آخر
        if "Assistant:" in response:
            response = response.split("Assistant:")[-1].strip()
        
        return response
        
    except Exception as e:
        print(f"❌ خطا در تولید پاسخ: {e}")
        return "متأسفم، در پردازش مشکلی پیش آمد"

def generate_huggingface_response(prompt: str):
    """تولید پاسخ با Hugging Face (fallback)"""
    try:
        url = "https://api-inference.huggingface.co/models/microsoft/DialoGPT-medium"
        headers = {"Authorization": f"Bearer {HF_TOKEN}"}
        data = {"inputs": prompt, "parameters": {"max_length": 100}}
        
        response = requests.post(url, headers=headers, json=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if isinstance(result, list) and len(result) > 0:
                return result[0].get('generated_text', 'پاسخ نامعلوم')
        return "پاسخ نامعلوم"
    except Exception as e:
        return f"خطا در اتصال: {str(e)}"

# =================═ دستورات ربات ====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دستور شروع"""
    user = update.effective_user
    await save_user(user.id, user.username, user.first_name, user.last_name)
    
    welcome_text = (
        "👋 سلام! به ربات هوشمند خوش آمدید!\n\n"
        "من با هوش مصنوعی StepFun کار می‌کنم و حافظه دارم!\n"
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
        
        # تولید پاسخ با StepFun
        bot_response = generate_stepfun_response(user_text, history)
        
        # اگر StepFun جواب نداد، از Hugging Face استفاده کن
        if not bot_response or "پاسخ نامعلوم" in bot_response:
            bot_response = generate_huggingface_response(user_text)
        
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
    for msg in history[-5:]:  # فقط ۵ تا آخر
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
    
    # دستورات
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("history", history_cmd))
    application.add_handler(CommandHandler("stats", stats_cmd))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("🚀 ربات هوشمند با حافظه شروع به کار کرد!")
    print("📊 همه پیام‌ها در Supabase ذخیره می‌شوند")
    print("🧠 از مدل StepFun AI استفاده می‌کند")
    
    application.run_polling()

if __name__ == '__main__':
    main()
