"""
Admin Panel Handler for DruzhikBot
Sadece ADMIN_IDS listesindeki kullanıcılar erişebilir.
"""

import asyncio
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes
import database as db
from config import ADMIN_IDS, TIMEZONE
from config import ADMIN_IDS, TIMEZONE
from utils import get_main_keyboard_markup, is_back_button
import pytz
import state

def is_admin(user_id: int) -> bool:
    """Kullanıcının admin olup olmadığını kontrol eder"""
    return user_id in ADMIN_IDS

def get_admin_keyboard():
    """Admin menü klavyesi (Reply Keyboard)"""
    keyboard = [
        ["📊 İstatistikler", "👥 Kullanıcı Listesi"],
        ["📢 Duyuru Gönder"],
        ["◀️ Geri"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Admin paneli ana komutu"""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("⛔ Bu komuta erişim yetkiniz yok.")
        return
    
    # State başlat
    await state.clear_user_states(user_id)
    await state.set_state(user_id, state.ADMIN_MENU_ACTIVE)
    
    await update.message.reply_text(
        "🔧 *Admin Paneli*\n\nBir işlem seçin:",
        reply_markup=get_admin_keyboard(),
        parse_mode="Markdown"
    )

async def handle_admin_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Admin paneli mesaj handler'ı (Reply Keyboard)"""
    user_id = update.effective_user.id
    
    if not await state.check_state(user_id, state.ADMIN_MENU_ACTIVE):
        return False
    
    if not is_admin(user_id):
        return False
    
    text = update.message.text.strip()
    
    # Geri butonu
    if is_back_button(text):
        await state.clear_user_states(user_id)
        lang = await asyncio.to_thread(db.get_user_lang, user_id)
        await update.message.reply_text(
            "🏠 Ana menüye döndünüz.",
            reply_markup=get_main_keyboard_markup(lang, user_id)
        )
        return True
    
    # İstatistikler
    if "İstatistik" in text:
        await show_stats_reply(update, context)
        return True
    
    # Kullanıcı Listesi
    if "Kullanıcı" in text:
        await show_users_reply(update, context)
        return True
    
    # Duyuru Gönder
    if "Duyuru" in text:
        await start_broadcast_reply(update, context)
        return True
    
    return False

async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Admin panel callback handler"""
    query = update.callback_query
    user_id = query.from_user.id
    
    if not is_admin(user_id):
        await query.answer("⛔ Yetkiniz yok!", show_alert=True)
        return
    
    await query.answer()
    
    if query.data == "admin_stats":
        await show_stats(query, context)
    elif query.data == "admin_broadcast":
        await start_broadcast(query, context)
    elif query.data == "admin_users":
        await show_users(query, context)
    elif query.data == "admin_exit_to_menu":
        # Admin panelini kapat ve ana menüye dön
        user_id = query.from_user.id
        lang = await asyncio.to_thread(db.get_user_lang, user_id)
        await query.delete_message()
        await query.message.chat.send_message(
            "🏠 Ana menüye döndünüz.",
            reply_markup=get_main_keyboard_markup(lang, user_id)
        )
    elif query.data == "admin_close":
        await query.delete_message()
    elif query.data == "admin_back":
        await query.edit_message_text(
            "🔧 *Admin Paneli*\n\nBir işlem seçin:",
            reply_markup=get_admin_keyboard(),
            parse_mode="Markdown"
        )

async def show_stats(query, context):
    """İstatistikleri göster"""
    try:
        # Kullanıcı sayısı
        users = await asyncio.to_thread(db.get_all_users_count)
        notes = await asyncio.to_thread(db.get_all_notes_count)
        reminders = await asyncio.to_thread(db.get_all_reminders_count)
        
        # AI kullanım istatistikleri (Veritabanından)
        # TODO: Implement granular daily usage if needed. For now showing total.
        # total_ai_usage = sum(state.ai_daily_usage.values()) 
        # ai_active_users = len(state.ai_daily_usage)
        
        tz = pytz.timezone(TIMEZONE)
        now = datetime.now(tz).strftime("%d.%m.%Y %H:%M")
        
        stats_text = f"""📊 *Bot İstatistikleri*

👥 Toplam Kullanıcı: *{users}*
📝 Toplam Not: *{notes}*
⏰ Aktif Hatırlatıcı: *{reminders}*

🕐 Güncelleme: {now}
"""
        keyboard = [[InlineKeyboardButton("◀️ Geri", callback_data="admin_back")]]
        await query.edit_message_text(
            stats_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    except Exception as e:
        await query.edit_message_text(f"❌ Hata: {e}")

async def start_broadcast(query, context):
    """Duyuru gönderme modunu başlat"""
    user_id = query.from_user.id
    context.user_data['admin_broadcast'] = True
    
    # Inline mesajı sil ve yeni mesaj gönder (mesaj ID'sini sakla)
    await query.delete_message()
    
    # Reply Keyboard ile Geri butonu
    reply_keyboard = ReplyKeyboardMarkup([["🔙 Admin Paneli"]], resize_keyboard=True, one_time_keyboard=True)
    
    broadcast_msg = await query.message.chat.send_message(
        "📢 *Duyuru Gönder*\n\n"
        "Tüm kullanıcılara göndermek istediğiniz mesajı yazın.\n"
        "İptal etmek için aşağıdaki butona basın.",
        reply_markup=reply_keyboard,
        parse_mode="Markdown"
    )
    # Mesaj ID'sini sakla (sonra silmek için)
    context.user_data['broadcast_prompt_msg_id'] = broadcast_msg.message_id

async def handle_broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Duyuru mesajını işle ve gönder"""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        return False
    
    if not context.user_data.get('admin_broadcast'):
        return False
    
    message = update.message.text.strip()
    
    # Geri butonuna basıldıysa iptal et
    if is_back_button(message):
        context.user_data['admin_broadcast'] = False
        # Prompt mesajını sil
        prompt_msg_id = context.user_data.pop('broadcast_prompt_msg_id', None)
        if prompt_msg_id:
            try:
                await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=prompt_msg_id)
            except Exception:
                pass
        # Admin menüsüne dön (Ana menü yerine)
        await state.clear_user_states(user_id)
        await state.set_state(user_id, state.ADMIN_MENU_ACTIVE)
        await update.message.reply_text(
            "🔧 *Admin Paneli*\n\nBir işlem seçin:",
            reply_markup=get_admin_keyboard(),
            parse_mode="Markdown"
        )
        return True
    
    context.user_data['admin_broadcast'] = False
    
    # Prompt mesajını sil
    prompt_msg_id = context.user_data.pop('broadcast_prompt_msg_id', None)
    if prompt_msg_id:
        try:
            await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=prompt_msg_id)
        except Exception:
            pass
    
    # Durum mesajı
    status_msg = await update.message.reply_text("📤 Duyuru gönderiliyor...")
    
    try:
        # ASYNC BROADCAST TASK
        async def broadcast_task(users, message_text):
             sent = 0
             failed = 0
             for uid in users:
                 try:
                     await context.bot.send_message(
                         chat_id=uid,
                         text=f"📢 *Geliştirici Duyurusu*\n\n{message_text}\n\n_— DruzhikBot Geliştiricisi_",
                         parse_mode="Markdown"
                     )
                     sent += 1
                 except Exception:
                     failed += 1
                 await asyncio.sleep(0.05)
             
             try:
                 await status_msg.edit_text(
                    f"✅ *Duyuru Tamamlandı*\n\n"
                    f"📤 Gönderilen: {sent}\n"
                    f"❌ Başarısız: {failed}",
                    parse_mode="Markdown",
                    reply_markup=None
                 )
             except Exception:
                 pass

        users = await asyncio.to_thread(db.get_all_user_ids)
        asyncio.create_task(broadcast_task(users, message))
        
        # Don't wait, return to menu immediately
        await update.message.reply_text("⏳ Duyuru işlemi arka planda başlatıldı.")

        # Ana menüye dön
        lang = await asyncio.to_thread(db.get_user_lang, user_id)
        await update.message.reply_text("🏠 Ana menüye döndünüz.", reply_markup=get_main_keyboard_markup(lang, user_id))
    except Exception as e:
        await status_msg.edit_text(f"❌ Hata: {e}")
    
    return True

async def show_users(query, context):
    """Son kullanıcıları listele"""
    try:
        users = await asyncio.to_thread(db.get_recent_users, 10)
        
        if not users:
            users_text = "👥 Henüz kullanıcı yok."
        else:
            lines = ["👥 *Son 10 Kullanıcı*\n"]
            for i, user in enumerate(users, 1):
                uid = user.get('user_id', 'N/A')
                lang = user.get('language', '?')
                lines.append(f"{i}. `{uid}` ({lang})")
            users_text = "\n".join(lines)
        
        keyboard = [[InlineKeyboardButton("◀️ Geri", callback_data="admin_back")]]
        await query.edit_message_text(
            users_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    except Exception as e:
        await query.edit_message_text(f"❌ Hata: {e}")

# --- REPLY KEYBOARD BASED HELPERS ---

async def show_stats_reply(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """İstatistikleri göster (Reply Keyboard için)"""
    try:
        users = await asyncio.to_thread(db.get_all_users_count)
        notes = await asyncio.to_thread(db.get_all_notes_count)
        reminders = await asyncio.to_thread(db.get_all_reminders_count)
        
        tz = pytz.timezone(TIMEZONE)
        now = datetime.now(tz).strftime("%d.%m.%Y %H:%M")
        
        stats_text = f"""📊 *Bot İstatistikleri*

👥 Toplam Kullanıcı: *{users}*
📝 Toplam Not: *{notes}*
⏰ Aktif Hatırlatıcı: *{reminders}*

🕐 Güncelleme: {now}
"""
        await update.message.reply_text(stats_text, parse_mode="Markdown", reply_markup=get_admin_keyboard())
    except Exception as e:
        await update.message.reply_text(f"❌ Hata: {e}")

async def show_users_reply(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Son kullanıcıları listele (Reply Keyboard için)"""
    try:
        users = await asyncio.to_thread(db.get_recent_users, 10)
        
        if not users:
            users_text = "👥 Henüz kullanıcı yok."
        else:
            lines = ["👥 *Son 10 Kullanıcı*\n"]
            for i, user in enumerate(users, 1):
                uid = user.get('user_id', 'N/A')
                lang = user.get('language', '?')
                lines.append(f"{i}. `{uid}` ({lang})")
            users_text = "\n".join(lines)
        
        await update.message.reply_text(users_text, parse_mode="Markdown", reply_markup=get_admin_keyboard())
    except Exception as e:
        await update.message.reply_text(f"❌ Hata: {e}")

async def start_broadcast_reply(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Duyuru gönderme modunu başlat (Reply Keyboard için)"""
    user_id = update.effective_user.id
    context.user_data['admin_broadcast'] = True
    await state.clear_user_states(user_id)  # Admin menüsünden çık
    
    reply_keyboard = ReplyKeyboardMarkup([["🔙 Admin Paneli"]], resize_keyboard=True, one_time_keyboard=True)
    
    await update.message.reply_text(
        "📢 *Duyuru Gönder*\n\n"
        "Tüm kullanıcılara göndermek istediğiniz mesajı yazın.\n"
        "İptal etmek için aşağıdaki butona basın.",
        reply_markup=reply_keyboard,
        parse_mode="Markdown"
    )

