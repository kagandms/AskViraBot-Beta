
from .common import (
    SOCIAL_MEDIA_LINKS, 
    CITY_NAMES_TRANSLATED, 
    turkish_lower, 
    generate_mappings_from_buttons
)
from .localization import i18n
import os

# Load locales using absolute path based on file location
_current_dir = os.path.dirname(os.path.abspath(__file__))
_locales_dir = os.path.join(os.path.dirname(_current_dir), "locales")

if os.path.exists(_locales_dir):
    i18n.load_locales(_locales_dir)
else:
    print(f"⚠️ Locales directory not found: {_locales_dir}")

# --- TEXTS ---
# Reconstructed from JSON
TEXTS = i18n.get_all_texts()

# --- BUTTONS ---
# Reconstructed from JSON
ALL_BUTTONS = i18n.get_all_buttons()

MAIN_BUTTONS = ALL_BUTTONS.get("MAIN_BUTTONS", {})
TOOLS_BUTTONS = ALL_BUTTONS.get("TOOLS_BUTTONS", {})
VIDEO_DOWNLOADER_BUTTONS = ALL_BUTTONS.get("VIDEO_DOWNLOADER_BUTTONS", {})
GAMES_BUTTONS = ALL_BUTTONS.get("GAMES_BUTTONS", {})
FORMAT_SELECTION_BUTTONS = ALL_BUTTONS.get("FORMAT_SELECTION_BUTTONS", {})
TKM_BUTTONS = ALL_BUTTONS.get("TKM_BUTTONS", {})
NOTES_BUTTONS = ALL_BUTTONS.get("NOTES_BUTTONS", {})
DELETE_NOTES_BUTTONS = ALL_BUTTONS.get("DELETE_NOTES_BUTTONS", {})
PDF_CONVERTER_BUTTONS = ALL_BUTTONS.get("PDF_CONVERTER_BUTTONS", {})
REMINDER_BUTTONS = ALL_BUTTONS.get("REMINDER_BUTTONS", {})
INPUT_BACK_BUTTONS = ALL_BUTTONS.get("INPUT_BACK_BUTTONS", {})
GAME_MODE_BUTTONS = ALL_BUTTONS.get("GAME_MODE_BUTTONS", {})
BET_BUTTONS = ALL_BUTTONS.get("BET_BUTTONS", {})


# --- MANUEL MAPPINGS (Özel durumlar için) ---
# Bazı butonlar birden fazla varyant gerektirdiği için manuel tutulur
MANUAL_MAPPINGS = {
    "menu": {"🏠 menüye dön", "🏠 back to menu", "🏠 назад в меню", "🔙 geri", "🔙 back", "🔙 назад", "🔙 ana menü", "🔙 main menu", "🔙 главное меню"},
    "back_to_tools": {"🔙 araçlar menüsü", "🔙 tools menu", "🔙 меню инструментов"},
    "back_to_tools": {"🔙 araçlar menüsü", "🔙 tools menu", "🔙 меню инструментов"},
    "back_to_notes": {"🔙 notlar menüsü", "🔙 notes menu", "🔙 меню заметок"},
    "admin_panel_button": {"🔒 yönetim", "🔒 admin", "🔒 управление"},
    "metro_main_button": {"🚇 canlı metro istanbul", "🚇 canlı metro i̇stanbul", "🚇 live metro istanbul", "🚇 metro istanbul", "metro", "canlı metro", "🚇 метро стамбул"},
}


# RE-IMPLEMENTING AUTO_MAPPINGS MORE ROBUSTLY
# Since we have the full dicts, we can pick specific items.
def extract_button_set(button_dict, row_idx, col_idx):
    """Extracts a specific button's translations from a button dictionary."""
    subset = {}
    for lang, rows in button_dict.items():
        if row_idx < len(rows) and col_idx < len(rows[row_idx]):
            subset[lang] = [[rows[row_idx][col_idx]]]
    return generate_mappings_from_buttons(subset)


AUTO_MAPPINGS = {
    # Ana menü
    "tools_main_button": extract_button_set(MAIN_BUTTONS, 0, 0),     # Row 0, Col 0: Tools
    "tools_main_button": extract_button_set(MAIN_BUTTONS, 0, 0),     # Row 0, Col 0: Tools
    
    "language": extract_button_set(MAIN_BUTTONS, 1, 0),              # Row 1, Col 0: Language
    "developer_main_button": extract_button_set(MAIN_BUTTONS, 1, 1), # Row 1, Col 1: Developer
    
    "ai_main_button": extract_button_set(MAIN_BUTTONS, 2, 0),        # Row 2, Col 0: AI
    "help_button": extract_button_set(MAIN_BUTTONS, 2, 1),           # Row 2, Col 1: Help
    
    # Tools
    "notes_main_button": extract_button_set(TOOLS_BUTTONS, 0, 0),
    "reminder": extract_button_set(TOOLS_BUTTONS, 0, 1),
    "qrcode_button": extract_button_set(TOOLS_BUTTONS, 1, 0),
    "pdf_converter_main_button": extract_button_set(TOOLS_BUTTONS, 1, 1),
    "weather_main_button": extract_button_set(TOOLS_BUTTONS, 2, 0),
    # metro_main_button is in MANUAL_MAPPINGS with all variants
    "video_downloader_main_button": extract_button_set(TOOLS_BUTTONS, 3, 0),
    "shazam_main_button": extract_button_set(TOOLS_BUTTONS, 3, 1),

    # Games (Restored - No Gambling)
    "xox_game": extract_button_set(GAMES_BUTTONS, 0, 0),
    "dice": extract_button_set(GAMES_BUTTONS, 0, 1),
    "coinflip": extract_button_set(GAMES_BUTTONS, 1, 0),
    "tkm_main": extract_button_set(GAMES_BUTTONS, 1, 1),
    "player_stats": extract_button_set(GAMES_BUTTONS, 2, 0),



    # Notes
    "add_note_button": extract_button_set(NOTES_BUTTONS, 0, 0),
    "edit_note_button": extract_button_set(NOTES_BUTTONS, 0, 1),
    "show_all_notes_button": extract_button_set(NOTES_BUTTONS, 1, 0),
    "delete_note_button": extract_button_set(NOTES_BUTTONS, 1, 1),
    
    "select_delete_note_button": extract_button_set(DELETE_NOTES_BUTTONS, 0, 0),
    
    # TKM
    "tkm_rock": extract_button_set(TKM_BUTTONS, 0, 0),
    "tkm_paper": extract_button_set(TKM_BUTTONS, 1, 0),
    "tkm_scissors": extract_button_set(TKM_BUTTONS, 2, 0),
    

    
    # PDF
    "text_to_pdf_button": extract_button_set(PDF_CONVERTER_BUTTONS, 0, 0),
    "image_to_pdf_button": extract_button_set(PDF_CONVERTER_BUTTONS, 1, 0),
    "document_to_pdf_button": extract_button_set(PDF_CONVERTER_BUTTONS, 2, 0),
    
    # Reminder
    "add_reminder_button": extract_button_set(REMINDER_BUTTONS, 0, 0),
    "show_reminders_button": extract_button_set(REMINDER_BUTTONS, 1, 0),
    "delete_reminder_button": extract_button_set(REMINDER_BUTTONS, 2, 0),
    
    # Video
    "video_platform_tiktok": extract_button_set(VIDEO_DOWNLOADER_BUTTONS, 0, 0),
    "video_platform_twitter": extract_button_set(VIDEO_DOWNLOADER_BUTTONS, 0, 1),
    "video_platform_instagram": extract_button_set(VIDEO_DOWNLOADER_BUTTONS, 1, 0),
    
    "format_video": extract_button_set(FORMAT_SELECTION_BUTTONS, 0, 0),
    "format_audio": extract_button_set(FORMAT_SELECTION_BUTTONS, 0, 1),
    "back_to_platform": extract_button_set(FORMAT_SELECTION_BUTTONS, 1, 0),
    
    # AI (Manual extraction cause it's not in a neat grid sometimes or depends on structure)
    # Re-checking indices...
    # AI is Row 2 from Main Menu.
    "ai_start_chat": generate_mappings_from_buttons({"tr": [["🧠 Sohbete Başla"]], "en": [["🧠 Start Chat"]], "ru": [["🧠 Начать Чат"]]}), 
    "ai_end_chat": generate_mappings_from_buttons({"tr": [["🔚 Sohbeti Bitir"]], "en": [["🔚 End Chat"]], "ru": [["🔚 Завершить Чат"]]}),
    "ai_back_to_menu": generate_mappings_from_buttons({"tr": [["🔙 Ana Menü"]], "en": [["🔙 Main Menu"]], "ru": [["🔙 Главное Меню"]]}),
}

# --- BİRLEŞTİRİLMİŞ BUTTON_MAPPINGS ---
BUTTON_MAPPINGS = {**AUTO_MAPPINGS, **MANUAL_MAPPINGS}