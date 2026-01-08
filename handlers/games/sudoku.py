"""
Sudoku Game Handler
Opens a Telegram Web App for playing Sudoku
"""

import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ContextTypes
import database as db
from texts import TEXTS

import logging
logger = logging.getLogger(__name__)


async def sudoku_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Opens Sudoku Web App"""
    user_id = update.effective_user.id
    lang = await db.get_user_lang(user_id)
    
    # Get the web app URL from environment
    base_url = os.getenv("RENDER_EXTERNAL_URL", "").rstrip("/")
    if not base_url:
        # Fallback for local development
        base_url = "http://localhost:8080"
    
    sudoku_url = f"{base_url}/web/sudoku.html"
    
    # Create Web App button with back button
    web_app = WebAppInfo(url=sudoku_url)
    back_texts = {"tr": "🔙 Oyun Odası", "en": "🔙 Game Room", "ru": "🔙 Игровая Комната"}
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(
            text="🧩 Sudoku Oyna" if lang == "tr" else "🧩 Play Sudoku" if lang == "en" else "🧩 Играть в Судоку",
            web_app=web_app
        )],
        [InlineKeyboardButton(
            text=back_texts.get(lang, back_texts["en"]),
            callback_data="back_to_games"
        )]
    ])
    
    prompts = {
        "tr": "🧩 *Sudoku*\n\n9x9'luk klasik Sudoku bulmacası!\n\n🎯 *Zorluk Seviyeleri:*\n• Kolay - Yeni başlayanlar için\n• Orta - Biraz deneyim gerektirir\n• Zor - Uzmanlar için\n\n📝 *İpucu:* Not modunu kullanarak olası sayıları işaretleyebilirsin!",
        "en": "🧩 *Sudoku*\n\nClassic 9x9 Sudoku puzzle!\n\n🎯 *Difficulty Levels:*\n• Easy - For beginners\n• Medium - Requires some experience\n• Hard - For experts\n\n📝 *Tip:* Use note mode to mark possible numbers!",
        "ru": "🧩 *Судоку*\n\nКлассическая головоломка Судоку 9x9!\n\n🎯 *Уровни сложности:*\n• Лёгкий - Для новичков\n• Средний - Требует опыта\n• Сложный - Для экспертов\n\n📝 *Совет:* Используй режим заметок для возможных чисел!"
    }
    
    await update.effective_message.reply_text(
        prompts.get(lang, prompts["en"]),
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    
    logger.info(f"User {user_id} opened Sudoku game")


# --- MODULAR SETUP ---
def setup(app):
    """Register Sudoku handlers"""
    from telegram.ext import CommandHandler
    from core.router import register_button
    
    # Command
    app.add_handler(CommandHandler("sudoku", sudoku_start))
    
    # Button registration
    register_button("sudoku_main", sudoku_start)
    
    logger.info("✅ Sudoku module loaded")
