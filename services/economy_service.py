
import logging
from config import supabase, ADMIN_IDS
from typing import Any
from datetime import date, timedelta

logger = logging.getLogger(__name__)

# --- COINS ---
def get_user_coins(user_id: int | str) -> int:
    if int(user_id) in ADMIN_IDS:
        return 999999999
    
    if not supabase: return 1000
    try:
        response = supabase.table("users").select("coins").eq("user_id", str(user_id)).execute()
        if response.data:
            coins = response.data[0].get("coins")
            return coins if coins is not None else 1000
        return 1000
    except Exception as e:
        logger.error(f"Coin getirme hatası (User: {user_id}): {e}")
        return 1000

def set_user_coins(user_id: int | str, amount: int) -> bool:
    if not supabase: return False
    try:
        supabase.table("users").update({"coins": amount}).eq("user_id", str(user_id)).execute()
        return True
    except Exception as e:
        logger.error(f"Coin güncelleme hatası (User: {user_id}): {e}")
        return False

def add_user_coins(user_id: int | str, amount: int) -> int:
    if not supabase: return 1000
    try:
        current_coins = get_user_coins(user_id)
        new_coins = current_coins + amount
        if new_coins < 0: new_coins = 0
            
        set_user_coins(user_id, new_coins)
        return new_coins
    except Exception as e:
        logger.error(f"Coin ekleme hatası (User: {user_id}): {e}")
        return 1000

# --- DAILY BONUS ---
def get_daily_bonus_status(user_id: int | str) -> dict:
    if not supabase: return {"can_claim": True, "streak": 1}
    try:
        response = supabase.table("daily_bonuses").select("*").eq("user_id", str(user_id)).execute()
        if not response.data:
            return {"can_claim": True, "streak": 1}
        
        last_claimed = response.data[0]["last_claimed_date"]
        streak = response.data[0]["streak_count"]
        
        today = date.today()
        last_date = date.fromisoformat(last_claimed)
        
        if last_date < today:
            if last_date == today - timedelta(days=1):
                new_streak = streak + 1
            elif last_date == today:
                new_streak = streak
            else:
                new_streak = 1
            return {"can_claim": True, "streak": new_streak, "last_claimed": last_claimed}
            
        return {"can_claim": False, "streak": streak, "last_claimed": last_claimed}
    except Exception as e:
        logger.error(f"Daily bonus status check error: {e}")
        return {"can_claim": True, "streak": 1}

def claim_daily_bonus(user_id: int | str) -> int:
    if not supabase: return 0
    try:
        status = get_daily_bonus_status(user_id)
        if not status["can_claim"]: return 0
            
        streak = status["streak"]
        base_reward = 100
        streak_bonus = min((streak - 1) * 10, 500)
        total_reward = base_reward + streak_bonus
        
        add_user_coins(user_id, total_reward)
        
        today_str = date.today().isoformat()
        data = {
            "user_id": str(user_id),
            "last_claimed_date": today_str,
            "streak_count": streak
        }
        supabase.table("daily_bonuses").upsert(data).execute()
        return total_reward
    except Exception as e:
        logger.error(f"Claim daily bonus error: {e}")
        return 0
