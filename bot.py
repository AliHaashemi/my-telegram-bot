import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from supabase import create_client, Client
from openai import OpenAI

# دریافت توکن‌ها از متغیرهای محیطی
BOT_TOKEN = os.environ.get('BOT_TOKEN')
HF_TOKEN = os.environ.get('HF_TOKEN')
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')

# بررسی وجود همه متغیرها
if not BOT_TOKEN:
    raise ValueError("❌ لطفاً BOT_TOKEN را تنظیم کنید")
if not HF_TOKEN:
    raise ValueError("❌ لطفاً HF_TOKEN را تنظیم کنید")
if not SUPABASE_URL:
    raise ValueError("❌ لطفاً SUPABASE_URL را تنظیم کنید")
if not SUPABASE_KEY:
    raise ValueError("❌ لطفاً SUPABASE_KEY را تنظیم کنید")

# ایجاد کلاینت Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ایجاد کلاینت OpenAI برای Hugging Face
client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=HF_TOKEN,
)

def query_moonshot_ai(prompt):
    """ارسال درخواست به هوش مصنوعی Moonshot"""
    try:
        completion = client.chat.completions.create(
            model="moonshotai/Kimi-K2-Instruct-0905:together",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=500,
            temperature=0.7
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"خطا در پردازش هوش مصنوعی: {str(e)}"

async def save_user(update: Update):
    """ذخیره اطلاعات کاربر در دیتابیس Supabase"""
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
            print(f"✅ کاربر جدید ثبت شد: {user.id}")
        else:
            # آپدیت کاربر موجود
            supabase.table("users").update({
                "message_count": existing_user.data[0]["message_count"] + 1,
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name
            }).eq("user_id", user.id).execute()
            
    except Exception as e:
        print(f"❌ خطا در ذخیره کاربر: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دستور شروع ربات"""
    await save_user(update)
    await update.message.reply_text(
        'سلام! 👋\n'
        'من یک ربات هوشمندم که با Moonshot AI کار می‌کنم.\n'
        'هر پیامی بفرستید با هوش مصنوعی پاسخ می‌دم!'
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پردازش پیام‌های کاربر"""
    await save_user(update)
    user_text = update.message.text
    
    # نشان دادن وضعیت تایپ کردن
    await update.message.reply_chat_action("typing")
    
    # دریافت پاسخ از هوش مصنوعی
    response_text = query_moonshot_ai(user_text)
    
    # ارسال پاسخ به کاربر
    await update.message.reply_text(response_text[:4000])

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """آمار کاربران"""
    try:
        result = supabase.table("users").select("count").execute()
        total_users = len(result.data)
        
        # محاسبه مجموع پیام‌ها
        total_messages = supabase.table("users").select("message_count").execute()
        total_msg_count = sum(user['message_count'] for user in total_messages.data)
        
        await update.message.reply_text(
            f"📊 آمار ربات:\n"
            f"👥 تعداد کاربران: {total_users}\n"
            f"💬 مجموع پیام‌ها: {total_msg_count}"
        )
    except Exception as e:
        await update.message.reply_text(f"❌ خطا در دریافت آمار: {e}")

async def myinfo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """اطلاعات کاربر فعلی"""
    user = update.effective_user
    try:
        user_data = supabase.table("users").select("*").eq("user_id", user.id).execute()
        
        if user_data.data:
            data = user_data.data[0]
            await update.message.reply_text(
                f"👤 اطلاعات شما:\n"
                f"🆔 ID: {data['user_id']}\n"
                f"👤 نام: {data['first_name']} {data['last_name']}\n"
                f"📧 username: @{data['username']}\n"
                f"💬 تعداد پیام‌ها: {data['message_count']}\n"
                f"📅 عضو since: {data['created_at']}"
            )
        else:
            await update.message.reply_text("❌ اطلاعات شما یافت نشد")
    except Exception as e:
        await update.message.reply_text(f"❌ خطا در دریافت اطلاعات: {e}")

def main():
    """تابع اصلی اجرای ربات"""
    # ایجاد برنامه ربات
    application = Application.builder().token(BOT_TOKEN).build()
    
    # اضافه کردن دستورات
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("stats", stats))
    application.add_handler(CommandHandler("myinfo", myinfo))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("✅ ربات با قابلیت‌های زیر شروع به کار کرد:")
    print("   - هوش مصنوعی Moonshot")
    print("   - دیتابیس Supabase")
    print("   - ذخیره اطلاعات کاربران")
    print("   - دستورات مدیریتی")
    
    # اجرای ربات
    application.run_polling()

if __name__ == '__main__':
    main()
