import os
from dotenv import load_dotenv
from supabase import create_client, Client

# --- SABİTLER ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# .env dosyasını yükle (Explicit path)
env_path = os.path.join(BASE_DIR, ".env")
load_dotenv(env_path)

# Font dosyasının proje ana dizininde (main.py ile aynı yerde) olduğunu varsayıyoruz
FONT_PATH = os.path.join(BASE_DIR, "DejaVuSans.ttf")
NOTES_PER_PAGE = 5
TIMEZONE = os.getenv("TIMEZONE", "Europe/Istanbul")  # Varsayilan: Turkiye

# --- API ANAHTARLARI ---
# --- CONFIGURATION (Vira Production) ---
# Bu klasör Vira Production (Gerçek) botu içindir.
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not BOT_TOKEN:
    print("❌ HATA: TELEGRAM_BOT_TOKEN bulunamadı! Lütfen .env dosyasını kontrol edin.")
    print(f"   Beklenen .env yolu: {env_path}")
    print("   İçerik formatı: TELEGRAM_BOT_TOKEN=123456:ABC-DEF...")
BOT_NAME = "Vira"
OPENWEATHERMAP_API_KEY = os.getenv("OPENWEATHERMAP_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
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