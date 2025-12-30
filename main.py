import asyncio
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters, CallbackQueryHandler

# Modülleri içe aktar
from config import BOT_TOKEN
from keep_alive import keep_alive
import database as db
import state
from texts import TEXTS, BUTTON_MAPPINGS
from utils import get_main_keyboard_markup

# Handler'ları içe aktar
from handlers import general, notes, reminders, games, tools

async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = db.get_user_lang(update.effective_user.id)
    await update.message.reply_text(TEXTS["unknown_command"][lang])

# --- ANA BUTON YÖNETİCİSİ (ROUTER) ---
async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower() if update.message.text else ""
    user_id = update.effective_user.id
    lang = db.get_user_lang(user_id)

    # 1. State Kontrolleri (Kullanıcı bir şey yazması bekleniyorsa)
    if user_id in state.waiting_for_new_note_input:
        await notes.handle_new_note_input(update, context)
        return
    if user_id in state.waiting_for_reminder_input:
        await reminders.process_reminder_input(update, context)
        return
    if user_id in state.waiting_for_qr_data:
        await tools.generate_and_send_qr(update, context, update.message.text)
        return
    if user_id in state.playing_tkm:
        await games.tkm_play(update, context)
        return
    if user_id in state.waiting_for_pdf_conversion_input:
        if update.message.document or update.message.photo or update.message.text:
            await tools.handle_pdf_input(update, context)
        return
    if user_id in state.waiting_for_weather_city:
        await tools.get_weather_data(update, context, update.message.text)
        return

    # 2. Buton Eşleşmeleri
    if text in BUTTON_MAPPINGS["menu"]:
        await general.menu_command(update, context)
    elif text in BUTTON_MAPPINGS["notes_main_button"]:
        await notes.notes_menu(update, context)
    elif text in BUTTON_MAPPINGS["add_note_button"]:
        await notes.prompt_new_note(update, context)
    elif text in BUTTON_MAPPINGS["show_all_notes_button"]:
        await notes.shownotes_command(update, context)
    elif text in BUTTON_MAPPINGS["delete_note_button"]:
        await notes.deletenotes_menu(update, context)
    elif text in BUTTON_MAPPINGS["select_delete_note_button"]:
        await notes.select_note_to_delete_prompt(update, context)
    elif text in BUTTON_MAPPINGS["dice"]:
        await games.dice_command(update, context)
    elif text in BUTTON_MAPPINGS["coinflip"]:
        await games.coinflip_command(update, context)
    elif text in BUTTON_MAPPINGS["time"]:
        await tools.time_command(update, context)
    elif text in BUTTON_MAPPINGS["reminder"]:
        await reminders.reminder_menu(update, context)
    elif text in BUTTON_MAPPINGS["add_reminder_button"]:
        await reminders.prompt_reminder_input(update, context)
    elif text in BUTTON_MAPPINGS["show_reminders_button"]:
        await reminders.show_reminders_command(update, context)
    elif text in BUTTON_MAPPINGS["delete_reminder_button"]:
        await reminders.delete_reminder_menu(update, context)
    elif text in BUTTON_MAPPINGS["tkm_main"]:
        await games.tkm_start(update, context)
    elif text in BUTTON_MAPPINGS["qrcode_button"]:
        await tools.qrcode_command(update, context)
    elif text in BUTTON_MAPPINGS["pdf_converter_main_button"]:
        await tools.pdf_converter_menu(update, context)
    elif text in BUTTON_MAPPINGS["text_to_pdf_button"]:
        await tools.prompt_text_for_pdf(update, context)
    elif text in BUTTON_MAPPINGS["image_to_pdf_button"] or text in BUTTON_MAPPINGS["document_to_pdf_button"]:
        await tools.prompt_file_for_pdf(update, context)
    elif text in BUTTON_MAPPINGS["weather_main_button"]:
        await tools.weather_command(update, context)
    elif text in BUTTON_MAPPINGS["developer_main_button"]:
        await tools.show_developer_info(update, context)
    elif text in BUTTON_MAPPINGS["language"]:
        language_keyboard = ReplyKeyboardMarkup([["🇹🇷 Türkçe", "🇬🇧 English", "🇷🇺 Русский"]], resize_keyboard=True)
        await update.message.reply_text("Lütfen bir dil seçin:", reply_markup=language_keyboard)
    elif text in {"🇹🇷 türkçe", "🇬🇧 english", "🇷🇺 русский"}:
        await general.set_language(update, context)
    else:
        # Eşleşme yoksa
        await unknown_command(update, context)

async def on_startup(application):
    print("Bot başlatılıyor... Bekleyen hatırlatıcılar kontrol ediliyor.")
    await reminders.start_pending_reminders(application)

def main():
    keep_alive() # Flask sunucusu

    app = ApplicationBuilder().token(BOT_TOKEN).post_init(on_startup).build()

    # Handler Listesi
    handlers_list = [
        CommandHandler("start", general.start),
        CommandHandler("menu", general.menu_command),
        CommandHandler(["tr", "en", "ru"], general.set_language),
        CommandHandler("time", tools.time_command),
        CommandHandler("notes", notes.notes_menu),
        CommandHandler("deletenotes", notes.deletenotes_menu),
        CommandHandler("addnote", notes.addnote_command),
        CommandHandler("shownotes", notes.shownotes_command),
        CommandHandler("tkm", games.tkm_start),
        CommandHandler("decisionwheel", games.decision_wheel_command),
        CommandHandler("dice", games.dice_command),
        CommandHandler("coinflip", games.coinflip_command),
        CommandHandler("remind", reminders.remind_command),
        CommandHandler("qrcode", tools.qrcode_command),
        CommandHandler("pdfconverter", tools.pdf_converter_menu),
        CommandHandler("weather", tools.weather_command),
        CommandHandler("developer", tools.show_developer_info),
        
        # Callbacks
        CallbackQueryHandler(notes.delete_note_callback, pattern=r"^(delete_note_\d+|notes_prev_page|notes_next_page|delete_notes_back_inline)$"),
        CallbackQueryHandler(tools.weather_callback_query, pattern=r"^weather_"),
        CallbackQueryHandler(tools.handle_social_media_callbacks, pattern=r"^(back_to_main_menu)$"),
        CallbackQueryHandler(reminders.delete_reminder_callback, pattern=r"^(delete_rem_\d+|reminders_back_inline)$"),
        
        # Messages
        MessageHandler(filters.TEXT & (~filters.COMMAND) | filters.Document.ALL | filters.PHOTO, handle_buttons),
        MessageHandler(filters.COMMAND, unknown_command)
    ]

    for handler in handlers_list:
        app.add_handler(handler)
    
    print("DruzhikBot çalışıyor...")
    app.run_polling()

if __name__ == "__main__":
    main()