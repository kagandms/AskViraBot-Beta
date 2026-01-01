"""
Metro Istanbul Handler
Provides real-time metro departure times using IBB Metro Istanbul API
"""

import asyncio
import logging
from datetime import datetime
import pytz
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import database as db
from texts import TEXTS
from utils import get_tools_keyboard_markup
from rate_limiter import rate_limit

logger = logging.getLogger(__name__)

# Istanbul timezone
ISTANBUL_TZ = pytz.timezone('Europe/Istanbul')

# API Base URL
METRO_API_BASE = "https://api.ibb.gov.tr/MetroIstanbul/api/MetroMobile/V2"

# --- API HELPER FUNCTIONS ---

async def fetch_lines():
    """Fetch all metro lines"""
    try:
        response = await asyncio.to_thread(
            lambda: requests.get(f"{METRO_API_BASE}/GetLines", timeout=10)
        )
        data = response.json()
        if data.get("Success"):
            return data.get("Data", [])
    except Exception as e:
        logger.error(f"Metro API Error (GetLines): {e}")
    return []

async def fetch_stations_by_line(line_id: int):
    """Fetch stations for a specific line"""
    try:
        response = await asyncio.to_thread(
            lambda: requests.get(f"{METRO_API_BASE}/GetStationById/{line_id}", timeout=10)
        )
        data = response.json()
        if data.get("Success"):
            return data.get("Data", [])
    except Exception as e:
        logger.error(f"Metro API Error (GetStationById): {e}")
    return []

async def fetch_directions_by_line(line_id: int):
    """Fetch directions for a specific line"""
    try:
        response = await asyncio.to_thread(
            lambda: requests.get(f"{METRO_API_BASE}/GetDirectionById/{line_id}", timeout=10)
        )
        data = response.json()
        if data.get("Success"):
            return data.get("Data", [])
    except Exception as e:
        logger.error(f"Metro API Error (GetDirectionById): {e}")
    return []

async def fetch_timetable(station_id: int, direction_id: int):
    """Fetch departure times for a station and direction"""
    try:
        now = datetime.now(ISTANBUL_TZ).strftime("%Y-%m-%dT%H:%M:%S+03:00")
        payload = {
            "BoardingStationId": station_id,
            "DirectionId": direction_id,
            "DateTime": now
        }
        response = await asyncio.to_thread(
            lambda: requests.post(
                f"{METRO_API_BASE}/GetTimeTable",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
        )
        data = response.json()
        if data.get("Success"):
            return data.get("Data", [])
    except Exception as e:
        logger.error(f"Metro API Error (GetTimeTable): {e}")
    return []


# --- COMMAND HANDLERS ---

@rate_limit("heavy")
async def metro_menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show metro line selection menu"""
    user_id = update.effective_user.id
    lang = await asyncio.to_thread(db.get_user_lang, user_id)
    
    lines = await fetch_lines()
    
    if not lines:
        await update.message.reply_text(
            TEXTS["metro_api_error"][lang],
            reply_markup=get_tools_keyboard_markup(lang)
        )
        return
    
    # Filter to show only metro lines (M1A, M1B, M2, M3, etc.)
    # Exclude trams (T), funiculars (F), cable cars (TF), marmaray
    metro_lines = [line for line in lines if line.get("Name", "").startswith("M")]
    
    if not metro_lines:
        await update.message.reply_text(
            TEXTS["metro_api_error"][lang],
            reply_markup=get_tools_keyboard_markup(lang)
        )
        return
    
    keyboard = []
    row = []
    for line in metro_lines:
        line_name = line.get("Name", "")
        line_id = line.get("Id")
        if line_name and line_id:
            row.append(InlineKeyboardButton(
                f"🚇 {line_name}",
                callback_data=f"metro_line_{line_id}_{line_name}"
            ))
            if len(row) == 3:
                keyboard.append(row)
                row = []
    if row:
        keyboard.append(row)
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        TEXTS["metro_menu_prompt"][lang],
        reply_markup=reply_markup
    )


async def metro_line_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle line selection, show stations"""
    query = update.callback_query
    user_id = query.from_user.id
    lang = await asyncio.to_thread(db.get_user_lang, user_id)
    
    await query.answer()
    
    # Parse callback data: metro_line_{line_id}_{line_name}
    parts = query.data.split("_")
    line_id = int(parts[2])
    line_name = "_".join(parts[3:])  # Handle line names with underscores
    
    # Store line info in context for later
    context.user_data["metro_line_id"] = line_id
    context.user_data["metro_line_name"] = line_name
    
    stations = await fetch_stations_by_line(line_id)
    
    if not stations:
        await query.message.edit_text(
            TEXTS["metro_api_error"][lang]
        )
        return
    
    keyboard = []
    row = []
    for station in stations:
        station_name = station.get("Description", station.get("Name", ""))
        station_id = station.get("Id")
        if station_name and station_id:
            # Truncate long names
            display_name = station_name[:20] + "..." if len(station_name) > 20 else station_name
            row.append(InlineKeyboardButton(
                f"📍 {display_name}",
                callback_data=f"metro_station_{station_id}"
            ))
            if len(row) == 2:
                keyboard.append(row)
                row = []
    if row:
        keyboard.append(row)
    
    # Add back button
    keyboard.append([InlineKeyboardButton(
        TEXTS["back_button_inline"][lang],
        callback_data="metro_back_lines"
    )])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.edit_text(
        TEXTS["metro_select_station"][lang].format(line=line_name),
        reply_markup=reply_markup
    )


async def metro_station_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle station selection, show directions"""
    query = update.callback_query
    user_id = query.from_user.id
    lang = await asyncio.to_thread(db.get_user_lang, user_id)
    
    await query.answer()
    
    # Parse callback data: metro_station_{station_id}
    station_id = int(query.data.split("_")[2])
    context.user_data["metro_station_id"] = station_id
    
    line_id = context.user_data.get("metro_line_id")
    line_name = context.user_data.get("metro_line_name", "")
    
    if not line_id:
        await query.message.edit_text(TEXTS["metro_api_error"][lang])
        return
    
    directions = await fetch_directions_by_line(line_id)
    
    if not directions:
        await query.message.edit_text(TEXTS["metro_api_error"][lang])
        return
    
    keyboard = []
    for direction in directions:
        direction_name = direction.get("DirectionName", "")
        direction_id = direction.get("DirectionId")
        if direction_name and direction_id:
            keyboard.append([InlineKeyboardButton(
                f"➡️ {direction_name}",
                callback_data=f"metro_dir_{direction_id}"
            )])
    
    # Add back button
    keyboard.append([InlineKeyboardButton(
        TEXTS["back_button_inline"][lang],
        callback_data=f"metro_line_{line_id}_{line_name}"
    )])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.edit_text(
        TEXTS["metro_select_direction"][lang],
        reply_markup=reply_markup
    )


async def metro_direction_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle direction selection, show departure times"""
    query = update.callback_query
    user_id = query.from_user.id
    lang = await asyncio.to_thread(db.get_user_lang, user_id)
    
    await query.answer()
    
    # Parse callback data: metro_dir_{direction_id}
    direction_id = int(query.data.split("_")[2])
    
    station_id = context.user_data.get("metro_station_id")
    line_name = context.user_data.get("metro_line_name", "")
    
    if not station_id:
        await query.message.edit_text(TEXTS["metro_api_error"][lang])
        return
    
    # Fetch timetable
    timetable_data = await fetch_timetable(station_id, direction_id)
    
    if not timetable_data:
        await query.message.edit_text(TEXTS["metro_no_departures"][lang])
        return
    
    # Build response message
    timetable = timetable_data[0]  # Get first result
    station_name = timetable.get("BoardingStationName", "İstasyon")
    last_station = timetable.get("LastStation", "")
    times = timetable.get("TimeInfos", {}).get("Times", [])
    
    if not times:
        await query.message.edit_text(TEXTS["metro_no_departures"][lang])
        return
    
    # Calculate minutes until each departure using Istanbul timezone
    now = datetime.now(ISTANBUL_TZ)
    departure_lines = []
    
    for time_str in times[:6]:  # Show next 6 departures
        try:
            hour, minute = map(int, time_str.split(":"))
            departure_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            # If departure time is in the past, skip
            if departure_time < now:
                continue
            
            minutes_until = int((departure_time - now).total_seconds() / 60)
            
            if minutes_until <= 1:
                departure_lines.append(f"🚇 {time_str} (şimdi)")
            else:
                departure_lines.append(f"🕒 {time_str} ({minutes_until} dk)")
        except:
            departure_lines.append(f"🕒 {time_str}")
    
    if not departure_lines:
        await query.message.edit_text(TEXTS["metro_no_departures"][lang])
        return
    
    header = TEXTS["metro_departures_header"][lang].format(
        line=line_name,
        station=station_name,
        direction=last_station
    )
    
    message = header + "\n\n" + "\n".join(departure_lines)
    
    # Add refresh and back buttons
    keyboard = [
        [InlineKeyboardButton("🔄 Yenile", callback_data=f"metro_dir_{direction_id}")],
        [InlineKeyboardButton(TEXTS["back_button_inline"][lang], callback_data="metro_back_lines")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.edit_text(message, reply_markup=reply_markup)


async def metro_back_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle back to lines menu"""
    query = update.callback_query
    user_id = query.from_user.id
    lang = await asyncio.to_thread(db.get_user_lang, user_id)
    
    await query.answer()
    
    lines = await fetch_lines()
    
    if not lines:
        await query.message.edit_text(TEXTS["metro_api_error"][lang])
        return
    
    # Filter to show only metro lines (M1A, M1B, M2, M3, etc.)
    metro_lines = [line for line in lines if line.get("Name", "").startswith("M")]
    
    keyboard = []
    row = []
    for line in metro_lines:
        line_name = line.get("Name", "")
        line_id = line.get("Id")
        if line_name and line_id:
            row.append(InlineKeyboardButton(
                f"🚇 {line_name}",
                callback_data=f"metro_line_{line_id}_{line_name}"
            ))
            if len(row) == 3:
                keyboard.append(row)
                row = []
    if row:
        keyboard.append(row)
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.edit_text(
        TEXTS["metro_menu_prompt"][lang],
        reply_markup=reply_markup
    )


# Main callback query dispatcher
async def metro_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Route metro callback queries to appropriate handlers"""
    query = update.callback_query
    data = query.data
    
    if data.startswith("metro_line_"):
        await metro_line_callback(update, context)
    elif data.startswith("metro_station_"):
        await metro_station_callback(update, context)
    elif data.startswith("metro_dir_"):
        await metro_direction_callback(update, context)
    elif data == "metro_back_lines":
        await metro_back_callback(update, context)
