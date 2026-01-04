# router.py - Dinamik Buton Yönlendirme Sistemi
# Bu dosya, buton-handler eşleştirmelerini merkezi olarak yönetir.
# Yeni buton eklemek için sadece BUTTON_HANDLERS listesine bir tuple eklemek yeterli.

from handlers import general, notes, reminders, games, tools, admin, ai_chat, metro, pdf, video, weather

# --- ÖZEL HANDLER'LAR ---
# Bazı butonlar özel parametre veya mantık gerektirdiği için lambda kullanılır

async def show_language_keyboard(update, context):
    """Dil seçim klavyesini gösterir"""
    from telegram import ReplyKeyboardMarkup
    from utils import cleanup_context
    import state
    import asyncio
    import database as db
    
    user_id = update.effective_user.id
    lang = await asyncio.to_thread(db.get_user_lang, user_id)
    
    # Cleanup previous context
    await cleanup_context(context, user_id)
    
    language_keyboard = ReplyKeyboardMarkup([["🇹🇷 Türkçe", "🇬🇧 English", "🇷🇺 Русский"]], resize_keyboard=True)
    sent_msg = await update.message.reply_text("Lütfen bir dil seçin:", reply_markup=language_keyboard)
    
    # Save message ID for cleanup
    await state.set_state(user_id, "language_selection", {"message_id": sent_msg.message_id})

# --- BUTON HANDLER EŞLEŞTİRMELERİ ---
# Format: (mapping_key, handler_function)
# Sıralama önemli: Önce eşleşen çalışır

BUTTON_HANDLERS = [
    # === ANA MENÜ ===
    ("menu", general.menu_command),
    ("tools_main_button", general.tools_menu_command),
    ("back_to_tools", general.tools_menu_command),
    ("back_to_games", games.games_menu),
    ("back_to_notes", notes.notes_menu),
    ("notes_main_button", notes.notes_menu),
    ("games_main_button", games.games_menu),
    ("reminder", reminders.reminder_menu),
    ("language", show_language_keyboard),
    ("developer_main_button", tools.show_developer_info),
    ("admin_panel_button", admin.admin_command),
    ("help_button", general.help_command),
    
    # === NOTLAR MENÜSÜ ===
    ("add_note_button", notes.prompt_new_note),
    ("edit_note_button", notes.edit_notes_menu),
    ("show_all_notes_button", notes.shownotes_command),
    ("delete_note_button", notes.deletenotes_menu),
    ("select_delete_note_button", notes.select_note_to_delete_prompt),
    
    # === OYUNLAR MENÜSÜ ===
    ("xox_game", games.xox_start),
    ("dice", games.dice_command),
    ("coinflip", games.coinflip_command),
    ("tkm_main", games.tkm_start),
    ("blackjack_main", games.blackjack_start),
    ("player_stats", games.show_player_stats),
    ("slot_main", games.slot_start),
    
    # === ARAÇLAR ===
    ("time", tools.time_command),
    ("qrcode_button", tools.qrcode_command),
    ("pdf_converter_main_button", pdf.pdf_converter_menu),
    ("weather_main_button", weather.weather_command),
    
    # === PDF SUB-MENÜ ===
    ("text_to_pdf_button", pdf.prompt_text_for_pdf),
    ("image_to_pdf_button", pdf.prompt_file_for_pdf),
    ("document_to_pdf_button", pdf.prompt_file_for_pdf),
    
    # === VIDEO DOWNLOADER ===
    ("video_downloader_main_button", video.video_downloader_menu),
    ("back_to_platform", video.video_downloader_menu),
    
    # === HATIRLATICI MENÜSÜ ===
    ("add_reminder_button", reminders.prompt_reminder_input),
    ("show_reminders_button", reminders.show_reminders_command),
    ("delete_reminder_button", reminders.delete_reminder_menu),
    
    # === AI ASISTAN ===
    ("ai_main_button", ai_chat.ai_menu),
    ("ai_start_chat", ai_chat.start_ai_chat),
    ("ai_end_chat", ai_chat.end_ai_chat),
    ("ai_back_to_menu", general.menu_command),
    
    # === METRO ===
    ("metro_main_button", metro.metro_menu_command),
]

# --- ÖZEL PLATFORM HANDLER'LARI ---
# Bu handler'lar parametre gerektirdiği için ayrı tutulur
VIDEO_PLATFORM_HANDLERS = {
    "video_platform_tiktok": ("tiktok", video.set_video_platform),
    "video_platform_twitter": ("twitter", video.set_video_platform),
    "video_platform_instagram": ("instagram", video.set_video_platform),
}

FORMAT_HANDLERS = {
    "format_video": ("video", video.set_download_format),
    "format_audio": ("audio", video.set_download_format),
}

# --- DİL BUTONLARI ---
LANGUAGE_BUTTONS = {"🇹🇷 türkçe", "🇬🇧 english", "🇷🇺 русский"}
