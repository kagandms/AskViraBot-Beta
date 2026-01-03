from telegram import ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
# TOOLS_BUTTONS eklendi
from texts import MAIN_BUTTONS, NOTES_BUTTONS, DELETE_NOTES_BUTTONS, INPUT_BACK_BUTTONS, PDF_CONVERTER_BUTTONS, SOCIAL_MEDIA_LINKS, REMINDER_BUTTONS, TEXTS, GAMES_BUTTONS, TOOLS_BUTTONS, CITY_NAMES_TRANSLATED
from config import ADMIN_IDS
from typing import Optional

# --- KLAVYE OLUŞTURUCULAR ---

def get_main_keyboard_markup(lang: str, user_id: Optional[int] = None) -> ReplyKeyboardMarkup:
    # Ana menü klavyesi
    buttons = [row[:] for row in MAIN_BUTTONS.get(lang, MAIN_BUTTONS["en"])]  # Deep copy
    
    # Admin kullanıcıya özel buton ekle
    if user_id and user_id in ADMIN_IDS:
        admin_button = {"tr": "🔒 Yönetim", "en": "🔒 Admin", "ru": "🔒 Управление"}
        buttons.append([admin_button.get(lang, admin_button["en"])])
    
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

def get_games_keyboard_markup(lang: str) -> ReplyKeyboardMarkup:
    # Oyunlar menüsü klavyesi (YENİ EKLENEN)
    buttons = GAMES_BUTTONS.get(lang, GAMES_BUTTONS["en"])
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

def get_notes_keyboard_markup(lang: str) -> ReplyKeyboardMarkup:
    # Notlar menüsü klavyesi
    buttons = NOTES_BUTTONS.get(lang, NOTES_BUTTONS["en"])
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

def get_tools_keyboard_markup(lang: str) -> ReplyKeyboardMarkup:
    # Araçlar menüsü klavyesi
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
    # Hava durumu şehir seçimi için Reply Keyboard
    cities_dict = CITY_NAMES_TRANSLATED.get(lang, CITY_NAMES_TRANSLATED["en"])
    # Dictionary values (şehir isimleri) alınıyor
    city_names = list(cities_dict.values())
    
    # 2'li satırlar halinde düzenle
    keyboard = []
    row = []
    for city in city_names:
        row.append(city)
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
        
    # Geri butonu - tüm dillere uygun
    back_texts = {"tr": "⬅️ Geri", "en": "⬅️ Back", "ru": "⬅️ Назад"}
    back_text = back_texts.get(lang, back_texts["en"])
    keyboard.append([back_text])
    
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def format_remaining_time(remaining_seconds: float, lang: str) -> str:
    days = int(remaining_seconds // (24 * 3600))
    remaining_seconds %= (24 * 3600)
    hours = int(remaining_seconds // 3600)
    remaining_seconds %= 3600
    minutes = int(remaining_seconds // 60)
    seconds = int(remaining_seconds % 60)
    if days > 0: return TEXTS["remaining_time_format"][lang].format(days=days, hours=hours, minutes=minutes, seconds=seconds)
    else: return TEXTS["remaining_time_format_short"][lang].format(hours=hours, minutes=minutes, seconds=seconds)