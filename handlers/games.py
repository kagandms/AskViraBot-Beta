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

# --- XOX (TIC TAC TOE) - REPLY KEYBOARD VERSION ---

def get_xox_board_reply_markup(board):
    """3x3 XOX tahtası (Reply Keyboard) - Numaralı"""
    keyboard = []
    
    # Mapping for empty cells to numbers/emojis
    # 0 1 2
    # 3 4 5
    # 6 7 8
    
    # Numpad düzeni (1-9)
    # 1 2 3
    # 4 5 6
    # 7 8 9
    
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
    
    # Geri butonu
    back = TEXTS["back_button"][lang] if "back_button" in TEXTS else ("⬅️ Geri" if lang == "tr" else "⬅️ Back")
    
    keyboard = [
        [labels[0], labels[1], labels[2]],
        [back]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

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

# --- BOT ZORLUK SEVİYELERİ (Aynı kalıyor) ---
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
async def xox_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Zorluk seçimini başlat (Reply Keyboard)"""
    user_id = update.effective_user.id
    lang = await asyncio.to_thread(db.get_user_lang, user_id)
    
    # State ayarla
    state.clear_user_states(user_id)
    state.playing_xox[user_id] = {"board": [" "]*9, "difficulty": None, "active": False}
    
    # Zorluk seçim metni
    difficulty_prompt = {
        "tr": "🎮 XOX Oyunu\n\nZorluk seviyesi seçin:",
        "en": "🎮 XOX Game\n\nSelect difficulty level:",
        "ru": "🎮 Игра XOX\n\nВыберите уровень сложности:"
    }
    
    await update.message.reply_text(
        difficulty_prompt.get(lang, difficulty_prompt["en"]),
        reply_markup=get_xox_difficulty_reply_markup(lang)
    )

async def handle_xox_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """XOX hamlelerini ve seçimlerini yönetir"""
    user_id = update.effective_user.id
    if user_id not in state.playing_xox:
        return
        
    text = update.message.text
    lang = await asyncio.to_thread(db.get_user_lang, user_id)
    game_state = state.playing_xox[user_id]
    
    # ÇIKIŞ / GERİ KONTROLÜ
    if "Back" in text or "Geri" in text or "Назад" in text or "Menu" in text or "Menü" in text:
        state.playing_xox.pop(user_id, None)
        await games_menu(update, context)
        return
        
    # ZORLUK SEÇİMİ (Henüz oyun başlamadıysa)
    if not game_state["active"]:
        diff_map = {
            "🟢 Kolay": "easy", "🟢 Easy": "easy", "🟢 Легко": "easy",
            "🟡 Orta": "medium", "🟡 Medium": "medium", "🟡 Средне": "medium",
            "🔴 Zor": "hard", "🔴 Hard": "hard", "🔴 Сложно": "hard"
        }
        
        selected_diff = None
        for key, val in diff_map.items():
            if key in text:
                selected_diff = val
                break
        
        if selected_diff:
            game_state["difficulty"] = selected_diff
            game_state["active"] = True
            await update.message.reply_text(
                f"{TEXTS['xox_welcome'][lang]}",
                reply_markup=get_xox_board_reply_markup(game_state["board"])
            )
        else:
            await update.message.reply_text(TEXTS["xox_invalid_move"][lang])
        return

    # OYUN HAMLESİ
    # Gelen text: 1️⃣, 2️⃣... vs. veya düz sayılar
    mapping = {"1️⃣": 0, "2️⃣": 1, "3️⃣": 2, "4️⃣": 3, "5️⃣": 4, "6️⃣": 5, "7️⃣": 6, "8️⃣": 7, "9️⃣": 8}
    
    # Toleranslı eşleşme: önce tam eşleşme dene
    move_index = mapping.get(text.strip())
    
    # Eğer bulunamazsa, metin içinde anahtar ara
    if move_index is None:
        for emoji, idx in mapping.items():
            if emoji in text:
                move_index = idx
                break
    
    # Hala bulunamazsa düz sayıları kontrol et
    if move_index is None:
        text_clean = text.strip()
        if text_clean in ["1", "2", "3", "4", "5", "6", "7", "8", "9"]:
            move_index = int(text_clean) - 1
    
    if move_index is None:
        await update.message.reply_text(TEXTS["xox_invalid_move"][lang])
        return
        
    board = game_state["board"]
    
    # Dolu kare kontrolü
    if board[move_index] != " ":
        await update.message.reply_text(TEXTS["xox_invalid_move"][lang])
        return
        
    # KULLANICI HAMLESİ (X)
    board[move_index] = "X"
    winner = check_winner(board)
    
    if winner:
        await finish_get_xox_game(update, board, winner, lang, user_id, game_state["difficulty"])
        return
        
    # BOT HAMLESİ (O)
    bot_move = bot_make_move(board, game_state["difficulty"])
    if bot_move is not None:
        board[bot_move] = "O"
        winner = check_winner(board)
        if winner:
            await finish_get_xox_game(update, board, winner, lang, user_id, game_state["difficulty"])
            return
            
    # OYUN DEVAM
    await update.message.reply_text(
        TEXTS["xox_bot_moved"][lang] if "xox_bot_moved" in TEXTS else "Bot played.",
        reply_markup=get_xox_board_reply_markup(board)
    )

async def finish_get_xox_game(update, board, winner, lang, user_id, difficulty):
    """Oyunu bitir"""
    msg = ""
    if winner == "X": msg = TEXTS["xox_win"][lang]
    elif winner == "O": msg = TEXTS["xox_lose"][lang]
    else: msg = TEXTS["xox_draw"][lang]
    
    await update.message.reply_text(
        msg,
        reply_markup=get_xox_board_reply_markup(board)
    )
    
    # LOGLAMA
    await asyncio.to_thread(db.log_xox_game, user_id, winner, difficulty)
    
    # 2 Saniye bekle sonra menüye dön
    await asyncio.sleep(2)
    state.playing_xox.pop(user_id, None)
    await games_menu(update, context=None) # context=None olabilir çünkü games_menu context kullanmıyor (user_id update'den alınıyor)
    # NOT: games_menu update.effective_user.id kullanıyor, bu yüzden update objesi geçerli olmalı.


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
    user_id = update.effective_user.id
    lang = "en"  # Fallback dil
    try:
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