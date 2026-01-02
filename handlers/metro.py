"""
Metro Istanbul Handler
Provides real-time metro departure times using IBB Metro Istanbul API
Optimized with caching and async HTTP requests for better performance
"""

import asyncio
import logging
from datetime import datetime, timedelta
import pytz
import aiohttp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
import database as db
from texts import TEXTS
from utils import get_tools_keyboard_markup
from rate_limiter import rate_limit
import state

logger = logging.getLogger(__name__)

# Istanbul timezone
ISTANBUL_TZ = pytz.timezone('Europe/Istanbul')

# API Base URL
METRO_API_BASE = "https://api.ibb.gov.tr/MetroIstanbul/api/MetroMobile/V2"

# --- CACHING SYSTEM ---
# Cache for metro lines (rarely changes)
_lines_cache = {"data": None, "expires": None}
# Cache for stations by line_id
_stations_cache = {}
# Cache TTL (Time To Live)
LINES_CACHE_TTL = timedelta(minutes=10)
STATIONS_CACHE_TTL = timedelta(minutes=5)

# Global HTTP session for connection pooling
_http_session = None


async def get_http_session():
    """Get or create a shared HTTP session for connection pooling"""
    global _http_session
    if _http_session is None or _http_session.closed:
        timeout = aiohttp.ClientTimeout(total=10)
        _http_session = aiohttp.ClientSession(timeout=timeout)
    return _http_session


async def close_http_session():
    """Close the HTTP session (call on bot shutdown)"""
    global _http_session
    if _http_session and not _http_session.closed:
        await _http_session.close()
        _http_session = None


# --- API HELPER FUNCTIONS ---

async def fetch_lines(force_refresh=False):
    """Fetch all metro lines with caching"""
    global _lines_cache
    
    # Check cache first
    now = datetime.now()
    if not force_refresh and _lines_cache["data"] and _lines_cache["expires"] and now < _lines_cache["expires"]:
        logger.debug("Returning cached metro lines")
        return _lines_cache["data"]
    
    try:
        session = await get_http_session()
        async with session.get(f"{METRO_API_BASE}/GetLines") as response:
            data = await response.json()
            if data.get("Success"):
                result = data.get("Data", [])
                # Update cache
                _lines_cache["data"] = result
                _lines_cache["expires"] = now + LINES_CACHE_TTL
                logger.debug("Fetched and cached metro lines from API")
                return result
    except Exception as e:
        logger.error(f"Metro API Error (GetLines): {e}")
        # Return cached data if available, even if expired
        if _lines_cache["data"]:
            logger.debug("Returning expired cache due to API error")
            return _lines_cache["data"]
    return []


async def fetch_stations_by_line(line_id: int, force_refresh=False):
    """Fetch stations for a specific line with caching"""
    global _stations_cache
    
    # Check cache first
    now = datetime.now()
    cache_key = str(line_id)
    if not force_refresh and cache_key in _stations_cache:
        cached = _stations_cache[cache_key]
        if cached["expires"] and now < cached["expires"]:
            logger.debug(f"Returning cached stations for line {line_id}")
            return cached["data"]
    
    try:
        session = await get_http_session()
        async with session.get(f"{METRO_API_BASE}/GetStationById/{line_id}") as response:
            data = await response.json()
            if data.get("Success"):
                result = data.get("Data", [])
                # Update cache
                _stations_cache[cache_key] = {
                    "data": result,
                    "expires": now + STATIONS_CACHE_TTL
                }
                logger.debug(f"Fetched and cached stations for line {line_id}")
                return result
    except Exception as e:
        logger.error(f"Metro API Error (GetStationById): {e}")
        # Return cached data if available
        if cache_key in _stations_cache:
            return _stations_cache[cache_key]["data"]
    return []


async def fetch_directions_by_line(line_id: int):
    """Fetch directions for a specific line (not cached - small data)"""
    try:
        session = await get_http_session()
        async with session.get(f"{METRO_API_BASE}/GetDirectionById/{line_id}") as response:
            data = await response.json()
            if data.get("Success"):
                return data.get("Data", [])
    except Exception as e:
        logger.error(f"Metro API Error (GetDirectionById): {e}")
    return []


async def fetch_timetable(station_id: int, direction_id: int):
    """Fetch departure times for a station and direction (never cached - real-time data)"""
    try:
        now = datetime.now(ISTANBUL_TZ).strftime("%Y-%m-%dT%H:%M:%S+03:00")
        payload = {
            "BoardingStationId": station_id,
            "DirectionId": direction_id,
            "DateTime": now
        }
        session = await get_http_session()
        async with session.post(
            f"{METRO_API_BASE}/GetTimeTable",
            json=payload,
            headers={"Content-Type": "application/json"}
        ) as response:
            data = await response.json()
            if data.get("Success"):
                return data.get("Data", [])
    except Exception as e:
        logger.error(f"Metro API Error (GetTimeTable): {e}")
    return []


# --- HANDLER LOGIC (REPLY KEYBOARD) ---

@rate_limit("heavy")
async def metro_menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Metro menüsünü başlat (Hatları listele)"""
    user_id = update.effective_user.id
    lang = await asyncio.to_thread(db.get_user_lang, user_id)
    
    # State başlat
    state.clear_user_states(user_id)
    state.metro_browsing.add(user_id)
    state.metro_selection[user_id] = {} # Boş seçim
    
    # Loading mesajı
    loading_texts = {"tr": "⏳ Hatlar yükleniyor...", "en": "⏳ Loading lines...", "ru": "⏳ Загрузка линий..."}
    loading_msg = await update.message.reply_text(loading_texts.get(lang, loading_texts["en"]))
    
    lines = await fetch_lines()
    
    # Loading mesajını sil
    try:
        await loading_msg.delete()
    except Exception:
        pass
    
    if not lines:
        await update.message.reply_text(TEXTS["metro_api_error"][lang])
        return

    # Sadece Metro hatları (M ile başlayanlar)
    metro_lines = [line for line in lines if line.get("Name", "").startswith("M")]
    
    if not metro_lines:
        await update.message.reply_text(TEXTS["metro_api_error"][lang])
        return
        
    # Klavye oluştur (2'li sıra)
    keyboard = []
    row = []
    for line in metro_lines:
        line_name = line.get("Name", "")
        if line_name:
            row.append(f"🚇 {line_name}")
            if len(row) == 2:
                keyboard.append(row)
                row = []
    if row:
        keyboard.append(row)
    
    # Geri butonu
    back_text = TEXTS["back_button"][lang] if "back_button" in TEXTS else ("⬅️ Geri" if lang == "tr" else "⬅️ Back")
    keyboard.append([back_text])
    
    await update.message.reply_text(
        TEXTS["metro_menu_prompt"][lang],
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True),
        parse_mode="Markdown"
    )

async def handle_metro_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Metro menüsü içindeki metin etkileşimlerini yönetir"""
    user_id = update.effective_user.id
    if user_id not in state.metro_browsing:
        return
        
    text = update.message.text
    lang = await asyncio.to_thread(db.get_user_lang, user_id)
    
    # Geri / Menü Kontrolü
    from texts import BUTTON_MAPPINGS
    back_keywords = BUTTON_MAPPINGS.get("back_button", []) + ["⬅️ Geri", "⬅️ Back", "geri", "back"]
    menu_keywords = BUTTON_MAPPINGS.get("menu", [])
    
    current_selection = state.metro_selection.get(user_id, {})
    
    # 1. MENÜYE DÖNÜŞ (Eğer ana menü komutu geldiyse)
    if text.lower() in menu_keywords:
        from handlers.general import tools_menu_command
        state.metro_browsing.discard(user_id)
        state.metro_selection.pop(user_id, None)
        await tools_menu_command(update, context)
        return

    # 2. GERİ BUOTNU MANTIĞI
    if text in back_keywords or text.lower() in back_keywords:
        # Eğer İstasyon seçiliyse -> Yön seçimi iptal, İstasyonlara dön (Aslında Yönü iptal edip İstasyon listesini tekrar gösteriyoruz, yani Hat seçili duruma dönüyoruz)
        # SIRA: Hat Seçimi -> İstasyon Seçimi -> Yön Seçimi
        
        if "station" in current_selection:
            # İstasyondan hatta dön
            current_selection.pop("station", None)
            current_selection.pop("station_name", None)
            await show_stations(update, context, current_selection["line"], current_selection["line_name"], lang)
            return
            
        elif "line" in current_selection:
            # Hattan hat listesine dön
            current_selection.pop("line", None)
            current_selection.pop("line_name", None)
            await metro_menu_command(update, context) # Hatları listele
            return
            
        else:
            # Metro'dan çık, Araçlar menüsüne dön
            from handlers.general import tools_menu_command
            state.metro_browsing.discard(user_id)
            state.metro_selection.pop(user_id, None)
            await tools_menu_command(update, context)
            return

    # 3. İLERİ YÖNLÜ SEÇİMLER
    
    # A) HAT SEÇİMİ (Henüz hat seçilmemişse)
    if "line" not in current_selection:
        lines = await fetch_lines()
        # Text "🚇 M1A Yenikapı..." gibi gelebilir. Parse etmeliyiz.
        # Basitçe text içinde M1A, M2 gibi kodları arayabiliriz veya tam eşleşme
        
        selected_line = None
        for line in lines:
            name = line.get("Name", "")
            # Kullanıcı butonuna tıkladıysa "🚇 M1A..." formatında gelir
            if name and name in text:
                selected_line = line
                break
        
        if selected_line:
            state.metro_selection[user_id]["line"] = selected_line["Id"]
            state.metro_selection[user_id]["line_name"] = selected_line["Name"]
            await show_stations(update, context, selected_line["Id"], selected_line["Name"], lang)
        else:
            await update.message.reply_text(TEXTS["invalid_selection"][lang])
        return

    # B) İSTASYON SEÇİMİ (Hat var, İstasyon yoksa)
    if "station" not in current_selection:
        stations = await fetch_stations_by_line(current_selection["line"])
        selected_station = None
        
        for station in stations:
            name = station.get("Description", station.get("Name", ""))
            # Butonda "📍 İstasyon Adı" yazıyor
            if name and name in text:
                selected_station = station
                break
        
        if selected_station:
            state.metro_selection[user_id]["station"] = selected_station["Id"]
            state.metro_selection[user_id]["station_name"] = selected_station.get("Description", "")
            await show_directions(update, context, current_selection["line"], selected_station["Id"], lang)
        else:
            await update.message.reply_text(TEXTS["invalid_selection"][lang])
        return

    # C) YÖN SEÇİMİ (Hat var, İstasyon var) -> Saatleri Göster
    # Yön seçimi yapıldığında state değişmez, sadece saatler gösterilir.
    # Kullanıcı tekrar farklı yön seçebilir veya geri dönebilir.
    
    directions = await fetch_directions_by_line(current_selection["line"])
    selected_dir = None
    
    for direction in directions:
        name = direction.get("DirectionName", "")
        # Butonda "➡️ Yön Adı" yazıyor
        if name and name in text:
            selected_dir = direction
            break
            
    if selected_dir:
        await show_timetable(update, context, current_selection["station"], selected_dir["DirectionId"], selected_dir["DirectionName"], lang)
    else:
        # Eğer "Yenile" butonuna basıldıysa (bunu text olarak yakalamak zor olabilir,
        # bu yüzden yenileme yerine tekrar yön seçimi mantıklı.
        # Veya özel bir "🔄 Yenile" butonu eklenebilir ama hangi yönü yenileyeceğini bilmeliyiz.
        # Şimdilik Yön butonuna tekrar basması yeterli.
        await update.message.reply_text(TEXTS["invalid_selection"][lang])


# --- HELPER FUNCTIONS FOR REPLY FLOW ---

async def show_stations(update, context, line_id, line_name, lang):
    # Loading mesajı
    loading_texts = {"tr": "⏳ İstasyonlar yükleniyor...", "en": "⏳ Loading stations...", "ru": "⏳ Загрузка станций..."}
    loading_msg = await update.message.reply_text(loading_texts.get(lang, loading_texts["en"]))
    
    stations = await fetch_stations_by_line(line_id)
    
    try:
        await loading_msg.delete()
    except Exception:
        pass
    
    if not stations:
        await update.message.reply_text(TEXTS["metro_api_error"][lang])
        return
        
    keyboard = []
    row = []
    for station in stations:
        name = station.get("Description", station.get("Name", ""))
        if name:
            row.append(f"📍 {name}")
            if len(row) == 2:
                keyboard.append(row)
                row = []
    if row:
        keyboard.append(row)
        
    back_text = TEXTS["back_button"][lang] if "back_button" in TEXTS else ("⬅️ Geri" if lang == "tr" else "⬅️ Back")
    keyboard.append([back_text])
    
    await update.message.reply_text(
        TEXTS["metro_select_station"][lang].format(line=line_name),
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

async def show_directions(update, context, line_id, station_id, lang):
    # Loading mesajı
    loading_texts = {"tr": "⏳ Yönler yükleniyor...", "en": "⏳ Loading directions...", "ru": "⏳ Загрузка направлений..."}
    loading_msg = await update.message.reply_text(loading_texts.get(lang, loading_texts["en"]))
    
    directions = await fetch_directions_by_line(line_id)
    
    try:
        await loading_msg.delete()
    except Exception:
        pass
    
    if not directions:
        await update.message.reply_text(TEXTS["metro_api_error"][lang])
        return
        
    keyboard = []
    for direction in directions:
        name = direction.get("DirectionName", "")
        if name:
            keyboard.append([f"➡️ {name}"])
            
    back_text = TEXTS["back_button"][lang] if "back_button" in TEXTS else ("⬅️ Geri" if lang == "tr" else "⬅️ Back")
    keyboard.append([back_text])
    
    await update.message.reply_text(
        TEXTS["metro_select_direction"][lang],
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

async def show_timetable(update, context, station_id, direction_id, direction_name, lang):
    # Loading mesajı
    loading_texts = {"tr": "⏳ Sefer saatleri yükleniyor...", "en": "⏳ Loading departure times...", "ru": "⏳ Загрузка расписания..."}
    loading_msg = await update.message.reply_text(loading_texts.get(lang, loading_texts["en"]))
    
    timetable_data = await fetch_timetable(station_id, direction_id)
    
    try:
        await loading_msg.delete()
    except Exception:
        pass
    
    if not timetable_data:
        await update.message.reply_text(TEXTS["metro_no_departures"][lang])
        return
        
    timetable = timetable_data[0]
    times = timetable.get("TimeInfos", {}).get("Times", [])
    
    if not times:
        await update.message.reply_text(TEXTS["metro_no_departures"][lang])
        return
        
    now = datetime.now(ISTANBUL_TZ)
    departure_lines = []
    
    for time_str in times[:6]:
        try:
            hour, minute = map(int, time_str.split(":"))
            departure_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if departure_time < now: continue
            
            minutes_until = int((departure_time - now).total_seconds() / 60)
            
            if minutes_until <= 1:
                departure_lines.append(f"🚇 {time_str} ({'şimd' if lang=='tr' else 'now'})")
            else:
                departure_lines.append(f"🕒 {time_str} ({minutes_until} min/dk)")
        except ValueError:
            departure_lines.append(f"🕒 {time_str}")
            
    if not departure_lines:
        await update.message.reply_text(TEXTS["metro_no_departures"][lang])
        return
        
    header = TEXTS["metro_departures_header"][lang].format(
        line=state.metro_selection[update.effective_user.id].get("line_name", ""),
        station=state.metro_selection[update.effective_user.id].get("station_name", ""),
        direction=direction_name
    )
    
    message = header + "\n\n" + "\n".join(departure_lines)
    
    # Klavye değişmiyor, kullanıcı tekrar yön seçebilir
    await update.message.reply_text(message)
