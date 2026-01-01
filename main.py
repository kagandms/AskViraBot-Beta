import asyncio
import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters, CallbackQueryHandler

# Modülleri içe aktar
from config import BOT_TOKEN
from keep_alive import keep_alive
import database as db
import state
from texts import TEXTS, BUTTON_MAPPINGS
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
async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    # Metin varsa al, yoksa boş string (Dosya/Fotoğraf durumları için)
    text_raw = update.message.text if update.message.text else ""
    text = text_raw.lower().strip()
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

    # 3. Buton Eşleşmeleri
    
    # ANA MENÜ
    if text in BUTTON_MAPPINGS.get("menu", set()):
        await general.menu_command(update, context)
    elif text in BUTTON_MAPPINGS.get("tools_main_button", set()):
        await general.tools_menu_command(update, context)
    # YENİ: Araçlar Alt Menülerinden Geri Dönüş
    elif text in BUTTON_MAPPINGS.get("back_to_tools", set()):
        await general.tools_menu_command(update, context)
    elif text in BUTTON_MAPPINGS.get("notes_main_button", set()):
        await notes.notes_menu(update, context)
    elif text in BUTTON_MAPPINGS.get("games_main_button", set()):
        await games.games_menu(update, context)
    elif text in BUTTON_MAPPINGS.get("reminder", set()):
        await reminders.reminder_menu(update, context)
    elif text in BUTTON_MAPPINGS.get("language", set()):
        language_keyboard = ReplyKeyboardMarkup([["🇹🇷 Türkçe", "🇬🇧 English", "🇷🇺 Русский"]], resize_keyboard=True)
        await update.message.reply_text("Lütfen bir dil seçin:", reply_markup=language_keyboard)
        
    # Geliştirici butonu
    elif text in BUTTON_MAPPINGS.get("developer_main_button", set()):
        await tools.show_developer_info(update, context)
    
    # Admin Panel butonu (sadece adminler için)
    elif text in BUTTON_MAPPINGS.get("admin_panel_button", set()):
        await admin.admin_command(update, context)

    # NOTLAR MENÜSÜ
    elif text in BUTTON_MAPPINGS.get("add_note_button", set()):
        await notes.prompt_new_note(update, context)
    elif text in BUTTON_MAPPINGS.get("edit_note_button", set()):
        await notes.edit_notes_menu(update, context)
    elif text in BUTTON_MAPPINGS.get("show_all_notes_button", set()):
        await notes.shownotes_command(update, context)
    elif text in BUTTON_MAPPINGS.get("delete_note_button", set()):
        await notes.deletenotes_menu(update, context)
    elif text in BUTTON_MAPPINGS.get("select_delete_note_button", set()):
        await notes.select_note_to_delete_prompt(update, context)

    # OYUNLAR MENÜSÜ
    elif text in BUTTON_MAPPINGS.get("xox_game", set()):
        await games.xox_start(update, context)
    elif text in BUTTON_MAPPINGS.get("dice", set()):
        await games.dice_command(update, context)
    elif text in BUTTON_MAPPINGS.get("coinflip", set()):
        await games.coinflip_command(update, context)
        
    # TKM (Taş Kağıt Makas)
    elif text in BUTTON_MAPPINGS.get("tkm_main", set()):
        await games.tkm_start(update, context)

    # ARAÇLAR
    elif text in BUTTON_MAPPINGS.get("time", set()):
        await tools.time_command(update, context)
    elif text in BUTTON_MAPPINGS.get("qrcode_button", set()):
        await tools.qrcode_command(update, context)
    elif text in BUTTON_MAPPINGS.get("pdf_converter_main_button", set()):
        await tools.pdf_converter_menu(update, context)
    elif text in BUTTON_MAPPINGS.get("weather_main_button", set()):
        await tools.weather_command(update, context)
    
    # PDF SUB-MENÜ
    elif text in BUTTON_MAPPINGS.get("text_to_pdf_button", set()):
        await tools.prompt_text_for_pdf(update, context)
    elif text in BUTTON_MAPPINGS.get("image_to_pdf_button", set()) or text in BUTTON_MAPPINGS.get("document_to_pdf_button", set()):
        await tools.prompt_file_for_pdf(update, context)
    
    # VIDEO DOWNLOADER
    elif text in BUTTON_MAPPINGS.get("video_downloader_main_button", set()):
        await tools.video_downloader_menu(update, context)
    elif text in BUTTON_MAPPINGS.get("video_platform_tiktok", set()):
        await tools.set_video_platform(update, context, "tiktok")
    elif text in BUTTON_MAPPINGS.get("video_platform_twitter", set()):
        await tools.set_video_platform(update, context, "twitter")
    elif text in BUTTON_MAPPINGS.get("video_platform_instagram", set()):
        await tools.set_video_platform(update, context, "instagram")
    elif text in BUTTON_MAPPINGS.get("format_video", set()):
        await tools.set_download_format(update, context, "video")
    elif text in BUTTON_MAPPINGS.get("format_audio", set()):
        await tools.set_download_format(update, context, "audio")
    elif text in BUTTON_MAPPINGS.get("back_to_platform", set()):
        await tools.video_downloader_menu(update, context)

    # HATIRLATICI MENÜSÜ
    elif text in BUTTON_MAPPINGS.get("add_reminder_button", set()):
        await reminders.prompt_reminder_input(update, context)
    elif text in BUTTON_MAPPINGS.get("show_reminders_button", set()):
        await reminders.show_reminders_command(update, context)
    elif text in BUTTON_MAPPINGS.get("delete_reminder_button", set()):
        await reminders.delete_reminder_menu(update, context)
    
    # AI ASISTAN
    elif text in BUTTON_MAPPINGS.get("ai_main_button", set()):
        await ai_chat.ai_menu(update, context)
    elif text in BUTTON_MAPPINGS.get("ai_start_chat", set()):
        await ai_chat.start_ai_chat(update, context)
    elif text in BUTTON_MAPPINGS.get("ai_end_chat", set()):
        await ai_chat.end_ai_chat(update, context)
    elif text in BUTTON_MAPPINGS.get("ai_back_to_menu", set()):
        await general.menu_command(update, context)
    
    # METRO
    elif text in BUTTON_MAPPINGS.get("metro_main_button", set()):
        await metro.metro_menu_command(update, context)

    # DİL
    elif text in {"🇹🇷 türkçe", "🇬🇧 english", "🇷🇺 русский"}:
        await general.set_language(update, context)
    else:
        await unknown_command(update, context)

async def on_startup(application):
    logger.info("Bot başlatılıyor... Bekleyen hatırlatıcılar kontrol ediliyor.")
    await reminders.start_pending_reminders(application)

def main():
    keep_alive()

    app = ApplicationBuilder().token(BOT_TOKEN).post_init(on_startup).build()

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
        CallbackQueryHandler(games.xox_callback, pattern=r"^xox_(move_\d+|diff_(easy|medium|hard))$"),
        CallbackQueryHandler(tools.weather_callback_query, pattern=r"^weather_"),
        CallbackQueryHandler(tools.handle_social_media_callbacks, pattern=r"^(back_to_main_menu)$"),
        CallbackQueryHandler(reminders.delete_reminder_callback, pattern=r"^(delete_rem_\d+|reminders_back_inline)$"),
        CallbackQueryHandler(admin.admin_callback, pattern=r"^admin_"),
        CallbackQueryHandler(metro.metro_callback_query, pattern=r"^metro_"),
        
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