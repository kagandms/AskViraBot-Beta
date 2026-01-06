
import os
from .settings import settings
from supabase import create_client, Client

# --- EXPORTS (Compatibility with old config.py) ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT_PATH = os.path.join(BASE_DIR, "DejaVuSans.ttf")
NOTES_PER_PAGE = settings.NOTES_PER_PAGE
TIMEZONE = settings.TIMEZONE
BOT_NAME = settings.BOT_NAME
AI_DAILY_LIMIT = settings.AI_DAILY_LIMIT

# API KEYS (Validated by Pydantic on import)
BOT_TOKEN = settings.TELEGRAM_BOT_TOKEN.get_secret_value()
OPENWEATHERMAP_API_KEY = settings.OPENWEATHERMAP_API_KEY
OPENROUTER_API_KEY = settings.OPENROUTER_API_KEY
SUPABASE_URL = settings.SUPABASE_URL
SUPABASE_KEY = settings.SUPABASE_KEY.get_secret_value()

ADMIN_IDS = settings.get_admin_ids

# --- SINGLETONS ---
supabase: Client = None
try:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("✅ Supabase (PostgreSQL) Bağlantısı Başarılı! (via Pydantic Settings)")
except Exception as e:
    print(f"❌ Supabase Bağlantı Hatası: {e}")
