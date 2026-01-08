
"""
database.py - Facade for accessing services.
This file maintains backward compatibility by exporting functions from the new service layer.
"""
import logging
from config import supabase

# Loglama ayarı (Deprecated usage via this module, but kept for compatibility)
logger = logging.getLogger(__name__)

# --- SERVICES IMPORTS ---

from services.user_service import (
    get_user_lang, 
    set_user_lang_db,
    set_user_state, 
    get_user_state, 
    clear_user_state,
    get_all_users_count, 
    get_all_user_ids, 
    get_recent_users,
    get_user_model
)

from services.note_service import (
    get_user_notes, 
    add_user_note, 
    update_user_note, 
    delete_user_note_by_id,
    get_all_notes_count,
    get_notes, 
    add_note, 
    delete_note, 
    update_note
)

from services.game_service import (
    log_xox_game,
    log_tkm_game,
    log_coinflip,
    log_dice_roll,
    get_user_xox_stats,
    get_user_tkm_stats,
    save_web_game_score,     # NEW
    get_web_game_high_score, # NEW
    get_web_game_stats       # NEW
)

from services.ai_service import (
    get_ai_daily_usage, 
    set_ai_daily_usage, 
    increment_ai_usage, 
    get_ai_total_stats
)

from services.reminder_service import (
    get_all_reminders_db, 
    add_reminder_db, 
    remove_reminder_db,
    get_all_reminders_count
)

from services.activity_service import (
    log_qr_usage, 
    log_pdf_usage
)

# Export explicitly to satisfy linters/static analysis if needed
__all__ = [
    'get_user_lang', 'set_user_lang_db',
    'set_user_state', 'get_user_state', 'clear_user_state',
    'get_all_users_count', 'get_all_user_ids', 'get_recent_users', 'get_user_model',
    'get_user_notes', 'add_user_note', 'update_user_note', 'delete_user_note_by_id',
    'get_all_notes_count', 'get_notes', 'add_note', 'delete_note', 'update_note',
    'get_metro_favorites', 'add_metro_favorite', 'remove_metro_favorite', # Bunlar eksik?
    'get_ai_daily_usage', 'set_ai_daily_usage', 'increment_ai_usage', 'get_ai_total_stats',
    'get_all_reminders_db', 'add_reminder_db', 'remove_reminder_db', 'get_all_reminders_count',
    'log_qr_usage', 'log_pdf_usage',
    'log_xox_game', 'log_tkm_game', 'log_coinflip', 'log_dice_roll',
    'get_user_xox_stats', 'get_user_tkm_stats',
    'save_web_game_score', 'get_web_game_high_score', 'get_web_game_stats'
]
