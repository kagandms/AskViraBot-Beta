import asyncio
from telegram import Update
from telegram.ext import ContextTypes
import database as db
from texts import TEXTS

async def daily_bonus_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Günlük bonus komutu (/daily)"""
    user_id = update.effective_user.id
    lang = await asyncio.to_thread(db.get_user_lang, user_id)
    
    # Check status
    status = await asyncio.to_thread(db.get_daily_bonus_status, user_id)
    
    # Delete prompt message (clean up)
    try:
        await update.message.delete()
    except: pass
    
    if not status["can_claim"]:
        await update.message.reply_text(TEXTS["daily_bonus_already_claimed"][lang])
        return
        
    # Claim bonus
    reward = await asyncio.to_thread(db.claim_daily_bonus, user_id)
    streak = status["streak"]
    
    msg = TEXTS["daily_bonus_success"][lang].format(reward=reward, streak=streak)
    await update.message.reply_text(msg, parse_mode="Markdown")

async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Bakiye sorgulama komutu (/balance veya 💰 Cüzdan)"""
    user_id = update.effective_user.id
    lang = await asyncio.to_thread(db.get_user_lang, user_id)
    
    # Delete prompt message (clean up)
    try:
        await update.message.delete()
    except: pass
    
    coins = await asyncio.to_thread(db.get_user_coins, user_id)
    
    msg = TEXTS["wallet_status"][lang].format(coins=coins)
    await update.message.reply_text(msg, parse_mode="Markdown")
