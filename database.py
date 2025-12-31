import logging
from config import supabase

# Loglama ayarı: Bu modül için bir logger oluşturuyoruz
logger = logging.getLogger(__name__)

# --- KULLANICI İŞLEMLERİ ---
# Dil önbelleği (Cache) - DB yükünü azaltmak için
_user_lang_cache = {}

def get_user_lang(user_id):
    user_id = str(user_id)
    # 1. Önce cache'e bak
    if user_id in _user_lang_cache:
        return _user_lang_cache[user_id]
        
    if not supabase: return "en"
    try:
        # 2. Cache'de yoksa DB'den çek
        response = supabase.table("users").select("language").eq("user_id", user_id).execute()
        if response.data:
            lang = response.data[0]["language"]
        else:
            lang = "en"
            
        # 3. Sonucu cache'e kaydet
        _user_lang_cache[user_id] = lang
        return lang
    except Exception as e:
        logger.error(f"Dil getirme hatası (User: {user_id}): {e}")
        return "en"

def set_user_lang_db(user_id, lang):
    user_id = str(user_id)
    # 1. Cache'i güncelle
    _user_lang_cache[user_id] = lang
    
    if not supabase: return
    try:
        # 2. DB'yi güncelle
        data = {"user_id": user_id, "language": lang}
        supabase.table("users").upsert(data).execute()
    except Exception as e:
        logger.error(f"Dil kaydetme hatası (User: {user_id}, Lang: {lang}): {e}")

# --- NOT İŞLEMLERİ (CORE) ---
def get_user_notes(user_id):
    """Veritabanından notları ham (dict) formatında çeker."""
    if not supabase: return []
    try:
        response = supabase.table("notes").select("id, content").eq("user_id", str(user_id)).order("id").execute()
        return [note for note in response.data] 
    except Exception as e:
        logger.error(f"Notları getirme hatası (User: {user_id}): {e}")
        return []

def add_user_note(user_id, note_content):
    if not supabase: return
    try:
        data = {"user_id": str(user_id), "content": note_content}
        supabase.table("notes").insert(data).execute()
    except Exception as e:
        logger.error(f"Not ekleme hatası (User: {user_id}): {e}")

def update_user_note(note_id, new_content):
    if not supabase: return False
    try:
        supabase.table("notes").update({"content": new_content}).eq("id", note_id).execute()
        return True
    except Exception as e:
        logger.error(f"Not güncelleme hatası (ID: {note_id}): {e}")
        return False

def delete_user_note_by_id(note_id):
    if not supabase: return False
    try:
        supabase.table("notes").delete().eq("id", note_id).execute()
        return True
    except Exception as e:
        logger.error(f"Not silme hatası (ID: {note_id}): {e}")
        return False

# --- NOT İŞLEMLERİ (UYUMLULUK KATMANI / WRAPPERS) ---
# handlers/notes.py dosyasının beklediği fonksiyonlar

def get_notes(user_id):
    """Sadece not içeriklerini string listesi olarak döndürür."""
    raw_notes = get_user_notes(user_id)
    return [note['content'] for note in raw_notes]

def add_note(user_id, content):
    """add_user_note fonksiyonuna yönlendirir."""
    add_user_note(user_id, content)

def delete_note(user_id, note_number):
    """
    Sıra numarasına (1, 2, 3...) göre not siler.
    Önce listeyi çeker, sıra numarasını ID'ye çevirir ve siler.
    """
    raw_notes = get_user_notes(user_id)
    # note_number 1'den başlar, python listesi 0'dan
    index = note_number - 1
    
    if 0 <= index < len(raw_notes):
        note_id = raw_notes[index]['id']
        return delete_user_note_by_id(note_id)
    return False

def update_note(user_id, note_index, new_content):
    """
    Liste indeksine (0, 1, 2...) göre not günceller.
    """
    raw_notes = get_user_notes(user_id)
    
    if 0 <= note_index < len(raw_notes):
        note_id = raw_notes[note_index]['id']
        return update_user_note(note_id, new_content)
    return False

# --- HATIRLATICI İŞLEMLERİ ---
def get_all_reminders_db():
    if not supabase: return []
    try:
        response = supabase.table("reminders").select("*").execute()
        return response.data
    except Exception as e:
        logger.error(f"Hatırlatıcıları çekme hatası: {e}")
        return []

def add_reminder_db(reminder_data):
    if not supabase: return
    try:
        data_to_insert = {
            "user_id": str(reminder_data["user_id"]),
            "chat_id": str(reminder_data["chat_id"]),
            "message": reminder_data["message"],
            "time": reminder_data["time"]
        }
        supabase.table("reminders").insert(data_to_insert).execute()
    except Exception as e:
        logger.error(f"Hatırlatıcı ekleme hatası: {e}")

def remove_reminder_db(reminder_id):
    if not supabase: return
    try:
        supabase.table("reminders").delete().eq("id", reminder_id).execute()
    except Exception as e:
        logger.error(f"Hatırlatıcı silme hatası: {e}")
# --- ADMIN FONKSİYONLARI ---
def get_all_users_count():
    """Toplam kullanıcı sayısını döner"""
    if not supabase: return 0
    try:
        response = supabase.table("users").select("user_id", count="exact").execute()
        return response.count if response.count else 0
    except Exception as e:
        logger.error(f"Kullanıcı sayısı hatası: {e}")
        return 0

def get_all_notes_count():
    """Toplam not sayısını döner"""
    if not supabase: return 0
    try:
        response = supabase.table("notes").select("id", count="exact").execute()
        return response.count if response.count else 0
    except Exception as e:
        logger.error(f"Not sayısı hatası: {e}")
        return 0

def get_all_reminders_count():
    """Toplam hatırlatıcı sayısını döner"""
    if not supabase: return 0
    try:
        response = supabase.table("reminders").select("id", count="exact").execute()
        return response.count if response.count else 0
    except Exception as e:
        logger.error(f"Hatırlatıcı sayısı hatası: {e}")
        return 0

def get_all_user_ids():
    """Tüm kullanıcı ID'lerini döner (broadcast için)"""
    if not supabase: return []
    try:
        response = supabase.table("users").select("user_id").execute()
        return [int(u['user_id']) for u in response.data] if response.data else []
    except Exception as e:
        logger.error(f"Kullanıcı listesi hatası: {e}")
        return []

def get_recent_users(limit=10):
    """Son eklenen kullanıcıları döner"""
    if not supabase: return []
    try:
        response = supabase.table("users").select("*").order("created_at", desc=True).limit(limit).execute()
        return response.data if response.data else []
    except Exception as e:
        logger.error(f"Son kullanıcılar hatası: {e}")
        return []
        return []

# --- AKTİVİTE LOGLAMA (YENİ) ---
def log_qr_usage(user_id, content):
    """QR kod oluşturma işlemini loglar."""
    if not supabase: return
    try:
        data = {"user_id": str(user_id), "content": content}
        supabase.table("qr_logs").insert(data).execute()
    except Exception as e:
        logger.error(f"QR log hatası (User: {user_id}): {e}")

def log_pdf_usage(user_id, pdf_type):
    """PDF dönüştürme işlemini loglar (text, image, document)."""
    if not supabase: return
    try:
        data = {"user_id": str(user_id), "type": pdf_type}
        supabase.table("pdf_logs").insert(data).execute()
    except Exception as e:
        logger.error(f"PDF log hatası (User: {user_id}): {e}")

def log_xox_game(user_id, winner, difficulty):
    """XOX oyun sonucunu loglar."""
    if not supabase: return
    try:
        data = {"user_id": str(user_id), "winner": winner, "difficulty": difficulty}
        supabase.table("xox_logs").insert(data).execute()
    except Exception as e:
        logger.error(f"XOX log hatası (User: {user_id}): {e}")

def log_tkm_game(user_id, user_move, bot_move, result):
    """TKM oyun sonucunu loglar."""
    if not supabase: return
    try:
        data = {
            "user_id": str(user_id), 
            "user_move": user_move, 
            "bot_move": bot_move, 
            "result": result
        }
        supabase.table("tkm_logs").insert(data).execute()
    except Exception as e:
        logger.error(f"TKM log hatası (User: {user_id}): {e}")

def log_coinflip(user_id, result):
    """Yazı Tura sonucunu loglar."""
    if not supabase: return
    try:
        data = {"user_id": str(user_id), "result": result}
        supabase.table("coinflip_logs").insert(data).execute()
    except Exception as e:
        logger.error(f"Coinflip log hatası (User: {user_id}): {e}")

def log_dice_roll(user_id, result):
    """Zar atma sonucunu loglar."""
    if not supabase: return
    try:
        data = {"user_id": str(user_id), "result": str(result)}
        supabase.table("dice_logs").insert(data).execute()
    except Exception as e:
        logger.error(f"Dice log hatası (User: {user_id}): {e}")
