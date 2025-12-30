# Bu dosya, RAM üzerinde tutulan geçici verileri (state) saklar.

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
user_notes_page_index = {} # Sayfalama için

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