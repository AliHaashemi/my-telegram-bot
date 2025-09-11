import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from supabase import create_client, Client
from openai import OpenAI

# ---------- بارگذاری تنظیمات ----------
load_dotenv()

BOT_TOKEN = os.environ["BOT_TOKEN"]
HF_TOKEN = os.environ["HF_TOKEN"]
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]

# ---------- اتصال به سرویس‌ها ----------
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

ai_client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=HF_TOKEN
)

# ---------- ایجاد جدول‌ها اگر وجود ندارند ----------
def ensure_tables():
    supabase.rpc('exec_sql', {
        'query': """
        CREATE TABLE IF NOT EXISTS users (
            user_id BIGINT PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            lang_code TEXT,
            started_at TIMESTAMPTZ DEFAULT NOW()
        );
        """
    }).execute()

    supabase.rpc('exec_sql', {
        'query': """
        CREATE TABLE IF NOT EXISTS messages (
            id BIGSERIAL PRIMARY KEY,
            user_id BIGINT REFERENCES users(user_id),
            role TEXT CHECK (role IN ('user', 'assistant')),
            content TEXT,
            created_at TIMESTAMPTZ DEFAULT NOW()
        );
        """
    }).execute()

# ---------- تابع شروع ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    # ذخیره اطلاعات کاربر
    supabase.table("users").upsert({
        "user_id": user.id,
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "lang_code": user.language_code
    }).execute()

    await update.message.reply_text("سلام! من یک ربات هوش مصنوعی هستم. هر سوالی داری بپرس.")

# ---------- تابع دریافت پیام و پاسخ ----------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text

    # ذخیره پیام کاربر
    supabase.table("messages").insert({
        "user_id": user.id,
        "role": "user",
        "content": text
    }).execute()

    # دریافت تاریخچه مکالمه کاربر برای حافظه
    history = supabase.table("messages").select("role, content").eq("user_id", user.id).order("created_at", desc=False).execute()
    messages = [{"role": h["role"], "content": h["content"]} for h in history.data]

    # اضافه کردن پیام جدید
    messages.append({"role": "user", "content": text})

    # فراخوانی مدل هوش مصنوعی
    try:
        completion = ai_client.chat.completions.create(
            model="moonshotai/Kimi-K2-Instruct-0905:together",
            messages=messages[-15:]  # آخرین ۱۵ پیام برای حافظه
        )

        reply = completion.choices[0].message.content

        # ذخیره پاسخ
        supabase.table("messages").insert({
            "user_id": user.id,
            "role": "assistant",
            "content": reply
        }).execute()

        await update.message.reply_text(reply)

    except Exception as e:
        print("AI Error:", e)
        await update.message.reply_text("خطایی پیش اومد. لطفا بعداً دوباره تلاش کن.")

# ---------- اجرای بات ----------
def main():
    ensure_tables()

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("ربات در حال اجراست...")
    app.run_polling()

if __name__ == "__main__":
    main()
