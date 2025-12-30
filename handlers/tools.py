import os
import aiohttp
import qrcode
from io import BytesIO
import tempfile
from fpdf import FPDF
import img2pdf
from datetime import datetime
import pytz
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

import database as db
import state
from texts import TEXTS, BUTTON_MAPPINGS, CITY_NAMES_TRANSLATED
from config import OPENWEATHERMAP_API_KEY, FONT_PATH
from utils import get_pdf_converter_keyboard_markup, get_input_back_keyboard_markup, get_main_keyboard_markup

# --- TIME (EKSİK OLAN KISIM BURASIYDI) ---
async def time_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = db.get_user_lang(update.effective_user.id)
    cities = {
        "Istanbul": "Europe/Istanbul", "Moscow": "Europe/Moscow",
        "London": "Europe/London", "New York": "America/New_York", "Beijing": "Asia/Shanghai"
    }
    message = ""
    for city, tz in cities.items():
        try:
            tz_obj = pytz.timezone(tz)
            city_time = datetime.now(tz_obj).strftime("%Y-%m-%d %H:%M:%S")
            # Şehir isimlerini çevirerek göster
            translated_city = CITY_NAMES_TRANSLATED[lang].get(city, city)
            message += f"{translated_city}: {city_time}\n"
        except Exception as e:
            print(f"Zaman hatası ({city}): {e}")
            
    await update.message.reply_text(message)

# --- QR CODE ---
async def qrcode_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = db.get_user_lang(user_id)
    if context.args:
        await generate_and_send_qr(update, context, ' '.join(context.args))
    else:
        state.clear_user_states(user_id)
        state.waiting_for_qr_data.add(user_id)
        await update.message.reply_text(TEXTS["qrcode_prompt_input"][lang], reply_markup=get_input_back_keyboard_markup(lang))

async def generate_and_send_qr(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
    user_id = update.effective_user.id
    lang = db.get_user_lang(user_id)
    
    if data.lower() in BUTTON_MAPPINGS["menu"]:
        from handlers.general import menu_command
        await menu_command(update, context)
        return

    try:
        img = qrcode.make(data)
        bio = BytesIO()
        bio.name = "qrcode.png"
        img.save(bio, "PNG")
        bio.seek(0)
        await update.message.reply_photo(photo=bio, caption=TEXTS["qrcode_generated"][lang].format(data=data), reply_markup=get_main_keyboard_markup(lang))
    except Exception as e:
        await update.message.reply_text(TEXTS["error_occurred"][lang] + str(e))
    state.waiting_for_qr_data.discard(user_id)

# --- PDF CONVERTER ---
async def pdf_converter_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = db.get_user_lang(user_id)
    state.clear_user_states(user_id)
    await update.message.reply_text(TEXTS["pdf_converter_menu_prompt"][lang], reply_markup=get_pdf_converter_keyboard_markup(lang))

async def prompt_text_for_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = db.get_user_lang(user_id)
    state.clear_user_states(user_id)
    state.waiting_for_pdf_conversion_input.add(user_id)
    context.user_data['pdf_conversion_type'] = 'text'
    await update.message.reply_text(TEXTS["prompt_text_for_pdf"][lang], reply_markup=get_input_back_keyboard_markup(lang))

async def prompt_file_for_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = db.get_user_lang(user_id)
    state.clear_user_states(user_id)
    state.waiting_for_pdf_conversion_input.add(user_id)
    context.user_data['pdf_conversion_type'] = 'file'
    await update.message.reply_text(TEXTS["prompt_file_for_pdf"][lang] + "\n\n" + TEXTS["docx_conversion_warning"][lang], reply_markup=get_input_back_keyboard_markup(lang))

async def handle_pdf_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = db.get_user_lang(user_id)
    conversion_type = context.user_data.get('pdf_conversion_type')

    if update.message.text and update.message.text.lower() in BUTTON_MAPPINGS["menu"]:
        from handlers.general import menu_command
        await menu_command(update, context)
        return

    output_pdf_path = None
    try:
        output_pdf_name = f"converted_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        output_pdf_path = os.path.join(tempfile.gettempdir(), output_pdf_name)

        if conversion_type == 'text' and update.message.text:
            pdf = FPDF()
            pdf.add_page()
            if os.path.exists(FONT_PATH):
                try:
                    pdf.add_font("DejaVuSans", "", FONT_PATH, uni=True)
                    pdf.set_font("DejaVuSans", size=12)
                    pdf.multi_cell(0, 10, update.message.text)
                except:
                     pdf.set_font("Arial", size=12)
                     pdf.multi_cell(0, 10, update.message.text.encode('latin-1', 'replace').decode('latin-1'))
            else:
                pdf.set_font("Arial", size=12)
                pdf.multi_cell(0, 10, update.message.text.encode('latin-1', 'replace').decode('latin-1'))
            pdf.output(output_pdf_path)
        
        elif conversion_type == 'file':
            file_obj = update.message.document or update.message.photo[-1] if update.message.photo else None
            if not file_obj: raise ValueError(TEXTS["unsupported_file_type"][lang])

            with tempfile.NamedTemporaryFile(delete=False) as temp_input_file:
                input_file_path = temp_input_file.name

            file_to_download = await file_obj.get_file()
            await file_to_download.download_to_drive(input_file_path)
            
            original_filename = file_obj.file_name if hasattr(file_obj, 'file_name') else "image.jpg"
            file_extension = os.path.splitext(original_filename)[1].lower()
            if not file_extension and update.message.photo: file_extension = ".jpg"

            if file_extension in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']:
                with open(output_pdf_path, "wb") as f: f.write(img2pdf.convert(input_file_path))
            elif file_extension == '.txt':
                with open(input_file_path, 'r', encoding='utf-8') as f: text_content = f.read()
                pdf = FPDF()
                pdf.add_page()
                font_loaded = False
                if os.path.exists(FONT_PATH):
                    try:
                        pdf.add_font("DejaVuSans", "", FONT_PATH, uni=True)
                        pdf.set_font("DejaVuSans", size=12)
                        font_loaded = True
                    except: pass
                if not font_loaded:
                    pdf.set_font("Arial", size=12)
                    text_content = text_content.encode('latin-1', 'replace').decode('latin-1')
                pdf.multi_cell(0, 10, text_content)
                pdf.output(output_pdf_path)
            else: 
                raise ValueError(TEXTS["unsupported_file_type"][lang])
            if os.path.exists(input_file_path): os.remove(input_file_path)

        with open(output_pdf_path, 'rb') as f:
            await update.message.reply_document(document=f, caption=TEXTS["pdf_conversion_success"][lang])

    except Exception as e:
        await update.message.reply_text(TEXTS["error_occurred"][lang] + str(e))
    finally:
        state.clear_user_states(user_id)
        if output_pdf_path and os.path.exists(output_pdf_path): os.remove(output_pdf_path)

# --- WEATHER ---
async def weather_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = db.get_user_lang(user_id)
    state.clear_user_states(user_id)
    keyboard = []
    cities = ["Istanbul", "Moscow", "London", "New York", "Beijing"]
    for city in cities:
        keyboard.append([InlineKeyboardButton(CITY_NAMES_TRANSLATED[lang][city], callback_data=f"weather_{city.lower().replace(' ', '_')}")])
    keyboard.append([InlineKeyboardButton(TEXTS["back_button_inline"][lang], callback_data="weather_back_to_menu")])
    await update.message.reply_text(TEXTS["weather_select_city"][lang], reply_markup=InlineKeyboardMarkup(keyboard))

async def weather_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    lang = db.get_user_lang(user_id)
    await query.answer()

    if query.data.startswith("weather_"):
        if query.data == "weather_back_to_menu":
            from handlers.general import menu_command
            await menu_command(update, context)
            return

        city_key = query.data.replace("weather_", "")
        city_name_map = {v.lower().replace(' ', '_'): k for k, v in CITY_NAMES_TRANSLATED["en"].items()}
        city_name_en = city_name_map.get(city_key, "")

        if city_name_en:
            await query.edit_message_text(TEXTS["waiting_for_input"][lang], reply_markup=None)
            await get_weather_data(update, context, city_name_en)
        else:
            await context.bot.send_message(chat_id=query.message.chat_id, text=TEXTS["error_occurred"][lang] + "Invalid city selection.", reply_markup=get_main_keyboard_markup(lang))
    state.clear_user_states(user_id)

async def get_weather_data(update: Update, context: ContextTypes.DEFAULT_TYPE, city_name: str):
    user_id = update.effective_user.id
    lang = db.get_user_lang(user_id)
    try:
        if not OPENWEATHERMAP_API_KEY: raise ValueError("OpenWeatherMap API Key eksik.")
        weather_url = f"http://api.openweathermap.org/data/2.5/weather?q={city_name}&appid={OPENWEATHERMAP_API_KEY}&units=metric"
        async with aiohttp.ClientSession() as session:
            async with session.get(weather_url) as response:
                data = await response.json()

        if str(data.get("cod")) == "200":
            main_data = data["main"]
            weather_data = data["weather"][0]
            wind_data = data["wind"]
            temperature = main_data["temp"]
            feels_like = main_data["feels_like"]
            description = weather_data["description"]
            humidity = main_data["humidity"]
            wind_speed = wind_data["speed"]
            
            translated_description = description 
            
            message = TEXTS["weather_current"][lang].format(city=city_name.title(), temp=temperature, feels_like=feels_like, description=translated_description.capitalize(), humidity=humidity, wind_speed=wind_speed)
            await update.effective_message.reply_text(message, reply_markup=get_main_keyboard_markup(lang))
        elif str(data.get("cod")) == "404":
            await update.effective_message.reply_text(TEXTS["weather_city_not_found"][lang].format(city=city_name), reply_markup=get_main_keyboard_markup(lang))
        else:
            await update.effective_message.reply_text(TEXTS["weather_api_error"][lang] + f" ({data.get('message', 'Unknown error')})", reply_markup=get_main_keyboard_markup(lang))
    except Exception as e:
        await update.effective_message.reply_text(TEXTS["error_occurred"][lang] + str(e), reply_markup=get_main_keyboard_markup(lang))
    finally:
        state.clear_user_states(user_id)

async def show_developer_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = db.get_user_lang(user_id)
    state.clear_user_states(user_id)
    await update.message.reply_text(TEXTS["developer_info_prompt"][lang], reply_markup=get_social_media_keyboard(lang))

async def handle_social_media_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    lang = db.get_user_lang(user_id)
    await query.answer()
    if query.data == "back_to_main_menu":
        state.clear_user_states(user_id)
        from handlers.general import menu_command
        await menu_command(update, context)