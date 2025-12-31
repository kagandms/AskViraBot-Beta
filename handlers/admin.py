"""
Admin Panel Handler for DruzhikBot
Sadece ADMIN_IDS listesindeki kullanıcılar erişebilir.
"""

import asyncio
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import database as db
from config import ADMIN_IDS, TIMEZONE
import pytz

def is_admin(user_id: int) -> bool:
    """Kullanıcının admin olup olmadığını kontrol eder"""
    return user_id in ADMIN_IDS

def get_admin_keyboard():
    """Admin menü klavyesi"""
    keyboard = [
        [InlineKeyboardButton("📊 İstatistikler", callback_data="admin_stats")],
        [InlineKeyboardButton("📢 Duyuru Gönder", callback_data="admin_broadcast")],
        [InlineKeyboardButton("👥 Kullanıcı Listesi", callback_data="admin_users")],
        [InlineKeyboardButton("❌ Kapat", callback_data="admin_close")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin paneli ana komutu"""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        # Yetkisiz kullanıcılara sessizce yanıt verme veya uyar
        await update.message.reply_text("⛔ Bu komuta erişim yetkiniz yok.")
        return
    
    await update.message.reply_text(
        "🔧 *Admin Paneli*\n\nBir işlem seçin:",
        reply_markup=get_admin_keyboard(),
        parse_mode="Markdown"
    )

async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    
    keyboard = [[InlineKeyboardButton("❌ İptal", callback_data="admin_back")]]
    await query.edit_message_text(
        "📢 *Duyuru Gönder*\n\n"
        "Tüm kullanıcılara göndermek istediğiniz mesajı yazın.\n"
        "İptal etmek için aşağıdaki butona basın.",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def handle_broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Duyuru mesajını işle ve gönder"""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        return False
    
    if not context.user_data.get('admin_broadcast'):
        return False
    
    context.user_data['admin_broadcast'] = False
    message = update.message.text
    
    # Durum mesajı
    status_msg = await update.message.reply_text("📤 Duyuru gönderiliyor...")
    
    try:
        # Tüm kullanıcıları al
        users = await asyncio.to_thread(db.get_all_user_ids)
        
        sent = 0
        failed = 0
        
        for uid in users:
            try:
                await context.bot.send_message(
                    chat_id=uid,
                    text=f"📢 *Duyuru*\n\n{message}",
                    parse_mode="Markdown"
                )
                sent += 1
            except Exception:
                failed += 1
            
            # Rate limit için kısa bekleme
            await asyncio.sleep(0.05)
        
        await status_msg.edit_text(
            f"✅ *Duyuru Tamamlandı*\n\n"
            f"📤 Gönderilen: {sent}\n"
            f"❌ Başarısız: {failed}",
            parse_mode="Markdown"
        )
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
