import logging
from typing import Optional, Any
from config import supabase

# Loglama ayarı: Bu modül için bir logger oluşturuyoruz
logger = logging.getLogger(__name__)
# --- KULLANICI İŞLEMLERİ ---
# Dil önbelleği (Cache) - DB yükünü azaltmak için
_user_lang_cache: dict[str, str] = {}

def get_user_lang(user_id: int | str) -> str:
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

def set_user_lang_db(user_id: int | str, lang: str) -> None:
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
def get_user_notes(user_id: int | str) -> list[dict[str, Any]]:
    """Veritabanından notları ham (dict) formatında çeker."""
    if not supabase: return []
    try:
        response = supabase.table("notes").select("id, content").eq("user_id", str(user_id)).order("id").execute()
        return [note for note in response.data] 
    except Exception as e:
        logger.error(f"Notları getirme hatası (User: {user_id}): {e}")
        return []

def add_user_note(user_id: int | str, note_content: str) -> None:
    if not supabase: return
    try:
        data = {"user_id": str(user_id), "content": note_content}
        supabase.table("notes").insert(data).execute()
    except Exception as e:
        logger.error(f"Not ekleme hatası (User: {user_id}): {e}")

def update_user_note(note_id: int, new_content: str) -> bool:
    if not supabase: return False
    try:
        supabase.table("notes").update({"content": new_content}).eq("id", note_id).execute()
        return True
    except Exception as e:
        logger.error(f"Not güncelleme hatası (ID: {note_id}): {e}")
        return False

def delete_user_note_by_id(note_id: int) -> bool:
    if not supabase: return False
    try:
        supabase.table("notes").delete().eq("id", note_id).execute()
        return True
    except Exception as e:
        logger.error(f"Not silme hatası (ID: {note_id}): {e}")
        return False

# --- NOT İŞLEMLERİ (UYUMLULUK KATMANI / WRAPPERS) ---
# handlers/notes.py dosyasının beklediği fonksiyonlar

def get_notes(user_id: int | str) -> list[str]:
    """Sadece not içeriklerini string listesi olarak döndürür."""
    raw_notes = get_user_notes(user_id)
    return [note['content'] for note in raw_notes]

def add_note(user_id: int | str, content: str) -> None:
    """add_user_note fonksiyonuna yönlendirir."""
    add_user_note(user_id, content)

def delete_note(user_id: int | str, note_number: int) -> bool:
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

def update_note(user_id: int | str, note_index: int, new_content: str) -> bool:
    """
    Liste indeksine (0, 1, 2...) göre not günceller.
    """
    raw_notes = get_user_notes(user_id)
    
    if 0 <= note_index < len(raw_notes):
        note_id = raw_notes[note_index]['id']
        return update_user_note(note_id, new_content)
    return False

# --- HATIRLATICI İŞLEMLERİ ---
def get_all_reminders_db() -> list[dict[str, Any]]:
    if not supabase: return []
    try:
        response = supabase.table("reminders").select("*").execute()
        return response.data
    except Exception as e:
        logger.error(f"Hatırlatıcıları çekme hatası: {e}")
        return []

def add_reminder_db(reminder_data: dict[str, Any]) -> Optional[int]:
    """Hatırlatıcı ekler ve eklenen kaydın ID'sini döner."""
    if not supabase: return None
    try:
        data_to_insert = {
            "user_id": str(reminder_data["user_id"]),
            "chat_id": str(reminder_data["chat_id"]),
            "message": reminder_data["message"],
            "time": reminder_data["time"]
        }
        response = supabase.table("reminders").insert(data_to_insert).execute()
        # Eklenen kaydın ID'sini döndür
        if response.data and len(response.data) > 0:
            return response.data[0].get("id")
        return None
    except Exception as e:
        logger.error(f"Hatırlatıcı ekleme hatası: {e}")
        return None

def remove_reminder_db(reminder_id: int) -> None:
    if not supabase: return
    try:
        supabase.table("reminders").delete().eq("id", reminder_id).execute()
    except Exception as e:
        logger.error(f"Hatırlatıcı silme hatası: {e}")
# --- ADMIN FONKSİYONLARI ---
def get_all_users_count() -> int:
    """Toplam kullanıcı sayısını döner"""
    if not supabase: return 0
    try:
        response = supabase.table("users").select("user_id", count="exact").execute()
        return response.count if response.count else 0
    except Exception as e:
        logger.error(f"Kullanıcı sayısı hatası: {e}")
        return 0

def get_all_notes_count() -> int:
    """Toplam not sayısını döner"""
    if not supabase: return 0
    try:
        response = supabase.table("notes").select("id", count="exact").execute()
        return response.count if response.count else 0
    except Exception as e:
        logger.error(f"Not sayısı hatası: {e}")
        return 0

def get_all_reminders_count() -> int:
    """Toplam hatırlatıcı sayısını döner"""
    if not supabase: return 0
    try:
        response = supabase.table("reminders").select("id", count="exact").execute()
        return response.count if response.count else 0
    except Exception as e:
        logger.error(f"Hatırlatıcı sayısı hatası: {e}")
        return 0

def get_all_user_ids() -> list[int]:
    """Tüm kullanıcı ID'lerini döner (broadcast için)"""
    if not supabase: return []
    try:
        response = supabase.table("users").select("user_id").execute()
        return [int(u['user_id']) for u in response.data] if response.data else []
    except Exception as e:
        logger.error(f"Kullanıcı listesi hatası: {e}")
        return []

def get_recent_users(limit: int = 10) -> list[dict[str, Any]]:
    """Son eklenen kullanıcıları döner"""
    if not supabase: return []
    try:
        response = supabase.table("users").select("*").order("created_at", desc=True).limit(limit).execute()
        return response.data if response.data else []
    except Exception as e:
        logger.error(f"Son kullanıcılar hatası: {e}")
        return []

# --- AKTİVİTE LOGLAMA (YENİ) ---
def log_qr_usage(user_id: int | str, content: str) -> None:
    """QR kod oluşturma işlemini loglar."""
    if not supabase: return
    try:
        data = {"user_id": str(user_id), "content": content}
        supabase.table("qr_logs").insert(data).execute()
    except Exception as e:
        logger.error(f"QR log hatası (User: {user_id}): {e}")

def log_pdf_usage(user_id: int | str, pdf_type: str) -> None:
    """PDF dönüştürme işlemini loglar (text, image, document)."""
    if not supabase: return
    try:
        data = {"user_id": str(user_id), "type": pdf_type}
        supabase.table("pdf_logs").insert(data).execute()
    except Exception as e:
        logger.error(f"PDF log hatası (User: {user_id}): {e}")

def log_xox_game(user_id: int | str, winner: str, difficulty: str) -> None:
    """XOX oyun sonucunu loglar."""
    if not supabase: return
    try:
        data = {"user_id": str(user_id), "winner": winner, "difficulty": difficulty}
        supabase.table("xox_logs").insert(data).execute()
    except Exception as e:
        logger.error(f"XOX log hatası (User: {user_id}): {e}")

def log_tkm_game(user_id: int | str, user_move: str, bot_move: str, result: str) -> None:
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

def log_coinflip(user_id: int | str, result: str) -> None:
    """Yazı Tura sonucunu loglar."""
    if not supabase: return
    try:
        data = {"user_id": str(user_id), "result": result}
        supabase.table("coinflip_logs").insert(data).execute()
    except Exception as e:
        logger.error(f"Coinflip log hatası (User: {user_id}): {e}")

def log_dice_roll(user_id: int | str, result: int) -> None:
    """Zar atma sonucunu loglar."""
    if not supabase: return
    try:
        data = {"user_id": str(user_id), "result": str(result)}
        supabase.table("dice_logs").insert(data).execute()
    except Exception as e:
        logger.error(f"Dice log hatası (User: {user_id}): {e}")


# --- METRO FAVORİLERİ ---
def get_metro_favorites(user_id: int | str) -> list[dict[str, Any]]:
    """Kullanıcının metro favorilerini getirir."""
    if not supabase: return []
    try:
        response = supabase.table("metro_favorites").select("*").eq("user_id", str(user_id)).execute()
        return response.data if response.data else []
    except Exception as e:
        logger.error(f"Metro favorileri getirme hatası (User: {user_id}): {e}")
        return []


def add_metro_favorite(user_id: int | str, line_id: int, line_name: str, 
                       station_id: int, station_name: str, 
                       direction_id: int, direction_name: str) -> bool:
    """Kullanıcının metro favorilerine yeni kayıt ekler."""
    if not supabase: return False
    try:
        # Aynı favori varsa ekleme (duplicate kontrolü)
        existing = supabase.table("metro_favorites").select("id").eq("user_id", str(user_id)).eq("station_id", station_id).eq("direction_id", direction_id).execute()
        if existing.data:
            return False  # Zaten var
        
        data = {
            "user_id": str(user_id),
            "line_id": line_id,
            "line_name": line_name,
            "station_id": station_id,
            "station_name": station_name,
            "direction_id": direction_id,
            "direction_name": direction_name
        }
        supabase.table("metro_favorites").insert(data).execute()
        return True
    except Exception as e:
        logger.error(f"Metro favori ekleme hatası (User: {user_id}): {e}")
        return False


def remove_metro_favorite(favorite_id: int) -> bool:
    """Metro favorisini siler."""
    if not supabase: return False
    try:
        supabase.table("metro_favorites").delete().eq("id", favorite_id).execute()
        return True
    except Exception as e:
        logger.error(f"Metro favori silme hatası (ID: {favorite_id}): {e}")
        return False


# --- AI GÜNLÜK KULLANIM KALİKİLİĞİ ---
def get_ai_daily_usage(user_id: int | str, today_str: str) -> int:
    """Kullanıcının bugünkü AI kullanım sayısını döndürür."""
    if not supabase: return 0
    try:
        response = supabase.table("ai_usage").select("usage_count").eq("user_id", str(user_id)).eq("usage_date", today_str).execute()
        if response.data:
            return response.data[0]["usage_count"]
        return 0
    except Exception as e:
        logger.error(f"AI kullanım getirme hatası (User: {user_id}): {e}")
        return 0


def set_ai_daily_usage(user_id: int | str, today_str: str, count: int) -> None:
    """Kullanıcının bugünkü AI kullanım sayısını ayarlar."""
    if not supabase: return
    try:
        data = {"user_id": str(user_id), "usage_date": today_str, "usage_count": count}
        supabase.table("ai_usage").upsert(data, on_conflict="user_id,usage_date").execute()
    except Exception as e:
        logger.error(f"AI kullanım kaydetme hatası (User: {user_id}): {e}")


def increment_ai_usage(user_id: int | str, today_str: str) -> int:
    """Kullanıcının AI kullanımını 1 artırır ve yeni sayıyı döndürür."""
    if not supabase: return 0
    try:
        current = get_ai_daily_usage(user_id, today_str)
        new_count = current + 1
        set_ai_daily_usage(user_id, today_str, new_count)
        return new_count
    except Exception as e:
        logger.error(f"AI kullanım artırma hatası (User: {user_id}): {e}")
        return 0
