import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
import database as db
import state
from texts import TEXTS, BUTTON_MAPPINGS
from utils import get_notes_keyboard_markup, get_input_back_keyboard_markup, is_back_button

# --- NOTLAR MENÜSÜ ---
async def notes_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    # DB İŞLEMİ: Asenkron
    lang = await asyncio.to_thread(db.get_user_lang, user_id)
    await state.clear_user_states(user_id)
    await state.set_state(user_id, state.NOTES_IN_MENU)
    
    # Önceki "notları göster" mesajını sil
    prev_msg_id = context.user_data.get('show_notes_msg_id')
    if prev_msg_id:
        try:
            await context.bot.delete_message(chat_id=user_id, message_id=prev_msg_id)
        except Exception:
            pass
        context.user_data.pop('show_notes_msg_id', None)
    
    if update.callback_query:
        await update.callback_query.message.reply_text(
            TEXTS["notes_menu_prompt"][lang],
            reply_markup=get_notes_keyboard_markup(lang)
        )
    else:
        await update.message.reply_text(
            TEXTS["notes_menu_prompt"][lang],
            reply_markup=get_notes_keyboard_markup(lang)
        )

async def addnote_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    # DB İŞLEMİ: Asenkron
    lang = await asyncio.to_thread(db.get_user_lang, user_id)
    
    note_content = ' '.join(context.args)
    if note_content:
        # DB İŞLEMİ: Asenkron
        await asyncio.to_thread(db.add_note, user_id, note_content)
        await update.message.reply_text(TEXTS["note_saved"][lang] + note_content)
    else:
        await prompt_new_note(update, context)

async def prompt_new_note(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    # DB İŞLEMİ: Asenkron
    lang = await asyncio.to_thread(db.get_user_lang, user_id)
    await state.clear_user_states(user_id)
    await state.set_state(user_id, state.WAITING_FOR_NEW_NOTE_INPUT)
    await update.message.reply_text(TEXTS["prompt_new_note"][lang], reply_markup=get_input_back_keyboard_markup(lang))

async def handle_new_note_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    # DB İŞLEMİ: Asenkron
    lang = await asyncio.to_thread(db.get_user_lang, user_id)
    text = update.message.text
    text_lower = text.lower().strip()

    is_cancel_command = is_back_button(text)

    if is_cancel_command:
        await state.clear_user_states(user_id)
        await notes_menu(update, context)
        return

    # State zaten main.py'de kontrol edildi, burada tekrar kontrol gereksiz

    # DB İŞLEMİ: Asenkron (Not Ekleme)
    await asyncio.to_thread(db.add_note, user_id, text)
    
    await state.clear_user_states(user_id)
    await state.set_state(user_id, state.NOTES_IN_MENU)
    await update.message.reply_text(TEXTS["note_saved"][lang] + text, reply_markup=get_notes_keyboard_markup(lang))

async def shownotes_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    # DB İŞLEMİ: Asenkron (Dil ve Notlar)
    lang = await asyncio.to_thread(db.get_user_lang, user_id)
    notes = await asyncio.to_thread(db.get_notes, user_id)
    
    # Önceki "notları göster" mesajını sil
    prev_msg_id = context.user_data.get('show_notes_msg_id')
    if prev_msg_id:
        try:
            await context.bot.delete_message(chat_id=user_id, message_id=prev_msg_id)
        except Exception:
            pass
        context.user_data.pop('show_notes_msg_id', None)
    
    if not notes:
        sent_msg = await update.message.reply_text(TEXTS["no_notes"][lang], reply_markup=get_notes_keyboard_markup(lang))
    else:
        message = TEXTS["notes_header"][lang]
        for i, note in enumerate(notes, 1):
            message += f"{i}. {note}\n"
        sent_msg = await update.message.reply_text(message, reply_markup=get_notes_keyboard_markup(lang))
    
    # Mesaj ID'sini kaydet (Geçici UI durumu olduğu için persistent state'e gerek yok, context.user_data kalsa da olur ama silinirse sadece mesaj silinmez o kadar)
    context.user_data['show_notes_msg_id'] = sent_msg.message_id

# --- NOT SİLME ---
async def deletenotes_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    # DB İŞLEMİ: Asenkron
    lang = await asyncio.to_thread(db.get_user_lang, user_id)
    notes = await asyncio.to_thread(db.get_notes, user_id)
    
    # Önceki "notları göster" mesajını sil
    prev_msg_id = context.user_data.get('show_notes_msg_id')
    if prev_msg_id:
        try:
            await context.bot.delete_message(chat_id=user_id, message_id=prev_msg_id)
        except Exception:
            pass
        context.user_data.pop('show_notes_msg_id', None)
    
    if not notes:
        await update.message.reply_text(TEXTS["no_notes"][lang]) 
        return
    
    # Persistent page index
    state_data = await state.get_data(user_id)
    page = state_data.get('delete_notes_page', 0)
    
    notes_per_page = 5
    start_index = page * notes_per_page
    end_index = start_index + notes_per_page
    current_notes = notes[start_index:end_index]
    
    keyboard = []
    for i, note in enumerate(current_notes):
        note_index = start_index + i
        safe_note = note[:20] + "..." if len(note) > 20 else note
        button_text = f"{TEXTS['note_button_prefix'][lang]}{note_index + 1}: {safe_note}"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f"delete_note_{note_index}")])
    
    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton(TEXTS["previous_page"][lang], callback_data="notes_prev_page"))
    if end_index < len(notes):
        nav_row.append(InlineKeyboardButton(TEXTS["next_page"][lang], callback_data="notes_next_page"))
    if nav_row:
        keyboard.append(nav_row)
        
    keyboard.append([InlineKeyboardButton(TEXTS["back_button_inline"][lang], callback_data="delete_notes_back_inline")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Set state to deleting notes with current page data
    await state.set_state(user_id, state.DELETING_NOTES, {"delete_notes_page": page})
    
    if update.callback_query:
        await update.callback_query.edit_message_text(TEXTS["prompt_select_note_to_delete"][lang], reply_markup=reply_markup)
        # ID is already stored or known (it's the callback message)
    else:
        sent_msg = await update.message.reply_text(TEXTS["prompt_select_note_to_delete"][lang], reply_markup=reply_markup)
        context.user_data['show_notes_msg_id'] = sent_msg.message_id

async def select_note_to_delete_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    # Init page 0
    await state.clear_user_states(user_id)
    await state.set_state(user_id, state.DELETING_NOTES, {"delete_notes_page": 0})
    await deletenotes_menu(update, context)

async def delete_note_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user_id = query.from_user.id
    # DB İŞLEMİ: Asenkron
    lang = await asyncio.to_thread(db.get_user_lang, user_id)
    
    await query.answer()
    
    if query.data == "delete_notes_back_inline":
        await query.message.delete()
        await notes_menu(update, context)
        return
    
    # Get current state data
    state_data = await state.get_data(user_id)
    current_page = state_data.get('delete_notes_page', 0)

    if query.data == "notes_next_page":
        new_page = current_page + 1
        await state.set_state(user_id, state.DELETING_NOTES, {"delete_notes_page": new_page})
        await deletenotes_menu(update, context)
        return
        
    if query.data == "notes_prev_page":
        new_page = max(0, current_page - 1)
        await state.set_state(user_id, state.DELETING_NOTES, {"delete_notes_page": new_page})
        await deletenotes_menu(update, context)
        return
 
    if query.data.startswith("delete_note_"):
        note_index = int(query.data.split("_")[2])
        # DB İŞLEMİ: Asenkron
        notes = await asyncio.to_thread(db.get_notes, user_id)
        
        if 0 <= note_index < len(notes):
            deleted_note = notes[note_index]
            # DB İŞLEMİ: Asenkron (Not Silme)
            await asyncio.to_thread(db.delete_note, user_id, note_index + 1)
            
            await query.edit_message_text(
                f"{TEXTS['note_deleted'][lang]}: {deleted_note}",
                reply_markup=None
            )
            await deletenotes_menu(update, context) # Refresh list
        else:
             await query.edit_message_text(TEXTS["invalid_note_number"][lang])

# --- NOT DÜZENLEME ---
async def edit_notes_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    # DB İŞLEMİ: Asenkron
    lang = await asyncio.to_thread(db.get_user_lang, user_id)
    notes = await asyncio.to_thread(db.get_notes, user_id)
    
    await state.clear_user_states(user_id)
    await state.set_state(user_id, state.EDITING_NOTES)
    
    # Önceki "notları göster" mesajını sil
    prev_msg_id = context.user_data.get('show_notes_msg_id')
    if prev_msg_id:
        try:
            await context.bot.delete_message(chat_id=user_id, message_id=prev_msg_id)
        except Exception:
            pass
        context.user_data.pop('show_notes_msg_id', None)
    
    if not notes:
        await update.message.reply_text(TEXTS["no_notes"][lang])
        return

    keyboard = []
    for i, note in enumerate(notes):
        safe_note = note[:20] + "..." if len(note) > 20 else note
        button_text = f"{TEXTS['note_button_prefix'][lang]}{i + 1}: {safe_note}"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f"edit_note_{i}")])
    
    keyboard.append([InlineKeyboardButton(TEXTS["back_button_inline"][lang], callback_data="notes_back_inline")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.edit_message_text(TEXTS["edit_notes_menu_prompt"][lang], reply_markup=reply_markup)
    else:
        sent_msg = await update.message.reply_text(TEXTS["edit_notes_menu_prompt"][lang], reply_markup=reply_markup)
        context.user_data['show_notes_msg_id'] = sent_msg.message_id

async def handle_edit_note_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user_id = query.from_user.id
    # DB İŞLEMİ: Asenkron
    lang = await asyncio.to_thread(db.get_user_lang, user_id)
    await query.answer()

    if query.data == "notes_back_inline":
        await query.message.delete()
        await notes_menu(update, context)
        return
        
    if query.data.startswith("edit_note_"):
        note_index = int(query.data.split("_")[2])
        
        await state.clear_user_states(user_id)
        await state.set_state(user_id, state.WAITING_FOR_EDIT_NOTE_INPUT, {"editing_note_index": note_index})
        
        # DB İŞLEMİ: Asenkron
        notes = await asyncio.to_thread(db.get_notes, user_id)
        current_note = notes[note_index]
        
        # Mevcut notu göster ve düzenleme talimatı ver
        edit_prompt = {
            "tr": "✏️ *Mevcut Notunuz:*\n\n`{note}`\n\n👆 Yukarıdaki notu kopyalayıp düzenleyebilir veya yeni içerik yazabilirsiniz.",
            "en": "✏️ *Your Current Note:*\n\n`{note}`\n\n👆 You can copy and edit the note above, or write new content.",
            "ru": "✏️ *Ваша текущая заметка:*\n\n`{note}`\n\n👆 Вы можете скопировать и отредактировать заметку выше или написать новое содержимое."
        }
        
        # Markdown formatını bozmaması için backtickleri temizle
        safe_note = current_note.replace("`", "'")
        msg = edit_prompt.get(lang, edit_prompt["en"]).format(note=safe_note)
        
        # Yapıştır ve İptal butonları
        paste_text = {"tr": "📝 Yapıştır (yazıya ekle)", "en": "📝 Paste to input", "ru": "📝 Вставить"}
        cancel_text = {"tr": "❌ İptal", "en": "❌ Cancel", "ru": "❌ Отмена"}
        keyboard = [
            [InlineKeyboardButton(paste_text.get(lang, "📝 Paste"), switch_inline_query_current_chat=current_note)],
            [InlineKeyboardButton(cancel_text.get(lang, "❌ Cancel"), callback_data="notes_back_inline")]
        ]
        
        # Eski mesajı sil ve yeni mesaj gönder
        try:
            await query.message.delete()
        except Exception:
            pass
        
        # Inline butonlu mesaj
        sent_msg1 = await context.bot.send_message(
            chat_id=user_id,
            text=msg,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
        # Altta Geri butonu (ReplyKeyboard)
        back_btn = {"tr": "◀️ Geri", "en": "◀️ Back", "ru": "◀️ Назад"}
        reply_kb = ReplyKeyboardMarkup([[back_btn.get(lang, "◀️ Back")]], resize_keyboard=True)
        sent_msg2 = await context.bot.send_message(
            chat_id=user_id,
            text="👇",
            reply_markup=reply_kb
        )
        
        # Mesaj ID'lerini kaydet (Persistent state'e gerek yok, anlık UI)
        context.user_data['edit_note_msg_ids'] = [sent_msg1.message_id, sent_msg2.message_id]

async def handle_edit_note_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    # DB İŞLEMİ: Asenkron
    lang = await asyncio.to_thread(db.get_user_lang, user_id)
    new_text = update.message.text
    text_lower = new_text.lower().strip()
    
    is_cancel_command = (
        text_lower in BUTTON_MAPPINGS["menu"] or 
        text_lower in ["geri", "back", "назад", "◀️ geri", "◀️ back", "◀️ назад"]
    )

    if is_cancel_command:
        await state.clear_user_states(user_id)
        
        # Düzenleme mesajlarını sil
        msg_ids = context.user_data.pop('edit_note_msg_ids', [])
        for msg_id in msg_ids:
            try:
                await context.bot.delete_message(chat_id=user_id, message_id=msg_id)
            except Exception:
                pass
        
        # Düzenlenecek notlar sayfasına geri dön
        await edit_notes_menu(update, context)
        return

    # State zaten main.py'de kontrol edildi

    state_data = await state.get_data(user_id)
    note_index = state_data.get('editing_note_index')
    
    if note_index is not None:
        # DB İŞLEMİ: Asenkron (Güncelleme)
        await asyncio.to_thread(db.update_note, user_id, note_index, new_text)
        await state.clear_user_states(user_id)
        # return to menu state
        await state.set_state(user_id, state.NOTES_IN_MENU)
        await update.message.reply_text(TEXTS["note_updated"][lang], reply_markup=get_notes_keyboard_markup(lang))
    else:
        await update.message.reply_text(TEXTS["error_occurred"][lang])