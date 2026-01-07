import asyncio
from datetime import date
import logging
import time  # For rate limiting updates
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.error import BadRequest
from openai import AsyncOpenAI  # CHANGED: Use Async client

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
        # CHANGED: AsyncOpenAI
        client = AsyncOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=OPENROUTER_API_KEY
        )
        logger.info("✅ OpenRouter Async API yapılandırıldı.")
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
    lang = await db.get_user_lang(user_id)
    
    # Cleanup previous context
    from utils import cleanup_context
    await cleanup_context(context, user_id)
    
    # Delete user's button press
    try:
        await update.message.delete()
    except: pass
    
    await state.clear_user_states(user_id)
    
    remaining = await get_user_remaining_quota_async(user_id)
    
    # Adminler için "Sınırsız" göster
    if user_id in ADMIN_IDS:
        msg_text = TEXTS["ai_menu_prompt_admin"][lang]
    else:
        msg_text = TEXTS["ai_menu_prompt"][lang].format(remaining=remaining, limit=AI_DAILY_LIMIT)
    
    sent_msg = await update.message.reply_text(
        msg_text,
        reply_markup=get_ai_menu_keyboard(lang)
    )
    
    # Mesaj ID'sini kaydet
    await state.set_state(user_id, state.AI_MENU_ACTIVE, {"message_id": sent_msg.message_id})

async def start_ai_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """AI sohbet modunu başlat"""
    user_id = update.effective_user.id
    lang = await db.get_user_lang(user_id)
    
    remaining = await get_user_remaining_quota_async(user_id)
    if remaining <= 0:
        await update.message.reply_text(
            TEXTS["ai_limit_reached"][lang],
            reply_markup=get_main_keyboard_markup(lang)
        )
        return
    
    # Cleanup previous context (AI menu prompt)
    from utils import cleanup_context
    await cleanup_context(context, user_id)
    
    await state.clear_user_states(user_id)
    # Initialize with empty conversation history
    await state.set_state(user_id, state.AI_CHAT_ACTIVE, {"messages": []})
    
    # Delete user's button press
    try:
        await update.message.delete()
    except: pass
    
    sent_msg = await update.message.reply_text(
        TEXTS["ai_chat_started"][lang],
        reply_markup=get_ai_chat_keyboard(lang)
    )
    
    # Track message for cleanup
    await state.set_state(user_id, state.AI_CHAT_ACTIVE, {"messages": [], "message_id": sent_msg.message_id})

async def end_ai_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """AI sohbet modunu bitir"""
    user_id = update.effective_user.id
    lang = await db.get_user_lang(user_id)
    
    # Cleanup previous context
    from utils import cleanup_context, send_temp_message
    await cleanup_context(context, user_id)
    
    # Delete user's "end chat" message
    try:
        await update.message.delete()
    except: pass
    
    await state.clear_user_states(user_id)
    
    # Send temporary notification (auto-deletes after 3 seconds)
    await send_temp_message(update, user_id, TEXTS["ai_chat_ended"][lang], delay=3.0)
    
    # Go back to main menu
    from handlers.general import menu_command
    await menu_command(update, context)

async def handle_ai_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """AI sohbet modundaki mesajları işle (STREAMING)"""
    user_id = update.effective_user.id
    
    # State zaten main.py'de kontrol edildi
    
    lang = await db.get_user_lang(user_id)
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
    
    # Başlangıç mesajı
    initial_texts = {
        "tr": "🤔 ...",
        "en": "🤔 ...",
        "ru": "🤔 ..."
    }
    ai_msg = await update.message.reply_text(initial_texts.get(lang, "🤔 ..."))
    
    ai_response_content = ""
    
    try:
        # Get conversation history from state
        state_data = await state.get_data(user_id)
        message_history = state_data.get("messages", []) if state_data else []
        
        # OpenRouter API çağrısı - System Prompt
        system_prompt = """Sen ViraBot adlı bir Telegram botunun içinde çalışan yardımcı bir asistansın.
Kullanıcıyla sohbet et, sorularını yanıtla, yardımcı ol.
Kısa ve öz cevaplar ver (max 2-3 paragraf).
Emoji kullanabilirsin.
Kullanıcının dilinde yanıt ver."""
        
        # Build messages list with history
        api_messages = [{"role": "system", "content": system_prompt}]
        api_messages.extend(message_history)  # Add previous messages
        api_messages.append({"role": "user", "content": user_message})
        
        # STREAMING API REQUEST
        stream = await client.chat.completions.create(
            model=AI_MODEL,
            messages=api_messages,
            max_tokens=1000,
            stream=True  # ENABLE STREAMING
        )
        
        last_update_time = time.time()
        
        async for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                ai_response_content += delta
                
                # Rate Limiting: Update message every ~1.0 seconds
                current_time = time.time()
                if current_time - last_update_time > 1.0:
                    try:
                        # Append cursor
                        await ai_msg.edit_text(ai_response_content + " ▌")
                        last_update_time = current_time
                    except BadRequest as e:
                        # Ignore "Message is not modified" errors
                        if "Message is not modified" in str(e):
                            pass
                        else:
                            # Other errors (e.g. connection), log but try to continue
                            logger.warning(f"Stream update error: {e}")
        
        # Final cleanup: Remove cursor and ensure full text is shown
        if not ai_response_content:
            ai_response_content = "⚠️ Boş yanıt alındı."
            
        try:
            # Prepare footer
            if user_id in ADMIN_IDS:
                footer = TEXTS["ai_unlimited_text"][lang]
            else:
                # Increment usage
                await increment_usage_async(user_id)
                new_remaining = await get_user_remaining_quota_async(user_id)
                status_text = f"{new_remaining}/{AI_DAILY_LIMIT}"
                footer = TEXTS["ai_remaining_footer"][lang].format(status=status_text)
            
            final_text = f"{ai_response_content}\n\n{footer}"
            await ai_msg.edit_text(final_text, reply_markup=get_ai_chat_keyboard(lang))
            
        except BadRequest as e:
            logger.error(f"Final update error: {e}")

        # Save conversation to history
        message_history.append({"role": "user", "content": user_message})
        message_history.append({"role": "assistant", "content": ai_response_content})
        # Limit history
        if len(message_history) > 10:
            message_history = message_history[-10:]
        await state.set_state(user_id, state.AI_CHAT_ACTIVE, {"messages": message_history})
        
    except Exception as e:
        error_str = str(e)
        logger.error(f"AI Stream Error: {error_str}", exc_info=True)
        
        # Kullanıcıya hata bildir
        error_preview = error_str[:100] if len(error_str) > 100 else error_str
        try:
            await ai_msg.edit_text(
                f"❌ AI Hatası: {error_preview}",
                reply_markup=get_ai_chat_keyboard(lang)
            )
        except:
            # If edit fails (e.g. message deleted), send new
            await update.message.reply_text(f"❌ AI Hatası: {error_preview}")
    
    return True

# --- MODULAR SETUP ---
def setup(app):
    from telegram.ext import CommandHandler
    from core.router import router
    import state
    
    # 1. Commands
    # ai_menu is called via rate_limit wrapper usually, but here we can register it if needed as command?
    # main.py does: app.add_handler(CommandHandler("ai", ai_menu)) ? No, usually button based.
    # But let's check main.py. If "ai" command exists.
    # Assuming "ai" command exists or it's just menu based.
    # main.py usually has: CommandHandler("ai", ai_chat.ai_menu)
    app.add_handler(CommandHandler("ai", ai_menu))
    
    # 2. Router
    router.register(state.AI_CHAT_ACTIVE, handle_ai_message)
    router.register(state.AI_MENU_ACTIVE, ai_menu)
    
    logger.info("✅ AI Chat module loaded")
