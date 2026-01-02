import asyncio
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters, CallbackQueryHandler

# Modülleri içe aktar
from config import BOT_TOKEN
from keep_alive import keep_alive
import database as db
import state
from texts import TEXTS
from utils import get_main_keyboard_markup
from rate_limiter import is_rate_limited, get_remaining_cooldown

# Handler'ları içe aktar
from handlers import general, notes, reminders, games, tools, admin, ai_chat, metro

# --- LOGLAMA YAPILANDIRMASI ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    # DB İŞLEMİ: Asenkron yapıldı
    lang = await asyncio.to_thread(db.get_user_lang, user_id)
    await update.message.reply_text(TEXTS["unknown_command"][lang])

# --- ANA BUTON YÖNETİCİSİ (ROUTER) ---
async def handle_buttons_logic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    # Metin varsa al, yoksa boş string (Dosya/Fotoğraf durumları için)
    text_raw = update.message.text if update.message.text else ""
    # Türkçe İ/i karakterlerini doğru işlemek için turkish_lower kullanılır
    from texts import turkish_lower
    text = turkish_lower(text_raw).strip()
    user_id = update.effective_user.id
    
    # Genel Rate Limit Kontrolü
    if is_rate_limited(user_id, "general"):
        cooldown = get_remaining_cooldown(user_id, "general")
        lang = await asyncio.to_thread(db.get_user_lang, user_id)
        rate_limit_msgs = {
            "tr": f"⏳ Çok fazla istek gönderdiniz. Lütfen {cooldown} saniye bekleyin.",
            "en": f"⏳ Too many requests. Please wait {cooldown} seconds.",
            "ru": f"⏳ Слишком много запросов. Подождите {cooldown} секунд."
        }
        await update.message.reply_text(rate_limit_msgs.get(lang, rate_limit_msgs["en"]))
        return
    
    # DB İŞLEMİ: Router seviyesinde dil kontrolü (Asenkron)
    # Not: Handler'lar kendi içinde tekrar dil kontrolü yapabilir, 
    # ama asyncio.to_thread kullandığımız için bu işlem botu kilitlemez.
    # lang = await asyncio.to_thread(db.get_user_lang, user_id) 

    # Admin Broadcast Kontrolü
    if await admin.handle_broadcast_message(update, context):
        return
    
    # 2. State Kontrolleri
    if user_id in state.metro_browsing:
        await metro.handle_metro_message(update, context)
        return
    if user_id in state.playing_xox:
        await games.handle_xox_message(update, context)
        return
    if user_id in state.admin_menu_active:
        handled = await admin.handle_admin_message(update, context)
        if handled:
            return
    if user_id in state.developer_menu_active:
        handled = await tools.handle_developer_message(update, context)
        if handled:
            return
    if user_id in state.waiting_for_new_note_input:
        await notes.handle_new_note_input(update, context)
        return
    if user_id in state.waiting_for_edit_note_input:
        await notes.handle_edit_note_input(update, context)
        return
    if user_id in state.waiting_for_reminder_input:
        await reminders.process_reminder_input(update, context)
        return
    if user_id in state.waiting_for_qr_data:
        await tools.generate_and_send_qr(update, context, text_raw)
        return
    if user_id in state.playing_tkm:
        await games.tkm_play(update, context)
        return
    if user_id in state.waiting_for_pdf_conversion_input:
        if update.message.document or update.message.photo or update.message.text:
            await tools.handle_pdf_input(update, context)
        return
    if user_id in state.waiting_for_weather_city:
        await tools.get_weather_data(update, context, text_raw)
        return
    if user_id in state.waiting_for_video_link:
        await tools.download_and_send_media(update, context)
        return
    if user_id in state.ai_chat_active:
        await ai_chat.handle_ai_message(update, context)
        return

    # EĞER HİÇBİR STATE'E GİRMEDİYSE VE METİN YOKSA (Beklenmeyen Dosya)
    if not text:
        lang = await asyncio.to_thread(db.get_user_lang, user_id)
        msg_warn = {
            "tr": "⚠️ Beklenmeyen dosya. Lütfen önce menüden bir işlem (örn. PDF) seçin.",
            "en": "⚠️ Unexpected file. Please select an action from the menu first.",
            "ru": "⚠️ Неожиданный файл. Сначала выберите действие из меню."
        }
        await update.message.reply_text(msg_warn.get(lang, msg_warn["en"]))
        return

    # 3. Dinamik Buton Yönlendirme (Router Pattern)
    from texts import BUTTON_MAPPINGS
    from router import BUTTON_HANDLERS, VIDEO_PLATFORM_HANDLERS, FORMAT_HANDLERS, LANGUAGE_BUTTONS
    
    # Standart buton eşleşmeleri
    for mapping_key, handler in BUTTON_HANDLERS:
        if text in BUTTON_MAPPINGS.get(mapping_key, set()):
            await handler(update, context)
            return
    
    # Video platform butonları (parametre gerektiren)
    for mapping_key, (platform, handler) in VIDEO_PLATFORM_HANDLERS.items():
        if text in BUTTON_MAPPINGS.get(mapping_key, set()):
            await handler(update, context, platform)
            return
    
    # Format seçim butonları (parametre gerektiren)
    for mapping_key, (format_type, handler) in FORMAT_HANDLERS.items():
        if text in BUTTON_MAPPINGS.get(mapping_key, set()):
            await handler(update, context, format_type)
            return
    
    # Dil butonları
    if text in LANGUAGE_BUTTONS:
        await general.set_language(update, context)
        return
    
    # Hiçbir buton eşleşmedi
    await unknown_command(update, context)

async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await handle_buttons_logic(update, context)
    except Exception as e:
        logger.error(f"Error in handle_buttons: {e}", exc_info=True)
        # Hata detayını kullanıcıya göster (Debug için)
        if update.message:
            await update.message.reply_text(f"⚠️ Hata: {str(e)}")

async def on_startup(application):
    logger.info("Bot başlatılıyor... Bekleyen hatırlatıcılar kontrol ediliyor.")
    await reminders.start_pending_reminders(application)

async def on_shutdown(application):
    logger.info("Bot kapatılıyor... HTTP session temizleniyor.")
    await metro.close_http_session()

def main():
    keep_alive()

    app = ApplicationBuilder().token(BOT_TOKEN).post_init(on_startup).post_shutdown(on_shutdown).build()

    # Handler Listesi
    handlers_list = [
        CommandHandler("start", general.start),
        CommandHandler("menu", general.menu_command),
        CommandHandler("help", general.help_command),
        CommandHandler(["tr", "en", "ru"], general.set_language),
        
        # Tools
        CommandHandler("time", tools.time_command),
        CommandHandler("qrcode", tools.qrcode_command),
        CommandHandler("pdfconverter", tools.pdf_converter_menu),
        CommandHandler("weather", tools.weather_command),
        CommandHandler("developer", tools.show_developer_info),
        
        # Notes
        CommandHandler("notes", notes.notes_menu),
        CommandHandler("deletenotes", notes.deletenotes_menu),
        CommandHandler("addnote", notes.addnote_command),
        CommandHandler("editnote", notes.edit_notes_menu),
        CommandHandler("shownotes", notes.shownotes_command),
        
        # Games
        CommandHandler("games", games.games_menu),
        CommandHandler("tkm", games.tkm_start),
        CommandHandler("xox", games.xox_start),
        CommandHandler("dice", games.dice_command),
        CommandHandler("coinflip", games.coinflip_command),
        
        # Admin
        CommandHandler("admin", admin.admin_command),
        
        # Reminders
        CommandHandler("remind", reminders.remind_command),
        
        # Callbacks
        CallbackQueryHandler(notes.delete_note_callback, pattern=r"^(delete_note_\d+|notes_prev_page|notes_next_page|delete_notes_back_inline)$"),
        CallbackQueryHandler(notes.handle_edit_note_callback, pattern=r"^(edit_note_\d+|notes_back_inline)$"),
        # XOX removed (Reply Keyboard)
        # Weather removed (Reply Keyboard)
        CallbackQueryHandler(tools.handle_social_media_callbacks, pattern=r"^(back_to_main_menu)$"),
        CallbackQueryHandler(reminders.delete_reminder_callback, pattern=r"^(delete_rem_\d+|reminders_back_inline)$"),
        CallbackQueryHandler(admin.admin_callback, pattern=r"^admin_"),
        CallbackQueryHandler(tools.weather_callback_query, pattern=r"^forecast_"),
        # Metro removed (Reply Keyboard)
        
        # Messages
        MessageHandler(filters.TEXT & (~filters.COMMAND) | filters.Document.ALL | filters.PHOTO, handle_buttons),
        MessageHandler(filters.COMMAND, unknown_command)
    ]

    for handler in handlers_list:
        app.add_handler(handler)
    
    logger.info("DruzhikBot çalışıyor...")
    app.run_polling()

if __name__ == "__main__":
    main()