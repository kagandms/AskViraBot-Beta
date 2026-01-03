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
async def metro_menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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
    
    # Favoriler butonu
    fav_texts = {"tr": "⭐ Favorilerim", "en": "⭐ My Favorites", "ru": "⭐ Избранное"}
    keyboard.append([fav_texts.get(lang, fav_texts["en"])])
    
    # Geri butonu - Araçlar menüsüne döner
    back_texts = {"tr": "🔙 Araçlar Menüsü", "en": "🔙 Tools Menu", "ru": "🔙 Меню Инструментов"}
    keyboard.append([back_texts.get(lang, back_texts["en"])])
    
    await update.message.reply_text(
        TEXTS["metro_menu_prompt"][lang],
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True),
        parse_mode="Markdown"
    )

async def handle_metro_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Metro menüsü içindeki metin etkileşimlerini yönetir"""
    user_id = update.effective_user.id
    if user_id not in state.metro_browsing:
        return
        
    text = update.message.text
    from texts import turkish_lower
    text_lower = turkish_lower(text)
    
    lang = await asyncio.to_thread(db.get_user_lang, user_id)
    
    # Geri / Menü Kontrolü
    from texts import BUTTON_MAPPINGS
    back_keywords = BUTTON_MAPPINGS.get("back_to_tools", set()) | {"🔙 araçlar menüsü", "🔙 tools menu", "🔙 меню инструментов", "geri", "back", "назад"}
    menu_keywords = BUTTON_MAPPINGS.get("menu", [])
    
    current_selection = state.metro_selection.get(user_id, {})
    
    # 1. MENÜYE DÖNÜŞ (Eğer ana menü komutu geldiyse)
    if text_lower in menu_keywords:
        from handlers.general import tools_menu_command
        state.metro_browsing.discard(user_id)
        state.metro_selection.pop(user_id, None)
        await tools_menu_command(update, context)
        return

    # 2. GERİ BUOTNU MANTIĞI - Tüm geri butonlarını kontrol et
    all_back_keywords = back_keywords | {"🔙 hat listesi", "🔙 line list", "🔙 список линий", 
                                         "🔙 istasyon listesi", "🔙 station list", "🔙 список станций"}
    if text_lower in all_back_keywords or any(kw in text_lower for kw in ["geri", "back", "назад", "hat listesi", "istasyon listesi", "araçlar menüsü", "tools menu"]):
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

    # 2.2 FAVORİ KULLANIMI (En üstte kontrol edilmeli)
    # ⭐ FAV... butonuna basıldığında
    # DİKKAT: text_lower kullanma! "Favoriye Ekle" ile çakışıyor.
    # O yüzden direkt "⭐ FAV" (Büyük harf) kontrolü yapıyoruz.
    if text.startswith("⭐ FAV"):
        await use_favorite(update, context, text, lang, user_id)
        return

    # 2.5 FAVORİYE EKLE BUTONU KONTROLÜ (Önce kontrol edilmeli çünkü içinde ⭐ var)
    add_fav_keywords = ["favoriye ekle", "add to favorites", "добавить в избранное", "⭐ ekle", "⭐ add"]
    if any(kw in text_lower for kw in add_fav_keywords):
        await save_to_favorites(update, context, lang, user_id)
        return

    # 2.55 METRO MENÜSÜ GERİ BUTONU (Favoriler ana menüsünden gelir -> Hat Listesine dön)
    if any(kw in text_lower for kw in ["🔙 metro menüsü", "🔙 metro menu", "🔙 меню метро"]):
        await metro_menu_command(update, context)
        return

    # 2.6 FAVORİLER MENÜSÜ BUTONLARI (Alt menü butonları)
    # "Favori İstasyonlar" butonu
    if any(kw in text_lower for kw in ["favori istasyonlar", "favorite stations", "избранные станции", "🚀"]):
        await show_favorites_list(update, context, lang)
        return
    if any(kw in text_lower for kw in ["favorileri düzenle", "edit favorites", "ред. избранное"]):
        await show_favorites_edit_menu(update, context, lang)
        return

    # 2.7 ANA FAVORİLER BUTONU KONTROLÜ (En sona bırakıldı ki diğer ⭐'ları yutmasın)
    fav_keywords = ["favorilerim", "my favorites", "избранное", "⭐"]
    if any(kw in text_lower for kw in fav_keywords):
        await show_favorites(update, context, lang)
        return

    # 2.8 FAVORİLER MENÜSÜ GERİ BUTONU (Özel case)
    # Bu buton "Show Favorites List" içinden geliyor, ana favori menüsüne dönmeli
    fav_back_keywords = ["🔙 favoriler menüsü", "🔙 favorites menu", "🔙 меню избранного"]
    if any(kw in text_lower for kw in fav_back_keywords):
        await show_favorites(update, context, lang)
        return

    # 2.9 SİLME BUTONU KONTROLÜ (🗑️ FAV...)
    if text.startswith("🗑️ FAV"):
        await delete_favorite(update, context, text, lang, user_id)
        return

    # 3. İLERİ YÖNLÜ SEÇİMLER
    
    # A) HAT SEÇİMİ (Henüz hat seçilmemişse)
    if "line" not in current_selection:
        # Favori seçimi kontrolü BURADAN KALDIRILDI (Yukarı taşındı)
        
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
        
    # Geri butonu - Hat listesine döner
    back_texts = {"tr": "🔙 Hat Listesi", "en": "🔙 Line List", "ru": "🔙 Список Линий"}
    keyboard.append([back_texts.get(lang, back_texts["en"])])
    
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
            
    # Geri butonu - İstasyon listesine döner
    back_texts = {"tr": "🔙 İstasyon Listesi", "en": "🔙 Station List", "ru": "🔙 Список Станций"}
    keyboard.append([back_texts.get(lang, back_texts["en"])])
    
    await update.message.reply_text(
        TEXTS["metro_select_direction"][lang],
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

async def show_timetable(update, context, station_id, direction_id, direction_name, lang, is_favorite_view=False):
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
    
    # Butonları ayarla
    keyboard = []
    
    if not is_favorite_view:
        # Favoriye ekle butonu (Sadece normal gezintide göster)
        fav_add_texts = {"tr": "⭐ Favoriye Ekle", "en": "⭐ Add to Favorites", "ru": "⭐ Добавить в Избранное"}
        keyboard.append([fav_add_texts.get(lang, fav_add_texts["en"])])
        
        # İstasyon Listesine dön
        back_texts = {"tr": "🔙 İstasyon Listesi", "en": "🔙 Station List", "ru": "🔙 Список Станций"}
        keyboard.append([back_texts.get(lang, back_texts["en"])])
    else:
        # Favoriler Menüsüne dön
        back_texts = {"tr": "🔙 Favoriler Menüsü", "en": "🔙 Favorites Menu", "ru": "🔙 Меню Избранного"}
        keyboard.append([back_texts.get(lang, back_texts["en"])])

    await update.message.reply_text(
        message,
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )


# --- FAVORİ FONKSİYONLARI ---

async def show_favorites(update: Update, context: ContextTypes.DEFAULT_TYPE, lang: str) -> None:
    """Favoriler alt menüsünü gösterir (Göster / Düzenle)."""
    
    menu_texts = {
        "tr": "⭐ *Favoriler Menüsü*\n\nLütfen yapmak istediğiniz işlemi seçin:",
        "en": "⭐ *Favorites Menu*\n\nPlease select an action:",
        "ru": "⭐ *Меню Избранного*\n\nПожалуйста, выберите действие:"
    }
    
    btn_show = {"tr": "⭐ Favori İstasyonlar", "en": "⭐ Favorite Stations", "ru": "⭐ Избранные Станции"}
    btn_edit = {"tr": "✏️ Favorileri Düzenle", "en": "✏️ Edit Favorites", "ru": "✏️ Ред. Избранное"}
    btn_back = {"tr": "🔙 Metro Menüsü", "en": "🔙 Metro Menu", "ru": "🔙 Меню Метро"}
    
    keyboard = [
        [btn_show.get(lang, btn_show["en"]), btn_edit.get(lang, btn_edit["en"])],
        [btn_back.get(lang, btn_back["en"])]
    ]
    
    await update.message.reply_text(
        menu_texts.get(lang, menu_texts["en"]),
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True),
        parse_mode="Markdown"
    )

async def show_favorites_list(update: Update, context: ContextTypes.DEFAULT_TYPE, lang: str) -> None:
    """Favorileri HIZLI ERİŞİM butonlarıyla listeler."""
    user_id = update.effective_user.id
    favorites = await asyncio.to_thread(db.get_metro_favorites, user_id)
    
    if not favorites:
        no_fav_texts = {
            "tr": "📂 Listeniz boş.\nFavori eklemek için hat ve durak seçip 'Favoriye Ekle' butonuna basın.",
            "en": "📂 List is empty.\nTo add a favorite, select a line and station then press 'Add to Favorites'.",
            "ru": "📂 Список пуст.\nЧтобы добавить, выберите линию и станцию, затем нажмите 'Добавить'."
        }
        await update.message.reply_text(no_fav_texts.get(lang, no_fav_texts["en"]))
        await show_favorites(update, context, lang) # Menüye dön
        return
        
    keyboard = []
    # Header
    msg_lines = []
    header = {"tr": "🚀 *Hızlı Erişim*\nBir favoriye tıklayarak anında sefer saatlerini görebilirsiniz:\n", 
              "en": "🚀 *Quick Acess*\nClick a favorite to see departure times instantly:\n",
              "ru": "🚀 *Быстрый Доступ*\nНажмите, чтобы мгновенно увидеть расписание:\n"}
    msg_lines.append(header.get(lang, header["en"]))
    
    for i, fav in enumerate(favorites[:6], 1): # Max 6
        station = fav.get("station_name", "?")
        direction = fav.get("direction_name", "?")
        
        # Buton metni: "⭐ FAV1: Yenikapı -> Hacıosman"
        btn_text = f"⭐ FAV{i}: {station} -> {direction}"
        if len(btn_text) > 30: # Buton çok uzun olmasın
            btn_text = f"⭐ FAV{i}: {station[:10]}.. -> {direction[:10]}.."
            
        keyboard.append([btn_text])
        msg_lines.append(f"{i}. 🚇 {fav.get('line_name')} | {station} → {direction}")
        
    back_texts = {"tr": "🔙 Favoriler Menüsü", "en": "🔙 Favorites Menu", "ru": "🔙 Меню Избранного"}
    keyboard.append([back_texts.get(lang, back_texts["en"])])
    
    await update.message.reply_text(
        "\n".join(msg_lines),
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True),
        parse_mode="Markdown"
    )

async def show_favorites_edit_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, lang: str) -> None:
    """Favorileri SİLME butonlarıyla listeler."""
    user_id = update.effective_user.id
    favorites = await asyncio.to_thread(db.get_metro_favorites, user_id)
    
    if not favorites:
        no_fav_texts = {
            "tr": "📂 Listeniz boş. Silinecek bir şey yok.",
            "en": "📂 List is empty. Nothing to delete.",
            "ru": "📂 Список пуст. Нечего удалять."
        }
        await update.message.reply_text(no_fav_texts.get(lang, no_fav_texts["en"]))
        await show_favorites(update, context, lang)
        return

    keyboard = []
    # Header
    msg_lines = []
    header = {"tr": "🗑️ *Favori Silme*\nSilmek istediğiniz favoriye tıklayın:\n", 
              "en": "🗑️ *Delete Favorite*\nClick the favorite you want to delete:\n",
              "ru": "🗑️ *Удаление*\nНажмите, чтобы удалить:\n"}
    msg_lines.append(header.get(lang, header["en"]))
    
    for i, fav in enumerate(favorites[:6], 1): # Max 6
        station = fav.get("station_name", "?")
        direction = fav.get("direction_name", "?")
        
        # Buton metni: "🗑️ FAV1: Yenikapı -> Hacıosman"
        btn_text = f"🗑️ FAV{i}: {station} -> {direction}"
        if len(btn_text) > 30: 
            btn_text = f"🗑️ FAV{i}: {station[:10]}.. -> {direction[:10]}.."
            
        keyboard.append([btn_text])
        msg_lines.append(f"{i}. 🚇 {fav.get('line_name')} | {station} → {direction}")
        
    back_texts = {"tr": "🔙 Favoriler Menüsü", "en": "🔙 Favorites Menu", "ru": "🔙 Меню Избранного"}
    keyboard.append([back_texts.get(lang, back_texts["en"])])
    
    await update.message.reply_text(
        "\n".join(msg_lines),
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True),
        parse_mode="Markdown"
    )

async def delete_favorite(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, lang: str, user_id: int) -> None:
    """Seçilen favoriyi siler."""
    favorites = await asyncio.to_thread(db.get_metro_favorites, user_id)
    fav_index = -1
    
    try:
        # "🗑️ FAV1:" formatından numara çıkar
        fav_num = int(text.split("FAV")[1].split(":")[0].strip())
        fav_index = fav_num - 1
        
        if fav_index < 0 or fav_index >= len(favorites):
            raise ValueError
            
        fav = favorites[fav_index]
        
        # DB'den sil
        success = await asyncio.to_thread(
            db.remove_metro_favorite, 
            user_id, 
            fav["station_id"], 
            fav["direction_id"]
        )
        
        if success:
            del_texts = {"tr": "✅ Favori silindi!", "en": "✅ Favorite deleted!", "ru": "✅ Удалено!"}
            await update.message.reply_text(del_texts.get(lang, del_texts["en"]))
            # Listeyi yenile
            await show_favorites_edit_menu(update, context, lang)
        else:
            await update.message.reply_text("❌ Silinirken bir hata oluştu.")
            
    except (ValueError, IndexError, KeyError):
        await update.message.reply_text("⚠️ Geçersiz seçim.")


async def save_to_favorites(update: Update, context: ContextTypes.DEFAULT_TYPE, lang: str, user_id: int) -> None:
    """Mevcut seçimi favorilere kaydeder ve ANA MENÜYE yönlendirir."""
    selection = state.metro_selection.get(user_id, {})
    
    required_keys = ["line", "line_name", "station", "station_name", "direction_id", "direction_name"]
    if not all(k in selection for k in required_keys):
        await update.message.reply_text("⚠️ Hata: Seçim bilgisi eksik.")
        return
    
    success = await asyncio.to_thread(
        db.add_metro_favorite,
        user_id,
        selection["line"], selection["line_name"],
        selection["station"], selection["station_name"],
        selection["direction_id"], selection["direction_name"]
    )
    
    if success:
        success_texts = {
            "tr": f"✅ {selection['station_name']} favorilere eklendi! Ana menüye dönülüyor...",
            "en": f"✅ {selection['station_name']} added! Returning to main menu...",
            "ru": f"✅ {selection['station_name']} добавлен! Возврат в главное меню..."
        }
        await update.message.reply_text(success_texts.get(lang, success_texts["en"]))
        
        # Seçimi temizle ve Hat listesine (Ana Metro Menüsü) dön
        state.metro_selection[user_id] = {} # Reset selection
        await metro_menu_command(update, context)
        
    else:
        # Zaten varsa da dönelim mi? Kullanıcı "eklendi" sanıp dönmek isteyebilir.
        exists_texts = {
            "tr": "ℹ️ Bu istasyon zaten favori listenizde.",
            "en": "ℹ️ Already in favorites.",
            "ru": "ℹ️ Уже в избранном."
        }
        await update.message.reply_text(exists_texts.get(lang, exists_texts["en"]))
        # Burada kalabiliriz veya dönebiliriz. Şimdilik kalalım ki görsün.


async def use_favorite(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, lang: str, user_id: int) -> None:
    """Favoriden hızlı erişim - DİREKT SEFER SAATLERİNİ gösterir."""
    favorites = await asyncio.to_thread(db.get_metro_favorites, user_id)
    fav_index = -1
    
    # FAV numarasını çıkar (⭐ FAV1: ...)
    try:
        fav_num = int(text.split("FAV")[1].split(":")[0].strip())
        fav_index = fav_num - 1
        
        if fav_index < 0 or fav_index >= len(favorites):
            raise ValueError
            
        fav = favorites[fav_index]
        
        # State güncelle (Böylece geri butonu çalışır)
        state.metro_selection[user_id] = {
            "line": fav["line_id"],
            "line_name": fav["line_name"],
            "station": fav["station_id"],
            "station_name": fav["station_name"],
            "direction_id": fav["direction_id"],
            "direction_name": fav["direction_name"]
        }
        
        # Direkt saatleri göster (show_timetable)
        await show_timetable(
            update, context, 
            fav["station_id"], 
            fav["direction_id"], 
            fav["direction_name"], 
            lang,
            is_favorite_view=True
        )
        
    except (ValueError, IndexError, KeyError) as e:
        logger.error(f"Favori kullanım hatası: {e}")
        await update.message.reply_text("⚠️ Favori bilgisi alınamadı.")
    
    if fav_index < 0 or fav_index >= len(favorites):
        await update.message.reply_text("⚠️ Favori bulunamadı.")
        return
    
    fav = favorites[fav_index]
    
    # State'i güncelle
    state.metro_selection[user_id] = {
        "line": fav["line_id"],
        "line_name": fav["line_name"],
        "station": fav["station_id"],
        "station_name": fav["station_name"]
    }
    
    # Direkt sefer saatlerini göster
    await show_timetable(update, context, fav["station_id"], fav["direction_id"], fav["direction_name"], lang)

