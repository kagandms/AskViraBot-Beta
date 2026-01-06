
import logging
from config import supabase

logger = logging.getLogger(__name__)

# --- LOGGING ---
def log_xox_game(user_id: int | str, winner: str, difficulty: str) -> None:
    if not supabase: return
    try:
        data = {"user_id": str(user_id), "winner": winner, "difficulty": difficulty}
        supabase.table("xox_logs").insert(data).execute()
    except Exception as e:
        logger.error(f"XOX log hatası (User: {user_id}): {e}")

def log_tkm_game(user_id: int | str, user_move: str, bot_move: str, result: str) -> None:
    if not supabase: return
    try:
        data = {"user_id": str(user_id), "user_move": user_move, "bot_move": bot_move, "result": result}
        supabase.table("tkm_logs").insert(data).execute()
    except Exception as e:
        logger.error(f"TKM log hatası (User: {user_id}): {e}")

def log_coinflip(user_id: int | str, result: str) -> None:
    if not supabase: return
    try:
        data = {"user_id": str(user_id), "result": result}
        supabase.table("coinflip_logs").insert(data).execute()
    except Exception as e:
        logger.error(f"Coinflip log hatası (User: {user_id}): {e}")

def log_dice_roll(user_id: int | str, result: int) -> None:
    if not supabase: return
    try:
        data = {"user_id": str(user_id), "result": str(result)}
        supabase.table("dice_logs").insert(data).execute()
    except Exception as e:
        logger.error(f"Dice log hatası (User: {user_id}): {e}")

def log_blackjack_game(user_id: int | str, player_score: int, dealer_score: int, result: str) -> None:
    if not supabase: return
    try:
        data = {"user_id": str(user_id), "player_score": player_score, "dealer_score": dealer_score, "result": result}
        supabase.table("blackjack_logs").insert(data).execute()
    except Exception as e:
        logger.error(f"Blackjack log hatası (User: {user_id}): {e}")

def log_slot_game(user_id: int | str, symbols: str, result: str) -> None:
    if not supabase: return
    try:
        data = {"user_id": str(user_id), "symbols": symbols, "result": result}
        supabase.table("slot_logs").insert(data).execute()
    except Exception as e:
        logger.error(f"Slot log hatası (User: {user_id}): {e}")

# --- STATS ---
def get_user_xox_stats(user_id: int | str) -> dict[str, int]:
    if not supabase: return {"wins": 0, "losses": 0, "draws": 0, "total": 0}
    try:
        response = supabase.table("xox_logs").select("winner").eq("user_id", str(user_id)).execute()
        data = response.data if response.data else []
        wins = sum(1 for r in data if r.get("winner") == "X")
        losses = sum(1 for r in data if r.get("winner") == "O")
        draws = sum(1 for r in data if r.get("winner") == "Draw")
        return {"wins": wins, "losses": losses, "draws": draws, "total": len(data)}
    except Exception as e:
        logger.error(f"XOX stats hatası (User: {user_id}): {e}")
        return {"wins": 0, "losses": 0, "draws": 0, "total": 0}

def get_user_tkm_stats(user_id: int | str) -> dict[str, int]:
    if not supabase: return {"wins": 0, "losses": 0, "draws": 0, "total": 0}
    try:
        response = supabase.table("tkm_logs").select("result").eq("user_id", str(user_id)).execute()
        data = response.data if response.data else []
        wins = sum(1 for r in data if r.get("result") == "win")
        losses = sum(1 for r in data if r.get("result") == "lose")
        draws = sum(1 for r in data if r.get("result") == "draw")
        return {"wins": wins, "losses": losses, "draws": draws, "total": len(data)}
    except Exception as e:
        logger.error(f"TKM stats hatası (User: {user_id}): {e}")
        return {"wins": 0, "losses": 0, "draws": 0, "total": 0}

def get_user_blackjack_stats(user_id: int | str) -> dict[str, int]:
    if not supabase: return {"wins": 0, "losses": 0, "draws": 0, "total": 0}
    try:
        response = supabase.table("blackjack_logs").select("result").eq("user_id", str(user_id)).execute()
        data = response.data if response.data else []
        wins = sum(1 for r in data if r.get("result") == "win")
        losses = sum(1 for r in data if r.get("result") == "lose")
        draws = sum(1 for r in data if r.get("result") == "draw")
        return {"wins": wins, "losses": losses, "draws": draws, "total": len(data)}
    except Exception as e:
        logger.error(f"Blackjack stats hatası (User: {user_id}): {e}")
        return {"wins": 0, "losses": 0, "draws": 0, "total": 0}
