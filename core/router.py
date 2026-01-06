
import logging
import asyncio
from typing import Callable, Dict, Any, Awaitable, List, Tuple, Set

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes

import database as db
import state
from utils import cleanup_context
# Handlers imports for button mappings
from handlers import general, notes, reminders, games, tools, admin, ai_chat, metro, pdf, video, weather, economy, shazam

logger = logging.getLogger(__name__)

# --- STATE ROUTER SECTION ---

# Type alias for handler functions
StateHandler = Callable[[Update, ContextTypes.DEFAULT_TYPE], Awaitable[Any]]

class StateRouter:
    def __init__(self):
        self._handlers: Dict[str, StateHandler] = {}
        
    def register(self, state_name: str, handler: StateHandler):
        """Registers a handler for a specific state name."""
        self._handlers[state_name] = handler
        logger.debug(f"Registered handler for state: {state_name}")
        
    async def dispatch(self, state_name: str, update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
        """
        Dispatches the update to the handler registered for the given state.
        Returns True if a handler was found and executed, False otherwise.
        """
        handler = self._handlers.get(state_name)
        if handler:
            try:
                await handler(update, context)
                return True
            except Exception as e:
                # Use global error handler logic or log it here.
                # Ideally, we allow exception to bubble up to the global handler, 
                # but legacy code swallowed things. We log it nicely.
                logger.error(f"Error handling state '{state_name}': {e}", exc_info=True)
                return False
        return False

# Global StateRouter instance
router = StateRouter()


# --- BUTTON ROUTER SECTION ---

async def show_language_keyboard(update, context):
    """Dil seçim klavyesini gösterir"""
    user_id = update.effective_user.id
    # lang fetch removed as it wasn't used efficiently, simplified logic
    
    # Cleanup previous context
    await cleanup_context(context, user_id)
    
    # Delete user's button press
    try:
        if update.message:
            await update.message.delete()
    except Exception: pass
    
    language_keyboard = ReplyKeyboardMarkup([["🇹🇷 Türkçe", "🇬🇧 English", "🇷🇺 Русский"]], resize_keyboard=True)
    sent_msg = await update.message.reply_text("Lütfen bir dil seçin:", reply_markup=language_keyboard)
    
    # Save message ID for cleanup
    await state.set_state(user_id, "language_selection", {"message_id": sent_msg.message_id})

# --- BUTTON HANDLER EŞLEŞTİRMELERİ ---
# Format: (mapping_key, handler_function)

BUTTON_HANDLERS: List[Tuple[str, Callable]] = [
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
    
    # === EKONOMİ ===
    ("daily_bonus", economy.daily_bonus_command),
    ("balance", economy.balance_command),
    
    # === SHAZAM ===
    ("shazam_main_button", shazam.start_shazam_mode),

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
