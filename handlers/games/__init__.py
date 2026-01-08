
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

from .sudoku import sudoku_start
from .xox_web import xox_web_start
from .web_games import snake_start, game_2048_start, flappy_start, runner_start

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
from .core import games_menu

# handle_game_mode_selection removed (Vira - no betting modes)

# Callback handler for inline back buttons
async def back_to_games_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle back to games inline button callback"""
    from utils import get_games_keyboard_markup
    
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    lang = await db.get_user_lang(user_id)
    
    # Delete the message with inline keyboard
    try:
        await query.message.delete()
    except:
        pass
    
    # Send games menu directly (can't use games_menu because update.message is None)
    await context.bot.send_message(
        chat_id=user_id,
        text=TEXTS["games_menu_prompt"][lang],
        reply_markup=get_games_keyboard_markup(lang)
    )

# --- MODULAR SETUP ---
def setup(app):
    from telegram.ext import CommandHandler, CallbackQueryHandler
    from core.router import router, register_button
    import state
    
    # 1. Commands
    app.add_handler(CommandHandler("games", games_menu))
    app.add_handler(CommandHandler("tkm", tkm_start))
    app.add_handler(CommandHandler("xox", xox_start))
    app.add_handler(CommandHandler("dice", dice_command))
    app.add_handler(CommandHandler("coinflip", coinflip_command))
    app.add_handler(CommandHandler("stats", show_player_stats))
    app.add_handler(CommandHandler("sudoku", sudoku_start))
    
    # 2. Router
    router.register(state.PLAYING_XOX, handle_xox_message)
    router.register(state.PLAYING_TKM, tkm_play)
    # Mode selection removed for Vira (no betting)
    
    # 3. Buttons
    register_button("back_to_games", games_menu)
    register_button("games_main_button", games_menu)
    register_button("xox_game", xox_web_start)  # Web App version
    register_button("dice", dice_command)
    register_button("coinflip", coinflip_command)
    register_button("tkm_main", tkm_start)
    register_button("player_stats", show_player_stats)
    register_button("sudoku_main", sudoku_start)
    register_button("snake_main", snake_start)
    register_button("game_2048_main", game_2048_start)
    register_button("flappy_main", flappy_start)
    register_button("runner_main", runner_start)
    
    # 4. Callback Query Handlers (for inline keyboards)
    app.add_handler(CallbackQueryHandler(back_to_games_callback, pattern=r"^back_to_games$"))
    
    logger.info("✅ Games module loaded")
