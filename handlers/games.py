import asyncio
import logging
import random
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import database as db
import state
from texts import TEXTS, TKM_BUTTONS, BUTTON_MAPPINGS, GAMES_BUTTONS
from utils import get_games_keyboard_markup
from rate_limiter import rate_limit

# --- OYUNLAR MENÜSÜ ---
@rate_limit("games")
async def games_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Oyunlar Alt Menüsünü Açar"""
    user_id = update.effective_user.id
    # DB İŞLEMİ: Asenkron
    lang = await asyncio.to_thread(db.get_user_lang, user_id)
    state.clear_user_states(user_id)
    state.games_menu_active.add(user_id)
    
    await update.message.reply_text(
        TEXTS["games_menu_prompt"][lang], 
        reply_markup=get_games_keyboard_markup(lang)
    )

# --- XOX (TIC TAC TOE) ---
def get_xox_board_markup(board):
    """3x3 XOX tahtası oluşturur (Inline Keyboard)"""
    keyboard = []
    for i in range(3):
        row = []
        for j in range(3):
            index = i * 3 + j
            text = board[index]
            if text == " ": text = "⬜" # Boşluk için
            callback_data = f"xox_move_{index}"
            row.append(InlineKeyboardButton(text, callback_data=callback_data))
        keyboard.append(row)
    return InlineKeyboardMarkup(keyboard)

def get_xox_difficulty_markup(lang):
    """Zorluk seçimi için inline keyboard"""
    texts = {
        "tr": ["🟢 Kolay", "🟡 Orta", "🔴 Zor"],
        "en": ["🟢 Easy", "🟡 Medium", "🔴 Hard"],
        "ru": ["🟢 Легко", "🟡 Средне", "🔴 Сложно"]
    }
    labels = texts.get(lang, texts["en"])
    keyboard = [[
        InlineKeyboardButton(labels[0], callback_data="xox_diff_easy"),
        InlineKeyboardButton(labels[1], callback_data="xox_diff_medium"),
        InlineKeyboardButton(labels[2], callback_data="xox_diff_hard")
    ]]
    return InlineKeyboardMarkup(keyboard)

def check_winner(board):
    """Kazananı kontrol eder. Return: 'X', 'O', 'Draw' veya None"""
    wins = [(0,1,2), (3,4,5), (6,7,8), # Yatay
            (0,3,6), (1,4,7), (2,5,8), # Dikey
            (0,4,8), (2,4,6)]          # Çapraz
    
    for a, b, c in wins:
        if board[a] == board[b] == board[c] and board[a] != " ":
            return board[a]
    
    if " " not in board: return "Draw"
    return None

# --- BOT ZORLUK SEVİYELERİ ---
def bot_move_easy(board):
    """Kolay: Tamamen rastgele hamle"""
    empty = [i for i, x in enumerate(board) if x == " "]
    return random.choice(empty) if empty else None

def bot_move_medium(board):
    """Orta: Kazanma/engelleme stratejisi, yoksa rastgele"""
    wins = [(0,1,2), (3,4,5), (6,7,8), (0,3,6), (1,4,7), (2,5,8), (0,4,8), (2,4,6)]
    
    # 1. Kazanabilecek hamle var mı?
    for a, b, c in wins:
        line = [board[a], board[b], board[c]]
        if line.count("O") == 2 and line.count(" ") == 1:
            return [a, b, c][line.index(" ")]
    
    # 2. Rakibi engelleyecek hamle var mı?
    for a, b, c in wins:
        line = [board[a], board[b], board[c]]
        if line.count("X") == 2 and line.count(" ") == 1:
            return [a, b, c][line.index(" ")]
    
    # 3. Merkez boşsa al
    if board[4] == " ":
        return 4
    
    # 4. Rastgele köşe
    corners = [i for i in [0, 2, 6, 8] if board[i] == " "]
    if corners:
        return random.choice(corners)
    
    # 5. Rastgele boş
    return bot_move_easy(board)

def minimax(board, is_maximizing):
    """Zor: Minimax algoritması - yenilmez bot"""
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
    """Zor: Minimax ile en iyi hamle - YENİLMEZ"""
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
    """Zorluk seviyesine göre bot hamlesi"""
    if difficulty == "easy":
        return bot_move_easy(board)
    elif difficulty == "medium":
        return bot_move_medium(board)
    else:  # hard
        return bot_move_hard(board)

@rate_limit("games")
async def xox_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Zorluk seçimi ekranını göster"""
    user_id = update.effective_user.id
    lang = await asyncio.to_thread(db.get_user_lang, user_id)
    state.clear_user_states(user_id)
    
    # Zorluk seçim metni
    difficulty_prompt = {
        "tr": "🎮 XOX Oyunu\n\nZorluk seviyesi seçin:",
        "en": "🎮 XOX Game\n\nSelect difficulty level:",
        "ru": "🎮 Игра XOX\n\nВыберите уровень сложности:"
    }
    
    await update.message.reply_text(
        difficulty_prompt.get(lang, difficulty_prompt["en"]),
        reply_markup=get_xox_difficulty_markup(lang)
    )

async def xox_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    lang = await asyncio.to_thread(db.get_user_lang, user_id)
    
    await query.answer()
    
    # ZORLUK SEÇİMİ
    if query.data.startswith("xox_diff_"):
        difficulty = query.data.split("_")[2]  # easy, medium, hard
        board = [" "] * 9
        state.playing_xox[user_id] = {"board": board, "difficulty": difficulty}
        
        # Oyun başladı mesajı
        diff_names = {
            "tr": {"easy": "Kolay", "medium": "Orta", "hard": "Zor"},
            "en": {"easy": "Easy", "medium": "Medium", "hard": "Hard"},
            "ru": {"easy": "Легко", "medium": "Средне", "hard": "Сложно"}
        }
        diff_name = diff_names.get(lang, diff_names["en"]).get(difficulty, difficulty)
        
        await query.edit_message_text(
            f"{TEXTS['xox_welcome'][lang]}\n\n📊 {diff_name}",
            reply_markup=get_xox_board_markup(board)
        )
        return
    
    # OYUN HAMLESİ
    if not query.data.startswith("xox_move_"): 
        return
    
    move_index = int(query.data.split("_")[2])
    game_state = state.playing_xox.get(user_id)
    
    if not game_state:
        await query.answer(TEXTS["xox_invalid_move"][lang], show_alert=True)
        return
        
    board = game_state["board"]
    difficulty = game_state.get("difficulty", "easy")
    
    # Geçersiz hamle (dolu kutu)
    if board[move_index] != " ":
        await query.answer(TEXTS["xox_invalid_move"][lang], show_alert=True)
        return

    # KULLANICI HAMLESİ (X)
    board[move_index] = "X"
    winner = check_winner(board)
    
    if winner:
        await finish_xox_game(query, board, winner, lang, user_id, difficulty)
        return

    # BOT HAMLESİ (O) - Zorluk seviyesine göre
    bot_move = bot_make_move(board, difficulty)
    if bot_move is not None:
        board[bot_move] = "O"
        winner = check_winner(board)
        if winner:
            await finish_xox_game(query, board, winner, lang, user_id, difficulty)
            return
            
    # OYUN DEVAM EDİYOR (Tahtayı güncelle)
    await query.edit_message_reply_markup(reply_markup=get_xox_board_markup(board))

async def finish_xox_game(query, board, winner, lang, user_id, difficulty):
    """Oyunu bitir ve sonucu yaz"""
    await query.edit_message_reply_markup(reply_markup=get_xox_board_markup(board))
    
    msg = ""
    if winner == "X": msg = TEXTS["xox_win"][lang]
    elif winner == "O": msg = TEXTS["xox_lose"][lang]
    else: msg = TEXTS["xox_draw"][lang]
    
    await query.message.reply_text(msg)
    
    # LOGLAMA
    await asyncio.to_thread(db.log_xox_game, user_id, winner, difficulty)
    
    state.playing_xox.pop(user_id, None) # Oyunu hafızadan sil

# --- DİĞER OYUNLAR ---
@rate_limit("games")
async def dice_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # DB İŞLEMİ: Asenkron
    lang = await asyncio.to_thread(db.get_user_lang, update.effective_user.id)
    number = random.randint(1, 6)
    # LOGLAMA
    await asyncio.to_thread(db.log_dice_roll, update.effective_user.id, number)
    await update.message.reply_text(TEXTS["dice_rolled"][lang].format(number=number))

@rate_limit("games")
async def coinflip_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # DB İŞLEMİ: Asenkron
    lang = await asyncio.to_thread(db.get_user_lang, update.effective_user.id)
    result = random.choice(["heads", "tails"])
    # LOGLAMA
    await asyncio.to_thread(db.log_coinflip, update.effective_user.id, result)
    translations = {"tr": {"heads": "Yazı", "tails": "Tura"}, "en": {"heads": "Heads", "tails": "Tails"}, "ru": {"heads": "Орёл", "tails": "Решка"}}
    await update.message.reply_text(TEXTS["coinflip_result"][lang].format(result=translations[lang][result]))

# --- TAŞ KAĞIT MAKAS (GÜNCELLENDİ) ---
@rate_limit("games")
async def tkm_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    state.clear_user_states(user_id)
    state.playing_tkm.add(user_id)
    # DB İŞLEMİ: Asenkron
    lang = await asyncio.to_thread(db.get_user_lang, user_id)
    buttons = TKM_BUTTONS.get(lang, TKM_BUTTONS["en"])
    await update.message.reply_text(TEXTS["tkm_welcome"][lang], reply_markup=ReplyKeyboardMarkup(buttons, resize_keyboard=True))

async def tkm_play(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = update.effective_user.id
        # DB İŞLEMİ: Asenkron
        lang = await asyncio.to_thread(db.get_user_lang, user_id)
        user_move_raw = update.message.text.lower().strip()
        
        # Menüye Dönüş (Geri Butonu veya Menü Komutları)
        # Menüye Dönüş (Geri Butonu veya Menü Komutları)
        if user_move_raw in BUTTON_MAPPINGS["menu"] or user_move_raw in BUTTON_MAPPINGS.get("back_to_games", set()) or "geri" in user_move_raw or "back" in user_move_raw or "назад" in user_move_raw:
            # DÜZELTME: Ana menü yerine Oyunlar menüsüne dön
            await games_menu(update, context)
            return

        # ESNEK GİRİŞ KONTROLÜ (Emoji veya kelime bazlı eşleştirme)
        user_move = None
        
        rock_keywords = ["taş", "rock", "камень", "🪨"]
        paper_keywords = ["kağıt", "paper", "бумага", "📄", "📃", "📝"] 
        scissors_keywords = ["makas", "scissors", "ножницы", "✂️", "✂"]

        if any(k in user_move_raw for k in rock_keywords): 
            user_move = "taş"
        elif any(k in user_move_raw for k in paper_keywords): 
            user_move = "kağıt"
        elif any(k in user_move_raw for k in scissors_keywords): 
            user_move = "makas"

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
            
        # LOGLAMA
        await asyncio.to_thread(db.log_tkm_game, user_id, user_move, bot_move_standard, result_status)

        state.playing_tkm.discard(user_id)
        await update.message.reply_text(result_msg, reply_markup=get_games_keyboard_markup(lang))
        
    except Exception as e:
        logging.getLogger(__name__).error(f"TKM Error: {e}")
        await update.message.reply_text(TEXTS["error_occurred"][lang])
        state.playing_tkm.discard(user_id)