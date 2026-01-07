
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
    GAME_NAMES, get_game_mode_keyboard, games_menu, get_games_keyboard_markup
)

# --- BLACKJACK (21) ---
CARD_VALUES = {'A': 11, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, '10': 10, 'J': 10, 'Q': 10, 'K': 10}
CARD_SUITS = ['♠️', '♥️', '♦️', '♣️']
CARD_RANKS = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']

def create_deck():
    deck = [(rank, suit) for suit in CARD_SUITS for rank in CARD_RANKS]
    random.shuffle(deck)
    return deck

def card_to_str(card):
    return f"{card[0]}{card[1]}"

def hand_to_str(hand):
    return " ".join([card_to_str(c) for c in hand])

def calculate_score(hand):
    score = 0
    aces = 0
    for card in hand:
        rank = card[0]
        score += CARD_VALUES[rank]
        if rank == 'A': aces += 1
    while score > 21 and aces:
        score -= 10
        aces -= 1
    return score

def get_blackjack_keyboard(lang):
    texts = {
        "tr": [["🃏 Kart Çek (Hit)", "✋ Dur (Stand)"], ["🔙 Oyun Odası"]],
        "en": [["🃏 Hit", "✋ Stand"], ["🔙 Game Room"]],
        "ru": [["🃏 Ещё (Hit)", "✋ Хватит (Stand)"], ["🔙 Игровая Комната"]]
    }
    return ReplyKeyboardMarkup(texts.get(lang, texts["en"]), resize_keyboard=True)

def format_blackjack_state(player_hand, dealer_hand, lang, hide_dealer=True):
    player_score = calculate_score(player_hand)
    labels = {
        "tr": {"you": "🎴 Senin Elin", "dealer": "🏦 Krupiye", "score": "Skor"},
        "en": {"you": "🎴 Your Hand", "dealer": "🏦 Dealer", "score": "Score"},
        "ru": {"you": "🎴 Твои Карты", "dealer": "🏦 Дилер", "score": "Счёт"}
    }
    l = labels.get(lang, labels["en"])
    
    if hide_dealer and len(dealer_hand) >= 2:
        dealer_display = f"{card_to_str(dealer_hand[0])} 🂠"
        dealer_score_text = "?"
    else:
        dealer_display = hand_to_str(dealer_hand)
        dealer_score_text = str(calculate_score(dealer_hand))
    
    return (
        f"{l['dealer']}: {dealer_display} ({l['score']}: {dealer_score_text})\n"
        f"{l['you']}: {hand_to_str(player_hand)} ({l['score']}: {player_score})"
    )

@rate_limit("games")
async def blackjack_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Blackjack için mod seçimi göster"""
    user_id = update.effective_user.id
    lang = await db.get_user_lang(user_id)
    
    await cleanup_context(context, user_id)
    try: await update.message.delete()
    except: pass
    
    await state.clear_user_states(user_id)
    await state.set_state(user_id, state.WAITING_FOR_GAME_MODE, {"game": "blackjack"})
    
    game_name = GAME_NAMES["blackjack"].get(lang, GAME_NAMES["blackjack"]["en"])
    msg_text = TEXTS["game_mode_select"][lang].format(game_name=game_name)
    
    sent_msg = await update.message.reply_text(
        msg_text,
        reply_markup=get_game_mode_keyboard(lang),
        parse_mode="Markdown"
    )
    await state.set_state(user_id, state.WAITING_FOR_GAME_MODE, {"game": "blackjack", "message_id": sent_msg.message_id})

async def start_blackjack_game(update: Update, context: ContextTypes.DEFAULT_TYPE, bet_amount: int = 0) -> None:
    await blackjack_deal(update, context, bet_amount)

async def handle_blackjack_bet(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    lang = await db.get_user_lang(user_id)
    text = update.message.text
    
    if is_back_button(text):
        await games_menu(update, context)
        return

    try: await update.message.delete()
    except: pass
    
    amount = 0
    coins = await asyncio.to_thread(db.get_user_coins, user_id)
    
    if "all" in text.lower() or "hepsini" in text.lower() or "ва-банк" in text.lower() or "🎯" in text:
        amount = coins
    else:
        import re
        match = re.search(r'\d+', text)
        if match: amount = int(match.group())
        else:
            await update.message.reply_text("❌ Invalid bet.")
            return
            
    if amount <= 0:
        await update.message.reply_text("❌ Invalid amount.")
        return
        
    if amount > coins:
        msg = TEXTS["insufficient_funds"][lang].format(amount=amount, balance=coins)
        await update.message.reply_text(msg)
        return
        
    await asyncio.to_thread(db.add_user_coins, user_id, -amount)
    bet_msg = TEXTS["bet_placed"][lang].format(amount=amount)
    await update.message.reply_text(bet_msg, parse_mode="Markdown")
    await blackjack_deal(update, context, amount)


from models.game_state import BlackjackState

# ... (imports remain) ...

async def blackjack_deal(update: Update, context: ContextTypes.DEFAULT_TYPE, bet_amount: int) -> None:
    user_id = update.effective_user.id
    lang = await db.get_user_lang(user_id)
    
    await cleanup_context(context, user_id)
    deck = create_deck()
    player_hand = [deck.pop(), deck.pop()]
    dealer_hand = [deck.pop(), deck.pop()]
    
    await state.clear_user_states(user_id)
    
    # Use Model
    bj_state = BlackjackState(
        deck=deck, 
        player_hand=player_hand, 
        dealer_hand=dealer_hand, 
        bet_amount=bet_amount
    )
    
    # Check natural blackjack immediately
    player_score = calculate_score(player_hand)
    
    welcome_texts = {
        "tr": "🃏 *Blackjack (21)*\n\nKart çekerek 21'e yaklaşmaya çalış!\n21'i geçersen kaybedersin.\n\n",
        "en": "🃏 *Blackjack (21)*\n\nTry to get as close to 21 as possible!\nGo over 21 and you lose.\n\n",
        "ru": "🃏 *Блэкджек (21)*\n\nПопробуй приблизиться к 21!\nПревысишь 21 — проиграешь.\n\n"
    }
    
    msg = welcome_texts.get(lang, welcome_texts["en"])
    msg += format_blackjack_state(player_hand, dealer_hand, lang, hide_dealer=True)
    msg += f"\n💰 Bet: {bet_amount}"
    
    if player_score == 21:
        msg += "\n\n🎉 BLACKJACK!"
        # Log outcome for blackjack is usually immediate win 3:2 or 2:1 depending on rules, handled in finish
        await finish_blackjack(update, context, player_hand, dealer_hand, deck, lang, user_id)
        return
    
    sent_message = await update.message.reply_text(msg, reply_markup=get_blackjack_keyboard(lang), parse_mode="Markdown")
    
    # Update message_id in state
    bj_state.message_id = sent_message.message_id
    await state.set_state(user_id, state.PLAYING_BLACKJACK, bj_state.to_dict())

async def handle_blackjack_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    text = update.message.text.lower()
    lang = await db.get_user_lang(user_id)
    
    game_data_dict = await state.get_data(user_id)
    if not game_data_dict: return
    
    # Restore state model
    bj_state = BlackjackState.from_dict(game_data_dict)
    
    if is_back_button(text):
        try:
            if bj_state.message_id: await context.bot.delete_message(chat_id=user_id, message_id=bj_state.message_id)
            await update.message.delete()
        except Exception: pass
        await state.clear_user_states(user_id)
        await games_menu(update, context)
        return
    
    # State is managing hands now
    # We can use bj_state.player_hand etc. directly
    
    # HIT
    if any(k in text for k in ["hit", "çek", "ещё", "kart"]):
        try: await update.message.delete()
        except: pass
        
        bj_state.player_hand.append(bj_state.deck.pop())
        player_score = calculate_score(bj_state.player_hand)
        
        if player_score > 21:
            await finish_blackjack(update, context, bj_state.player_hand, bj_state.dealer_hand, bj_state.deck, lang, user_id, bust=True, message_id=bj_state.message_id)
            return
        
        # Save updated state
        await state.set_state(user_id, state.PLAYING_BLACKJACK, bj_state.to_dict())
        
        msg = format_blackjack_state(bj_state.player_hand, bj_state.dealer_hand, lang, hide_dealer=True)
        if player_score == 21: msg += "\n\n21! ✨"
        
        if bj_state.message_id:
            try: await context.bot.edit_message_text(chat_id=user_id, message_id=bj_state.message_id, text=msg, reply_markup=get_blackjack_keyboard(lang), parse_mode="Markdown")
            except: await update.message.reply_text(msg, reply_markup=get_blackjack_keyboard(lang))
        else:
            await update.message.reply_text(msg, reply_markup=get_blackjack_keyboard(lang))
        return
    
    # STAND
    if any(k in text for k in ["stand", "dur", "хватит", "✋"]):
        try: await update.message.delete()
        except: pass
        await finish_blackjack(update, context, bj_state.player_hand, bj_state.dealer_hand, bj_state.deck, lang, user_id, message_id=bj_state.message_id)
        return
    
    invalid_texts = {"tr": "Lütfen 'Kart Çek' veya 'Dur' butonlarını kullan.", "en": "Please use 'Hit' or 'Stand' buttons.", "ru": "Используйте кнопки 'Ещё' или 'Хватит'."}
    await update.message.reply_text(invalid_texts.get(lang, invalid_texts["en"]))


async def finish_blackjack(update, context, player_hand, dealer_hand, deck, lang, user_id, bust=False, message_id=None):
    player_score = calculate_score(player_hand)
    if not bust:
        while calculate_score(dealer_hand) < 17:
            dealer_hand.append(deck.pop())
    
    dealer_score = calculate_score(dealer_hand)
    
    game_result = "lose"
    result_key = "lose"
    
    if bust:
        result_key = "bust"
        game_result = "lose"
    elif dealer_score > 21:
        result_key = "dealer_bust"
        game_result = "win"
    elif player_score > dealer_score:
        result_key = "win"
        game_result = "win"
    elif player_score < dealer_score:
        result_key = "lose"
        game_result = "lose"
    else:
        result_key = "tie"
        game_result = "draw"
        
    # Reward
    game_data = await state.get_data(user_id)
    bet_amount = game_data.get("bet_amount", 0)
    reward = 0
    if game_result == "win":
        reward = bet_amount * 2
        await asyncio.to_thread(db.add_user_coins, user_id, reward)
    elif game_result == "draw":
        reward = bet_amount
        await asyncio.to_thread(db.add_user_coins, user_id, reward)
        
    msg = format_blackjack_state(player_hand, dealer_hand, lang, hide_dealer=False)
    
    result_texts = {
        "tr": {"bust": "💥 Battın! 21'i geçtin.", "win": "🎉 Kazandın!", "lose": "😞 Kaybettin!", "tie": "🤝 Berabere!", "dealer_bust": "🎉 Krupiye battı, sen kazandın!"},
        "en": {"bust": "💥 Bust! You went over 21.", "win": "🎉 You win!", "lose": "😞 You lose!", "tie": "🤝 It's a tie!", "dealer_bust": "🎉 Dealer busts, you win!"},
        "ru": {"bust": "💥 Перебор! Ты превысил 21.", "win": "🎉 Ты выиграл!", "lose": "😞 Ты проиграл!", "tie": "🤝 Ничья!", "dealer_bust": "🎉 У дилера перебор, ты выиграл!"}
    }
    r = result_texts.get(lang, result_texts["en"])
    result_text = r.get(result_key, result_key)
    
    if reward > 0:
        if game_result == "win": msg += f"\n\n{result_text}\n💰 +{reward} Coins"
        else: msg += f"\n\n{result_text}\n💰 +{reward} Coins (Refund)"
    else:
        msg += f"\n\n{result_text}"
    
    if message_id:
        try:
            await context.bot.edit_message_text(chat_id=user_id, message_id=message_id, text=msg, reply_markup=get_games_keyboard_markup(lang), parse_mode="Markdown")
        except: await update.message.reply_text(msg, reply_markup=get_games_keyboard_markup(lang), parse_mode="Markdown")
    else:
        await update.message.reply_text(msg, reply_markup=get_games_keyboard_markup(lang), parse_mode="Markdown")
    
    await asyncio.to_thread(db.log_blackjack_game, user_id, player_score, dealer_score, game_result)
    await asyncio.sleep(0.5)
    await state.clear_user_states(user_id)
