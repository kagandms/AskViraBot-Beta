
import asyncio
import logging
import random
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import database as db
import state
from texts import TEXTS, BUTTON_MAPPINGS, GAMES_BUTTONS, GAME_MODE_BUTTONS
from utils import get_games_keyboard_markup, is_back_button, cleanup_context
from rate_limiter import rate_limit

# --- CONSTANTS & HELPERS ---

# Game Names for display (Vira - Gambling removed)
GAME_NAMES = {
    "tkm": {"tr": "Taş Kağıt Makas", "en": "Rock Paper Scissors", "ru": "Камень Ножницы Бумага"}
}

# Helper: Get game mode keyboard
def get_game_mode_keyboard(lang):
    buttons = GAME_MODE_BUTTONS.get(lang, GAME_MODE_BUTTONS["en"])
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)



# --- GAMES MENU ---
@rate_limit("games")
async def games_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Oyunlar Alt Menüsünü Açar"""
    user_id = update.effective_user.id
    lang = await db.get_user_lang(user_id)
    
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

# --- PLAYER STATS ---
@rate_limit("games")
async def show_player_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Oyuncunun oyun istatistiklerini gösterir"""
    user_id = update.effective_user.id
    lang = await db.get_user_lang(user_id)
    
    # Cleanup previous context
    await cleanup_context(context, user_id)
    
    # Delete user's button press
    try:
        await update.message.delete()
    except: pass
    
    # İstatistikleri çek (Vira - Only XOX and TKM)
    xox_stats = await asyncio.to_thread(db.get_user_xox_stats, user_id)
    tkm_stats = await asyncio.to_thread(db.get_user_tkm_stats, user_id)
    
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
    msg_text += f"🪨📄✂️ {format_stats('Taş-Kağıt-Makas', tkm_stats)}"
    
    sent_msg = await update.message.reply_text(msg_text, reply_markup=get_games_keyboard_markup(lang), parse_mode="Markdown")
    
    await state.set_state(user_id, state.GAMES_MENU_ACTIVE, {"message_id": sent_msg.message_id})

# --- DICE & COINFLIP ---

    
# --- XOX Functions (Simplest to keep here for now as they are stateless mostly) ---
def get_xox_board_reply_markup(board):
    keyboard = []
    mapping = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣"]
    current_row = []
    for i in range(9):
        cell = board[i]
        text = mapping[i] if cell == " " else ("❌" if cell == "X" else "⭕")
        current_row.append(text)
        if len(current_row) == 3:
            keyboard.append(current_row)
            current_row = []
    keyboard.append(["🔙 Oyunlar Menüsü"])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_xox_difficulty_reply_markup(lang):
    texts = {"tr": ["🟢 Kolay", "🟡 Orta", "🔴 Zor"], "en": ["🟢 Easy", "🟡 Medium", "🔴 Hard"], "ru": ["🟢 Легко", "🟡 Средне", "🔴 Сложно"]}
    labels = texts.get(lang, texts["en"])
    back_texts = {"tr": "🔙 Oyun Odası", "en": "🔙 Game Room", "ru": "🔙 Игровая Комната"}
    back = back_texts.get(lang, back_texts["en"])
    return ReplyKeyboardMarkup([[labels[0], labels[1], labels[2]], [back]], resize_keyboard=True)

def check_winner(board):
    wins = [(0,1,2), (3,4,5), (6,7,8), (0,3,6), (1,4,7), (2,5,8), (0,4,8), (2,4,6)]
    for a, b, c in wins:
        if board[a] == board[b] == board[c] and board[a] != " ": return board[a]
    return "Draw" if " " not in board else None

def bot_make_move(board, difficulty="easy"):
    """XOX bot with proper AI based on difficulty level."""
    empty = [i for i, x in enumerate(board) if x == " "]
    if not empty:
        return None
    
    def minimax(board, depth, is_maximizing):
        """Minimax algorithm for optimal play."""
        winner = check_winner(board)
        if winner == "O": return 10 - depth  # Bot wins
        if winner == "X": return depth - 10  # Player wins
        if winner == "Draw": return 0  # Draw
        
        if is_maximizing:
            best_score = -float('inf')
            for i in range(9):
                if board[i] == " ":
                    board[i] = "O"
                    score = minimax(board, depth + 1, False)
                    board[i] = " "
                    best_score = max(score, best_score)
            return best_score
        else:
            best_score = float('inf')
            for i in range(9):
                if board[i] == " ":
                    board[i] = "X"
                    score = minimax(board, depth + 1, True)
                    board[i] = " "
                    best_score = min(score, best_score)
            return best_score
    
    def get_best_move(board):
        """Get the best move using minimax."""
        best_score = -float('inf')
        best_move = None
        for i in range(9):
            if board[i] == " ":
                board[i] = "O"
                score = minimax(board, 0, False)
                board[i] = " "
                if score > best_score:
                    best_score = score
                    best_move = i
        return best_move
    
    # Difficulty determines how often the bot plays optimally
    import random as rnd
    if difficulty == "easy":
        # 30% optimal, 70% random
        if rnd.random() < 0.3:
            return get_best_move(board)
        return rnd.choice(empty)
    elif difficulty == "medium":
        # 60% optimal, 40% random
        if rnd.random() < 0.6:
            return get_best_move(board)
        return rnd.choice(empty)
    else:  # hard
        # 100% optimal - unbeatable
        return get_best_move(board)

@rate_limit("games")
async def xox_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    lang = await db.get_user_lang(user_id)
    await cleanup_context(context, user_id)
    try: await update.message.delete()
    except: pass
    
    await state.clear_user_states(user_id)
    initial_game_state = {"board": [" "]*9, "difficulty": None, "active": False}
    await state.set_state(user_id, state.PLAYING_XOX, initial_game_state)
    
    difficulty_prompt = {
        "tr": "🎮 XOX Oyunu\n\nZorluk seviyesi seçin:",
        "en": "🎮 XOX Game\n\nSelect difficulty level:",
        "ru": "🎮 Игра XOX\n\nВыберите уровень сложности:"
    }
    sent_message = await update.message.reply_text(
        difficulty_prompt.get(lang, difficulty_prompt["en"]),
        reply_markup=get_xox_difficulty_reply_markup(lang)
    )
    initial_game_state["message_id"] = sent_message.message_id
    await state.set_state(user_id, state.PLAYING_XOX, initial_game_state)

async def handle_xox_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    text = update.message.text
    lang = await db.get_user_lang(user_id)
    game_state = await state.get_data(user_id)
    if not game_state: return

    if is_back_button(text):
        try: await update.message.delete()
        except: pass
        if "message_id" in game_state:
            try: await context.bot.delete_message(chat_id=user_id, message_id=game_state["message_id"])
            except: pass
        await state.clear_user_states(user_id)
        await games_menu(update, context)
        return

    # Difficulty Selection
    if not game_state.get("active"):
        text_lower = text.lower()
        selected_diff = None
        if "kolay" in text_lower or "easy" in text_lower or "легко" in text_lower: selected_diff = "easy"
        elif "orta" in text_lower or "medium" in text_lower or "средне" in text_lower: selected_diff = "medium"
        elif "zor" in text_lower or "hard" in text_lower or "сложно" in text_lower: selected_diff = "hard"
        
        if selected_diff:
            game_state["difficulty"] = selected_diff
            game_state["active"] = True
            try: await update.message.delete()
            except: pass
            if "message_id" in game_state:
                try: await context.bot.delete_message(chat_id=user_id, message_id=game_state["message_id"])
                except: pass
            
            welcome_text = f"{TEXTS['xox_welcome'][lang]} - {selected_diff.capitalize()}"
            board_msg = await update.message.reply_text(welcome_text, reply_markup=get_xox_board_reply_markup(game_state["board"]))
            game_state["message_id"] = board_msg.message_id
            await state.set_state(user_id, state.PLAYING_XOX, game_state)
        else:
            await update.message.reply_text(TEXTS["xox_invalid_move"][lang])
        return

    # Game Move
    mapping = {"1️⃣": 0, "2️⃣": 1, "3️⃣": 2, "4️⃣": 3, "5️⃣": 4, "6️⃣": 5, "7️⃣": 6, "8️⃣": 7, "9️⃣": 8}
    move_index = mapping.get(text.strip())
    if move_index is None:
        text_clean = text.strip()
        if text_clean in ["1", "2", "3", "4", "5", "6", "7", "8", "9"]:
            move_index = int(text_clean) - 1
            
    if move_index is None or game_state["board"][move_index] != " ":
        await update.message.reply_text(TEXTS["xox_invalid_move"][lang])
        return

    board = game_state["board"]
    board[move_index] = "X"
    winner = check_winner(board)
    
    if winner:
        await finish_get_xox_game(update, context, board, winner, lang, user_id, game_state["difficulty"])
        return

    bot_move = bot_make_move(board, game_state["difficulty"])
    if bot_move is not None:
        board[bot_move] = "O"
        winner = check_winner(board)
        if winner:
            await finish_get_xox_game(update, context, board, winner, lang, user_id, game_state["difficulty"])
            return

    game_state["board"] = board
    try: await update.message.delete()
    except: pass
    if "message_id" in game_state:
        try: await context.bot.delete_message(chat_id=user_id, message_id=game_state["message_id"])
        except: pass
        
    new_board_msg = await update.message.reply_text(
        TEXTS["xox_bot_moved"][lang] if "xox_bot_moved" in TEXTS else "Bot played.",
        reply_markup=get_xox_board_reply_markup(board)
    )
    game_state["message_id"] = new_board_msg.message_id
    await state.set_state(user_id, state.PLAYING_XOX, game_state)

async def finish_get_xox_game(update, context, board, winner, lang, user_id, difficulty):
    msg = ""
    if winner == "X": msg = TEXTS["xox_win"][lang]
    elif winner == "O": msg = TEXTS["xox_lose"][lang]
    else: msg = TEXTS["xox_draw"][lang]
    
    try:
        game_state = await state.get_data(user_id)
        if game_state and "message_id" in game_state:
            await context.bot.delete_message(chat_id=user_id, message_id=game_state["message_id"])
    except: pass
    
    await update.message.reply_text(msg, reply_markup=get_xox_board_reply_markup(board))
    await asyncio.to_thread(db.log_xox_game, user_id, winner, difficulty)
    await asyncio.sleep(0.5)
    await state.clear_user_states(user_id)
    await games_menu(update, context)
