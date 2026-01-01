# Bu dosya, RAM üzerinde tutulan geçici verileri (state) saklar.

# Mevcut durumlar
playing_tkm = set()
notes_in_menu = set()
deleting_notes = set()
waiting_for_qr_data = set()
waiting_for_reminder_input = set()
waiting_for_pdf_conversion_input = set()
waiting_for_weather_city = set()
reminder_menu_active = set()
waiting_for_reminder_delete = set()
waiting_for_new_note_input = set()
user_notes_page_index = {} 

# --- YENİ EKLENEN DURUMLAR ---
editing_notes = set()            # Kullanıcı not düzenleme menüsünde mi?
waiting_for_edit_note_input = {} # Kullanıcı şu an hangi notu düzenliyor? {user_id: note_id}
games_menu_active = set()        # Oyunlar menüsünde mi?
playing_xox = {}                 # XOX durumu (İlerisi için hazırlık)

# --- VIDEO DOWNLOADER DURUMLARI ---
waiting_for_video_link = {}      # Link bekliyor {user_id: {"platform": str, "format": str}}
waiting_for_format_selection = {}  # Format seçimi bekliyor {user_id: platform}

# --- METRO DURUMLARI ---
metro_browsing = set()       # Metro menüsünde geziniyor
metro_selection = {}         # Seçimler {user_id: {"line": id, "line_name": name, "station": id}}

def clear_user_states(user_id):
    """Kullanıcının tüm aktif durumlarını temizler."""
    playing_tkm.discard(user_id)
    notes_in_menu.discard(user_id)
    deleting_notes.discard(user_id)
    waiting_for_qr_data.discard(user_id)
    waiting_for_reminder_input.discard(user_id)
    waiting_for_pdf_conversion_input.discard(user_id)
    waiting_for_weather_city.discard(user_id)
    reminder_menu_active.discard(user_id)
    waiting_for_reminder_delete.discard(user_id)
    waiting_for_new_note_input.discard(user_id)
    user_notes_page_index.pop(user_id, None)
    
    # Yeni durumları da temizle
    editing_notes.discard(user_id)
    waiting_for_edit_note_input.pop(user_id, None)
    games_menu_active.discard(user_id)
    playing_xox.pop(user_id, None)
    
    # Video downloader
    waiting_for_video_link.pop(user_id, None)
    waiting_for_format_selection.pop(user_id, None)
    
    # AI Chat
    ai_chat_active.discard(user_id)
    
    # Metro
    metro_browsing.discard(user_id)
    metro_selection.pop(user_id, None)