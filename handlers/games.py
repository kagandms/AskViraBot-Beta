import asyncio
import logging
import random
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import database as db
import state
from texts import TEXTS, TKM_BUTTONS, BUTTON_MAPPINGS, GAMES_BUTTONS
from utils import get_games_keyboard_markup, is_back_button
from rate_limiter import rate_limit

# --- OYUNLAR MENÜSÜ ---
@rate_limit("games")
async def games_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Oyunlar Alt Menüsünü Açar"""
    user_id = update.effective_user.id
    # DB İŞLEMİ: Asenkron
    lang = await asyncio.to_thread(db.get_user_lang, user_id)
    await state.clear_user_states(user_id)
    await state.set_state(user_id, state.GAMES_MENU_ACTIVE)
    
    await update.message.reply_text(
        TEXTS["games_menu_prompt"][lang], 
        reply_markup=get_games_keyboard_markup(lang)
    )

# --- XOX (TIC TAC TOE) - INLINE KEYBOARD VERSION ---

def get_xox_board_inline_markup(board, game_over=False):
    """3x3 XOX tahtası (Inline Keyboard) - Büyük butonlar"""
    keyboard = []
    
    for row_start in range(0, 9, 3):
        row = []
        for i in range(row_start, row_start + 3):
            cell = board[i]
            if cell == " ":
                text = "⬜"  # Büyük boş kare
                callback = f"xox_{i}" if not game_over else "xox_noop"
            elif cell == "X":
                text = "❌"
                callback = "xox_noop"
            else:  # O
                text = "⭕"
                callback = "xox_noop"
            row.append(InlineKeyboardButton(text, callback_data=callback))
        keyboard.append(row)
    
    # Alt butonlar
    if game_over:
        keyboard.append([
            InlineKeyboardButton("🔄 Tekrar", callback_data="xox_restart"),
            InlineKeyboardButton("🔙 Çıkış", callback_data="xox_exit")
        ])
    else:
        keyboard.append([InlineKeyboardButton("🔙 Çıkış", callback_data="xox_exit")])
    
    return InlineKeyboardMarkup(keyboard)

def get_xox_difficulty_inline_markup(lang):
    """Zorluk seçimi için Inline keyboard"""
    labels = {
        "tr": ["🟢 Kolay", "🟡 Orta", "🔴 Zor"],
        "en": ["🟢 Easy", "🟡 Medium", "🔴 Hard"],
        "ru": ["🟢 Легко", "🟡 Средне", "🔴 Сложно"]
    }
    buttons = labels.get(lang, labels["en"])
    
    keyboard = [
        [InlineKeyboardButton(buttons[0], callback_data="xox_diff_easy"),
         InlineKeyboardButton(buttons[1], callback_data="xox_diff_medium"),
         InlineKeyboardButton(buttons[2], callback_data="xox_diff_hard")],
        [InlineKeyboardButton("🔙", callback_data="xox_exit")]
    ]
    return InlineKeyboardMarkup(keyboard)

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
    """XOX oyununu başlat (Inline Keyboard - single message)"""
    user_id = update.effective_user.id
    lang = await asyncio.to_thread(db.get_user_lang, user_id)
    
    # Kullanıcının mesajını sil (temiz UI)
    try:
        await update.message.delete()
    except Exception:
        pass
    
    difficulty_prompt = {
        "tr": "🎮 *XOX Oyunu*\n\nZorluk seviyesi seçin:",
        "en": "🎮 *XOX Game*\n\nSelect difficulty level:",
        "ru": "🎮 *Игра XOX*\n\nВыберите уровень сложности:"
    }
    
    sent_message = await context.bot.send_message(
        chat_id=user_id,
        text=difficulty_prompt.get(lang, difficulty_prompt["en"]),
        reply_markup=get_xox_difficulty_inline_markup(lang),
        parse_mode="Markdown"
    )
    
    # State kaydet
    await state.clear_user_states(user_id)
    await state.set_state(user_id, state.PLAYING_XOX, {
        "board": [" "]*9,
        "difficulty": None,
        "active": False,
        "message_id": sent_message.message_id,
        "lang": lang
    })

async def handle_xox_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """XOX Inline Keyboard callback'lerini işle"""
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data
    
    await query.answer()  # Callback onayı
    
    game_state = await state.get_data(user_id)
    if not game_state:
        await query.message.delete()
        return
    
    lang = game_state.get("lang", "en")
    board = game_state.get("board", [" "]*9)
    
    # --- ÇIKIŞ ---
    if data == "xox_exit":
        await query.message.delete()
        await state.clear_user_states(user_id)
        await context.bot.send_message(
            chat_id=user_id,
            text=TEXTS["games_menu_prompt"][lang],
            reply_markup=get_games_keyboard_markup(lang)
        )
        return
    
    # --- NOOP (dolu hücre veya oyun bitti) ---
    if data == "xox_noop":
        return
    
    # --- TEKRAR OYNA ---
    if data == "xox_restart":
        difficulty_prompt = {
            "tr": "🎮 *XOX Oyunu*\n\nZorluk seviyesi seçin:",
            "en": "🎮 *XOX Game*\n\nSelect difficulty level:",
            "ru": "🎮 *Игра XOX*\n\nВыберите уровень сложности:"
        }
        
        await query.message.edit_text(
            difficulty_prompt.get(lang, difficulty_prompt["en"]),
            reply_markup=get_xox_difficulty_inline_markup(lang),
            parse_mode="Markdown"
        )
        
        await state.set_state(user_id, state.PLAYING_XOX, {
            "board": [" "]*9,
            "difficulty": None,
            "active": False,
            "message_id": query.message.message_id,
            "lang": lang
        })
        return
    
    # --- ZORLUK SEÇİMİ ---
    if data.startswith("xox_diff_"):
        difficulty = data.replace("xox_diff_", "")
        
        game_state["difficulty"] = difficulty
        game_state["active"] = True
        game_state["board"] = [" "]*9
        
        await state.set_state(user_id, state.PLAYING_XOX, game_state)
        
        welcome = {
            "tr": "🎮 *XOX Oyunu*\n\nSen: ❌ | Bot: ⭕\n\nBir hücreye tıkla!",
            "en": "🎮 *XOX Game*\n\nYou: ❌ | Bot: ⭕\n\nTap a cell!",
            "ru": "🎮 *Игра XOX*\n\nТы: ❌ | Бот: ⭕\n\nНажми на клетку!"
        }
        
        await query.message.edit_text(
            welcome.get(lang, welcome["en"]),
            reply_markup=get_xox_board_inline_markup(game_state["board"]),
            parse_mode="Markdown"
        )
        return
    
    # --- OYUN HAMLESİ ---
    if data.startswith("xox_") and data[4:].isdigit():
        if not game_state.get("active"):
            return
        
        move_index = int(data[4:])
        
        if board[move_index] != " ":
            return  # Dolu hücre
        
        # KULLANICI HAMLESİ (X)
        board[move_index] = "X"
        winner = check_winner(board)
        
        if winner:
            await finish_xox_inline(query, context, board, winner, lang, user_id, game_state["difficulty"])
            return
        
        # BOT HAMLESİ (O)
        bot_move_idx = bot_make_move(board, game_state["difficulty"])
        if bot_move_idx is not None:
            board[bot_move_idx] = "O"
            winner = check_winner(board)
            if winner:
                await finish_xox_inline(query, context, board, winner, lang, user_id, game_state["difficulty"])
                return
        
        # OYUN DEVAM
        game_state["board"] = board
        await state.set_state(user_id, state.PLAYING_XOX, game_state)
        
        status = {
            "tr": "🎮 *XOX Oyunu*\n\nSen: ❌ | Bot: ⭕",
            "en": "🎮 *XOX Game*\n\nYou: ❌ | Bot: ⭕",
            "ru": "🎮 *Игра XOX*\n\nТы: ❌ | Бот: ⭕"
        }
        
        await query.message.edit_text(
            status.get(lang, status["en"]),
            reply_markup=get_xox_board_inline_markup(board),
            parse_mode="Markdown"
        )

async def finish_xox_inline(query, context, board, winner, lang, user_id, difficulty):
    """XOX oyununu bitir (Inline versiyonu)"""
    if winner == "X":
        msg = TEXTS["xox_win"][lang]
    elif winner == "O":
        msg = TEXTS["xox_lose"][lang]
    else:
        msg = TEXTS["xox_draw"][lang]
    
    await query.message.edit_text(
        f"🎮 *XOX*\n\n{msg}",
        reply_markup=get_xox_board_inline_markup(board, game_over=True),
        parse_mode="Markdown"
    )
    
    await asyncio.to_thread(db.log_xox_game, user_id, winner, difficulty)
    
    # State'i güncelle (oyun bitti)
    game_state = await state.get_data(user_id)
    if game_state:
        game_state["active"] = False
        await state.set_state(user_id, state.PLAYING_XOX, game_state)

# Legacy message handler (for Reply Keyboard compatibility)
async def handle_xox_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """XOX - eski Reply Keyboard desteği (geri uyumluluk)"""
    user_id = update.effective_user.id
    text = update.message.text if update.message.text else ""
    
    game_state = await state.get_data(user_id)
    if not game_state:
        return
    
    lang = game_state.get("lang", "en")
    
    # Sadece geri butonu için
    if is_back_button(text):
        try:
            if "message_id" in game_state:
                await context.bot.delete_message(chat_id=user_id, message_id=game_state["message_id"])
            await update.message.delete()
        except Exception:
            pass
        
        await state.clear_user_states(user_id)
        await games_menu(update, context)
        return
    
    # Diğer mesajları yoksay (Inline Keyboard kullanılıyor)
    try:
        await update.message.delete()
    except Exception:
        pass

# --- DİĞER OYUNLAR ---
@rate_limit("games")
async def dice_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    lang = await asyncio.to_thread(db.get_user_lang, update.effective_user.id)
    number = random.randint(1, 6)
    await asyncio.to_thread(db.log_dice_roll, update.effective_user.id, number)
    await update.message.reply_text(TEXTS["dice_rolled"][lang].format(number=number))

@rate_limit("games")
async def coinflip_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    lang = await asyncio.to_thread(db.get_user_lang, update.effective_user.id)
    result = random.choice(["heads", "tails"])
    await asyncio.to_thread(db.log_coinflip, update.effective_user.id, result)
    translations = {"tr": {"heads": "Yazı", "tails": "Tura"}, "en": {"heads": "Heads", "tails": "Tails"}, "ru": {"heads": "Орёл", "tails": "Решка"}}
    await update.message.reply_text(TEXTS["coinflip_result"][lang].format(result=translations[lang][result]))

# --- TAŞ KAĞIT MAKAS (GÜNCELLENDİ) ---
@rate_limit("games")
async def tkm_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    await state.clear_user_states(user_id)
    await state.set_state(user_id, state.PLAYING_TKM)
    lang = await asyncio.to_thread(db.get_user_lang, user_id)
    buttons = TKM_BUTTONS.get(lang, TKM_BUTTONS["en"])
    sent_msg = await update.message.reply_text(TEXTS["tkm_welcome"][lang], reply_markup=ReplyKeyboardMarkup(buttons, resize_keyboard=True))
    
    # Set state with message ID
    await state.set_state(user_id, state.PLAYING_TKM, {"message_id": sent_msg.message_id})

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

        await state.clear_user_states(user_id)
        await update.message.reply_text(result_msg, reply_markup=get_games_keyboard_markup(lang))
        
    except Exception as e:
        logging.getLogger(__name__).error(f"TKM Error: {e}")
        await update.message.reply_text(TEXTS["error_occurred"][lang])
        await state.clear_user_states(user_id)

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

def get_blackjack_inline_keyboard(lang, game_over=False):
    """Blackjack oyun klavyesi (Inline - Hit/Stand)"""
    if game_over:
        labels = {
            "tr": [["🔄 Tekrar Oyna", "🔙 Oyun Odası"]],
            "en": [["🔄 Play Again", "🔙 Game Room"]],
            "ru": [["🔄 Играть Снова", "🔙 Игровая"]]
        }
        buttons = labels.get(lang, labels["en"])
        keyboard = [
            [InlineKeyboardButton(buttons[0][0], callback_data="bj_restart"),
             InlineKeyboardButton(buttons[0][1], callback_data="bj_exit")]
        ]
    else:
        labels = {
            "tr": [["🃏 Kart Çek", "✋ Dur"]],
            "en": [["🃏 Hit", "✋ Stand"]],
            "ru": [["🃏 Ещё", "✋ Хватит"]]
        }
        buttons = labels.get(lang, labels["en"])
        keyboard = [
            [InlineKeyboardButton(buttons[0][0], callback_data="bj_hit"),
             InlineKeyboardButton(buttons[0][1], callback_data="bj_stand")],
            [InlineKeyboardButton("🔙", callback_data="bj_exit")]
        ]
    return InlineKeyboardMarkup(keyboard)

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

@rate_limit("games")
async def blackjack_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Blackjack oyununu başlat (Inline Keyboard - single message)"""
    user_id = update.effective_user.id
    lang = await asyncio.to_thread(db.get_user_lang, user_id)
    
    # Deste oluştur ve kartları dağıt
    deck = create_deck()
    player_hand = [deck.pop(), deck.pop()]
    dealer_hand = [deck.pop(), deck.pop()]
    
    player_score = calculate_score(player_hand)
    
    welcome_texts = {
        "tr": "🃏 *Blackjack (21)*\n\nKart çekerek 21'e yaklaşmaya çalış!\n21'i geçersen kaybedersin.\n\n",
        "en": "🃏 *Blackjack (21)*\n\nTry to get as close to 21 as possible!\nGo over 21 and you lose.\n\n",
        "ru": "🃏 *Блэкджек (21)*\n\nПопробуй приблизиться к 21!\nПревысишь 21 — проиграешь.\n\n"
    }
    
    msg = welcome_texts.get(lang, welcome_texts["en"])
    msg += format_blackjack_state(player_hand, dealer_hand, lang, hide_dealer=True)
    
    # Blackjack kontrolü (ilk 2 kart = 21)
    game_over = False
    if player_score == 21:
        msg += "\n\n🎉 *BLACKJACK!*"
        game_over = True
    
    # Kullanıcının başlatma mesajını sil (temiz UI)
    try:
        await update.message.delete()
    except Exception:
        pass
    
    sent_message = await context.bot.send_message(
        chat_id=user_id,
        text=msg, 
        reply_markup=get_blackjack_inline_keyboard(lang, game_over=game_over), 
        parse_mode="Markdown"
    )
    
    # State kaydet (message_id ile birlikte)
    await state.clear_user_states(user_id)
    await state.set_state(user_id, state.PLAYING_BLACKJACK, {
        "deck": deck,
        "player_hand": player_hand,
        "dealer_hand": dealer_hand,
        "message_id": sent_message.message_id,
        "lang": lang,
        "game_over": game_over
    })
    
    # Eğer Blackjack ise sonucu logla
    if game_over:
        await asyncio.to_thread(db.log_blackjack_game, user_id, player_score, calculate_score(dealer_hand), "win")

async def handle_blackjack_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Blackjack Inline Keyboard callback'lerini işle"""
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data
    
    await query.answer()  # Callback onayı
    
    game_data = await state.get_data(user_id)
    if not game_data:
        await query.message.delete()
        return
    
    lang = game_data.get("lang", "en")
    deck = game_data["deck"]
    player_hand = game_data["player_hand"]
    dealer_hand = game_data["dealer_hand"]
    
    # --- ÇIKIŞ ---
    if data == "bj_exit":
        await query.message.delete()
        await state.clear_user_states(user_id)
        # Games menüsünü göster (yeni mesaj olarak)
        await context.bot.send_message(
            chat_id=user_id,
            text=TEXTS["games_menu_prompt"][lang],
            reply_markup=get_games_keyboard_markup(lang)
        )
        return
    
    # --- TEKRAR OYNA ---
    if data == "bj_restart":
        await query.message.delete()
        # Yeni oyun başlat (fake update gönder)
        # Alternatif: Direkt fonksiyonu çağır
        new_deck = create_deck()
        new_player = [new_deck.pop(), new_deck.pop()]
        new_dealer = [new_deck.pop(), new_deck.pop()]
        
        welcome_texts = {
            "tr": "🃏 *Blackjack (21)*\n\nKart çekerek 21'e yaklaşmaya çalış!\n21'i geçersen kaybedersin.\n\n",
            "en": "🃏 *Blackjack (21)*\n\nTry to get as close to 21 as possible!\nGo over 21 and you lose.\n\n",
            "ru": "🃏 *Блэкджек (21)*\n\nПопробуй приблизиться к 21!\nПревысишь 21 — проиграешь.\n\n"
        }
        
        msg = welcome_texts.get(lang, welcome_texts["en"])
        msg += format_blackjack_state(new_player, new_dealer, lang, hide_dealer=True)
        
        player_score = calculate_score(new_player)
        game_over = player_score == 21
        if game_over:
            msg += "\n\n🎉 *BLACKJACK!*"
        
        sent = await context.bot.send_message(
            chat_id=user_id,
            text=msg,
            reply_markup=get_blackjack_inline_keyboard(lang, game_over=game_over),
            parse_mode="Markdown"
        )
        
        await state.set_state(user_id, state.PLAYING_BLACKJACK, {
            "deck": new_deck,
            "player_hand": new_player,
            "dealer_hand": new_dealer,
            "message_id": sent.message_id,
            "lang": lang,
            "game_over": game_over
        })
        
        if game_over:
            await asyncio.to_thread(db.log_blackjack_game, user_id, player_score, calculate_score(new_dealer), "win")
        return
    
    # Oyun bittiyse diğer butonları işleme
    if game_data.get("game_over"):
        return
    
    # --- HIT (Kart Çek) ---
    if data == "bj_hit":
        player_hand.append(deck.pop())
        player_score = calculate_score(player_hand)
        
        # Bust kontrolü
        if player_score > 21:
            # Oyun bitti - Kaybetti
            result_texts = {
                "tr": "💥 *Battın!* 21'i geçtin.",
                "en": "💥 *Bust!* You went over 21.",
                "ru": "💥 *Перебор!* Ты превысил 21."
            }
            msg = format_blackjack_state(player_hand, dealer_hand, lang, hide_dealer=False)
            msg += f"\n\n{result_texts.get(lang, result_texts['en'])}"
            
            await query.message.edit_text(
                msg, 
                reply_markup=get_blackjack_inline_keyboard(lang, game_over=True),
                parse_mode="Markdown"
            )
            
            game_data["game_over"] = True
            await state.set_state(user_id, state.PLAYING_BLACKJACK, game_data)
            await asyncio.to_thread(db.log_blackjack_game, user_id, player_score, calculate_score(dealer_hand), "lose")
            return
        
        # Devam et
        msg = format_blackjack_state(player_hand, dealer_hand, lang, hide_dealer=True)
        
        if player_score == 21:
            msg += "\n\n✨ *21!*"
        
        game_data["player_hand"] = player_hand
        game_data["deck"] = deck
        await state.set_state(user_id, state.PLAYING_BLACKJACK, game_data)
        
        await query.message.edit_text(
            msg,
            reply_markup=get_blackjack_inline_keyboard(lang),
            parse_mode="Markdown"
        )
        return
    
    # --- STAND (Dur) ---
    if data == "bj_stand":
        player_score = calculate_score(player_hand)
        
        # Krupiye oynamalı (16 veya altında kart çekmeli)
        while calculate_score(dealer_hand) < 17:
            dealer_hand.append(deck.pop())
        
        dealer_score = calculate_score(dealer_hand)
        
        result_texts = {
            "tr": {"win": "🎉 *Kazandın!*", "lose": "😞 *Kaybettin!*", "tie": "🤝 *Berabere!*", "dealer_bust": "🎉 *Krupiye battı, sen kazandın!*"},
            "en": {"win": "🎉 *You win!*", "lose": "😞 *You lose!*", "tie": "🤝 *It's a tie!*", "dealer_bust": "🎉 *Dealer busts, you win!*"},
            "ru": {"win": "🎉 *Ты выиграл!*", "lose": "😞 *Ты проиграл!*", "tie": "🤝 *Ничья!*", "dealer_bust": "🎉 *У дилера перебор!*"}
        }
        r = result_texts.get(lang, result_texts["en"])
        
        if dealer_score > 21:
            result = r["dealer_bust"]
            game_result = "win"
        elif player_score > dealer_score:
            result = r["win"]
            game_result = "win"
        elif player_score < dealer_score:
            result = r["lose"]
            game_result = "lose"
        else:
            result = r["tie"]
            game_result = "draw"
        
        msg = format_blackjack_state(player_hand, dealer_hand, lang, hide_dealer=False)
        msg += f"\n\n{result}"
        
        await query.message.edit_text(
            msg,
            reply_markup=get_blackjack_inline_keyboard(lang, game_over=True),
            parse_mode="Markdown"
        )
        
        game_data["game_over"] = True
        await state.set_state(user_id, state.PLAYING_BLACKJACK, game_data)
        await asyncio.to_thread(db.log_blackjack_game, user_id, player_score, dealer_score, game_result)

# Legacy message handler (for compatibility / back button from Reply Keyboard)
async def handle_blackjack_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Blackjack - eski Reply Keyboard desteği (geri uyumluluk)"""
    user_id = update.effective_user.id
    text = update.message.text.lower() if update.message.text else ""
    
    game_data = await state.get_data(user_id)
    if not game_data:
        return
    
    lang = game_data.get("lang", "en")
    
    # Sadece geri butonu için
    if is_back_button(text):
        try:
            if "message_id" in game_data:
                await context.bot.delete_message(chat_id=user_id, message_id=game_data["message_id"])
            await update.message.delete()
        except Exception:
            pass
        
        await state.clear_user_states(user_id)
        await games_menu(update, context)
        return
    
    # Diğer mesajları yoksay (Inline Keyboard kullanılıyor)
    try:
        await update.message.delete()
    except Exception:
        pass