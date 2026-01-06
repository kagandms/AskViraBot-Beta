
import asyncio
import logging
import random
from telegram import Update
from telegram.ext import ContextTypes
import database as db
import state
from texts import TEXTS, TKM_BUTTONS
from utils import is_back_button, cleanup_context
from rate_limiter import rate_limit
from telegram import ReplyKeyboardMarkup

from handlers.games.core import (
    GAME_NAMES, get_game_mode_keyboard, get_bet_keyboard_generic, 
    games_menu, parse_bet_amount, get_all_in_amount
)

# --- TAŞ KAĞIT MAKAS ---

@rate_limit("games")
async def tkm_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """TKM oyunu için mod seçimi göster"""
    user_id = update.effective_user.id
    lang = await asyncio.to_thread(db.get_user_lang, user_id)
    
    await cleanup_context(context, user_id)
    try: await update.message.delete()
    except: pass
    
    await state.clear_user_states(user_id)
    await state.set_state(user_id, state.WAITING_FOR_GAME_MODE, {"game": "tkm"})
    
    game_name = GAME_NAMES["tkm"].get(lang, GAME_NAMES["tkm"]["en"])
    msg_text = TEXTS["game_mode_select"][lang].format(game_name=game_name)
    
    sent_msg = await update.message.reply_text(
        msg_text,
        reply_markup=get_game_mode_keyboard(lang),
        parse_mode="Markdown"
    )
    await state.set_state(user_id, state.WAITING_FOR_GAME_MODE, {"game": "tkm", "message_id": sent_msg.message_id})

async def handle_tkm_bet(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle TKM bet amount selection"""
    user_id = update.effective_user.id
    lang = await asyncio.to_thread(db.get_user_lang, user_id)
    text = update.message.text if update.message.text else ""
    
    if is_back_button(text):
        await cleanup_context(context, user_id)
        try: await update.message.delete()
        except: pass
        await state.clear_user_states(user_id)
        await games_menu(update, context)
        return
    
    try: await update.message.delete()
    except: pass
    
    amount = parse_bet_amount(text, user_id)
    if amount is None:
        amount = await get_all_in_amount(text, user_id)
    
    if amount is None or amount <= 0:
        await update.message.reply_text("❌ Geçersiz miktar / Invalid amount")
        return
    
    coins = await asyncio.to_thread(db.get_user_coins, user_id)
    if amount > coins:
        msg = TEXTS["insufficient_funds"][lang].format(amount=amount, balance=coins)
        await update.message.reply_text(msg)
        return
    
    await asyncio.to_thread(db.add_user_coins, user_id, -amount)
    await state.clear_user_states(user_id)
    await start_tkm_game(update, context, bet_amount=amount)


from models.game_state import TKMState

# ...

async def start_tkm_game(update: Update, context: ContextTypes.DEFAULT_TYPE, bet_amount: int = 0) -> None:
    """Actually start the TKM game"""
    user_id = update.effective_user.id
    lang = await asyncio.to_thread(db.get_user_lang, user_id)
    
    # Use Model
    tkm_state = TKMState(bet_amount=bet_amount)
    await state.set_state(user_id, state.PLAYING_TKM, tkm_state.to_dict())
    
    buttons = TKM_BUTTONS.get(lang, TKM_BUTTONS["en"])
    welcome_text = TEXTS["tkm_welcome"][lang]
    if bet_amount > 0:
        welcome_text += f"\n\n💰 Bahsin: *{bet_amount} Coin* (Kazanırsan x2)"
    
    sent_msg = await update.message.reply_text(
        welcome_text, 
        reply_markup=ReplyKeyboardMarkup(buttons, resize_keyboard=True),
        parse_mode="Markdown"
    )
    
    tkm_state.message_id = sent_msg.message_id
    await state.set_state(user_id, state.PLAYING_TKM, tkm_state.to_dict())

async def tkm_play(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    lang = "en"
    try:
        lang = await asyncio.to_thread(db.get_user_lang, user_id)
        user_move_raw = update.message.text.lower().strip()
        
        game_data_dict = await state.get_data(user_id)
        if game_data_dict:
             tkm_state = TKMState.from_dict(game_data_dict)
        else:
             tkm_state = TKMState() # Safe fallback or return
        
        if is_back_button(user_move_raw):
            try:
                if tkm_state.message_id:
                    await context.bot.delete_message(chat_id=user_id, message_id=tkm_state.message_id)
                await update.message.delete()
            except Exception: pass
            await games_menu(update, context)
            return

        user_move = None
        rock_keywords = ["taş", "rock", "камень", "🪨"]
        paper_keywords = ["kağıt", "paper", "бумага", "📄", "📃", "📝"] 
        scissors_keywords = ["makas", "scissors", "ножницы", "✂️", "✂"]

        if any(k in user_move_raw for k in rock_keywords): user_move = "taş"
        elif any(k in user_move_raw for k in paper_keywords): user_move = "kağıt"
        elif any(k in user_move_raw for k in scissors_keywords): user_move = "makas"

        if user_move is None:
            await update.message.reply_text(TEXTS["tkm_invalid_input"][lang])
            return

        standard_moves = ["taş", "kağıt", "makas"]
        bot_move_standard = random.choice(standard_moves)
        
        display_moves = {
            "tr": {"taş": "Taş", "kağıt": "Kağıt", "makas": "Makas"}, 
            "en": {"taş": "Rock", "kağıt": "Paper", "makas": "Scissors"}, 
            "ru": {"taş": "Камень", "kağıt": "Бумага", "makas": "Ножницы"} 
        }
        
        bot_display = display_moves.get(lang, display_moves["tr"]).get(bot_move_standard, bot_move_standard)
        user_display = display_moves.get(lang, display_moves["tr"]).get(user_move, user_move)
        
        result_msg = f"{TEXTS['tkm_labels_bot'][lang]}: {bot_display}\n{TEXTS['tkm_labels_you'][lang]}: {user_display}\n"
        user_idx = standard_moves.index(user_move)
        bot_idx = standard_moves.index(bot_move_standard)

        result_status = "draw"
        if user_idx == bot_idx: 
            result_msg += TEXTS["tkm_tie"][lang]
            result_status = "draw"
        elif (user_idx - bot_idx + 3) % 3 == 1: 
            result_msg += TEXTS["tkm_win"][lang]
            result_status = "win"
        else: 
            result_msg += TEXTS["tkm_lose"][lang]
            result_status = "lose"
            
        await asyncio.to_thread(db.log_tkm_game, user_id, user_move, bot_move_standard, result_status)
        
        bet_amount = tkm_state.bet_amount
        
        if bet_amount > 0:
            if result_status == "win":
                winnings = bet_amount * 2
                await asyncio.to_thread(db.add_user_coins, user_id, winnings)
                result_msg += "\n\n" + TEXTS["game_win_coins"][lang].format(amount=winnings, multiplier=2)
            elif result_status == "draw":
                await asyncio.to_thread(db.add_user_coins, user_id, bet_amount)
                result_msg += "\n\n" + TEXTS["game_draw_refund"][lang].format(amount=bet_amount)
            else:
                result_msg += "\n\n" + TEXTS["game_lose_coins"][lang].format(amount=bet_amount)

        await state.clear_user_states(user_id)
        from handlers.games.core import get_games_keyboard_markup 
        await update.message.reply_text(result_msg, reply_markup=get_games_keyboard_markup(lang), parse_mode="Markdown")
        
    except Exception as e:
        logging.getLogger(__name__).error(f"TKM Error: {e}")
        from utils import send_temp_message
        await send_temp_message(update, user_id, TEXTS["error_occurred"][lang])
        await state.clear_user_states(user_id)

