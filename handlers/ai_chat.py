"""
AI Chat Handler for DruzhikBot
Google Gemini API Integration with Daily Limits
"""

import asyncio
from datetime import date
import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes

import database as db
import state
from config import GEMINI_API_KEY, AI_DAILY_LIMIT
from texts import TEXTS, BUTTON_MAPPINGS
from utils import get_main_keyboard_markup
from rate_limiter import rate_limit

logger = logging.getLogger(__name__)

# --- GEMINI YAPILANDIRMASI ---
model = None
if GEMINI_API_KEY:
    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')
        logger.info("✅ Gemini API yapılandırıldı.")
    except Exception as e:
        logger.error(f"❌ Gemini yapılandırma hatası: {e}")
else:
    logger.warning("⚠️ GEMINI_API_KEY eksik! AI özelliği çalışmayacak.")

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
    return max(0, AI_DAILY_LIMIT - used)

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
    
    await update.message.reply_text(
        TEXTS["ai_menu_prompt"][lang].format(remaining=remaining, limit=AI_DAILY_LIMIT),
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
    
    # API Key / Model kontrolü
    if not model:
        await update.message.reply_text(
            f"❌ AI servisi yapılandırılmamış.\nAPI Key: {'Var' if GEMINI_API_KEY else 'YOK'}",
            reply_markup=get_ai_chat_keyboard(lang)
        )
        return True
    
    # "Düşünüyor" mesajı
    thinking_msg = await update.message.reply_text(TEXTS["ai_thinking"][lang])
    
    try:
        # Gemini API çağrısı
        system_prompt = """Sen DruzhikBot adlı bir Telegram botunun içinde çalışan yardımcı bir asistansın.
        Kullanıcıyla sohbet et, sorularını yanıtla, yardımcı ol.
        Kısa ve öz cevaplar ver (max 2-3 paragraf).
        Emoji kullanabilirsin.
        Kullanıcının dilinde yanıt ver."""
        
        full_prompt = f"{system_prompt}\n\nKullanıcı: {user_message}"
        
        # Senkron API çağrısını thread'de çalıştır
        def call_gemini():
            return model.generate_content(full_prompt)
        
        response = await asyncio.to_thread(call_gemini)
        
        # Response kontrolü
        ai_response = None
        try:
            ai_response = response.text
        except ValueError as ve:
            logger.error(f"Gemini response.text error: {ve}")
            if hasattr(response, 'prompt_feedback') and response.prompt_feedback:
                ai_response = f"⚠️ İçerik engellendi: {response.prompt_feedback}"
            else:
                ai_response = "⚠️ Yanıt alınamadı, lütfen tekrar deneyin."
        except Exception as inner_e:
            logger.error(f"Gemini inner error: {inner_e}")
            ai_response = f"⚠️ Yanıt işleme hatası: {str(inner_e)[:50]}"
        
        if not ai_response:
            ai_response = "⚠️ Boş yanıt alındı, lütfen farklı bir soru sorun."
        
        # Sayacı artır
        increment_usage(user_id)
        new_remaining = get_user_remaining_quota(user_id)
        
        # Yanıtı gönder
        await thinking_msg.delete()
        
        # Kalan hak bilgisi ekle
        footer = TEXTS["ai_remaining_footer"][lang].format(remaining=new_remaining)
        await update.message.reply_text(
            f"{ai_response}\n\n{footer}",
            reply_markup=get_ai_chat_keyboard(lang)
        )
        
    except Exception as e:
        error_str = str(e)
        logger.error(f"AI Error: {error_str}")
        await thinking_msg.delete()
        
        # Kullanıcıya detaylı hata göster (debug için)
        error_preview = error_str[:100] if len(error_str) > 100 else error_str
        await update.message.reply_text(
            f"❌ AI Hatası: {error_preview}",
            reply_markup=get_ai_chat_keyboard(lang)
        )
    
    return True
