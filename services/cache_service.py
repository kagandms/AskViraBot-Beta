
import os
import logging
import asyncio
from typing import Optional, Any
import json

try:
    from redis.asyncio import Redis, ConnectionError
except ImportError:
    Redis = None
    ConnectionError = Exception

logger = logging.getLogger(__name__)

# Singleton Redis Client
redis_client: Optional[Redis] = None

def init_redis():
    """Redis bağlantısını başlat."""
    global redis_client
    redis_url = os.getenv("REDIS_URL")
    
    if not redis_url:
        logger.warning("⚠️ REDIS_URL not found in env. Caching disabled.")
        return

    if not Redis:
        logger.error("❌ Redis library not installed. Install with 'pip install redis'")
        return

    try:
        redis_client = Redis.from_url(
            redis_url, 
            decode_responses=True,
            socket_timeout=2.0
        )
        logger.info("✅ Redis Initialized")
    except Exception as e:
        logger.error(f"❌ Redis Init Error: {e}")

async def get_cache(key: str) -> Optional[Any]:
    """Get value from cache."""
    if not redis_client:
        return None
    try:
        value = await redis_client.get(key)
        return json.loads(value) if value else None
    except ConnectionError:
        logger.error("❌ Redis Connection Error (GET)")
        return None
    except Exception:
        # Simple string fallback if json load fails? 
        # For now assume mostly JSON. If raw string needed, handle separately.
        return value

async def set_cache(key: str, value: Any, ttl: int = 3600):
    """Set value to cache with TTL."""
    if not redis_client:
        return
    try:
        serialized = json.dumps(value)
        await redis_client.setex(key, ttl, serialized)
    except ConnectionError:
        logger.error("❌ Redis Connection Error (SET)")
    except Exception as e:
        logger.error(f"Redis Set Error: {e}")

async def delete_cache(key: str):
    """Delete value from cache."""
    if not redis_client:
        return
    try:
        await redis_client.delete(key)
    except Exception:
        pass
