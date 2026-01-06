import asyncio
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters, CallbackQueryHandler

# Modülleri içe aktar
from config import BOT_TOKEN
import database as db
import state
from texts import TEXTS, BUTTON_MAPPINGS
from utils import get_main_keyboard_markup
from rate_limiter import is_rate_limited, get_remaining_cooldown

# Handler'ları içe aktar
from handlers import general, notes, reminders, games, tools, admin, ai_chat, metro, pdf, video, weather, economy, shazam
from keep_alive import keep_alive
from utils import attach_user, handle_errors

# --- LOGLAMA YAPILANDIRMASI ---
from logger import setup_logging, get_logger
setup_logging()
logger = get_logger(__name__)

async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    # DB İŞLEMİ: Asenkron yapıldı
    lang = await asyncio.to_thread(db.get_user_lang, user_id)
    await update.message.reply_text(TEXTS["unknown_command"][lang])

from core import router

# --- ROUTER INIT ---
def init_router():
    """Register all state handlers to the router."""
    router.register(state.METRO_BROWSING, metro.handle_metro_message)
    router.register(state.PLAYING_XOX, games.handle_xox_message)
    router.register(state.ADMIN_MENU_ACTIVE, admin.handle_admin_message)
    router.register(state.DEVELOPER_MENU_ACTIVE, tools.handle_developer_message)
    router.register(state.WAITING_FOR_NEW_NOTE_INPUT, notes.handle_new_note_input)
    router.register(state.WAITING_FOR_EDIT_NOTE_INPUT, notes.handle_edit_note_input)
    router.register(state.WAITING_FOR_REMINDER_INPUT, reminders.process_reminder_input)
    router.register(state.WAITING_FOR_QR_DATA, tools.generate_and_send_qr)
    router.register(state.PLAYING_TKM, games.tkm_play)
    router.register(state.PLAYING_BLACKJACK, games.handle_blackjack_message)
    router.register(state.PLAYING_SLOT, games.slot_spin)
    router.register(state.WAITING_FOR_PDF_CONVERSION_INPUT, pdf.handle_pdf_input)
    router.register(state.WAITING_FOR_WEATHER_CITY, weather.get_weather_data)
    router.register(state.WAITING_FOR_VIDEO_LINK, video.download_and_send_media)
    router.register(state.WAITING_FOR_GAME_MODE, games.handle_game_mode_selection)
    router.register(state.WAITING_FOR_TKM_BET, games.handle_tkm_bet)
    router.register(state.WAITING_FOR_SLOT_BET, games.handle_slot_bet)
    router.register(state.WAITING_FOR_BJ_BET, games.handle_blackjack_bet)
    router.register(state.WAITING_FOR_SHAZAM, shazam.handle_shazam_input)
    router.register(state.AI_CHAT_ACTIVE, ai_chat.handle_ai_message)

    logger.info("✅ State Router Initialized with Handlers")

# Initialize router immediately
init_router()

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

    # Admin Broadcast Kontrolü - Özel Durum (State'den bağımsız araya girebilir)
    if await admin.handle_broadcast_message(update, context):
        return
    
    # 2. State Kontrolleri - ROUTER ISLEMI
    # Kullanıcının aktif state'ini al
    user_state = await state.get_state(user_id)
    if user_state:
        # Router'a sor: Bu state için bir handler var mı?
        # Varsa çalıştır ve çık.
        handled = await router.dispatch(user_state, update, context)
        if handled:
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
    # Unified import: Everything is now in core.router
    from core.router import BUTTON_HANDLERS, VIDEO_PLATFORM_HANDLERS, FORMAT_HANDLERS, LANGUAGE_BUTTONS
    
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
        # Hata detayını gizle
        if update.message:
            await update.message.reply_text("⚠️ Bir hata oluştu. Lütfen daha sonra tekrar deneyin.")

async def on_startup(application):
    logger.info("Bot başlatılıyor... Bekleyen hatırlatıcılar kontrol ediliyor.")
    await reminders.start_pending_reminders(application)

async def on_shutdown(application):
    logger.info("Bot kapatılıyor... HTTP session temizleniyor.")
    await metro.close_http_session()

def main():
    import os
    
    # Webhook configuration - Render provides RENDER_EXTERNAL_URL automatically
    WEBHOOK_URL = os.getenv("RENDER_EXTERNAL_URL", "")
    PORT = int(os.getenv("PORT", 8080))
    
    # Build telegram application
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
        CommandHandler("pdfconverter", pdf.pdf_converter_menu),
        CommandHandler("weather", weather.weather_command),
        CommandHandler("developer", tools.show_developer_info),
        
        # Notes
        CommandHandler("notes", notes.notes_menu),
        CommandHandler("deletenotes", notes.deletenotes_menu),
        CommandHandler("addnote", notes.addnote_command),
        CommandHandler("editnote", notes.edit_notes_menu),
        CommandHandler("shownotes", notes.shownotes_command),
        
        # Economy
        CommandHandler("daily", economy.daily_bonus_command),
        CommandHandler("balance", economy.balance_command),
        
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
        CallbackQueryHandler(tools.handle_social_media_callbacks, pattern=r"^(back_to_main_menu)$"),
        CallbackQueryHandler(reminders.delete_reminder_callback, pattern=r"^(delete_rem_\d+|reminders_back_inline)$"),
        CallbackQueryHandler(admin.admin_callback, pattern=r"^admin_"),
        CallbackQueryHandler(weather.weather_callback_query, pattern=r"^forecast_"),
        
        # Messages
        MessageHandler(filters.TEXT & (~filters.COMMAND) | filters.Document.ALL | filters.PHOTO, handle_buttons),
        MessageHandler(filters.COMMAND, unknown_command)
    ]

    for handler in handlers_list:
        app.add_handler(handler)
    
    # --- PRODUCTION MODE (Render) ---
    # Using polling + Flask health check for reliability on free tier
    # Flask runs on PORT for UptimeRobot, bot uses polling for Telegram
    if WEBHOOK_URL:
        logger.info(f"🚀 PRODUCTION MODE - Polling + Health Check")
        logger.info(f"🌐 Health check on port {PORT}")
        keep_alive()  # Flask server for UptimeRobot
        app.run_polling(drop_pending_updates=True)
    
    # --- POLLING MODE (Local development) ---
    else:
        logger.info("📡 POLLING MODE (No RENDER_EXTERNAL_URL found)")
        keep_alive()
        app.run_polling()

if __name__ == "__main__":
    main()