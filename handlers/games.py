import random
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
import database as db
import state
from texts import TEXTS, TKM_BUTTONS, BUTTON_MAPPINGS

async def dice_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = db.get_user_lang(update.effective_user.id)
    number = random.randint(1, 6)
    await update.message.reply_text(TEXTS["dice_rolled"][lang].format(number=number))

async def coinflip_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = db.get_user_lang(update.effective_user.id)
    result = random.choice(["heads", "tails"])
    translations = {"tr": {"heads": "Yazı", "tails": "Tura"}, "en": {"heads": "Heads", "tails": "Tails"}, "ru": {"heads": "Орёл", "tails": "Решка"}}
    await update.message.reply_text(TEXTS["coinflip_result"][lang].format(result=translations[lang][result]))

async def decision_wheel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = db.get_user_lang(update.effective_user.id)
    options = context.args
    if len(options) < 2:
        await update.message.reply_text(TEXTS["decision_wheel_usage"][lang])
        return
    chosen = random.choice(options)
    await update.message.reply_text(TEXTS["decision_wheel_chosen"][lang] + chosen)

async def tkm_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    state.clear_user_states(user_id)
    state.playing_tkm.add(user_id)
    lang = db.get_user_lang(user_id)
    buttons = TKM_BUTTONS.get(lang, TKM_BUTTONS["en"])
    await update.message.reply_text(TEXTS["tkm_welcome"][lang], reply_markup=ReplyKeyboardMarkup(buttons, resize_keyboard=True))

async def tkm_play(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = db.get_user_lang(user_id)
    user_move_raw = update.message.text.lower()
    
    user_move = None
    if user_move_raw in BUTTON_MAPPINGS.get("tkm_rock", set()): user_move = "taş"
    elif user_move_raw in BUTTON_MAPPINGS.get("tkm_paper", set()): user_move = "kağıt"
    elif user_move_raw in BUTTON_MAPPINGS.get("tkm_scissors", set()): user_move = "makas"

    if user_move is None:
        if user_move_raw in BUTTON_MAPPINGS["menu"]:
             from handlers.general import menu_command
             await menu_command(update, context)
             return
        await update.message.reply_text(TEXTS["unknown_command"][lang])
        return

    standard_moves = ["taş", "kağıt", "makas"]
    bot_move_standard = random.choice(standard_moves)
    display_moves = {"tr": {"taş": "Taş", "kağıt": "Kağıt", "makas": "Makas"}, "en": {"taş": "Rock", "kağıt": "Paper", "makas": "Scissors"}, "ru": {"taş": "Камень", "каğıt": "Бумага", "makas": "Ножницы"}}
    
    result_msg = f"{TEXTS['tkm_labels_bot'][lang]}: {display_moves[lang][bot_move_standard]}\n{TEXTS['tkm_labels_you'][lang]}: {display_moves[lang][user_move]}\n"
    user_idx = standard_moves.index(user_move)
    bot_idx = standard_moves.index(bot_move_standard)

    if user_idx == bot_idx: result_msg += TEXTS["tkm_tie"][lang]
    elif (user_idx - bot_idx + 3) % 3 == 1: result_msg += TEXTS["tkm_win"][lang]
    else: result_msg += TEXTS["tkm_lose"][lang]

    await update.message.reply_text(result_msg)