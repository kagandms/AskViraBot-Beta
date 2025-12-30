from telegram import Update
from telegram.ext import ContextTypes
import database as db
import state
from texts import TEXTS
from utils import get_main_keyboard_markup

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    state.clear_user_states(user_id)
    lang = db.get_user_lang(user_id)
    await update.message.reply_text(TEXTS["start"][lang])

async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = db.get_user_lang(user_id)
    state.clear_user_states(user_id)
    await update.message.reply_text(
        TEXTS["menu_prompt"][lang],
        reply_markup=get_main_keyboard_markup(lang)
    )

async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    text = update.message.text.lower()
    lang_to_set = None
    if "türkçe" in text: lang_to_set = "tr"
    elif "english" in text: lang_to_set = "en"
    elif "русский" in text: lang_to_set = "ru"
    else:
        command_lang = update.message.text[1:].lower()
        if command_lang in ["tr", "en", "ru"]:
            lang_to_set = command_lang

    if lang_to_set:
        db.set_user_lang_db(user_id, lang_to_set)
        await update.message.reply_text(TEXTS["language_set"][lang_to_set])
        await menu_command(update, context)