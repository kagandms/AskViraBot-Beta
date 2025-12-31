from telegram import ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
# TOOLS_BUTTONS eklendi
from texts import MAIN_BUTTONS, NOTES_BUTTONS, DELETE_NOTES_BUTTONS, INPUT_BACK_BUTTONS, PDF_CONVERTER_BUTTONS, SOCIAL_MEDIA_LINKS, REMINDER_BUTTONS, TEXTS, GAMES_BUTTONS, TOOLS_BUTTONS

# --- KLAVYE OLUŞTURUCULAR ---

def get_main_keyboard_markup(lang):
    # Ana menü klavyesi
    buttons = MAIN_BUTTONS.get(lang, MAIN_BUTTONS["en"])
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

def get_games_keyboard_markup(lang):
    # Oyunlar menüsü klavyesi (YENİ EKLENEN)
    buttons = GAMES_BUTTONS.get(lang, GAMES_BUTTONS["en"])
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

def get_notes_keyboard_markup(lang):
    # Notlar menüsü klavyesi
    buttons = NOTES_BUTTONS.get(lang, NOTES_BUTTONS["en"])
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

def get_tools_keyboard_markup(lang):
    # Araçlar menüsü klavyesi
    buttons = TOOLS_BUTTONS.get(lang, TOOLS_BUTTONS["en"])
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

def get_delete_notes_keyboard_markup(lang):
    buttons = DELETE_NOTES_BUTTONS.get(lang, DELETE_NOTES_BUTTONS["en"])
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

def get_input_back_keyboard_markup(lang):
    buttons = INPUT_BACK_BUTTONS.get(lang, INPUT_BACK_BUTTONS["en"])
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

def get_pdf_converter_keyboard_markup(lang):
    buttons = PDF_CONVERTER_BUTTONS.get(lang, PDF_CONVERTER_BUTTONS["en"])
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

def get_social_media_keyboard(lang):
    keyboard = [
        [InlineKeyboardButton(TEXTS["my_website"][lang], url=SOCIAL_MEDIA_LINKS["website"])], 
        [InlineKeyboardButton("📸 Instagram", url=SOCIAL_MEDIA_LINKS["instagram"])],
        [InlineKeyboardButton("✈️ Telegram", url=SOCIAL_MEDIA_LINKS["telegram"])],
        [InlineKeyboardButton("👔 LinkedIn", url=SOCIAL_MEDIA_LINKS["linkedin"])],
        [InlineKeyboardButton(TEXTS["back_button_inline"][lang], callback_data="back_to_main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_reminder_keyboard_markup(lang):
    buttons = REMINDER_BUTTONS.get(lang, REMINDER_BUTTONS["en"])
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

def format_remaining_time(remaining_seconds: float, lang: str) -> str:
    days = int(remaining_seconds // (24 * 3600))
    remaining_seconds %= (24 * 3600)
    hours = int(remaining_seconds // 3600)
    remaining_seconds %= 3600
    minutes = int(remaining_seconds // 60)
    seconds = int(remaining_seconds % 60)
    if days > 0: return TEXTS["remaining_time_format"][lang].format(days=days, hours=hours, minutes=minutes, seconds=seconds)
    else: return TEXTS["remaining_time_format_short"][lang].format(hours=hours, minutes=minutes, seconds=seconds)