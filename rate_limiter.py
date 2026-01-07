"""
Rate Limiter Module for ViraBot
Kullanıcı bazlı rate limiting sistemi.
"""

import time
from collections import defaultdict
from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes
import asyncio
import database as db

# Rate limit ayarları (dakika başına istek sayısı)
RATE_LIMITS = {
    "general": 45,      # Genel limit
    "games": 30,        # Oyunlar için
    "heavy": 30,        # Yoğun işlemler (PDF, QR, hava durumu)
}

# Kullanıcı istek geçmişi: {user_id: {category: [timestamp1, timestamp2, ...]}}
user_requests = defaultdict(lambda: defaultdict(list))

# Rate limit süresi (saniye cinsinden - 1 dakika)
WINDOW_SECONDS = 60

# Memory leak önleme: Son temizleme zamanı ve temizleme aralığı
_last_cleanup_time = time.time()
CLEANUP_INTERVAL = 300  # Her 5 dakikada bir temizlik yap (saniye)
INACTIVE_THRESHOLD = 600  # 10 dakika aktif olmayan kullanıcıları temizle (saniye)
def _cleanup_old_records():
    """
    Eski ve inaktif kullanıcı kayıtlarını temizler.
    Memory leak önlemek için periyodik olarak çağrılır.
    """
    global _last_cleanup_time
    current_time = time.time()
    
    # Sadece belirli aralıklarla temizlik yap
    if current_time - _last_cleanup_time < CLEANUP_INTERVAL:
        return
    
    _last_cleanup_time = current_time
    users_to_remove = []
    
    for user_id in list(user_requests.keys()):
        user_data = user_requests[user_id]
        all_timestamps = []
        
        # Tüm kategorilerdeki timestamp'leri topla
        for category in list(user_data.keys()):
            # Eski timestamp'leri temizle
            user_data[category] = [
                ts for ts in user_data[category]
                if current_time - ts < WINDOW_SECONDS
            ]
            all_timestamps.extend(user_data[category])
            
            # Boş kategoriyi sil
            if not user_data[category]:
                del user_data[category]
        
        # Hiç aktif kaydı kalmayan veya uzun süredir inaktif olan kullanıcıyı işaretle
        if not all_timestamps:
            users_to_remove.append(user_id)
        elif current_time - max(all_timestamps) > INACTIVE_THRESHOLD:
            users_to_remove.append(user_id)
    
    # İşaretlenen kullanıcıları sil
    for user_id in users_to_remove:
        if user_id in user_requests:
            del user_requests[user_id]
def is_rate_limited(user_id: int, category: str = "general") -> bool:
    """
    Kullanıcının rate limit'e takılıp takılmadığını kontrol eder.
    
    Args:
        user_id: Telegram kullanıcı ID'si
        category: Limit kategorisi ("general", "games", "heavy")
    
    Returns:
        True eğer kullanıcı limite takıldıysa, False değilse
    """
    # Periyodik temizlik (memory leak önleme)
    _cleanup_old_records()

    current_time = time.time()
    limit = RATE_LIMITS.get(category, RATE_LIMITS["general"])
    
    # Eski istekleri temizle (pencere dışındakiler)
    user_requests[user_id][category] = [
        ts for ts in user_requests[user_id][category]
        if current_time - ts < WINDOW_SECONDS
    ]
    
    # Limit kontrolü
    if len(user_requests[user_id][category]) >= limit:
        return True
    
    # Yeni isteği kaydet
    user_requests[user_id][category].append(current_time)
    return False
def get_remaining_cooldown(user_id: int, category: str = "general") -> int:
    """
    Kullanıcının ne kadar süre beklemesi gerektiğini döner.
    
    Returns:
        Kalan bekleme süresi (saniye)
    """
    # Periyodik temizlik (memory leak önleme)
    _cleanup_old_records()

    if not user_requests[user_id][category]:
        return 0
    
    current_time = time.time()
    oldest_request = min(user_requests[user_id][category])
    remaining = WINDOW_SECONDS - (current_time - oldest_request)
    
    return max(0, int(remaining))
def rate_limit(category: str = "general"):
    """
    Rate limiting decorator'ü.
    
    Kullanım:
        @rate_limit("games")
        async def my_game_handler(update, context):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):

            
            user_id = update.effective_user.id
            
            if is_rate_limited(user_id, category):
                cooldown = get_remaining_cooldown(user_id, category)
                
                # Kullanıcının dilini al
                lang = await db.get_user_lang(user_id)
                
                # Çok dilli rate limit mesajları
                messages = {
                    "general": {
                        "tr": f"⏳ Çok fazla istek gönderdiniz. Lütfen {cooldown} saniye bekleyin.",
                        "en": f"⏳ Too many requests. Please wait {cooldown} seconds.",
                        "ru": f"⏳ Слишком много запросов. Подождите {cooldown} секунд."
                    },
                    "games": {
                        "tr": f"🎮 Oyun limitine ulaştınız. Lütfen {cooldown} saniye bekleyin.",
                        "en": f"🎮 Game limit reached. Please wait {cooldown} seconds.",
                        "ru": f"🎮 Лимит игр достигнут. Подождите {cooldown} секунд."
                    },
                    "heavy": {
                        "tr": f"⚙️ İşlem limitine ulaştınız. Lütfen {cooldown} saniye bekleyin.",
                        "en": f"⚙️ Operation limit reached. Please wait {cooldown} seconds.",
                        "ru": f"⚙️ Лимит операций достигнут. Подождите {cooldown} секунд."
                    },
                }
                
                category_msgs = messages.get(category, messages["general"])
                message = category_msgs.get(lang, category_msgs["en"])
                
                if update.message:
                    await update.message.reply_text(message)
                elif update.callback_query:
                    await update.callback_query.answer(message, show_alert=True)
                
                return None
            
            return await func(update, context, *args, **kwargs)
        return wrapper
    return decorator
def clear_user_limits(user_id: int):
    """Belirli bir kullanıcının tüm limitlerini temizler."""
    if user_id in user_requests:
        del user_requests[user_id]
def get_user_stats(user_id: int) -> dict:
    """Kullanıcının mevcut istek istatistiklerini döner."""
    current_time = time.time()
    stats = {}
    
    for category, limit in RATE_LIMITS.items():
        # Geçerli istekleri say
        valid_requests = [
            ts for ts in user_requests[user_id][category]
            if current_time - ts < WINDOW_SECONDS
        ]
        stats[category] = {
            "used": len(valid_requests),
            "limit": limit,
            "remaining": limit - len(valid_requests)
        }
    
    return stats
