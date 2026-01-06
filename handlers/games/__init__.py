
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

from .tkm import (
    tkm_start,
    handle_tkm_bet,
    start_tkm_game,
    tkm_play
)

from .slot import (
    slot_start,
    handle_slot_bet,
    start_slot_game,
    slot_spin
)

from .blackjack import (
    blackjack_start,
    start_blackjack_game,
    handle_blackjack_bet,
    handle_blackjack_message
)

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

async def handle_game_mode_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles Fun/Coin mode selection for all games"""
    user_id = update.effective_user.id
    lang = await asyncio.to_thread(db.get_user_lang, user_id)
    text = update.message.text.lower() if update.message.text else ""
    
    # Get current game from state data
    state_data = await state.get_data(user_id)
    game = state_data.get("game", "")
    
    # Back check
    if is_back_button(text):
        await cleanup_context(context, user_id)
        try: await update.message.delete()
        except: pass
        await state.clear_user_states(user_id)
        # Assuming games_menu is available
        await games_menu(update, context)
        return
    
    # Delete user input
    try: await update.message.delete()
    except: pass
    
    # Check for "Fun" mode
    fun_keywords = ["eğlencesine", "just for fun", "для удовольствия", "🎮"]
    coin_keywords = ["coinle", "with coins", "за монеты", "💰"]
    
    is_fun_mode = any(k in text for k in fun_keywords)
    is_coin_mode = any(k in text for k in coin_keywords)
    
    if is_fun_mode:
        # Start game in fun mode (no coins)
        await state.clear_user_states(user_id)
        if game == "tkm":
            await start_tkm_game(update, context, bet_amount=0)
        elif game == "slot":
            await start_slot_game(update, context, bet_amount=0)
        elif game == "blackjack":
            await start_blackjack_game(update, context, bet_amount=0)
    elif is_coin_mode:
        # Show bet selection
        coins = await asyncio.to_thread(db.get_user_coins, user_id)
        if coins < 50:
            msg = TEXTS["insufficient_funds"][lang].format(amount=50, balance=coins)
            await update.message.reply_text(msg)
            await state.clear_user_states(user_id)
            await games_menu(update, context)
            return
        
        # Set appropriate bet state
        if game == "tkm":
            await state.set_state(user_id, state.WAITING_FOR_TKM_BET)
        elif game == "slot":
            await state.set_state(user_id, state.WAITING_FOR_SLOT_BET)
        elif game == "blackjack":
            await state.set_state(user_id, state.WAITING_FOR_BJ_BET)
        
        msg_text = TEXTS["bet_select_prompt"][lang].format(balance=coins)
        sent_msg = await update.message.reply_text(
            msg_text,
            reply_markup=get_bet_keyboard_generic(lang),
            parse_mode="Markdown"
        )
        
        await state.set_state(user_id, 
            state.WAITING_FOR_TKM_BET if game == "tkm" else 
            state.WAITING_FOR_SLOT_BET if game == "slot" else 
            state.WAITING_FOR_BJ_BET, 
            {"message_id": sent_msg.message_id}
        )
    else:
        # Invalid selection - ignore
        pass
