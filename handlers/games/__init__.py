
# handlers/games/__init__.py
# Expose everything to maintain compatibility with "from handlers import games"

from .core import (
    games_menu,
    show_player_stats,
    dice_command,
    coinflip_command,
    xox_start,
    handle_xox_message,
    get_game_mode_keyboard
)

import logging
logger = logging.getLogger(__name__)

from .tkm import (
    tkm_start,
    start_tkm_game,
    tkm_play
)

# Slot and Blackjack imports removed

# Shared handler for mode selection (dispatch to specific games)
# This one needs to be defined here or in core and import others.
# Since it depends on start_tkm_game, start_slot_game, etc., it's tricky to put in core without circular imports.
# Best place is __init__ or a new 'dispatcher.py'.
# Let's put it here for now to tie everything together.

import asyncio
from telegram import Update
from telegram.ext import ContextTypes
import database as db
import state
from texts import TEXTS
from utils import is_back_button, cleanup_context
from .core import games_menu, get_bet_keyboard_generic

# handle_game_mode_selection removed (Vira - no betting modes)

# --- MODULAR SETUP ---
def setup(app):
    from telegram.ext import CommandHandler
    from core.router import router, register_button
    import state
    
    # 1. Commands
    app.add_handler(CommandHandler("games", games_menu))
    app.add_handler(CommandHandler("tkm", tkm_start))
    app.add_handler(CommandHandler("xox", xox_start))
    app.add_handler(CommandHandler("dice", dice_command))
    app.add_handler(CommandHandler("coinflip", coinflip_command))
    app.add_handler(CommandHandler("stats", show_player_stats))
    
    # 2. Router
    router.register(state.PLAYING_XOX, handle_xox_message)
    router.register(state.PLAYING_TKM, tkm_play)
    # Mode selection removed for Vira (no betting)
    
    # 3. Buttons
    register_button("back_to_games", games_menu)
    register_button("games_main_button", games_menu)
    register_button("xox_game", xox_start)
    register_button("dice", dice_command)
    register_button("coinflip", coinflip_command)
    register_button("tkm_main", tkm_start)
    register_button("player_stats", show_player_stats)
    
    logger.info("✅ Games module loaded")
