import asyncio
from telegram import Update
from telegram.ext import ContextTypes
import database as db
import state
from texts import TEXTS
from utils import get_main_keyboard_markup

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    state.clear_user_states(user_id)
    # DB İŞLEMİ: Asenkron
    lang = await asyncio.to_thread(db.get_user_lang, user_id)
    await update.message.reply_text(TEXTS["start"][lang])
    await update.message.reply_text(TEXTS["start"][lang])

async def tools_menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = await asyncio.to_thread(db.get_user_lang, user_id)
    
    from utils import get_tools_keyboard_markup
    await update.message.reply_text(
        TEXTS["tools_menu_prompt"][lang],
        reply_markup=get_tools_keyboard_markup(lang)
    )
async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ana menüyü gösterir. Hem komut hem de callback (geri tuşu) ile çalışır."""
    user_id = update.effective_user.id
    # DB İŞLEMİ: Asenkron
    lang = await asyncio.to_thread(db.get_user_lang, user_id)
    state.clear_user_states(user_id)
    
    # Eğer callback query (buton) üzerinden geldiyse
    if update.callback_query:
        # Menüyü yeni mesaj olarak gönder (eski mesajı düzenlemek bazen karışıklık yaratır)
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=TEXTS["menu_prompt"][lang],
            reply_markup=get_main_keyboard_markup(lang)
        )
    # Normal mesaj (/menu veya metin) üzerinden geldiyse
    else:
        await update.message.reply_text(
            TEXTS["menu_prompt"][lang],
            reply_markup=get_main_keyboard_markup(lang)
        )

async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    text = update.message.text.lower()
    lang_to_set = None
    if "türkçe" in text: lang_to_set = "tr"
    elif "english" in text: lang_to_set = "en"
    elif "русский" in text: lang_to_set = "ru"
    else:
        command_lang = update.message.text[1:].lower()
        if command_lang in ["tr", "en", "ru"]:
            lang_to_set = command_lang

    if lang_to_set:
        # DB İŞLEMİ: Asenkron
        await asyncio.to_thread(db.set_user_lang_db, user_id, lang_to_set)
        await update.message.reply_text(TEXTS["language_set"][lang_to_set])
        await menu_command(update, context)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Tüm komutları ve özellikleri listeler"""
    user_id = update.effective_user.id
    lang = await asyncio.to_thread(db.get_user_lang, user_id)
    
    help_texts = {
        "tr": """📚 *DruzhikBot Yardım*

*📝 Notlar*
• /addnote - Yeni not ekle
• /mynotes - Notlarını görüntüle

*⏰ Hatırlatıcılar*
• /remind - Hatırlatıcı kur
  Örnek: `/remind 14:30 toplantı`

*🎮 Oyunlar*
• /xox - XOX oyna (3 zorluk seviyesi)
• /dice - Zar at
• /coinflip - Yazı tura at
• /tkm - Taş Kağıt Makas

*🛠 Araçlar*
• PDF Çevirici - Metin/dosyayı PDF'e dönüştür
• QR Kod - QR kod oluştur
• Hava Durumu - Şehir hava durumu

*⚙️ Ayarlar*
• /tr /en /ru - Dil değiştir
• /menu - Ana menü

*💡 İpucu:* Menü butonlarını kullanarak tüm özelliklere erişebilirsin!""",

        "en": """📚 *DruzhikBot Help*

*📝 Notes*
• /addnote - Add a new note
• /mynotes - View your notes

*⏰ Reminders*
• /remind - Set a reminder
  Example: `/remind 14:30 meeting`

*🎮 Games*
• /xox - Play XOX (3 difficulty levels)
• /dice - Roll a dice
• /coinflip - Flip a coin
• /tkm - Rock Paper Scissors

*🛠 Tools*
• PDF Converter - Convert text/file to PDF
• QR Code - Generate QR codes
• Weather - City weather info

*⚙️ Settings*
• /tr /en /ru - Change language
• /menu - Main menu

*💡 Tip:* Use menu buttons to access all features!""",

        "ru": """📚 *Помощь DruzhikBot*

*📝 Заметки*
• /addnote - Добавить заметку
• /mynotes - Просмотреть заметки

*⏰ Напоминания*
• /remind - Установить напоминание
  Пример: `/remind 14:30 встреча`

*🎮 Игры*
• /xox - Играть в XOX (3 уровня сложности)
• /dice - Бросить кубик
• /coinflip - Подбросить монету
• /tkm - Камень Ножницы Бумага

*🛠 Инструменты*
• PDF Конвертер - Конвертировать в PDF
• QR Код - Создать QR код
• Погода - Погода в городе

*⚙️ Настройки*
• /tr /en /ru - Сменить язык
• /menu - Главное меню

*💡 Совет:* Используйте кнопки меню для доступа ко всем функциям!"""
    }
    
    await update.message.reply_text(
        help_texts.get(lang, help_texts["en"]),
        parse_mode="Markdown"
    )