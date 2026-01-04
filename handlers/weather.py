import asyncio
import logging
import aiohttp
from datetime import datetime as dt, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import database as db
import state
from texts import TEXTS, BUTTON_MAPPINGS, CITY_NAMES_TRANSLATED
from config import OPENWEATHERMAP_API_KEY
from utils import get_weather_cities_keyboard, get_tools_keyboard_markup, is_back_button
from rate_limiter import rate_limit

# --- WEATHER CACHE SYSTEM ---
_weather_cache = {}  # {city_name_lower: {"data": {...}, "expires": datetime, "lang": str}}
WEATHER_CACHE_TTL = timedelta(minutes=10)

logger = logging.getLogger(__name__)

@rate_limit("heavy")
async def weather_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    lang = await asyncio.to_thread(db.get_user_lang, user_id)
    
    api_key = OPENWEATHERMAP_API_KEY
    if not api_key:
        await update.message.reply_text(
            "⚠️ Hava durumu servisi şu anda kullanılamıyor.",
            reply_markup=get_tools_keyboard_markup(lang)
        )
        return
    
    if context.args:
        city = ' '.join(context.args)
        await get_weather_data(update, context, city)
    else:
        await state.clear_user_states(user_id)
        await state.set_state(user_id, state.WAITING_FOR_WEATHER_CITY)
        
        await update.message.reply_text(
            TEXTS["weather_prompt_city"][lang],
            reply_markup=get_weather_cities_keyboard(lang)
        )

async def get_weather_data(update: Update, context: ContextTypes.DEFAULT_TYPE, city_name):
    user_id = update.effective_user.id
    lang = await asyncio.to_thread(db.get_user_lang, user_id)

    original_city_name = city_name
    for lang_code, cities in CITY_NAMES_TRANSLATED.items():
        for english_name, translated_name in cities.items():
            if city_name.strip() == translated_name.strip():
                city_name = english_name
                break
        if city_name != original_city_name:
            break

    city_name_lower = city_name.lower().strip()
    if is_back_button(city_name_lower):
        from handlers.general import tools_menu_command
        await state.clear_user_states(user_id)
        await tools_menu_command(update, context)
        return
    
    api_key = OPENWEATHERMAP_API_KEY
    if not api_key:
        target_message = update.message if update.message else update.callback_query.message
        await target_message.reply_text("API Key eksik! (Config dosyasını kontrol edin)")
        await state.clear_user_states(user_id)
        return

    target_message = update.message if update.message else update.callback_query.message
    
    # --- CACHE CHECK ---
    cache_key = f"{city_name_lower}_{lang}"
    now = dt.now()
    
    if cache_key in _weather_cache:
        cached = _weather_cache[cache_key]
        if now < cached["expires"]:
            # Cache HIT - use cached data
            logger.debug(f"CACHE HIT: {cache_key}")
            data = cached["data"]
            
            msg = TEXTS["weather_current"][lang].format(
                city=data["city"],
                temp=data["temp"],
                feels_like=data["feels_like"],
                description=data["description"],
                humidity=data["humidity"],
                wind_speed=data["wind_speed"]
            )
            
            forecast_keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton(TEXTS["weather_forecast_button"][lang], callback_data=f"forecast_{data['city']}")]
            ])
            
            await target_message.reply_text(msg, reply_markup=get_weather_cities_keyboard(lang))
            await target_message.reply_text("👆", reply_markup=forecast_keyboard)
            return
    
    # --- API CALL (Cache MISS) ---
    logger.debug(f"CACHE MISS: {cache_key} - Fetching from API")
    weather_lang = lang 
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city_name}&appid={api_key}&units=metric&lang={weather_lang}"

    try:
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as response:
                api_data = await response.json()

        if api_data["cod"] == 200:
            weather_desc = api_data["weather"][0]["description"]
            temp = api_data["main"]["temp"]
            feels_like = api_data["main"]["feels_like"]
            humidity = api_data["main"]["humidity"]
            wind_speed = api_data["wind"]["speed"]
            city = api_data["name"]
            
            # --- CACHE STORE ---
            _weather_cache[cache_key] = {
                "data": {
                    "city": city,
                    "temp": temp,
                    "feels_like": feels_like,
                    "description": weather_desc.title(),
                    "humidity": humidity,
                    "wind_speed": wind_speed
                },
                "expires": now + WEATHER_CACHE_TTL
            }
            logger.debug(f"CACHED: {cache_key} for {WEATHER_CACHE_TTL}")
            
            msg = TEXTS["weather_current"][lang].format(
                city=city,
                temp=temp,
                feels_like=feels_like,
                description=weather_desc.title(),
                humidity=humidity,
                wind_speed=wind_speed
            )
            
            forecast_keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton(TEXTS["weather_forecast_button"][lang], callback_data=f"forecast_{city}")]
            ])
            
            await target_message.reply_text(msg, reply_markup=get_weather_cities_keyboard(lang))
            await target_message.reply_text("👆", reply_markup=forecast_keyboard)
        else:
            await target_message.reply_text(TEXTS["weather_city_not_found"][lang].format(city=city_name))

    except asyncio.TimeoutError:
        await target_message.reply_text(TEXTS["weather_api_error"][lang])
    except aiohttp.ClientError:
        await target_message.reply_text(TEXTS["weather_api_error"][lang])
    except Exception as e:
        logger.error(f"Weather Error: {e}")
        await target_message.reply_text(TEXTS["weather_api_error"][lang])
    
async def weather_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user_id = query.from_user.id
    lang = await asyncio.to_thread(db.get_user_lang, user_id)
    
    await query.answer()
    
    if query.data.startswith("forecast_"):
        city = query.data.replace("forecast_", "")
        await get_forecast_data(update, context, city, lang)
        return
    
    if query.data.startswith("weather_"):
        city_key = query.data.split("_")[1]
        try:
            await query.message.delete()
        except Exception:
            pass
        await get_weather_data(update, context, city_key)

async def get_forecast_data(update: Update, context: ContextTypes.DEFAULT_TYPE, city: str, lang: str):
    from collections import defaultdict
    
    api_key = OPENWEATHERMAP_API_KEY
    if not api_key:
        return
    
    url = f"http://api.openweathermap.org/data/2.5/forecast?q={city}&appid={api_key}&units=metric&lang={lang}"
    query = update.callback_query
    
    try:
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as response:
                data = await response.json()
        
        if data.get("cod") != "200":
            await query.message.edit_text(TEXTS["weather_api_error"][lang])
            return
        
        daily_data = defaultdict(list)
        day_names = {
            "tr": ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"],
            "en": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
            "ru": ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
        }
        
        for item in data["list"]:
            date = dt.fromtimestamp(item["dt"])
            day_key = date.strftime("%Y-%m-%d")
            daily_data[day_key].append({
                "temp": item["main"]["temp"],
                "desc": item["weather"][0]["description"],
                "icon": item["weather"][0]["main"],
                "date": date
            })
        
        icon_map = {
            "Clear": "☀️", "Clouds": "☁️", "Rain": "🌧️", "Drizzle": "🌦️",
            "Thunderstorm": "⛈️", "Snow": "❄️", "Mist": "🌫️", "Fog": "🌫️",
            "Haze": "🌫️", "Dust": "🌫️", "Smoke": "🌫️"
        }
        
        lines = [TEXTS["weather_forecast_title"][lang].format(city=city)]
        
        for i, (day_key, items) in enumerate(sorted(daily_data.items())[:5]):
            temps = [item["temp"] for item in items]
            max_temp = round(max(temps))
            min_temp = round(min(temps))
            
            mid_item = items[len(items) // 2]
            desc = mid_item["desc"].title()
            icon = icon_map.get(mid_item["icon"], "🌡️")
            
            day_date = mid_item["date"]
            day_name = day_names.get(lang, day_names["en"])[day_date.weekday()]
            
            today_labels = {"tr": "Bugün", "en": "Today", "ru": "Сегодня"}
            tomorrow_labels = {"tr": "Yarın", "en": "Tomorrow", "ru": "Завтра"}
            
            if i == 0:
                day_name = today_labels.get(lang, "Today")
            elif i == 1:
                day_name = tomorrow_labels.get(lang, "Tomorrow")
            
            line = TEXTS["weather_day_format"][lang].format(
                day=day_name, icon=icon, max_temp=max_temp, min_temp=min_temp, desc=desc
            )
            lines.append(line)
        
        forecast_msg = "\n".join(lines)
        
        try:
            await query.message.edit_text(forecast_msg, parse_mode="Markdown")
        except Exception:
            await query.message.reply_text(forecast_msg, parse_mode="Markdown")
        
    except Exception as e:
        logging.getLogger(__name__).error(f"Forecast Error: {e}")
        await query.message.reply_text(TEXTS["weather_api_error"][lang])
