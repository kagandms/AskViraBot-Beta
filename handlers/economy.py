import asyncio
from telegram import Update
from telegram.ext import ContextTypes
import database as db
from texts import TEXTS
from utils import get_main_keyboard_markup, get_games_keyboard_markup

async def daily_bonus_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Günlük bonus komutu (/daily)"""
    user_id = update.effective_user.id
    lang = await db.get_user_lang(user_id)
    
    # Check status
    status = await asyncio.to_thread(db.get_daily_bonus_status, user_id)
    
    # Delete prompt message (clean up)
    try:
        await update.message.delete()
    except: pass
    
    if not status["can_claim"]:
        await context.bot.send_message(
            chat_id=user_id,
            text=TEXTS["daily_bonus_already_claimed"][lang],
            reply_markup=get_games_keyboard_markup(lang)
        )
        return
        
    # Claim bonus
    reward = await asyncio.to_thread(db.claim_daily_bonus, user_id)
    new_streak = status["streak"] + 1
    
    msg = TEXTS["daily_bonus_success"][lang].format(reward=reward, streak=new_streak)
    await context.bot.send_message(
        chat_id=user_id,
        text=msg,
        reply_markup=get_games_keyboard_markup(lang),
        parse_mode="Markdown"
    )

async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Bakiye sorgulama komutu (/balance veya 💰 Cüzdan)"""
    user_id = update.effective_user.id
    lang = await db.get_user_lang(user_id)
    
    # Delete prompt message (clean up)
    try:
        await update.message.delete()
    except: pass
    
    coins = await asyncio.to_thread(db.get_user_coins, user_id)
    
    msg = TEXTS["wallet_status"][lang].format(coins=coins)
    await context.bot.send_message(
        chat_id=user_id,
        text=msg,
        reply_markup=get_games_keyboard_markup(lang),
        parse_mode="Markdown"
    )


# --- MODULAR SETUP ---
def setup(app):
    from telegram.ext import CommandHandler
    
    app.add_handler(CommandHandler("daily", daily_bonus_command))
    app.add_handler(CommandHandler("balance", balance_command))
    
    logger = logging.getLogger(__name__) # Ensure logger exists or use predefined
    # economy.py doesn't seem to define 'logger' at top level based on view_file usage
    # Actually it implies logging is not used or it uses basic config.
    # It imports nothing but asyncio, update, context, db, texts, utils.
    # I should import logging inside setup or rely on print? No, use logger.
    import logging
    logging.getLogger(__name__).info("✅ Economy module loaded")
