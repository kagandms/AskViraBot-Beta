import asyncio
import re
import logging
from datetime import datetime, timedelta
import pytz
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import database as db
import state
from texts import TEXTS, BUTTON_MAPPINGS
from config import TIMEZONE
from utils import get_reminder_keyboard_markup, get_input_back_keyboard_markup, format_remaining_time

async def reminder_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    # DB İŞLEMİ: Asenkron
    lang = await asyncio.to_thread(db.get_user_lang, user_id)
    
    # Cleanup previous context
    from utils import cleanup_context
    await cleanup_context(context, user_id)
    
    # Delete user's button press
    try:
        await update.message.delete()
    except: pass
    
    await state.clear_user_states(user_id)
    
    sent_msg = await update.message.reply_text(TEXTS["reminder_menu_prompt"][lang], reply_markup=get_reminder_keyboard_markup(lang))
    
    # Track message for cleanup
    await state.set_state(user_id, state.REMINDER_MENU_ACTIVE, {"message_id": sent_msg.message_id})

async def show_reminders_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    # DB İŞLEMİ: Asenkron
    lang = await asyncio.to_thread(db.get_user_lang, user_id)
    
    # Cleanup user trigger
    try:
        await update.message.delete()
    except: pass
    
    reminders = await asyncio.to_thread(db.get_all_reminders_db)
    user_reminders = [r for r in reminders if str(r.get("user_id")) == str(user_id)]
    
    if not user_reminders:
        await update.message.reply_text(TEXTS["no_reminders"][lang], reply_markup=get_reminder_keyboard_markup(lang))
        return

    message = TEXTS["reminders_header"][lang]
    now = datetime.now(pytz.utc)
    
    # Çeviri metinleri
    remaining_text = {"tr": "Kalan", "en": "Remaining", "ru": "Осталось"}
    expired_text = {"tr": "Süresi Doldu", "en": "Expired", "ru": "Истёк"}
    error_text = {"tr": "Hata", "en": "Error", "ru": "Ошибка"}
    unknown_text = {"tr": "Bilinmeyen", "en": "Unknown", "ru": "Неизвестно"}
    
    for i, reminder in enumerate(user_reminders):
        try:
            target_time = datetime.fromisoformat(reminder["time"])
            remaining_seconds = (target_time - now).total_seconds()
            time_formatted = target_time.astimezone(pytz.timezone(TIMEZONE)).strftime('%Y-%m-%d %H:%M')
            if remaining_seconds > 0:
                message += f"{i+1}. {time_formatted} - {reminder['message']} ({remaining_text.get(lang, 'Remaining')}: {format_remaining_time(remaining_seconds, lang)})\n"
            else:
                message += f"{i+1}. {time_formatted} - {reminder['message']} ({expired_text.get(lang, 'Expired')})\n"
        except Exception as e:
            message += f"{i+1}. [{error_text.get(lang, 'Error')}] - {reminder.get('message', unknown_text.get(lang, 'Unknown'))}\n"
    await update.message.reply_text(message, reply_markup=get_reminder_keyboard_markup(lang))

async def prompt_reminder_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    # DB İŞLEMİ: Asenkron
    lang = await asyncio.to_thread(db.get_user_lang, user_id)
    await state.clear_user_states(user_id)
    sent_msg = await update.message.reply_text(TEXTS["remind_prompt_input"][lang], reply_markup=get_input_back_keyboard_markup(lang))
    await state.set_state(user_id, state.WAITING_FOR_REMINDER_INPUT, {"message_id": sent_msg.message_id})

async def process_reminder_input(update: Update, context: ContextTypes.DEFAULT_TYPE, input_string: str = None):
    user_id = update.effective_user.id
    # DB İŞLEMİ: Asenkron
    lang = await asyncio.to_thread(db.get_user_lang, user_id)
    text = input_string if input_string else update.message.text

    if text.lower() in BUTTON_MAPPINGS["menu"]:
        # Cleanup
        try:
            state_data = await state.get_data(user_id)
            if "message_id" in state_data:
                await context.bot.delete_message(chat_id=user_id, message_id=state_data["message_id"])
            await update.message.delete()
        except Exception:
            pass

        await state.clear_user_states(user_id)
        await reminder_menu(update, context)
        return

    match = re.match(r"^(\d{1,2}:\d{2})\s*(?:(\d{4}-\d{2}-\d{2})\s*)?(.*)$", text.strip())
    if not match or not match.group(3).strip():
        # Cleanup invalid input message
        try:
             await update.message.delete()
        except: pass
        await update.message.reply_text(TEXTS["remind_usage"][lang], reply_markup=get_reminder_keyboard_markup(lang))
        return

    time_arg = match.group(1)
    date_arg = match.group(2)
    message = match.group(3).strip()
    istanbul_tz = pytz.timezone(TIMEZONE)
    now = datetime.now(istanbul_tz)

    try:
        time_dt = datetime.strptime(time_arg, "%H:%M")
        if date_arg:
            target = istanbul_tz.localize(datetime.strptime(date_arg, "%Y-%m-%d")).replace(hour=time_dt.hour, minute=time_dt.minute, second=0, microsecond=0)
        else:
            target = istanbul_tz.localize(datetime.combine(now.date(), time_dt.time()))
            if target < now: target += timedelta(days=1)

        remaining_seconds = (target - now).total_seconds()
        remaining_time_str = format_remaining_time(remaining_seconds, lang)
        time_str = target.strftime('%Y-%m-%d %H:%M')
        
        reminder_data = {"user_id": user_id, "chat_id": update.effective_chat.id, "time": target.astimezone(pytz.utc).isoformat(), "message": message}
        # DB İŞLEMİ: Asenkron - Eklenen kaydın ID'sini al
        reminder_id = await asyncio.to_thread(db.add_reminder_db, reminder_data)
        
        await update.message.reply_text(
            TEXTS["reminder_set"][lang].format(time_str=time_str, message=message, remaining_time=remaining_time_str),
            reply_markup=get_reminder_keyboard_markup(lang)
        )
        await state.clear_user_states(user_id)
        # ID'yi direkt olarak task'a geçir
        asyncio.create_task(reminder_task(context.application, update.effective_chat.id, message, remaining_seconds, reminder_id))

    except Exception as e:
        await update.message.reply_text(TEXTS["error_occurred"][lang] + str(e), reply_markup=get_reminder_keyboard_markup(lang))
        await state.clear_user_states(user_id)

async def reminder_task(application, chat_id, message, wait_seconds, reminder_id):
    """Belirtilen süre sonunda hatırlatıcı mesajı gönderir ve DB'den siler."""
    logger = logging.getLogger(__name__)
    
    await asyncio.sleep(wait_seconds)
    try:
        await application.bot.send_message(chat_id=chat_id, text=f"🔔 Reminder: {message}")
        # Hatırlatıcıyı veritabanından sil
        if reminder_id:
            await asyncio.to_thread(db.remove_reminder_db, reminder_id)
    except Exception as e:
        logger.error(f"Hatırlatıcı gönderilemedi (chat_id: {chat_id}): {e}")

async def delete_reminder_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    # DB İŞLEMİ: Asenkron
    lang = await asyncio.to_thread(db.get_user_lang, user_id)
    reminders = await asyncio.to_thread(db.get_all_reminders_db)
    user_reminders = [r for r in reminders if str(r.get("user_id")) == str(user_id)]
    
    if not user_reminders:
        msg = TEXTS["no_reminders"][lang]
        markup = get_reminder_keyboard_markup(lang)
        await state.clear_user_states(user_id)
        if update.callback_query: await update.callback_query.edit_message_text(msg, reply_markup=markup)
        else: await update.message.reply_text(msg, reply_markup=markup)
        return
    
    await state.clear_user_states(user_id)
    await state.set_state(user_id, state.WAITING_FOR_REMINDER_DELETE)
    
    keyboard = []
    for i, reminder in enumerate(user_reminders):
        rem_id = reminder['id']
        try:
            time_obj = datetime.fromisoformat(reminder['time']).astimezone(pytz.timezone(TIMEZONE))
            time_str = time_obj.strftime('%H:%M %d.%m.%Y')
        except Exception:
            time_str = "Invalid Date"
            
        btn_txt = f"{i+1}. {reminder['message']} ({time_str})"
        if len(btn_txt) > 50: btn_txt = btn_txt[:47] + "..."
        keyboard.append([InlineKeyboardButton(btn_txt, callback_data=f"delete_rem_{rem_id}")])
        
    keyboard.append([InlineKeyboardButton(TEXTS["back_button_inline"][lang], callback_data="reminders_back_inline")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.callback_query: await update.callback_query.edit_message_text(TEXTS["prompt_select_reminder_to_delete"][lang], reply_markup=reply_markup)
    else: await update.message.reply_text(TEXTS["prompt_select_reminder_to_delete"][lang], reply_markup=reply_markup)

async def delete_reminder_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user_id = query.from_user.id
    # DB İŞLEMİ: Asenkron
    lang = await asyncio.to_thread(db.get_user_lang, user_id)
    await query.answer()
    if query.data == "reminders_back_inline":
        await state.clear_user_states(user_id)
        await query.edit_message_text(TEXTS["reminder_menu_prompt"][lang], reply_markup=None)
        await context.bot.send_message(chat_id=query.message.chat_id, text=TEXTS["reminder_menu_prompt"][lang], reply_markup=get_reminder_keyboard_markup(lang))
        return
    if query.data.startswith("delete_rem_"):
        try:
            reminder_id_to_delete = int(query.data.split("_")[2])
            # DB İŞLEMİ: Asenkron
            await asyncio.to_thread(db.remove_reminder_db, reminder_id_to_delete)
            await query.edit_message_text(f"{TEXTS['reminder_deleted'][lang]}")
            await delete_reminder_menu(update, context)
        except (ValueError, IndexError) as e:
            await query.edit_message_text(TEXTS["error_occurred"][lang] + str(e))
            await delete_reminder_menu(update, context)

async def remind_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if context.args: await process_reminder_input(update, context, ' '.join(context.args))
    else: await reminder_menu(update, context)

async def start_pending_reminders(application):
    # DB İŞLEMİ: Asenkron
    reminders = await asyncio.to_thread(db.get_all_reminders_db)
    now = datetime.now(pytz.utc)
    for reminder in reminders:
        if isinstance(reminder.get("time"), str):
            try: target_time = datetime.fromisoformat(reminder["time"])
            except ValueError: continue
        else: continue

        if target_time > now:
            wait_seconds = (target_time - now).total_seconds()
            asyncio.create_task(reminder_task(application, reminder["chat_id"], reminder["message"], wait_seconds, reminder.get("id")))
        else:
            # DB İŞLEMİ: Asenkron
            await asyncio.to_thread(db.remove_reminder_db, reminder.get("id"))