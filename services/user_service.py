
import logging
from typing import Any
from config import supabase
import asyncio

logger = logging.getLogger(__name__)

# --- LANGUAGE ---

from models.user_model import UserModel

# --- USER MODEL ACCESS ---
def get_user_model(user_id: int | str) -> UserModel:
    """Fetch full user object as Pydantic model."""
    user_id = str(user_id)
    if not supabase: return UserModel(user_id=user_id)
    try:
        response = supabase.table("users").select("*").eq("user_id", user_id).execute()
        if response.data:
            return UserModel(**response.data[0])
        return UserModel(user_id=user_id)
    except Exception as e:
        logger.error(f"User model fetch error: {e}")
        return UserModel(user_id=user_id)

# --- LANGUAGE ---
from services.cache_service import get_cache, set_cache, delete_cache

# --- LANGUAGE ---
# _user_lang_cache removed in favor of Redis

async def get_user_lang(user_id: int | str) -> str:
    user_id = str(user_id)
    cache_key = f"lang:{user_id}"
    
    # 1. Try Cache
    cached = await get_cache(cache_key)
    if cached:
        return cached
        
    # 2. Fallback to DB (Sync call wrapped in thread)
    def _fetch_db():
        if not supabase: return "en"
        try:
            response = supabase.table("users").select("language").eq("user_id", user_id).execute()
            if response.data:
                return response.data[0]["language"]
            return "en"
        except Exception as e:
            logger.error(f"Dil getirme hatası (User: {user_id}): {e}")
            return "en"

    lang = await asyncio.to_thread(_fetch_db)
    
    # 3. Set Cache
    await set_cache(cache_key, lang, ttl=86400) # 24 hours
    return lang

async def set_user_lang_db(user_id: int | str, lang: str) -> None:
    user_id = str(user_id)
    cache_key = f"lang:{user_id}"
    
    # 1. Update Cache
    await set_cache(cache_key, lang, ttl=86400)
    
    # 2. Update DB (Sync call wrapped in thread)
    def _update_db():
        if not supabase: return
        try:
            data = {"user_id": user_id, "language": lang}
            supabase.table("users").upsert(data).execute()
        except Exception as e:
            logger.error(f"Dil kaydetme hatası (User: {user_id}, Lang: {lang}): {e}")
            
    await asyncio.to_thread(_update_db)

# --- STATE MANAGEMENT ---
def set_user_state(user_id: int | str, state_name: str, state_data: dict = None) -> None:
    if not supabase: return
    if state_data is None: state_data = {}
    
    try:
        data = {
            "user_id": str(user_id),
            "state_name": state_name,
            "state_data": state_data,
            "updated_at": "now()"
        }
        supabase.table("user_states").upsert(data).execute()
    except Exception as e:
        logger.error(f"Error setting state for {user_id}: {e}")

def get_user_state(user_id: int | str) -> dict:
    if not supabase: return None
    try:
        response = supabase.table("user_states").select("*").eq("user_id", str(user_id)).execute()
        if response.data:
            return response.data[0]
        return None
    except Exception as e:
        logger.error(f"Error getting state for {user_id}: {e}")
        return None

def clear_user_state(user_id: int | str) -> None:
    if not supabase: return
    try:
        supabase.table("user_states").delete().eq("user_id", str(user_id)).execute()
    except Exception as e:
        logger.error(f"Error clearing state for {user_id}: {e}")

# --- ADMIN ---
def get_all_users_count() -> int:
    if not supabase: return 0
    try:
        response = supabase.table("users").select("user_id", count="exact").execute()
        return response.count if response.count else 0
    except Exception as e:
        logger.error(f"Kullanıcı sayısı hatası: {e}")
        return 0

def get_all_user_ids() -> list[int]:
    if not supabase: return []
    try:
        response = supabase.table("users").select("user_id").execute()
        return [int(u['user_id']) for u in response.data] if response.data else []
    except Exception as e:
        logger.error(f"Kullanıcı listesi hatası: {e}")
        return []

def get_recent_users(limit: int = 10) -> list[UserModel]:
    if not supabase: return []
    try:
        response = supabase.table("users").select("*").order("created_at", desc=True).limit(limit).execute()
        # Return list of UserModels
        return [UserModel(**u) for u in response.data] if response.data else []
    except Exception as e:
        logger.error(f"Son kullanıcılar hatası: {e}")
        return []

