import os
from dotenv import load_dotenv
from supabase import create_client, Client

# .env dosyasını yükle
load_dotenv()

# --- SABİTLER ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Font dosyasının proje ana dizininde (main.py ile aynı yerde) olduğunu varsayıyoruz
FONT_PATH = os.path.join(BASE_DIR, "DejaVuSans.ttf")
NOTES_PER_PAGE = 5
TIMEZONE = os.getenv("TIMEZONE", "Europe/Istanbul")  # Varsayilan: Turkiye

# --- API ANAHTARLARI ---
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENWEATHERMAP_API_KEY = os.getenv("OPENWEATHERMAP_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
AI_DAILY_LIMIT = 30  # Kullanıcı başına günlük AI mesaj limiti
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# --- ADMIN AYARLARI ---
# ADMIN_IDS: Virgülle ayrılmış Telegram user ID'leri (örn: "123456789,987654321")
_admin_ids_str = os.getenv("ADMIN_IDS", "")
ADMIN_IDS = [int(x.strip()) for x in _admin_ids_str.split(",") if x.strip().isdigit()]

# --- SUPABASE BAĞLANTISI ---
supabase: Client = None
if not SUPABASE_URL or not SUPABASE_KEY:
    print("⚠️ UYARI: SUPABASE_URL veya SUPABASE_KEY eksik! Veritabanı çalışmayacak.")
else:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("✅ Supabase (PostgreSQL) Bağlantısı Başarılı!")
    except Exception as e:
        print(f"❌ Supabase Bağlantı Hatası: {e}")