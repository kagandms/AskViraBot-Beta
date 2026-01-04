"""
AI Chat Handler for ViraBot
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

# --- GÜNLÜK LİMİT KONTROLÜ (VERİTABANI İLE) ---
def get_today_str() -> str:
    """Bugünün tarihini 'YYYY-MM-DD' formatında döndürür."""
    return date.today().isoformat()


async def get_user_remaining_quota_async(user_id: int) -> int:
    """Kullanıcının kalan günlük mesaj hakkı (asenkron, DB destekli)."""
    today = get_today_str()
    used = await asyncio.to_thread(db.get_ai_daily_usage, user_id, today)
    # Admin kullanıcılara 999 limit
    limit = 999 if user_id in ADMIN_IDS else AI_DAILY_LIMIT
    return max(0, limit - used)


async def increment_usage_async(user_id: int) -> None:
    """Kullanıcının günlük sayacını artır (asenkron, DB destekli)."""
    today = get_today_str()
    await asyncio.to_thread(db.increment_ai_usage, user_id, today)


# --- HANDLER'LAR ---
@rate_limit("heavy")
async def ai_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """AI asistan ana menüsü"""
    user_id = update.effective_user.id
    lang = await asyncio.to_thread(db.get_user_lang, user_id)
    await state.clear_user_states(user_id)
    
    remaining = await get_user_remaining_quota_async(user_id)
    
    # Adminler için "Sınırsız" göster
    if user_id in ADMIN_IDS:
        msg = TEXTS["ai_menu_prompt_admin"][lang]
    else:
        msg = TEXTS["ai_menu_prompt"][lang].format(remaining=remaining, limit=AI_DAILY_LIMIT)
    
    await update.message.reply_text(
        msg,
        reply_markup=get_ai_menu_keyboard(lang)
    )

async def start_ai_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """AI sohbet modunu başlat"""
    user_id = update.effective_user.id
    lang = await asyncio.to_thread(db.get_user_lang, user_id)
    
    remaining = await get_user_remaining_quota_async(user_id)
    if remaining <= 0:
        await update.message.reply_text(
            TEXTS["ai_limit_reached"][lang],
            reply_markup=get_main_keyboard_markup(lang)
        )
        return
    
    await state.clear_user_states(user_id)
    # Initialize with empty conversation history
    await state.set_state(user_id, state.AI_CHAT_ACTIVE, {"messages": []})
    
    await update.message.reply_text(
        TEXTS["ai_chat_started"][lang],
        reply_markup=get_ai_chat_keyboard(lang)
    )

async def end_ai_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """AI sohbet modunu bitir"""
    user_id = update.effective_user.id
    lang = await asyncio.to_thread(db.get_user_lang, user_id)
    
    await state.clear_user_states(user_id)
    
    await update.message.reply_text(
        TEXTS["ai_chat_ended"][lang],
        reply_markup=get_main_keyboard_markup(lang, user_id)
    )

async def handle_ai_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """AI sohbet modundaki mesajları işle"""
    user_id = update.effective_user.id
    
    # State zaten main.py'de kontrol edildi
    
    lang = await asyncio.to_thread(db.get_user_lang, user_id)
    user_message = update.message.text
    
    # Sohbeti bitir kontrolü
    if user_message.lower() in BUTTON_MAPPINGS.get("ai_end_chat", set()):
        await end_ai_chat(update, context)
        return True
    
    # Günlük limit kontrolü
    remaining = await get_user_remaining_quota_async(user_id)
    if remaining <= 0:
        await state.clear_user_states(user_id)
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
    
    # "Düşünüyor" mesajı - döngülü güncelleme
    thinking_texts = {
        "tr": ["🤔 Düşünüyorum...", "💭 İsteğiniz işleniyor...", "⏳ Az kaldı..."],
        "en": ["🤔 Thinking...", "💭 Processing your request...", "⏳ Almost there..."],
        "ru": ["🤔 Думаю...", "💭 Обрабатываю запрос...", "⏳ Почти готово..."]
    }
    thinking_msg = await update.message.reply_text(thinking_texts.get(lang, thinking_texts["en"])[0])
    
    # Mesaj döngüsü arka planda (2 sn aralıklarla)
    async def update_thinking_message():
        texts = thinking_texts.get(lang, thinking_texts["en"])
        for i in range(1, len(texts)):
            await asyncio.sleep(3.7)  # 3.7 saniye aralıklarla güncelle
            try:
                await thinking_msg.edit_text(texts[i])
            except Exception:
                break
    
    update_task = asyncio.create_task(update_thinking_message())
    
    try:
        # Get conversation history from state
        state_data = await state.get_data(user_id)
        message_history = state_data.get("messages", []) if state_data else []
        
        # OpenRouter API çağrısı
        system_prompt = """Sen ViraBot adlı bir Telegram botunun içinde çalışan yardımcı bir asistansın.
Kullanıcıyla sohbet et, sorularını yanıtla, yardımcı ol.
Kısa ve öz cevaplar ver (max 2-3 paragraf).
Emoji kullanabilirsin.
Kullanıcının dilinde yanıt ver."""
        
        # Build messages list with history
        api_messages = [{"role": "system", "content": system_prompt}]
        api_messages.extend(message_history)  # Add previous messages
        api_messages.append({"role": "user", "content": user_message})
        
        def call_openrouter():
            return client.chat.completions.create(
                model=AI_MODEL,
                messages=api_messages,
                max_tokens=1000
            )
        
        response = await asyncio.to_thread(call_openrouter)
        
        # Döngüyü durdur
        update_task.cancel()
        
        # Response kontrolü
        ai_response = None
        if response.choices and len(response.choices) > 0:
            ai_response = response.choices[0].message.content
        
        if not ai_response:
            ai_response = "⚠️ Boş yanıt alındı, lütfen farklı bir soru sorun."
        
        # Sayacı artır
        await increment_usage_async(user_id)
        new_remaining = await get_user_remaining_quota_async(user_id)
        
        # Save conversation to history (keep last 10 messages = 5 exchanges)
        message_history.append({"role": "user", "content": user_message})
        message_history.append({"role": "assistant", "content": ai_response})
        # Limit to last 10 messages to save DB space
        if len(message_history) > 10:
            message_history = message_history[-10:]
        await state.set_state(user_id, state.AI_CHAT_ACTIVE, {"messages": message_history})
        
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
