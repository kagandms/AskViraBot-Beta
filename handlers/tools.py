import asyncio
from datetime import datetime
import logging
import os

logger = logging.getLogger(__name__)
import qrcode
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
import database as db
import state
from texts import TEXTS, BUTTON_MAPPINGS, SOCIAL_MEDIA_LINKS
from utils import get_input_back_keyboard_markup, get_main_keyboard_markup, get_weather_cities_keyboard, is_back_button, cleanup_context
from rate_limiter import rate_limit

# --- YARDIMCI FONKSİYONLAR ---
# (Diğer modüller tarafından kullanılıyor olabilir, burada kalsın veya utils'e taşınabilir)
# Şu an için burada sadece yerel kullanılanlar kalacak.

# --- ZAMAN KOMUTU ---
async def time_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    now = datetime.now().strftime("%H:%M:%S")
    await update.message.reply_text(f"🕒 Saat: {now}")

# --- QR KOD ---
@rate_limit("heavy")
async def qrcode_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    lang = await asyncio.to_thread(db.get_user_lang, user_id)
    
    if context.args:
        data = ' '.join(context.args)
        await generate_and_send_qr(update, context, data)
    else:
        await state.clear_user_states(user_id)
        
        # Cleanup
        try:
            await update.message.delete()
        except Exception as e:
            logger.debug(f"Failed to delete message in qrcode_command: {e}")
        
        sent_message = await update.message.reply_text(
            TEXTS["qrcode_prompt_input"][lang],
            reply_markup=get_input_back_keyboard_markup(lang)
        )
        
        await state.set_state(user_id, state.WAITING_FOR_QR_DATA, {"message_id": sent_message.message_id})

async def generate_and_send_qr(update: Update, context: ContextTypes.DEFAULT_TYPE, data):
    user_id = update.effective_user.id
    lang = await asyncio.to_thread(db.get_user_lang, user_id)

    data_lower = data.lower().strip()
    if is_back_button(data):
        # Cleanup
        await cleanup_context(context, user_id)
        try:
            await update.message.delete()
        except Exception as e:
            logger.debug(f"Failed to delete message in generate_and_send_qr: {e}")

        from handlers.general import tools_menu_command
        await state.clear_user_states(user_id)
        await tools_menu_command(update, context)
        return

    file_path = f"qr_{user_id}.png"
    
    try:
        img = qrcode.make(data)
        img.save(file_path)
        
        await asyncio.to_thread(db.log_qr_usage, user_id, data)
        
        with open(file_path, 'rb') as photo:
            await update.message.reply_photo(photo, caption=TEXTS["qrcode_generated"][lang].format(data=data), reply_markup=get_main_keyboard_markup(lang))
            
    except Exception as e:
        await update.message.reply_text(TEXTS["error_occurred"][lang] + str(e))
        
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)
    
    await state.clear_user_states(user_id)

# --- GELİŞTİRİCİ ---
def get_developer_keyboard(lang):
    """Geliştirici menü klavyesi"""
    labels = {
        "tr": [["🌐 Web Sitem", "📸 Instagram"], ["✈️ Telegram", "💼 LinkedIn"], ["🔙 Geri"]],
        "en": [["🌐 My Website", "📸 Instagram"], ["✈️ Telegram", "💼 LinkedIn"], ["🔙 Back"]],
        "ru": [["🌐 Мой Сайт", "📸 Instagram"], ["✈️ Telegram", "💼 LinkedIn"], ["🔙 Назад"]]
    }
    return ReplyKeyboardMarkup(labels.get(lang, labels["en"]), resize_keyboard=True)

async def show_developer_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    lang = await asyncio.to_thread(db.get_user_lang, user_id)
    
    # Cleanup previous messages
    await cleanup_context(context, user_id)
    
    # Delete user's button press
    try:
        await update.message.delete()
    except Exception as e:
        logger.debug(f"Failed to delete message in show_developer_info: {e}")
    
    await state.clear_user_states(user_id)
    
    dev_text = {
        "tr": "👨‍💻 *Geliştirici Bilgileri*\n\nSosyal medya hesaplarıma aşağıdaki bağlantılardan ulaşabilirsiniz:",
        "en": "👨‍💻 *Developer Info*\n\nYou can reach my social media accounts through the links below:",
        "ru": "👨‍💻 *Информация о разработчике*\n\nВы можете связаться со мной через соцсети по ссылкам ниже:"
    }
    
    msg = await update.message.reply_text(
        dev_text.get(lang, dev_text["en"]),
        reply_markup=get_developer_keyboard(lang),
        parse_mode="Markdown"
    )
    
    await state.set_state(user_id, state.DEVELOPER_MENU_ACTIVE, {"message_id": msg.message_id})

async def handle_developer_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    
    if not await state.check_state(user_id, state.DEVELOPER_MENU_ACTIVE):
        return False
    
    text = update.message.text.lower()
    lang = await asyncio.to_thread(db.get_user_lang, user_id)
    
    if is_back_button(text):
        # State temizliğini menu_command içinde cleanup_context yapacak
        if "developer_last_link_msg" in context.user_data:
            try:
                await context.user_data["developer_last_link_msg"].delete()
            except Exception as e:
                logger.debug(f"Failed to delete previous developer link message: {e}")
            # del context.user_data["developer_last_link_msg"] # Optional safety

        try:
            await update.message.delete()
        except Exception as e:
            logger.debug(f"Failed to delete message in handle_developer_message: {e}")
        
        from handlers.general import menu_command
        await menu_command(update, context)
        return True
    
    link = None
    if "web" in text or "сайт" in text:
        link = SOCIAL_MEDIA_LINKS["website"]
    elif "instagram" in text:
        link = SOCIAL_MEDIA_LINKS["instagram"]
    elif "telegram" in text:
        link = SOCIAL_MEDIA_LINKS["telegram"]
    elif "linkedin" in text:
        link = SOCIAL_MEDIA_LINKS["linkedin"]
    
    if link:
        if "developer_last_link_msg" in context.user_data:
            try:
                await context.user_data["developer_last_link_msg"].delete()
            except Exception as e:
                logger.debug(f"Failed to delete previous developer link message (2): {e}")
        
        msg = await update.message.reply_text(f"🔗 {link}", reply_markup=get_developer_keyboard(lang))
        context.user_data["developer_last_link_msg"] = msg
        return True
    
    return False

async def handle_social_media_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    if query.data == "back_to_main_menu":
        await query.message.delete()