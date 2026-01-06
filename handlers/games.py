import asyncio
import logging
import random
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import database as db
import state
from texts import TEXTS, TKM_BUTTONS, BUTTON_MAPPINGS, GAMES_BUTTONS, GAME_MODE_BUTTONS, BET_BUTTONS
from utils import get_games_keyboard_markup, is_back_button, cleanup_context
from rate_limiter import rate_limit

# --- OYUNLAR MENÜSÜ ---
@rate_limit("games")
async def games_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Oyunlar Alt Menüsünü Açar"""
    user_id = update.effective_user.id
    # DB İŞLEMİ: Asenkron
    lang = await asyncio.to_thread(db.get_user_lang, user_id)
    
    # Önceki oyun mesajlarını temizle
    await cleanup_context(context, user_id)
    
    # Delete user's button press
    try:
        await update.message.delete()
    except: pass
    
    await state.clear_user_states(user_id)
    await state.set_state(user_id, state.GAMES_MENU_ACTIVE)
    
    msg = await update.message.reply_text(
        TEXTS["games_menu_prompt"][lang], 
        reply_markup=get_games_keyboard_markup(lang)
    )
    
    # Mesaj ID'sini kaydet
    await state.set_state(user_id, state.GAMES_MENU_ACTIVE, {"message_id": msg.message_id})

# --- OYUNCU İSTATİSTİKLERİ ---
@rate_limit("games")
async def show_player_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Oyuncunun oyun istatistiklerini gösterir"""
    user_id = update.effective_user.id
    lang = await asyncio.to_thread(db.get_user_lang, user_id)
    
    # Cleanup previous context (e.g. game room menu)
    await cleanup_context(context, user_id)
    
    # Delete user's button press
    try:
        await update.message.delete()
    except: pass
    
    # İstatistikleri çek
    xox_stats = await asyncio.to_thread(db.get_user_xox_stats, user_id)
    tkm_stats = await asyncio.to_thread(db.get_user_tkm_stats, user_id)
    bj_stats = await asyncio.to_thread(db.get_user_blackjack_stats, user_id)
    
    # Başlıklar
    headers = {
        "tr": {"title": "📊 *Oyun İstatistikleriniz*", "win": "✅ Kazanma", "lose": "❌ Kaybetme", "draw": "🤝 Berabere", "total": "Toplam"},
        "en": {"title": "📊 *Your Game Stats*", "win": "✅ Wins", "lose": "❌ Losses", "draw": "🤝 Draws", "total": "Total"},
        "ru": {"title": "📊 *Ваша Статистика*", "win": "✅ Победы", "lose": "❌ Поражения", "draw": "🤝 Ничьи", "total": "Всего"}
    }
    h = headers.get(lang, headers["en"])
    
    def format_stats(name, stats):
        return (
            f"*{name}*\n"
            f"  {h['win']}: {stats['wins']} | {h['lose']}: {stats['losses']} | {h['draw']}: {stats['draws']}\n"
            f"  {h['total']}: {stats['total']}"
        )
    
    msg_text = f"{h['title']}\n\n"
    msg_text += f"❌⭕ {format_stats('XOX', xox_stats)}\n\n"
    msg_text += f"🪨📄✂️ {format_stats('Taş-Kağıt-Makas', tkm_stats)}\n\n"
    msg_text += f"🃏 {format_stats('Blackjack', bj_stats)}"
    
    sent_msg = await update.message.reply_text(msg_text, reply_markup=get_games_keyboard_markup(lang), parse_mode="Markdown")
    
    # Mesaj ID'sini kaydet - çıkışta silinmesi için
    await state.set_state(user_id, state.GAMES_MENU_ACTIVE, {"message_id": sent_msg.message_id})


# --- XOX (TIC TAC TOE) - REPLY KEYBOARD VERSION ---
# ... (Helper functions remain same until xox_start) ...
def get_xox_board_reply_markup(board):
    """3x3 XOX tahtası (Reply Keyboard) - Numaralı"""
    keyboard = []
    mapping = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣"]
    
    current_row = []
    for i in range(9):
        cell = board[i]
        if cell == " ":
            text = mapping[i]
        else:
            text = "❌" if cell == "X" else "⭕"
        current_row.append(text)
        if len(current_row) == 3:
            keyboard.append(current_row)
            current_row = []
            
    # Çıkış butonu
    keyboard.append(["🔙 Oyunlar Menüsü"])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_xox_difficulty_reply_markup(lang):
    """Zorluk seçimi için Reply keyboard"""
    texts = {
        "tr": ["🟢 Kolay", "🟡 Orta", "🔴 Zor"],
        "en": ["🟢 Easy", "🟡 Medium", "🔴 Hard"],
        "ru": ["🟢 Легко", "🟡 Средне", "🔴 Сложно"]
    }
    labels = texts.get(lang, texts["en"])
    back_texts = {"tr": "🔙 Oyun Odası", "en": "🔙 Game Room", "ru": "🔙 Игровая Комната"}
    back = back_texts.get(lang, back_texts["en"])
    
    keyboard = [
        [labels[0], labels[1], labels[2]],
        [back]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# ... (check_winner, bot_move functions remain same) ...
def check_winner(board):
    wins = [(0,1,2), (3,4,5), (6,7,8), (0,3,6), (1,4,7), (2,5,8), (0,4,8), (2,4,6)]
    for a, b, c in wins:
        if board[a] == board[b] == board[c] and board[a] != " ":
            return board[a]
    if " " not in board: return "Draw"
    return None

def bot_move_easy(board):
    empty = [i for i, x in enumerate(board) if x == " "]
    return random.choice(empty) if empty else None

def bot_move_medium(board):
    wins = [(0,1,2), (3,4,5), (6,7,8), (0,3,6), (1,4,7), (2,5,8), (0,4,8), (2,4,6)]
    for a, b, c in wins:
        line = [board[a], board[b], board[c]]
        if line.count("O") == 2 and line.count(" ") == 1: return [a, b, c][line.index(" ")]
    for a, b, c in wins:
        line = [board[a], board[b], board[c]]
        if line.count("X") == 2 and line.count(" ") == 1: return [a, b, c][line.index(" ")]
    if board[4] == " ": return 4
    corners = [i for i in [0, 2, 6, 8] if board[i] == " "]
    if corners: return random.choice(corners)
    return bot_move_easy(board)

def minimax(board, is_maximizing):
    winner = check_winner(board)
    if winner == "O": return 10
    if winner == "X": return -10
    if winner == "Draw": return 0
    if is_maximizing:
        best = -float('inf')
        for i in range(9):
            if board[i] == " ":
                board[i] = "O"
                score = minimax(board, False)
                board[i] = " "
                best = max(best, score)
        return best
    else:
        best = float('inf')
        for i in range(9):
            if board[i] == " ":
                board[i] = "X"
                score = minimax(board, True)
                board[i] = " "
                best = min(best, score)
        return best

def bot_move_hard(board):
    best_score = -float('inf')
    best_move = None
    for i in range(9):
        if board[i] == " ":
            board[i] = "O"
            score = minimax(board, False)
            board[i] = " "
            if score > best_score:
                best_score = score
                best_move = i
    return best_move

def bot_make_move(board, difficulty="easy"):
    if difficulty == "easy": return bot_move_easy(board)
    elif difficulty == "medium": return bot_move_medium(board)
    else: return bot_move_hard(board)

@rate_limit("games")
async def xox_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Zorluk seçimini başlat (Reply Keyboard)"""
    user_id = update.effective_user.id
    lang = await asyncio.to_thread(db.get_user_lang, user_id)
    
    # Cleanup previous context
    await cleanup_context(context, user_id)
    
    # Delete user's button press
    try:
        await update.message.delete()
    except: pass
    
    # State ayarla
    await state.clear_user_states(user_id)
    initial_game_state = {"board": [" "]*9, "difficulty": None, "active": False}
    await state.set_state(user_id, state.PLAYING_XOX, initial_game_state)
    
    # Zorluk seçim metni
    difficulty_prompt = {
        "tr": "🎮 XOX Oyunu\n\nZorluk seviyesi seçin:",
        "en": "🎮 XOX Game\n\nSelect difficulty level:",
        "ru": "🎮 Игра XOX\n\nВыберите уровень сложности:"
    }
    
    sent_message = await update.message.reply_text(
        difficulty_prompt.get(lang, difficulty_prompt["en"]),
        reply_markup=get_xox_difficulty_reply_markup(lang)
    )
    
    # Update state with message id (requires fetching current state first if we want to preserve other fields, but here we are initializing)
    # Actually, we set initial state just above. Let's update it.
    initial_game_state["message_id"] = sent_message.message_id
    await state.set_state(user_id, state.PLAYING_XOX, initial_game_state)

async def handle_xox_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """XOX hamlelerini ve seçimlerini yönetir"""
    user_id = update.effective_user.id
    # State zaten main.py'de kontrol edildi
        
    text = update.message.text
    lang = await asyncio.to_thread(db.get_user_lang, user_id)
    
    # Retrieve game state from DB
    game_state = await state.get_data(user_id)
    if not game_state: # Should not happen if check_state passed
        return

    # ÇIKIŞ / GERİ KONTROLÜ
    if is_back_button(text):
        # Kullanıcı mesajını sil
        try:
            await update.message.delete()
        except Exception: pass
        
        # Önceki mesajı da sil
        if "message_id" in game_state:
            try:
                await context.bot.delete_message(chat_id=user_id, message_id=game_state["message_id"])
            except: pass
        
        await state.clear_user_states(user_id)
        await games_menu(update, context)
        return
        
    # ZORLUK SEÇİMİ
    text_lower = text.lower()
    if not game_state.get("active"):
        selected_diff = None
        
        if "kolay" in text_lower or "easy" in text_lower or "легко" in text_lower:
            selected_diff = "easy"
        elif "orta" in text_lower or "medium" in text_lower or "средне" in text_lower:
            selected_diff = "medium"
        elif "zor" in text_lower or "hard" in text_lower or "сложно" in text_lower:
            selected_diff = "hard"
        
        if selected_diff:
            game_state["difficulty"] = selected_diff
            game_state["active"] = True
            
            # Zorluk metinleri
            diff_texts = {
                "easy": {"tr": "Kolay", "en": "Easy", "ru": "Легко"},
                "medium": {"tr": "Orta", "en": "Medium", "ru": "Средне"},
                "hard": {"tr": "Zor", "en": "Hard", "ru": "Сложно"}
            }
            d_text = diff_texts[selected_diff].get(lang, diff_texts[selected_diff]["en"])
            
            # Cleanup: Delete user's "Easy/Medium/Hard" message
            try:
                await update.message.delete()
            except: pass
            
            # Cleanup: Delete "Select Difficulty" prompt
            # (Retrieve ID from state or context if available, or just cleanup_context)
            # Since we are in the same handler session, we can use cleanup_context if it targets the right things.
            # But cleanup_context uses stored "message_id".
            # Initial state had "message_id" of prompt.
            if "message_id" in game_state:
                try:
                    await context.bot.delete_message(chat_id=user_id, message_id=game_state["message_id"])
                except: pass
            
            # Send Welcome with Mode
            # "XOX (...) - Kolay oyununa hoş geldin!"
            welcome_text = f"{TEXTS['xox_welcome'][lang]} - {d_text}"
            
            board_msg = await update.message.reply_text(
                welcome_text,
                reply_markup=get_xox_board_reply_markup(game_state["board"])
            )
            
            # Save Board Message ID for future updates
            game_state["message_id"] = board_msg.message_id
            await state.set_state(user_id, state.PLAYING_XOX, game_state)
            
        else:
            await update.message.reply_text(TEXTS["xox_invalid_move"][lang])
        return

    # OYUN HAMLESİ
    mapping = {"1️⃣": 0, "2️⃣": 1, "3️⃣": 2, "4️⃣": 3, "5️⃣": 4, "6️⃣": 5, "7️⃣": 6, "8️⃣": 7, "9️⃣": 8}
    move_index = mapping.get(text.strip())
    
    if move_index is None:
        for emoji, idx in mapping.items():
            if emoji in text:
                move_index = idx
                break
    
    if move_index is None:
        text_clean = text.strip()
        if text_clean in ["1", "2", "3", "4", "5", "6", "7", "8", "9"]:
            move_index = int(text_clean) - 1
    
    if move_index is None:
        await update.message.reply_text(TEXTS["xox_invalid_move"][lang])
        return
        
    board = game_state["board"]
    
    if board[move_index] != " ":
        await update.message.reply_text(TEXTS["xox_invalid_move"][lang])
        return
        
    # KULLANICI HAMLESİ (X)
    board[move_index] = "X"
    winner = check_winner(board)
    
    if winner:
        await finish_get_xox_game(update, context, board, winner, lang, user_id, game_state["difficulty"])
        return
        
    # BOT HAMLESİ (O)
    bot_move = bot_make_move(board, game_state["difficulty"])
    if bot_move is not None:
        board[bot_move] = "O"
        winner = check_winner(board)
        if winner:
            await finish_get_xox_game(update, context, board, winner, lang, user_id, game_state["difficulty"])
            return
            
    # OYUN DEVAM -> DB GÜNCELLE
    game_state["board"] = board
    
    # 1. Kullanıcı hamle mesajını sil ("1", "5" vb)
    try:
        await update.message.delete()
    except: pass
    
    # 2. Eski board mesajını sil
    if "message_id" in game_state:
        try:
            await context.bot.delete_message(chat_id=user_id, message_id=game_state["message_id"])
        except: pass
        
    # 3. Yeni board gönder
    new_board_msg = await update.message.reply_text(
        TEXTS["xox_bot_moved"][lang] if "xox_bot_moved" in TEXTS else "Bot played.",
        reply_markup=get_xox_board_reply_markup(board)
    )
    
    # 4. Yeni ID'yi kaydet
    game_state["message_id"] = new_board_msg.message_id
    await state.set_state(user_id, state.PLAYING_XOX, game_state)

async def finish_get_xox_game(update, context, board, winner, lang, user_id, difficulty):
    """Oyunu bitir"""
    msg = ""
    if winner == "X": msg = TEXTS["xox_win"][lang]
    elif winner == "O": msg = TEXTS["xox_lose"][lang]
    else: msg = TEXTS["xox_draw"][lang]
    
    # Clean up previous board message if it exists
    try:
        game_state = await state.get_data(user_id)
        if game_state and "message_id" in game_state:
            await context.bot.delete_message(chat_id=user_id, message_id=game_state["message_id"])
    except: pass
    
    await update.message.reply_text(
        msg,
        reply_markup=get_xox_board_reply_markup(board)
    )
    
    await asyncio.to_thread(db.log_xox_game, user_id, winner, difficulty)
    
    await asyncio.sleep(0.5)
    await state.clear_user_states(user_id)
    await games_menu(update, context)



# --- DİĞER OYUNLAR ---
@rate_limit("games")
async def dice_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    lang = await asyncio.to_thread(db.get_user_lang, user_id)
    number = random.randint(1, 6)
    await asyncio.to_thread(db.log_dice_roll, user_id, number)
    
    # Delete user's button press
    try:
        await update.message.delete()
    except: pass
    
    # Send result (stays on screen)
    await update.message.reply_text(TEXTS["dice_rolled"][lang].format(number=number), reply_markup=get_games_keyboard_markup(lang))

@rate_limit("games")
async def coinflip_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    lang = await asyncio.to_thread(db.get_user_lang, user_id)
    result = random.choice(["heads", "tails"])
    await asyncio.to_thread(db.log_coinflip, user_id, result)
    translations = {"tr": {"heads": "Yazı", "tails": "Tura"}, "en": {"heads": "Heads", "tails": "Tails"}, "ru": {"heads": "Орёл", "tails": "Решка"}}
    
    # Delete user's button press
    try:
        await update.message.delete()
    except: pass
    
    # Send result (stays on screen)
    await update.message.reply_text(TEXTS["coinflip_result"][lang].format(result=translations[lang][result]), reply_markup=get_games_keyboard_markup(lang))

# --- TAŞ KAĞIT MAKAS (GÜNCELLENDİ) ---

# Helper: Get game mode keyboard
def get_game_mode_keyboard(lang):
    buttons = GAME_MODE_BUTTONS.get(lang, GAME_MODE_BUTTONS["en"])
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

# Helper: Get bet keyboard
def get_bet_keyboard_generic(lang):
    buttons = BET_BUTTONS.get(lang, BET_BUTTONS["en"])
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

# Game Names for display
GAME_NAMES = {
    "tkm": {"tr": "Taş Kağıt Makas", "en": "Rock Paper Scissors", "ru": "Камень Ножницы Бумага"},
    "slot": {"tr": "Slot Makinesi", "en": "Slot Machine", "ru": "Слот Машина"},
    "blackjack": {"tr": "Blackjack (21)", "en": "Blackjack (21)", "ru": "Блэкджек (21)"}
}

@rate_limit("games")
async def tkm_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """TKM oyunu için mod seçimi göster"""
    user_id = update.effective_user.id
    lang = await asyncio.to_thread(db.get_user_lang, user_id)
    
    # Cleanup
    await cleanup_context(context, user_id)
    
    # Delete user's button press
    try:
        await update.message.delete()
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
        try:
            await update.message.delete()
        except: pass
        await state.clear_user_states(user_id)
        await games_menu(update, context)
        return
    
    # Delete user input
    try:
        await update.message.delete()
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
        
        # Store message_id for cleanup
        await state.set_state(user_id, 
            state.WAITING_FOR_TKM_BET if game == "tkm" else 
            state.WAITING_FOR_SLOT_BET if game == "slot" else 
            state.WAITING_FOR_BJ_BET, 
            {"message_id": sent_msg.message_id}
        )
    else:
        # Invalid selection - ignore
        pass

async def handle_tkm_bet(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle TKM bet amount selection"""
    user_id = update.effective_user.id
    lang = await asyncio.to_thread(db.get_user_lang, user_id)
    text = update.message.text if update.message.text else ""
    
    # Back check
    if is_back_button(text):
        await cleanup_context(context, user_id)
        try:
            await update.message.delete()
        except: pass
        await state.clear_user_states(user_id)
        await games_menu(update, context)
        return
    
    # Delete user input
    try:
        await update.message.delete()
    except: pass
    
    # Parse bet amount
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
    
    # Deduct bet
    await asyncio.to_thread(db.add_user_coins, user_id, -amount)
    
    # Start game
    await state.clear_user_states(user_id)
    await start_tkm_game(update, context, bet_amount=amount)

def parse_bet_amount(text: str, user_id: int) -> int | None:
    """Extract numeric bet amount from text"""
    import re
    match = re.search(r'\d+', text)
    if match:
        return int(match.group())
    return None

async def get_all_in_amount(text: str, user_id: int) -> int | None:
    """Check if user wants all-in and return their balance"""
    all_in_keywords = ["hepsini", "all in", "ва-банк", "🎯"]
    if any(k in text.lower() for k in all_in_keywords):
        return await asyncio.to_thread(db.get_user_coins, user_id)
    return None

async def start_tkm_game(update: Update, context: ContextTypes.DEFAULT_TYPE, bet_amount: int = 0) -> None:
    """Actually start the TKM game"""
    user_id = update.effective_user.id
    lang = await asyncio.to_thread(db.get_user_lang, user_id)
    
    await state.set_state(user_id, state.PLAYING_TKM, {"bet_amount": bet_amount})
    
    buttons = TKM_BUTTONS.get(lang, TKM_BUTTONS["en"])
    
    welcome_text = TEXTS["tkm_welcome"][lang]
    if bet_amount > 0:
        welcome_text += f"\n\n💰 Bahsin: *{bet_amount} Coin* (Kazanırsan x2)"
    
    sent_msg = await update.message.reply_text(
        welcome_text, 
        reply_markup=ReplyKeyboardMarkup(buttons, resize_keyboard=True),
        parse_mode="Markdown"
    )
    await state.set_state(user_id, state.PLAYING_TKM, {"message_id": sent_msg.message_id, "bet_amount": bet_amount})

async def tkm_play(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    lang = "en"
    try:
        lang = await asyncio.to_thread(db.get_user_lang, user_id)
        user_move_raw = update.message.text.lower().strip()
        
        if is_back_button(user_move_raw):
            try:
                # Retrieve state data to get message ID
                st_data = await state.get_data(user_id)
                if "message_id" in st_data:
                    await context.bot.delete_message(chat_id=user_id, message_id=st_data["message_id"])
                await update.message.delete()
            except Exception:
                pass
                
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
        
        # --- COIN PROCESSING ---
        st_data = await state.get_data(user_id)
        bet_amount = st_data.get("bet_amount", 0)
        
        if bet_amount > 0:
            if result_status == "win":
                # x2 multiplier
                winnings = bet_amount * 2
                await asyncio.to_thread(db.add_user_coins, user_id, winnings)
                result_msg += "\n\n" + TEXTS["game_win_coins"][lang].format(amount=winnings, multiplier=2)
            elif result_status == "draw":
                # Refund bet
                await asyncio.to_thread(db.add_user_coins, user_id, bet_amount)
                result_msg += "\n\n" + TEXTS["game_draw_refund"][lang].format(amount=bet_amount)
            else:  # lose
                # Bet already deducted
                result_msg += "\n\n" + TEXTS["game_lose_coins"][lang].format(amount=bet_amount)
        # -----------------------

        await state.clear_user_states(user_id)
        await update.message.reply_text(result_msg, reply_markup=get_games_keyboard_markup(lang), parse_mode="Markdown")
        
    except Exception as e:
        logging.getLogger(__name__).error(f"TKM Error: {e}")
        from utils import send_temp_message
        await send_temp_message(update, user_id, TEXTS["error_occurred"][lang])
        await state.clear_user_states(user_id)

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
    
    # Cleanup
    await cleanup_context(context, user_id)
    
    # Delete user's button press
    try:
        await update.message.delete()
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
    
    # Back check
    if is_back_button(text):
        await cleanup_context(context, user_id)
        try:
            await update.message.delete()
        except: pass
        await state.clear_user_states(user_id)
        await games_menu(update, context)
        return
    
    # Delete user input
    try:
        await update.message.delete()
    except: pass
    
    # Parse bet amount
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
    
    # Start game (bet will be deducted per spin)
    await state.clear_user_states(user_id)
    await start_slot_game(update, context, bet_amount=amount)

async def start_slot_game(update: Update, context: ContextTypes.DEFAULT_TYPE, bet_amount: int = 0) -> None:
    """Actually start the Slot game"""
    user_id = update.effective_user.id
    lang = await asyncio.to_thread(db.get_user_lang, user_id)
    
    await state.set_state(user_id, state.PLAYING_SLOT, {"bet_amount": bet_amount})
    
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
    
    await state.set_state(user_id, state.PLAYING_SLOT, {"message_id": sent_msg.message_id, "bet_amount": bet_amount})

async def slot_spin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Slot makinesini çevir (Animasyonlu)"""
    user_id = update.effective_user.id
    lang = await asyncio.to_thread(db.get_user_lang, user_id)
    text = update.message.text.lower() if update.message.text else ""
    
    # Geri kontrolü
    if is_back_button(text):
        # Cleanup previous context (slot welcome/result message)
        await cleanup_context(context, user_id)
        
        # Delete user's back button press
        try:
            await update.message.delete()
        except: pass
        
        await state.clear_user_states(user_id)
        await games_menu(update, context)
        return
    
    # Spin kontrolü
    spin_keywords = ["çevir", "spin", "крутить", "🎰"]
    if not any(k in text for k in spin_keywords):
        return

    # Delete user's spin button press
    try:
        await update.message.delete()
    except: pass
    
    # --- BETTING LOGIC ---
    st_data = await state.get_data(user_id)
    bet_amount = st_data.get("bet_amount", 0)
    
    # If betting mode, check and deduct funds per spin
    if bet_amount > 0:
        current_coins = await asyncio.to_thread(db.get_user_coins, user_id)
        
        if current_coins < bet_amount:
            msg = TEXTS["insufficient_funds"][lang].format(amount=bet_amount, balance=current_coins)
            await update.message.reply_text(msg)
            return
            
        # Deduct bet for this spin
        await asyncio.to_thread(db.add_user_coins, user_id, -bet_amount)
    # ---------------------

    slots = ["🍒", "🍋", "🍇", "🍊", "💎", "7️⃣"]
    
    # 1. Animasyon (Dönen slotlar)
    msg = await state.get_data(user_id)
    message_id = msg.get("message_id")
    
    # Basit animasyon (3 aşamalı)
    for _ in range(3):
        temp_result = [random.choice(slots) for _ in range(3)]
        temp_text = f"🎰 *Slot Machine*\n\n   {'   '.join(temp_result)}\n\n🔄 Spinning..."
        if message_id:
            try:
                await context.bot.edit_message_text(
                    chat_id=user_id,
                    message_id=message_id,
                    text=temp_text,
                    reply_markup=get_slot_keyboard(lang),
                    parse_mode="Markdown"
                )
            except: pass
        await asyncio.sleep(0.5)

    # 2. Sonuç Belirleme
    # Biraz hile yapalım (Kazanma şansını ayarla)
    chance = random.randint(1, 100)
    
    if chance == 1: # %1 İhtimalle Jackpot (777)
        final_result = ["7️⃣", "7️⃣", "7️⃣"]
    elif chance <= 20: # %19 İhtimalle 3'lü (Herhangi)
        symbol = random.choice(slots)
        final_result = [symbol, symbol, symbol]
    elif chance <= 50: # %30 İhtimalle 2'li
        symbol = random.choice(slots)
        final_result = [symbol, symbol, random.choice([s for s in slots if s != symbol])]
        random.shuffle(final_result)
    else: # Kayıp
        final_result = [random.choice(slots) for _ in range(3)]
        # Eğer şans eseri aynı geldiyse boz
        if final_result[0] == final_result[1] == final_result[2]:
             final_result[2] = random.choice([s for s in slots if s != final_result[0]])
    
    # 3. Sonuç Mesajı ve Ödül
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
    
    # Calculate reward based on bet_amount
    reward = 0
    win_msg = ""
    
    if bet_amount > 0:  # Coin mode
        if multiplier > 0:
            reward = bet_amount * multiplier
            await asyncio.to_thread(db.add_user_coins, user_id, reward)
            win_msg = TEXTS["game_win_coins"][lang].format(amount=reward, multiplier=multiplier)
        else:
            win_msg = TEXTS["game_lose_coins"][lang].format(amount=bet_amount)
        
        new_balance = await asyncio.to_thread(db.get_user_coins, user_id)
        final_text = f"🎰 *Slot Machine*\n\n   {result_line}\n\n{outcome_text}\n{win_msg}\n\n💰 Bakiye: {new_balance}"
    else:  # Fun mode
        final_text = f"🎰 *Slot Machine (Fun)*\n\n   {result_line}\n\n{outcome_text}"
    
    # Log game
    await asyncio.to_thread(db.log_slot_game, user_id, f"{final_result[0]}{final_result[1]}{final_result[2]}", "win" if multiplier > 0 else "lose")

    if message_id:
        try:
            await context.bot.edit_message_text(
                chat_id=user_id,
                message_id=message_id,
                text=final_text,
                reply_markup=get_slot_keyboard(lang),
                parse_mode="Markdown"
            )
        except: 
            await update.message.reply_text(final_text, reply_markup=get_slot_keyboard(lang), parse_mode="Markdown")
    else:
        await update.message.reply_text(final_text, reply_markup=get_slot_keyboard(lang), parse_mode="Markdown")
    
    # Keep state with bet_amount for next spin
    st_data["message_id"] = message_id
    await state.set_state(user_id, state.PLAYING_SLOT, st_data)


# --- BLACKJACK (21) ---
CARD_VALUES = {'A': 11, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, '10': 10, 'J': 10, 'Q': 10, 'K': 10}
CARD_SUITS = ['♠️', '♥️', '♦️', '♣️']
CARD_RANKS = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']

def create_deck():
    """52 kartlık deste oluştur"""
    deck = [(rank, suit) for suit in CARD_SUITS for rank in CARD_RANKS]
    random.shuffle(deck)
    return deck

def card_to_str(card):
    """Kartı görsel string'e çevir"""
    return f"{card[0]}{card[1]}"

def hand_to_str(hand):
    """Eli görsel string'e çevir"""
    return " ".join([card_to_str(c) for c in hand])

def calculate_score(hand):
    """El skorunu hesapla (As: 1 veya 11)"""
    score = 0
    aces = 0
    for card in hand:
        rank = card[0]
        score += CARD_VALUES[rank]
        if rank == 'A':
            aces += 1
    # As'ları 1 olarak say eğer 21'i aşıyorsa
    while score > 21 and aces:
        score -= 10
        aces -= 1
    return score

def get_blackjack_keyboard(lang):
    """Blackjack oyun klavyesi (Hit/Stand)"""
    texts = {
        "tr": [["🃏 Kart Çek (Hit)", "✋ Dur (Stand)"], ["🔙 Oyun Odası"]],
        "en": [["🃏 Hit", "✋ Stand"], ["🔙 Game Room"]],
        "ru": [["🃏 Ещё (Hit)", "✋ Хватит (Stand)"], ["🔙 Игровая Комната"]]
    }
    return ReplyKeyboardMarkup(texts.get(lang, texts["en"]), resize_keyboard=True)

def format_blackjack_state(player_hand, dealer_hand, lang, hide_dealer=True):
    """Oyun durumunu formatla"""
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


# Valid bet amounts
BJ_BETS = ["50", "100", "200", "500", "All In"]

def get_bet_keyboard(lang):
    """Bahis miktarı klavyesi"""
    # 3'lü satir
    row1 = [f"{b} Coin" for b in BJ_BETS[:3]]
    row2 = [f"{b} Coin" if b != "All In" else "All In" for b in BJ_BETS[3:]]
    from texts import BUTTON_MAPPINGS
    back_btn = "🔙 Back" # Fallback
    # Try to find back button text from mappings or strings
    # Simple hardcode for now or import
    back_key_map = {
        "tr": [["50", "100", "200"], ["500", "HEPSİ"], ["🔙 Ana Menü"]],
        "en": [["50", "100", "200"], ["500", "ALL IN"], ["🔙 Main Menu"]],
        "ru": [["50", "100", "200"], ["500", "ВА-БАНК"], ["🔙 Главное Меню"]]
    }
    return ReplyKeyboardMarkup(back_key_map.get(lang, back_key_map["en"]), resize_keyboard=True)

@rate_limit("games")
async def blackjack_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Blackjack için mod seçimi göster"""
    user_id = update.effective_user.id
    lang = await asyncio.to_thread(db.get_user_lang, user_id)
    
    # Cleanup previous context
    await cleanup_context(context, user_id)
    
    # Delete user's button press
    try:
        await update.message.delete()
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
    """Actually start the Blackjack game - Fun mode or after bet selection"""
    user_id = update.effective_user.id
    lang = await asyncio.to_thread(db.get_user_lang, user_id)
    
    # If betting mode, coins already deducted
    await blackjack_deal(update, context, bet_amount)


async def handle_blackjack_bet(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Blackjack bahis miktarını işle"""
    user_id = update.effective_user.id
    lang = await asyncio.to_thread(db.get_user_lang, user_id)
    text = update.message.text
    
    # Geri butonu kontrolü
    if is_back_button(text):
        await games_menu(update, context)
        return

    # Delete user input
    try:
        await update.message.delete()
    except: pass
    
    # Parse amount
    amount = 0
    coins = await asyncio.to_thread(db.get_user_coins, user_id)
    
    if "all" in text.lower() or "hepsini" in text.lower() or "ва-банк" in text.lower() or "🎯" in text:
        amount = coins
    else:
        # Extract number
        import re
        match = re.search(r'\d+', text)
        if match:
            amount = int(match.group())
        else:
            # Invalid input
            await update.message.reply_text("❌ Invalid bet.")
            return
            
    if amount <= 0:
        await update.message.reply_text("❌ Invalid amount.")
        return
        
    if amount > coins:
        msg = TEXTS["insufficient_funds"][lang].format(amount=amount, balance=coins)
        await update.message.reply_text(msg)
        return
        
    # Deduct bet and start game
    await asyncio.to_thread(db.add_user_coins, user_id, -amount)
    
    # Confirm bet msg (ephemeral)
    bet_msg = TEXTS["bet_placed"][lang].format(amount=amount)
    await update.message.reply_text(bet_msg, parse_mode="Markdown")
    
    # Start actual game
    await blackjack_deal(update, context, amount)


async def blackjack_deal(update: Update, context: ContextTypes.DEFAULT_TYPE, bet_amount: int) -> None:
    """Kartları dağıt ve oyunu başlat (Internal)"""
    user_id = update.effective_user.id
    lang = await asyncio.to_thread(db.get_user_lang, user_id)
    
    # Cleanup previous context (bet menu)
    await cleanup_context(context, user_id)
    
    # Deste oluştur ve kartları dağıt
    deck = create_deck()
    player_hand = [deck.pop(), deck.pop()]
    dealer_hand = [deck.pop(), deck.pop()]
    
    # State kaydet
    await state.clear_user_states(user_id)
    await state.set_state(user_id, state.PLAYING_BLACKJACK, {
        "deck": deck,
        "player_hand": player_hand,
        "dealer_hand": dealer_hand,
        "bet_amount": bet_amount
    })
    
    player_score = calculate_score(player_hand)
    
    welcome_texts = {
        "tr": "🃏 *Blackjack (21)*\n\nKart çekerek 21'e yaklaşmaya çalış!\n21'i geçersen kaybedersin.\n\n",
        "en": "🃏 *Blackjack (21)*\n\nTry to get as close to 21 as possible!\nGo over 21 and you lose.\n\n",
        "ru": "🃏 *Блэкджек (21)*\n\nПопробуй приблизиться к 21!\nПревысишь 21 — проиграешь.\n\n"
    }
    
    msg = welcome_texts.get(lang, welcome_texts["en"])
    msg += format_blackjack_state(player_hand, dealer_hand, lang, hide_dealer=True)
    msg += f"\n💰 Bet: {bet_amount}"
    
    # Blackjack kontrolü (ilk 2 kart = 21)
    if player_score == 21:
        msg += "\n\n🎉 BLACKJACK!"
        await finish_blackjack(update, context, player_hand, dealer_hand, deck, lang, user_id)
        return
    
    sent_message = await update.message.reply_text(msg, reply_markup=get_blackjack_keyboard(lang), parse_mode="Markdown")
    
    # Store message ID for cleanup
    # Need to update state because message_id is new
    await state.set_state(user_id, state.PLAYING_BLACKJACK, {
        "deck": deck,
        "player_hand": player_hand,
        "dealer_hand": dealer_hand,
        "bet_amount": bet_amount,
        "message_id": sent_message.message_id
    })

async def handle_blackjack_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Blackjack hamlelerini işle"""
    user_id = update.effective_user.id
    text = update.message.text.lower()
    lang = await asyncio.to_thread(db.get_user_lang, user_id)
    
    game_data = await state.get_data(user_id)
    if not game_data:
        return
    
    # Geri kontrolü
    # Geri kontrolü
    if is_back_button(text):
        # Cleanup messages
        try:
            if "message_id" in game_data:
                await context.bot.delete_message(chat_id=user_id, message_id=game_data["message_id"])
            await update.message.delete()
        except Exception:
            pass

        await state.clear_user_states(user_id)
        await games_menu(update, context)
        return
    
    deck = game_data["deck"]
    player_hand = game_data["player_hand"]
    dealer_hand = game_data["dealer_hand"]
    
    # HIT (Kart Çek)
    if any(k in text for k in ["hit", "çek", "ещё", "kart"]):
        # Delete user's button press
        try:
            await update.message.delete()
        except: pass
        
        player_hand.append(deck.pop())
        player_score = calculate_score(player_hand)
        
        # Bust kontrolü
        if player_score > 21:
            await finish_blackjack(update, context, player_hand, dealer_hand, deck, lang, user_id, bust=True, message_id=game_data.get("message_id"))
            return
        
        # State güncelle
        game_data["player_hand"] = player_hand
        game_data["deck"] = deck
        await state.set_state(user_id, state.PLAYING_BLACKJACK, game_data)
        
        msg = format_blackjack_state(player_hand, dealer_hand, lang, hide_dealer=True)
        
        if player_score == 21:
            msg += "\n\n21! ✨"
        
        # Edit existing message instead of sending new one
        if "message_id" in game_data:
            try:
                await context.bot.edit_message_text(
                    chat_id=user_id,
                    message_id=game_data["message_id"],
                    text=msg,
                    reply_markup=get_blackjack_keyboard(lang),
                    parse_mode="Markdown"
                )
            except Exception:
                # Fallback to new message if edit fails
                await update.message.reply_text(msg, reply_markup=get_blackjack_keyboard(lang))
        else:
            await update.message.reply_text(msg, reply_markup=get_blackjack_keyboard(lang))
        return
    
    # STAND (Dur)
    if any(k in text for k in ["stand", "dur", "хватит", "✋"]):
        # Delete user's button press
        try:
            await update.message.delete()
        except: pass
        
        await finish_blackjack(update, context, player_hand, dealer_hand, deck, lang, user_id, message_id=game_data.get("message_id"))
        return
    
    # Geçersiz giriş
    invalid_texts = {
        "tr": "Lütfen 'Kart Çek' veya 'Dur' butonlarını kullan.",
        "en": "Please use 'Hit' or 'Stand' buttons.",
        "ru": "Используйте кнопки 'Ещё' или 'Хватит'."
    }
    await update.message.reply_text(invalid_texts.get(lang, invalid_texts["en"]))

async def finish_blackjack(update, context, player_hand, dealer_hand, deck, lang, user_id, bust=False, message_id=None):
    """Blackjack oyununu bitir"""
    player_score = calculate_score(player_hand)
    
    # Krupiye oynamalı (16 veya altında kart çekmeli)
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
        
    # --- BETTING REWARD ---
    # Retrieve bet from state
    game_data = await state.get_data(user_id)
    bet_amount = game_data.get("bet_amount", 0)
    
    reward = 0
    if game_result == "win":
        # Blackjack check (21 with 2 cards) - Usually handled before, but check here if needed
        # Assuming standard win x2
        reward = bet_amount * 2
        await asyncio.to_thread(db.add_user_coins, user_id, reward)
    elif game_result == "draw":
        reward = bet_amount
        await asyncio.to_thread(db.add_user_coins, user_id, reward)
    # ----------------------

    # Sonucu göster
    msg = format_blackjack_state(player_hand, dealer_hand, lang, hide_dealer=False)
    
    # Add reward text
    result_texts = {
        "tr": {"bust": "💥 Battın! 21'i geçtin.", "win": "🎉 Kazandın!", "lose": "😞 Kaybettin!", "tie": "🤝 Berabere!", "dealer_bust": "🎉 Krupiye battı, sen kazandın!"},
        "en": {"bust": "💥 Bust! You went over 21.", "win": "🎉 You win!", "lose": "😞 You lose!", "tie": "🤝 It's a tie!", "dealer_bust": "🎉 Dealer busts, you win!"},
        "ru": {"bust": "💥 Перебор! Ты превысил 21.", "win": "🎉 Ты выиграл!", "lose": "😞 Ты проиграл!", "tie": "🤝 Ничья!", "dealer_bust": "🎉 У дилера перебор, ты выиграл!"}
    }
    r = result_texts.get(lang, result_texts["en"])
    result_text = r.get(result_key, result_key)
    
    if reward > 0:
        if game_result == "win":
            win_msg = TEXTS["coin_earned"][lang].format(amount=reward - bet_amount) # Net profit shown? Or total return? Usually "You won X" implies total or profit. Let's show total return or "You won X coins".
            # TEXTS["coin_earned"] says "You won X coins". Let's use total return.
            msg += f"\n\n{result_text}\n💰 +{reward} Coins"
        else: # Draw
            msg += f"\n\n{result_text}\n💰 +{reward} Coins (Refund)"
    else:
        msg += f"\n\n{result_text}"
    
    if message_id:
        try:
            await context.bot.edit_message_text(
                chat_id=user_id,
                message_id=message_id,
                text=msg,
                reply_markup=get_games_keyboard_markup(lang),
                parse_mode="Markdown"
            )
        except Exception:
            await update.message.reply_text(msg, reply_markup=get_games_keyboard_markup(lang), parse_mode="Markdown")
    else:
        await update.message.reply_text(msg, reply_markup=get_games_keyboard_markup(lang), parse_mode="Markdown")
    
    # Log
    await asyncio.to_thread(db.log_blackjack_game, user_id, player_score, dealer_score, game_result)
    
    # State cleared implicitly or explicit?
    # Usually clear playing state
    await asyncio.sleep(0.5)
    await state.clear_user_states(user_id)