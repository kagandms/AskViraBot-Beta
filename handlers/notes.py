from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import database as db
import state
from texts import TEXTS, BUTTON_MAPPINGS
from config import NOTES_PER_PAGE
from utils import get_notes_keyboard_markup, get_delete_notes_keyboard_markup, get_input_back_keyboard_markup, get_main_keyboard_markup

async def notes_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = db.get_user_lang(user_id)
    state.clear_user_states(user_id)
    state.notes_in_menu.add(user_id)
    await update.message.reply_text(
        TEXTS["notes_menu_prompt"][lang],
        reply_markup=get_notes_keyboard_markup(lang)
    )

async def deletenotes_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = db.get_user_lang(user_id)
    state.clear_user_states(user_id)
    state.deleting_notes.add(user_id)
    await update.message.reply_text(
        TEXTS["delete_notes_menu_prompt"][lang],
        reply_markup=get_delete_notes_keyboard_markup(lang)
    )

async def prompt_new_note(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = db.get_user_lang(user_id)
    state.clear_user_states(user_id)
    state.notes_in_menu.add(user_id) 
    state.waiting_for_new_note_input.add(user_id)
    await update.message.reply_text(TEXTS["prompt_new_note"][lang], reply_markup=get_input_back_keyboard_markup(lang))

async def handle_new_note_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = db.get_user_lang(user_id)
    text = update.message.text

    if text.lower() in BUTTON_MAPPINGS["menu"]:
        state.clear_user_states(user_id)
        await notes_menu(update, context)
        return

    db.add_user_note(user_id, text)
    state.clear_user_states(user_id) 
    state.notes_in_menu.add(user_id) 
    await update.message.reply_text(TEXTS["note_saved"][lang] + text, reply_markup=get_notes_keyboard_markup(lang))

async def shownotes_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    lang = db.get_user_lang(user_id)
    notes_data = db.get_user_notes(user_id)
    if not notes_data:
        await update.message.reply_text(TEXTS["no_notes"][lang], reply_markup=get_notes_keyboard_markup(lang))
        return
    message = TEXTS["notes_header"][lang] + "\n".join(f"{i}. {note['content']}" for i, note in enumerate(notes_data, 1))
    await update.message.reply_text(message, reply_markup=get_notes_keyboard_markup(lang))

async def addnote_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    lang = db.get_user_lang(user_id)
    note_content = ' '.join(context.args) if context.args else ""
    if not note_content:
        await update.message.reply_text(TEXTS["addnote_no_content"][lang])
        return
    db.add_user_note(user_id, note_content)
    await update.message.reply_text(TEXTS["note_saved"][lang] + note_content, reply_markup=get_main_keyboard_markup(lang))

async def select_note_to_delete_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = db.get_user_lang(user_id)
    notes_data = db.get_user_notes(user_id)
    if not notes_data:
        msg = TEXTS["no_notes"][lang]
        markup = get_delete_notes_keyboard_markup(lang)
        if update.callback_query: await update.callback_query.edit_message_text(msg, reply_markup=markup)
        else: await update.message.reply_text(msg, reply_markup=markup)
        state.deleting_notes.discard(user_id)
        return
    state.deleting_notes.add(user_id)
    state.user_notes_page_index[user_id] = 0
    await send_notes_for_deletion(update, context)

async def send_notes_for_deletion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = db.get_user_lang(user_id)
    notes_data = db.get_user_notes(user_id)
    current_page = state.user_notes_page_index.get(user_id, 0)

    if not notes_data:
        state.clear_user_states(user_id)
        msg = TEXTS["no_notes"][lang]
        markup = get_delete_notes_keyboard_markup(lang)
        if update.callback_query: await update.callback_query.edit_message_text(msg, reply_markup=markup)
        else: await update.message.reply_text(msg, reply_markup=markup)
        return

    start_index = current_page * NOTES_PER_PAGE
    end_index = start_index + NOTES_PER_PAGE
    display_notes = notes_data[start_index:end_index]

    keyboard = []
    for i, note_obj in enumerate(display_notes):
        note_id = note_obj['id']
        note_content = note_obj['content']
        button_text = f"{TEXTS['note_button_prefix'][lang]}{start_index + i + 1}: {note_content}"
        if len(button_text) > 50: button_text = button_text[:47] + "..."
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f"delete_note_{note_id}")])

    pagination_buttons = []
    if current_page > 0: pagination_buttons.append(InlineKeyboardButton(TEXTS["previous_page"][lang], callback_data="notes_prev_page"))
    if end_index < len(notes_data): pagination_buttons.append(InlineKeyboardButton(TEXTS["next_page"][lang], callback_data="notes_next_page"))
    if pagination_buttons: keyboard.append(pagination_buttons)
    keyboard.append([InlineKeyboardButton(TEXTS["back_button_inline"][lang], callback_data="delete_notes_back_inline")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    message = TEXTS["prompt_select_note_to_delete"][lang] + "\n\n" + "\n".join(f"{start_index + i + 1}. {n['content']}" for i, n in enumerate(display_notes))

    if update.callback_query: await update.callback_query.edit_message_text(message, reply_markup=reply_markup)
    else: await update.message.reply_text(message, reply_markup=reply_markup)

async def delete_note_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    lang = db.get_user_lang(user_id)
    await query.answer()

    if query.data == "notes_next_page":
        state.user_notes_page_index[user_id] = state.user_notes_page_index.get(user_id, 0) + 1
        await send_notes_for_deletion(update, context)
        return
    elif query.data == "notes_prev_page":
        state.user_notes_page_index[user_id] = max(0, state.user_notes_page_index.get(user_id, 0) - 1)
        await send_notes_for_deletion(update, context)
        return
    elif query.data == "delete_notes_back_inline":
        state.clear_user_states(user_id)
        await query.edit_message_text(TEXTS["delete_notes_menu_prompt"][lang], reply_markup=get_delete_notes_keyboard_markup(lang))
        return

    if query.data.startswith("delete_note_"):
        try:
            note_id_to_delete = int(query.data.split("_")[2])
            success = db.delete_user_note_by_id(note_id_to_delete)
            if success:
                notes_data = db.get_user_notes(user_id)
                current_page_notes_count = len(notes_data) - (state.user_notes_page_index.get(user_id, 0) * NOTES_PER_PAGE)
                if current_page_notes_count <= 0 and state.user_notes_page_index.get(user_id, 0) > 0:
                    state.user_notes_page_index[user_id] -= 1
                await query.edit_message_text(f"{TEXTS['note_deleted'][lang]}")
                await send_notes_for_deletion(update, context)
            else:
                await query.edit_message_text(TEXTS["error_occurred"][lang])
                await send_notes_for_deletion(update, context)
        except (ValueError, IndexError) as e:
            await query.edit_message_text(TEXTS["error_occurred"][lang] + str(e))
            await send_notes_for_deletion(update, context)