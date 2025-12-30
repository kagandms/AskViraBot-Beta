from config import supabase

# --- KULLANICI İŞLEMLERİ ---
def get_user_lang(user_id):
    if not supabase: return "en"
    try:
        response = supabase.table("users").select("language").eq("user_id", str(user_id)).execute()
        if response.data:
            return response.data[0]["language"]
        return "en"
    except Exception as e:
        print(f"Dil getirme hatası: {e}")
        return "en"

def set_user_lang_db(user_id, lang):
    if not supabase: return
    try:
        data = {"user_id": str(user_id), "language": lang}
        supabase.table("users").upsert(data).execute()
    except Exception as e:
        print(f"Dil kaydetme hatası: {e}")

# --- NOT İŞLEMLERİ ---
def get_user_notes(user_id):
    if not supabase: return []
    try:
        response = supabase.table("notes").select("id, content").eq("user_id", str(user_id)).order("id").execute()
        return [note for note in response.data] 
    except Exception as e:
        print(f"Notları getirme hatası: {e}")
        return []

def add_user_note(user_id, note_content):
    if not supabase: return
    try:
        data = {"user_id": str(user_id), "content": note_content}
        supabase.table("notes").insert(data).execute()
    except Exception as e:
        print(f"Not ekleme hatası: {e}")

def delete_user_note_by_id(note_id):
    if not supabase: return False
    try:
        supabase.table("notes").delete().eq("id", note_id).execute()
        return True
    except Exception as e:
        print(f"Not silme hatası: {e}")
        return False

# --- HATIRLATICI İŞLEMLERİ ---
def get_all_reminders_db():
    if not supabase: return []
    try:
        response = supabase.table("reminders").select("*").execute()
        return response.data
    except Exception as e:
        print(f"Hatırlatıcıları çekme hatası: {e}")
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
        print(f"Hatırlatıcı ekleme hatası: {e}")

def remove_reminder_db(reminder_id):
    if not supabase: return
    try:
        supabase.table("reminders").delete().eq("id", reminder_id).execute()
    except Exception as e:
        print(f"Hatırlatıcı silme hatası: {e}")