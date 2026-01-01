"""
AI Chat Handler for DruzhikBot
OpenRouter API Integration with DeepSeek Model
"""

import asyncio
from datetime import date
import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from openai import OpenAI

import database as db
import state
from config import OPENROUTER_API_KEY, AI_DAILY_LIMIT, ADMIN_IDS
from texts import TEXTS, BUTTON_MAPPINGS
from utils import get_main_keyboard_markup
from rate_limiter import rate_limit

logger = logging.getLogger(__name__)

# --- OPENROUTER YAPILANDIRMASI ---
client = None
if OPENROUTER_API_KEY:
    try:
        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=OPENROUTER_API_KEY
        )
        logger.info("✅ OpenRouter API yapılandırıldı.")
    except Exception as e:
        logger.error(f"❌ OpenRouter yapılandırma hatası: {e}")
else:
    logger.warning("⚠️ OPENROUTER_API_KEY eksik! AI özelliği çalışmayacak.")

# Model adı
AI_MODEL = "deepseek/deepseek-r1-0528:free"

# --- AI MENÜ BUTONLARI ---
AI_MENU_BUTTONS = {
    "tr": [["🧠 Sohbete Başla"], ["🔙 Ana Menü"]],
    "en": [["🧠 Start Chat"], ["🔙 Main Menu"]],
    "ru": [["🧠 Начать Чат"], ["🔙 Главное Меню"]]
}

def get_ai_menu_keyboard(lang):
    buttons = AI_MENU_BUTTONS.get(lang, AI_MENU_BUTTONS["en"])
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

def get_ai_chat_keyboard(lang):
    """AI sohbet modunda altta gösterilecek klavye"""
    buttons = {
        "tr": [["🔚 Sohbeti Bitir"]],
        "en": [["🔚 End Chat"]],
        "ru": [["🔚 Завершить Чат"]]
    }
    return ReplyKeyboardMarkup(buttons.get(lang, buttons["en"]), resize_keyboard=True)

# --- GÜNLÜK LİMİT KONTROLÜ ---
def check_and_reset_daily_limits():
    """Yeni gün başladıysa tüm kullanım sayaçlarını sıfırla"""
    today = date.today()
    if state.ai_last_reset_date != today:
        state.ai_daily_usage.clear()
        state.ai_last_reset_date = today

def get_user_remaining_quota(user_id: int) -> int:
    """Kullanıcının kalan günlük mesaj hakkı"""
    check_and_reset_daily_limits()
    used = state.ai_daily_usage.get(user_id, 0)
    # Admin kullanıcılara 999 limit
    limit = 999 if user_id in ADMIN_IDS else AI_DAILY_LIMIT
    return max(0, limit - used)

def increment_usage(user_id: int):
    """Kullanıcının günlük sayacını artır"""
    check_and_reset_daily_limits()
    state.ai_daily_usage[user_id] = state.ai_daily_usage.get(user_id, 0) + 1

# --- HANDLER'LAR ---
@rate_limit("heavy")
async def ai_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """AI asistan ana menüsü"""
    user_id = update.effective_user.id
    lang = await asyncio.to_thread(db.get_user_lang, user_id)
    state.clear_user_states(user_id)
    
    remaining = get_user_remaining_quota(user_id)
    
    # Adminler için "Sınırsız" göster
    if user_id in ADMIN_IDS:
        msg = TEXTS["ai_menu_prompt_admin"][lang]
    else:
        msg = TEXTS["ai_menu_prompt"][lang].format(remaining=remaining, limit=AI_DAILY_LIMIT)
    
    await update.message.reply_text(
        msg,
        reply_markup=get_ai_menu_keyboard(lang)
    )

async def start_ai_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """AI sohbet modunu başlat"""
    user_id = update.effective_user.id
    lang = await asyncio.to_thread(db.get_user_lang, user_id)
    
    remaining = get_user_remaining_quota(user_id)
    if remaining <= 0:
        await update.message.reply_text(
            TEXTS["ai_limit_reached"][lang],
            reply_markup=get_main_keyboard_markup(lang)
        )
        return
    
    state.clear_user_states(user_id)
    state.ai_chat_active.add(user_id)
    
    await update.message.reply_text(
        TEXTS["ai_chat_started"][lang],
        reply_markup=get_ai_chat_keyboard(lang)
    )

async def end_ai_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """AI sohbet modunu bitir"""
    user_id = update.effective_user.id
    lang = await asyncio.to_thread(db.get_user_lang, user_id)
    
    state.ai_chat_active.discard(user_id)
    
    await update.message.reply_text(
        TEXTS["ai_chat_ended"][lang],
        reply_markup=get_main_keyboard_markup(lang)
    )

async def handle_ai_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """AI sohbet modundaki mesajları işle"""
    user_id = update.effective_user.id
    
    if user_id not in state.ai_chat_active:
        return False
    
    lang = await asyncio.to_thread(db.get_user_lang, user_id)
    user_message = update.message.text
    
    # Sohbeti bitir kontrolü
    if user_message.lower() in BUTTON_MAPPINGS.get("ai_end_chat", set()):
        await end_ai_chat(update, context)
        return True
    
    # Günlük limit kontrolü
    remaining = get_user_remaining_quota(user_id)
    if remaining <= 0:
        state.ai_chat_active.discard(user_id)
        await update.message.reply_text(
            TEXTS["ai_limit_reached"][lang],
            reply_markup=get_main_keyboard_markup(lang)
        )
        return True
    
    # API Key / Client kontrolü
    if not client:
        await update.message.reply_text(
            f"❌ AI servisi yapılandırılmamış.\nAPI Key: {'Var' if OPENROUTER_API_KEY else 'YOK'}",
            reply_markup=get_ai_chat_keyboard(lang)
        )
        return True
    
    # "Düşünüyor" mesajı
    thinking_msg = await update.message.reply_text(TEXTS["ai_thinking"][lang])
    
    try:
        # OpenRouter API çağrısı
        system_prompt = """Sen DruzhikBot adlı bir Telegram botunun içinde çalışan yardımcı bir asistansın.
Kullanıcıyla sohbet et, sorularını yanıtla, yardımcı ol.
Kısa ve öz cevaplar ver (max 2-3 paragraf).
Emoji kullanabilirsin.
Kullanıcının dilinde yanıt ver."""
        
        def call_openrouter():
            return client.chat.completions.create(
                model=AI_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=500
            )
        
        response = await asyncio.to_thread(call_openrouter)
        
        # Response kontrolü
        ai_response = None
        if response.choices and len(response.choices) > 0:
            ai_response = response.choices[0].message.content
        
        if not ai_response:
            ai_response = "⚠️ Boş yanıt alındı, lütfen farklı bir soru sorun."
        
        # Sayacı artır
        increment_usage(user_id)
        new_remaining = get_user_remaining_quota(user_id)
        
        # Yanıtı gönder
        await thinking_msg.delete()
        
        # Kalan hak bilgisi ekle
        if user_id in ADMIN_IDS:
            footer = TEXTS["ai_unlimited_text"][lang]
        else:
            status_text = f"{new_remaining}/{AI_DAILY_LIMIT}"
            footer = TEXTS["ai_remaining_footer"][lang].format(status=status_text)
            
        await update.message.reply_text(
            f"{ai_response}\n\n{footer}",
            reply_markup=get_ai_chat_keyboard(lang)
        )
        
    except Exception as e:
        error_str = str(e)
        logger.error(f"AI Error: {error_str}")
        await thinking_msg.delete()
        
        # Kullanıcıya detaylı hata göster
        error_preview = error_str[:100] if len(error_str) > 100 else error_str
        await update.message.reply_text(
            f"❌ AI Hatası: {error_preview}",
            reply_markup=get_ai_chat_keyboard(lang)
        )
    
    return True
