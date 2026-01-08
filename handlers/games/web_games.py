"""
Web Games Handler
Opens Telegram Web Apps for various games: Snake, 2048, Flappy Bird, Runner
"""

import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ContextTypes
import database as db

import logging
logger = logging.getLogger(__name__)


def get_web_url(game_name: str, lang: str = "tr") -> str:
    """Generate Web App URL with language parameter"""
    base_url = os.getenv("RENDER_EXTERNAL_URL", "").rstrip("/")
    if not base_url:
        base_url = "http://localhost:8080"
    return f"{base_url}/web/{game_name}.html?lang={lang}"


async def snake_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Opens Snake Web App"""
    user_id = update.effective_user.id
    lang = await db.get_user_lang(user_id)
    
    web_app = WebAppInfo(url=get_web_url("snake", lang))
    play_texts = {"tr": "🐍 Snake Oyna", "en": "🐍 Play Snake", "ru": "🐍 Играть в Snake"}
    back_texts = {"tr": "🔙 Oyun Odası", "en": "🔙 Game Room", "ru": "🔙 Игровая Комната"}
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(text=play_texts.get(lang, play_texts["en"]), web_app=web_app)],
        [InlineKeyboardButton(text=back_texts.get(lang, back_texts["en"]), callback_data="back_to_games")]
    ])
    
    prompts = {
        "tr": "🐍 *Snake*\n\nKlasik yılan oyunu!\n\n🎮 Yemi ye ve büyü\n⚠️ Duvarlara ve kendine çarpma\n🏆 En yüksek skoru kır!",
        "en": "🐍 *Snake*\n\nClassic snake game!\n\n🎮 Eat food and grow\n⚠️ Don't hit walls or yourself\n🏆 Beat the high score!",
        "ru": "🐍 *Snake*\n\nКлассическая игра Змейка!\n\n🎮 Ешь еду и расти\n⚠️ Не врезайся в стены\n🏆 Побей рекорд!"
    }
    
    await update.effective_message.reply_text(
        prompts.get(lang, prompts["en"]),
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    logger.info(f"User {user_id} opened Snake game")


async def game_2048_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Opens 2048 Web App"""
    user_id = update.effective_user.id
    lang = await db.get_user_lang(user_id)
    
    web_app = WebAppInfo(url=get_web_url("2048", lang))
    play_texts = {"tr": "🔢 2048 Oyna", "en": "🔢 Play 2048", "ru": "🔢 Играть в 2048"}
    back_texts = {"tr": "🔙 Oyun Odası", "en": "🔙 Game Room", "ru": "🔙 Игровая Комната"}
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(text=play_texts.get(lang, play_texts["en"]), web_app=web_app)],
        [InlineKeyboardButton(text=back_texts.get(lang, back_texts["en"]), callback_data="back_to_games")]
    ])
    
    prompts = {
        "tr": "🔢 *2048*\n\nBağımlılık yapan puzzle oyunu!\n\n⬆️⬇️⬅️➡️ Kaydır ve birleştir\n🎯 2048'e ulaş\n🧠 Strateji gerektirir!",
        "en": "🔢 *2048*\n\nAddictive puzzle game!\n\n⬆️⬇️⬅️➡️ Swipe and merge\n🎯 Reach 2048\n🧠 Requires strategy!",
        "ru": "🔢 *2048*\n\nЗатягивающая головоломка!\n\n⬆️⬇️⬅️➡️ Свайп и объединяй\n🎯 Достигни 2048\n🧠 Нужна стратегия!"
    }
    
    await update.effective_message.reply_text(
        prompts.get(lang, prompts["en"]),
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    logger.info(f"User {user_id} opened 2048 game")


async def flappy_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Opens Flappy Bird Web App"""
    user_id = update.effective_user.id
    lang = await db.get_user_lang(user_id)
    
    web_app = WebAppInfo(url=get_web_url("flappy", lang))
    play_texts = {"tr": "🐦 Flappy Bird Oyna", "en": "🐦 Play Flappy Bird", "ru": "🐦 Играть в Flappy Bird"}
    back_texts = {"tr": "🔙 Oyun Odası", "en": "🔙 Game Room", "ru": "🔙 Игровая Комната"}
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(text=play_texts.get(lang, play_texts["en"]), web_app=web_app)],
        [InlineKeyboardButton(text=back_texts.get(lang, back_texts["en"]), callback_data="back_to_games")]
    ])
    
    prompts = {
        "tr": "🐦 *Flappy Bird*\n\nEfsanevi zor oyun!\n\n👆 Ekrana dokun = Zıpla\n🚧 Borulara çarpma\n😤 Sinirlerine hakim ol!",
        "en": "🐦 *Flappy Bird*\n\nLegendary hard game!\n\n👆 Tap screen = Jump\n🚧 Avoid pipes\n😤 Keep calm!",
        "ru": "🐦 *Flappy Bird*\n\nЛегендарная сложная игра!\n\n👆 Тап = Прыжок\n🚧 Избегай труб\n😤 Сохраняй спокойствие!"
    }
    
    await update.effective_message.reply_text(
        prompts.get(lang, prompts["en"]),
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    logger.info(f"User {user_id} opened Flappy Bird game")


async def runner_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Opens Endless Runner Web App"""
    user_id = update.effective_user.id
    lang = await db.get_user_lang(user_id)
    
    web_app = WebAppInfo(url=get_web_url("runner", lang))
    play_texts = {"tr": "🏃 Runner Oyna", "en": "🏃 Play Runner", "ru": "🏃 Играть в Runner"}
    back_texts = {"tr": "🔙 Oyun Odası", "en": "🔙 Game Room", "ru": "🔙 Игровая Комната"}
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(text=play_texts.get(lang, play_texts["en"]), web_app=web_app)],
        [InlineKeyboardButton(text=back_texts.get(lang, back_texts["en"]), callback_data="back_to_games")]
    ])
    
    prompts = {
        "tr": "🏃 *Endless Runner*\n\nSonsuz koşu macerası!\n\n👆 Dokun = Zıpla\n✌️ Çift zıplama var!\n🏆 Ne kadar uzağa gidebilirsin?",
        "en": "🏃 *Endless Runner*\n\nEndless running adventure!\n\n👆 Tap = Jump\n✌️ Double jump available!\n🏆 How far can you go?",
        "ru": "🏃 *Endless Runner*\n\nБесконечный бег!\n\n👆 Тап = Прыжок\n✌️ Двойной прыжок!\n🏆 Как далеко убежишь?"
    }
    
    await update.effective_message.reply_text(
        prompts.get(lang, prompts["en"]),
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    logger.info(f"User {user_id} opened Runner game")
