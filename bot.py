```python
import os
import json
import asyncio
from datetime import datetime
from typing import Dict, List

from dotenv import load_dotenv
from openai import OpenAI
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

from supabase import create_client, Client

load_dotenv()

# ---------- تنظیمات اولیه ----------
BOT_TOKEN   = os.environ["BOT_TOKEN"]
HF_TOKEN    = os.environ["HF_TOKEN"]
SUPABASE_URL= os.environ["SUPABASE_URL"]
SUPABASE_KEY= os.environ["SUPABASE_KEY"]

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

openai_client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=HF_TOKEN,
)

# ---------- دیتابیس سوپابیس ----------
def ensure_tables():
    # جدول users
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
        """}).execute()

    # جدول messages
    supabase.rpc('exec_sql', {
        'query': """
        CREATE TABLE IF NOT EXISTS messages (
            id BIGSERIAL PRIMARY KEY,
            user_id BIGINT REFERENCES users(user_id),
            role TEXT CHECK (
