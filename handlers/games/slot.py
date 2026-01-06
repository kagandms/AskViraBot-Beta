
import asyncio
import logging
import random
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
import database as db
import state
from texts import TEXTS
from utils import is_back_button, cleanup_context
from rate_limiter import rate_limit

from handlers.games.core import (
    GAME_NAMES, get_game_mode_keyboard, get_bet_keyboard_generic, 
    games_menu, parse_bet_amount, get_all_in_amount
)

# --- SLOT MAKİNESİ ---
SLOT_SYMBOLS = ["🍎", "🍋", "🍒", "🍇", "🔔", "⭐", "💎", "7️⃣"]
SLOT_JACKPOT = "7️⃣"

def get_slot_keyboard(lang):
    """Slot makinesi klavyesi"""
    spin_texts = {"tr": "🎰 ÇEVİR!", "en": "🎰 SPIN!", "ru": "🎰 КРУТИТЬ!"}
    back_texts = {"tr": "🔙 Oyun Odası", "en": "🔙 Game Room", "ru": "🔙 Игровая Комната"}
    return ReplyKeyboardMarkup([
        [spin_texts.get(lang, spin_texts["en"])],
        [back_texts.get(lang, back_texts["en"])]
    ], resize_keyboard=True)

@rate_limit("games")
async def slot_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Slot makinesi için mod seçimi göster"""
    user_id = update.effective_user.id
    lang = await asyncio.to_thread(db.get_user_lang, user_id)
    
    await cleanup_context(context, user_id)
    try: await update.message.delete()
    except: pass
    
    await state.clear_user_states(user_id)
    await state.set_state(user_id, state.WAITING_FOR_GAME_MODE, {"game": "slot"})
    
    game_name = GAME_NAMES["slot"].get(lang, GAME_NAMES["slot"]["en"])
    msg_text = TEXTS["game_mode_select"][lang].format(game_name=game_name)
    
    sent_msg = await update.message.reply_text(
        msg_text,
        reply_markup=get_game_mode_keyboard(lang),
        parse_mode="Markdown"
    )
    await state.set_state(user_id, state.WAITING_FOR_GAME_MODE, {"game": "slot", "message_id": sent_msg.message_id})

async def handle_slot_bet(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle Slot bet amount selection"""
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
    
    await state.clear_user_states(user_id)
    await start_slot_game(update, context, bet_amount=amount)


from models.game_state import SlotState

# ...

async def start_slot_game(update: Update, context: ContextTypes.DEFAULT_TYPE, bet_amount: int = 0) -> None:
    """Actually start the Slot game"""
    user_id = update.effective_user.id
    lang = await asyncio.to_thread(db.get_user_lang, user_id)
    
    # Use Model
    slot_state = SlotState(bet_amount=bet_amount)
    
    if bet_amount > 0:
        welcome = {
            "tr": f"🎰 *Slot Makinesi*\n\n💰 Spin başı: *{bet_amount} Coin*\n\n🎲 2 aynı = x2 | 3 aynı = x5 | Jackpot = x50\n\nÇevirmek için butona bas!",
            "en": f"🎰 *Slot Machine*\n\n💰 Per spin: *{bet_amount} Coins*\n\n🎲 2 match = x2 | 3 match = x5 | Jackpot = x50\n\nPress button to spin!",
            "ru": f"🎰 *Слот Машина*\n\n💰 За спин: *{bet_amount} монет*\n\n🎲 2 совпадения = x2 | 3 = x5 | Джекпот = x50\n\nНажми кнопку!"
        }
    else:
        welcome = {
            "tr": "🎰 *Slot Makinesi (Eğlence)*\n\n3 aynı sembol = Kazandın!\n7️⃣ 7️⃣ 7️⃣ = JACKPOT!\n\nÇevirmek için butona bas!",
            "en": "🎰 *Slot Machine (Fun Mode)*\n\n3 matching symbols = You win!\n7️⃣ 7️⃣ 7️⃣ = JACKPOT!\n\nPress the button to spin!",
            "ru": "🎰 *Слот Машина (Для удовольствия)*\n\n3 одинаковых = Победа!\n7️⃣ 7️⃣ 7️⃣ = ДЖЕКПОТ!\n\nНажми кнопку!"
        }
    
    sent_msg = await update.message.reply_text(
        welcome.get(lang, welcome["en"]),
        reply_markup=get_slot_keyboard(lang),
        parse_mode="Markdown"
    )
    
    slot_state.message_id = sent_msg.message_id
    await state.set_state(user_id, state.PLAYING_SLOT, slot_state.to_dict())

async def slot_spin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Slot makinesini çevir (Animasyonlu)"""
    user_id = update.effective_user.id
    lang = await asyncio.to_thread(db.get_user_lang, user_id)
    text = update.message.text.lower() if update.message.text else ""
    
    if is_back_button(text):
        await cleanup_context(context, user_id)
        try: await update.message.delete()
        except: pass
        await state.clear_user_states(user_id)
        await games_menu(update, context)
        return
    
    spin_keywords = ["çevir", "spin", "крутить", "🎰"]
    if not any(k in text for k in spin_keywords):
        return

    try: await update.message.delete()
    except: pass
    
    game_data_dict = await state.get_data(user_id)
    slot_state = SlotState.from_dict(game_data_dict)
    bet_amount = slot_state.bet_amount
    
    if bet_amount > 0:
        current_coins = await asyncio.to_thread(db.get_user_coins, user_id)
        if current_coins < bet_amount:
            msg = TEXTS["insufficient_funds"][lang].format(amount=bet_amount, balance=current_coins)
            await update.message.reply_text(msg)
            return
        await asyncio.to_thread(db.add_user_coins, user_id, -bet_amount)

    slots = ["🍒", "🍋", "🍇", "🍊", "💎", "7️⃣"]
    message_id = slot_state.message_id
    
    for _ in range(3):
        temp_result = [random.choice(slots) for _ in range(3)]
        temp_text = f"🎰 *Slot Machine*\n\n   {'   '.join(temp_result)}\n\n🔄 Spinning..."
        if message_id:
            try:
                await context.bot.edit_message_text(
                    chat_id=user_id, message_id=message_id, text=temp_text,
                    reply_markup=get_slot_keyboard(lang), parse_mode="Markdown"
                )
            except: pass
        await asyncio.sleep(0.5)

    chance = random.randint(1, 100)
    if chance == 1: final_result = ["7️⃣", "7️⃣", "7️⃣"]
    elif chance <= 20:
        symbol = random.choice(slots)
        final_result = [symbol, symbol, symbol]
    elif chance <= 50:
        symbol = random.choice(slots)
        final_result = [symbol, symbol, random.choice([s for s in slots if s != symbol])]
        random.shuffle(final_result)
    else:
        final_result = [random.choice(slots) for _ in range(3)]
        if final_result[0] == final_result[1] == final_result[2]:
             final_result[2] = random.choice([s for s in slots if s != final_result[0]])
    
    result_line = "   ".join(final_result)
    multiplier = 0
    outcome_text = ""
    
    if final_result == ["7️⃣", "7️⃣", "7️⃣"]:
        multiplier = 50
        outcome_text = "JACKPOT!!! 💰💰💰"
    elif final_result[0] == final_result[1] == final_result[2]:
        multiplier = 5
        outcome_text = "WIN!! 🎉"
    elif final_result[0] == final_result[1] or final_result[1] == final_result[2] or final_result[0] == final_result[2]:
        multiplier = 2
        outcome_text = "Nice! 2 Match 👍"
    else:
        outcome_text = "Lost... 📉"
    
    reward = 0
    win_msg = ""
    
    if bet_amount > 0:
        if multiplier > 0:
            reward = bet_amount * multiplier
            await asyncio.to_thread(db.add_user_coins, user_id, reward)
            win_msg = TEXTS["game_win_coins"][lang].format(amount=reward, multiplier=multiplier)
        else:
            win_msg = TEXTS["game_lose_coins"][lang].format(amount=bet_amount)
        new_balance = await asyncio.to_thread(db.get_user_coins, user_id)
        final_text = f"🎰 *Slot Machine*\n\n   {result_line}\n\n{outcome_text}\n{win_msg}\n\n💰 Bakiye: {new_balance}"
    else:
        final_text = f"🎰 *Slot Machine (Fun)*\n\n   {result_line}\n\n{outcome_text}"
    
    await asyncio.to_thread(db.log_slot_game, user_id, f"{final_result[0]}{final_result[1]}{final_result[2]}", "win" if multiplier > 0 else "lose")

    if message_id:
        try:
            await context.bot.edit_message_text(
                chat_id=user_id, message_id=message_id, text=final_text,
                reply_markup=get_slot_keyboard(lang), parse_mode="Markdown"
            )
        except: 
            sent_msg = await update.message.reply_text(final_text, reply_markup=get_slot_keyboard(lang), parse_mode="Markdown")
            message_id = sent_msg.message_id
    else:
        sent_msg = await update.message.reply_text(final_text, reply_markup=get_slot_keyboard(lang), parse_mode="Markdown")
        message_id = sent_msg.message_id
    
    slot_state.message_id = message_id
    await state.set_state(user_id, state.PLAYING_SLOT, slot_state.to_dict())

