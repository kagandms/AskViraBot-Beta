"""
XOX (Tic-Tac-Toe) Web Game Handler
Opens a Telegram Web App for playing XOX
"""

import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ContextTypes
import database as db

import logging
logger = logging.getLogger(__name__)


async def xox_web_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Opens XOX Web App"""
    user_id = update.effective_user.id
    lang = await db.get_user_lang(user_id)
    
    # Get the web app URL from environment
    base_url = os.getenv("RENDER_EXTERNAL_URL", "").rstrip("/")
    if not base_url:
        base_url = "http://localhost:8080"
    
    xox_url = f"{base_url}/web/xox.html"
    
    # Create Web App button with back button
    web_app = WebAppInfo(url=xox_url)
    play_texts = {"tr": "❌⭕ XOX Oyna", "en": "❌⭕ Play XOX", "ru": "❌⭕ Играть в XOX"}
    back_texts = {"tr": "🔙 Oyun Odası", "en": "🔙 Game Room", "ru": "🔙 Игровая Комната"}
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(
            text=play_texts.get(lang, play_texts["en"]),
            web_app=web_app
        )],
        [InlineKeyboardButton(
            text=back_texts.get(lang, back_texts["en"]),
            callback_data="back_to_games"
        )]
    ])
    
    prompts = {
        "tr": "❌⭕ *XOX (Tic-Tac-Toe)*\n\nKlasik XOX oyunu!\n\n🎯 *Zorluk Seviyeleri:*\n• 🟢 Kolay - Rahat kazanabilirsin\n• 🟡 Orta - Dikkatli ol\n• 🔴 Zor - Yenilmez bot!\n\n📊 Skor takibi ve harika animasyonlar!",
        "en": "❌⭕ *XOX (Tic-Tac-Toe)*\n\nClassic XOX game!\n\n🎯 *Difficulty Levels:*\n• 🟢 Easy - You can win easily\n• 🟡 Medium - Be careful\n• 🔴 Hard - Unbeatable bot!\n\n📊 Score tracking and awesome animations!",
        "ru": "❌⭕ *XOX (Крестики-нолики)*\n\nКлассическая игра XOX!\n\n🎯 *Уровни сложности:*\n• 🟢 Лёгкий - Легко победить\n• 🟡 Средний - Будь осторожен\n• 🔴 Сложный - Непобедимый бот!\n\n📊 Счёт и красивые анимации!"
    }
    
    await update.effective_message.reply_text(
        prompts.get(lang, prompts["en"]),
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    
    logger.info(f"User {user_id} opened XOX web game")
