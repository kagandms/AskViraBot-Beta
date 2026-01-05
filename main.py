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
from handlers import general, notes, reminders, games, tools, admin, ai_chat, metro, pdf, video, weather
from keep_alive import keep_alive

# --- LOGLAMA YAPILANDIRMASI ---
from logger import setup_logging, get_logger
setup_logging()
logger = get_logger(__name__)

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
    if await state.check_state(user_id, state.METRO_BROWSING):
        await metro.handle_metro_message(update, context)
        return
    if await state.check_state(user_id, state.PLAYING_XOX):
        await games.handle_xox_message(update, context)
        return
    if await state.check_state(user_id, state.ADMIN_MENU_ACTIVE):
        handled = await admin.handle_admin_message(update, context)
        if handled:
            return
    if await state.check_state(user_id, state.DEVELOPER_MENU_ACTIVE):
        handled = await tools.handle_developer_message(update, context)
        if handled:
            return
    if await state.check_state(user_id, state.WAITING_FOR_NEW_NOTE_INPUT):
        await notes.handle_new_note_input(update, context)
        return
    if await state.check_state(user_id, state.WAITING_FOR_EDIT_NOTE_INPUT):
        await notes.handle_edit_note_input(update, context)
        return
    if await state.check_state(user_id, state.WAITING_FOR_REMINDER_INPUT):
        await reminders.process_reminder_input(update, context)
        return
    if await state.check_state(user_id, state.WAITING_FOR_QR_DATA):
        await tools.generate_and_send_qr(update, context, text_raw)
        return
    if await state.check_state(user_id, state.PLAYING_TKM):
        await games.tkm_play(update, context)
        return
    if await state.check_state(user_id, state.PLAYING_BLACKJACK):
        await games.handle_blackjack_message(update, context)
        return
    if await state.check_state(user_id, state.PLAYING_SLOT):
        await games.slot_spin(update, context)
        return
    if await state.check_state(user_id, state.WAITING_FOR_PDF_CONVERSION_INPUT):
        if update.message.document or update.message.photo or update.message.text:
            await pdf.handle_pdf_input(update, context)
        return
    if await state.check_state(user_id, state.WAITING_FOR_WEATHER_CITY):
        await weather.get_weather_data(update, context, text_raw)
        return
    if await state.check_state(user_id, state.WAITING_FOR_VIDEO_LINK):
        await video.download_and_send_media(update, context)
        return
    if await state.check_state(user_id, state.AI_CHAT_ACTIVE):
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
    
    # --- WEBHOOK MODE (Render/Production) ---
    if WEBHOOK_URL:
        logger.info(f"🚀 WEBHOOK MODE - URL: {WEBHOOK_URL}")
        logger.info(f"🌐 Starting on port {PORT}")
        
        # Use python-telegram-bot's built-in webhook support with health check
        # The webhook runs on /{BOT_TOKEN}, and we add a health check on /
        from starlette.applications import Starlette
        from starlette.responses import PlainTextResponse
        from starlette.routing import Route
        
        async def health_check(request):
            return PlainTextResponse("Bot is alive!")
        
        # Create custom starlette app with health check route
        starlette_app = Starlette(routes=[
            Route("/", health_check, methods=["GET", "HEAD"]),
        ])
        
        app.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=BOT_TOKEN,
            webhook_url=f"{WEBHOOK_URL}/{BOT_TOKEN}",
            other_routes=starlette_app.routes  # Add health check routes
        )
    
    # --- POLLING MODE (Local development) ---
    else:
        logger.info("📡 POLLING MODE (No RENDER_EXTERNAL_URL found)")
        keep_alive()
        app.run_polling()

if __name__ == "__main__":
    main()