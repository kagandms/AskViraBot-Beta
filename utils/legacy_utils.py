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
        
    # Geri butonu - Araçlar menüsüne döner
    back_texts = {"tr": "🔙 Araçlar Menüsü", "en": "🔙 Tools Menu", "ru": "🔙 Меню Инструментов"}
    back_text = back_texts.get(lang, back_texts["en"])
    keyboard.append([back_text])
    
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def is_back_button(text: str) -> bool:
    """
    Checks if the given text corresponds to a 'Back' or 'Main Menu' button 
    in any supported language or context.
    """
    if not text:
        return False
        
    from texts import turkish_lower, BUTTON_MAPPINGS
    text_lower = turkish_lower(text)
    
    # Generic back keywords
    generic_back = {"geri", "back", "назад", "iptal", "cancel", "отмена"}
    
    # Check against mapped back buttons from texts.py
    mapped_back = BUTTON_MAPPINGS.get("back_to_main_menu", set()) | \
                  BUTTON_MAPPINGS.get("back_to_tools", set()) | \
                  BUTTON_MAPPINGS.get("back_to_games", set())
                  
    # Specific menu back buttons commonly used
    specific_back = {
        "🔙 ana menü", "🔙 main menu", "🔙 главное меню",
        "🔙 araçlar menüsü", "🔙 tools menu", "🔙 меню инструментов",
        "🔙 oyun odası", "🔙 game room", "🔙 игровая комната",
        "🔙 hat listesi", "🔙 line list", "🔙 список линий",
        "🔙 istasyon listesi", "🔙 station list", "🔙 список станций",
        "🔙 favoriler menüsü", "🔙 favorites menu", "🔙 меню избранного",
        "◀️ geri", "◀️ back", "◀️ назад"
    }

    return (text_lower in generic_back) or \
           (text_lower in mapped_back) or \
           (text_lower in specific_back) or \
           any(k in text_lower for k in ["🔙", "◀️"])

def format_remaining_time(remaining_seconds: float, lang: str) -> str:
    days = int(remaining_seconds // (24 * 3600))
    remaining_seconds %= (24 * 3600)
    hours = int(remaining_seconds // 3600)
    remaining_seconds %= 3600
    minutes = int(remaining_seconds // 60)
    seconds = int(remaining_seconds % 60)
    if days > 0: return TEXTS["remaining_time_format"][lang].format(days=days, hours=hours, minutes=minutes, seconds=seconds)
    else: return TEXTS["remaining_time_format_short"][lang].format(hours=hours, minutes=minutes, seconds=seconds)

async def cleanup_context(context, user_id):
    """
    Cleans up messages from previous context if stored in state data.
    """
    try:
        import state 
        import logging
        data = await state.get_data(user_id)
        
        # Tekil message_id temizliği (eski sistem)
        if "message_id" in data:
            try:
                await context.bot.delete_message(chat_id=user_id, message_id=data["message_id"])
            except Exception: pass
            
        # Çoklu message_ids temizliği (yeni sistem)
        if "message_ids" in data and isinstance(data["message_ids"], list):
            for mid in data["message_ids"]:
                try:
                    await context.bot.delete_message(chat_id=user_id, message_id=mid)
                except Exception: pass
    except Exception as e:
        # logging.error(f"Cleanup error: {e}")
        pass

async def send_temp_message(update_or_bot, chat_id: int, text: str, delay: float = 5.0):
    """
    Gönderilen mesajı belirli bir süre sonra otomatik siler.
    Hata mesajları ve kısa bilgilendirmeler için idealdir.
    """
    import asyncio
    try:
        # update nesnesi mi yoksa bot nesnesi mi geldi kontrol et
        if hasattr(update_or_bot, "message"):
            msg = await update_or_bot.message.reply_text(text)
        else:
            msg = await update_or_bot.send_message(chat_id=chat_id, text=text)
            
        await asyncio.sleep(delay)
        try:
            await msg.delete()
        except: pass
    except: pass

async def delete_user_message(update):
    """Kullanıcının gönderdiği mesajı siler (Eğer yetki varsa)"""
    try:
        if update.message:
            await update.message.delete()
    except: pass