import asyncio
from telegram import Update
from telegram.ext import ContextTypes
import database as db
import state
from texts import TEXTS
from utils import get_main_keyboard_markup


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Bot başlatma komutu."""
    user_id = update.effective_user.id
    await state.clear_user_states(user_id)
    # DB İŞLEMİ: Asenkron
    lang = await asyncio.to_thread(db.get_user_lang, user_id)
    await update.message.reply_text(TEXTS["start"][lang])


async def tools_menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Araçlar menüsünü gösterir."""
    user_id = update.effective_user.id
    lang = await asyncio.to_thread(db.get_user_lang, user_id)
    
    from utils import get_tools_keyboard_markup
    await update.message.reply_text(
        TEXTS["tools_menu_prompt"][lang],
        reply_markup=get_tools_keyboard_markup(lang)
    )


async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Ana menüyü gösterir. Hem komut hem de callback (geri tuşu) ile çalışır."""
    user_id = update.effective_user.id
    # DB İŞLEMİ: Asenkron
    lang = await asyncio.to_thread(db.get_user_lang, user_id)
    await state.clear_user_states(user_id)
    
    # Eğer callback query (buton) üzerinden geldiyse
    if update.callback_query:
        # Menüyü yeni mesaj olarak gönder (eski mesajı düzenlemek bazen karışıklık yaratır)
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=TEXTS["menu_prompt"][lang],
            reply_markup=get_main_keyboard_markup(lang, user_id)
        )
    # Normal mesaj (/menu veya metin) üzerinden geldiyse
    else:
        await update.message.reply_text(
            TEXTS["menu_prompt"][lang],
            reply_markup=get_main_keyboard_markup(lang, user_id)
        )


async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Kullanıcı dilini ayarlar."""
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


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Tüm komutları ve özellikleri listeler"""
    user_id = update.effective_user.id
    lang = await asyncio.to_thread(db.get_user_lang, user_id)
    
    help_texts = {
        "tr": """📚 *DruzhikBot Nasıl Kullanılır?*

🏠 *Ana Menü*
Tüm özelliklere menü butonlarından kolayca ulaşabilirsin!

━━━━━━━━━━━━━━━━━━━━

📝 *Notlar*
• ➕ Not Ekle – Yeni not kaydet
• 📋 Notları Göster – Tüm notlarını listele
• ✏️ Not Düzenle – Mevcut notu güncelle
• 🗑️ Not Sil – İstemediğin notu kaldır

━━━━━━━━━━━━━━━━━━━━

⏰ *Hatırlatıcılar*
• Belirli saat ve tarihte hatırlatma kur
• Örnek: `14:30 toplantı` veya `10:00 2025-12-31 yılbaşı`

━━━━━━━━━━━━━━━━━━━━

🎮 *Oyun Odası*
• ❌⭕ XOX – 3 zorluk seviyesi
• 🎲 Zar – Rastgele zar at
• 🪙 Yazı Tura – Şansını dene
• 🪨📄✂️ Taş-Kağıt-Makas – Bota karşı oyna

━━━━━━━━━━━━━━━━━━━━

🛠 *Araçlar*
• 📷 QR Kod – Metin/link'ten QR oluştur
• 📄 PDF Dönüştürücü – Metin, resim veya belgeyi PDF yap
• ☀️ Hava Durumu – 9 şehir + *5 günlük tahmin*
• 📥 Video İndir – TikTok, Twitter/X, Instagram
• 🚇 Canlı Metro İstanbul – Gerçek zamanlı sefer saatleri

━━━━━━━━━━━━━━━━━━━━

🤖 *AI Asistan (Beta)*
• Yapay zeka destekli sohbet
• Günlük 30 mesaj hakkı
• Her türlü soruyu sorabilirsin!

━━━━━━━━━━━━━━━━━━━━

⚙️ *Ayarlar*
• 🌐 Dil Değiştir – TR / EN / RU

💡 *İpucu:* Menü butonlarını kullanarak daha hızlı gezinebilirsin!""",

        "en": """📚 *DruzhikBot – How to Use?*

🏠 *Main Menu*
Access all features easily through the menu buttons!

━━━━━━━━━━━━━━━━━━━━

📝 *Notes*
• ➕ Add Note – Save a new note
• 📋 Show Notes – List all your notes
• ✏️ Edit Note – Update an existing note
• 🗑️ Delete Note – Remove unwanted notes

━━━━━━━━━━━━━━━━━━━━

⏰ *Reminders*
• Set reminders for specific time and date
• Example: `14:30 meeting` or `10:00 2025-12-31 new year`

━━━━━━━━━━━━━━━━━━━━

🎮 *Game Room*
• ❌⭕ XOX – 3 difficulty levels
• 🎲 Dice – Roll a random dice
• 🪙 Coinflip – Test your luck
• 🪨📄✂️ Rock-Paper-Scissors – Play against the bot

━━━━━━━━━━━━━━━━━━━━

🛠 *Tools*
• 📷 QR Code – Generate QR from text/link
• 📄 PDF Converter – Convert text, image or document to PDF
• ☀️ Weather – 9 cities + *5-day forecast*
• 📥 Video Download – TikTok, Twitter/X, Instagram
• 🚇 Live Metro Istanbul – Real-time departure schedules

━━━━━━━━━━━━━━━━━━━━

🤖 *AI Assistant (Beta)*
• AI-powered chat assistant
• 30 messages per day
• Ask anything you want!

━━━━━━━━━━━━━━━━━━━━

⚙️ *Settings*
• 🌐 Change Language – TR / EN / RU

💡 *Tip:* Use menu buttons for faster navigation!""",

        "ru": """📚 *DruzhikBot – Как использовать?*

🏠 *Главное меню*
Все функции доступны через кнопки меню!

━━━━━━━━━━━━━━━━━━━━

📝 *Заметки*
• ➕ Добавить – Сохранить новую заметку
• 📋 Показать – Список всех заметок
• ✏️ Изменить – Обновить заметку
• 🗑️ Удалить – Удалить ненужные заметки

━━━━━━━━━━━━━━━━━━━━

⏰ *Напоминания*
• Установите напоминание на конкретное время
• Пример: `14:30 встреча` или `10:00 2025-12-31 новый год`

━━━━━━━━━━━━━━━━━━━━

🎮 *Игровая комната*
• ❌⭕ XOX – 3 уровня сложности
• 🎲 Кубик – Бросить случайный кубик
• 🪙 Монета – Испытай удачу
• 🪨📄✂️ Камень-Ножницы-Бумага – Играй против бота

━━━━━━━━━━━━━━━━━━━━

🛠 *Инструменты*
• 📷 QR-код – Создать QR из текста/ссылки
• 📄 PDF Конвертер – Конвертировать в PDF
• ☀️ Погода – 9 городов + *5-дневный прогноз*
• 📥 Скачать видео – TikTok, Twitter/X, Instagram
• 🚇 Метро Стамбул – Расписание в реальном времени

━━━━━━━━━━━━━━━━━━━━

🤖 *AI Ассистент (Бета)*
• Чат с искусственным интеллектом
• 30 сообщений в день
• Спрашивай что угодно!

━━━━━━━━━━━━━━━━━━━━

⚙️ *Настройки*
• 🌐 Сменить язык – TR / EN / RU

💡 *Совет:* Используйте кнопки меню для быстрой навигации!"""
    }
    
    from utils import get_main_keyboard_markup
    await update.message.reply_text(
        help_texts.get(lang, help_texts["en"]),
        parse_mode="Markdown",
        reply_markup=get_main_keyboard_markup(lang, user_id)
    )