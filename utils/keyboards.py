
from telegram import ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from texts import MAIN_BUTTONS, NOTES_BUTTONS, DELETE_NOTES_BUTTONS, INPUT_BACK_BUTTONS, PDF_CONVERTER_BUTTONS, SOCIAL_MEDIA_LINKS, REMINDER_BUTTONS, TEXTS, GAMES_BUTTONS, TOOLS_BUTTONS, CITY_NAMES_TRANSLATED
from config import ADMIN_IDS
from typing import Optional

def get_main_keyboard_markup(lang: str, user_id: Optional[int] = None) -> ReplyKeyboardMarkup:
    # Ana menü klavyesi
    buttons = [row[:] for row in MAIN_BUTTONS.get(lang, MAIN_BUTTONS["en"])]  # Deep copy
    
    # Admin kullanıcıya özel buton ekle
    if user_id and user_id in ADMIN_IDS:
        admin_button = {"tr": "🔒 Yönetim", "en": "🔒 Admin", "ru": "🔒 Управление"}
        buttons.append([admin_button.get(lang, admin_button["en"])])
    
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

def get_games_keyboard_markup(lang: str) -> ReplyKeyboardMarkup:
    buttons = GAMES_BUTTONS.get(lang, GAMES_BUTTONS["en"])
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

def get_notes_keyboard_markup(lang: str) -> ReplyKeyboardMarkup:
    buttons = NOTES_BUTTONS.get(lang, NOTES_BUTTONS["en"])
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

def get_tools_keyboard_markup(lang: str) -> ReplyKeyboardMarkup:
    buttons = TOOLS_BUTTONS.get(lang, TOOLS_BUTTONS["en"])
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

def get_delete_notes_keyboard_markup(lang: str) -> ReplyKeyboardMarkup:
    buttons = DELETE_NOTES_BUTTONS.get(lang, DELETE_NOTES_BUTTONS["en"])
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

def get_input_back_keyboard_markup(lang: str) -> ReplyKeyboardMarkup:
    buttons = INPUT_BACK_BUTTONS.get(lang, INPUT_BACK_BUTTONS["en"])
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

def get_pdf_converter_keyboard_markup(lang: str) -> ReplyKeyboardMarkup:
    buttons = PDF_CONVERTER_BUTTONS.get(lang, PDF_CONVERTER_BUTTONS["en"])
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

def get_social_media_keyboard(lang: str) -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(TEXTS["my_website"][lang], url=SOCIAL_MEDIA_LINKS["website"])], 
        [InlineKeyboardButton("📸 Instagram", url=SOCIAL_MEDIA_LINKS["instagram"])],
        [InlineKeyboardButton("✈️ Telegram", url=SOCIAL_MEDIA_LINKS["telegram"])],
        [InlineKeyboardButton("👔 LinkedIn", url=SOCIAL_MEDIA_LINKS["linkedin"])],
        [InlineKeyboardButton(TEXTS["back_button_inline"][lang], callback_data="back_to_main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_reminder_keyboard_markup(lang: str) -> ReplyKeyboardMarkup:
    buttons = REMINDER_BUTTONS.get(lang, REMINDER_BUTTONS["en"])
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

def get_weather_cities_keyboard(lang: str) -> ReplyKeyboardMarkup:
    cities_dict = CITY_NAMES_TRANSLATED.get(lang, CITY_NAMES_TRANSLATED["en"])
    city_names = list(cities_dict.values())
    
    keyboard = []
    row = []
    for city in city_names:
        row.append(city)
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
        
    back_texts = {"tr": "🔙 Araçlar Menüsü", "en": "🔙 Tools Menu", "ru": "🔙 Меню Инструментов"}
    back_text = back_texts.get(lang, back_texts["en"])
    keyboard.append([back_text])
    
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
