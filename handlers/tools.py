import asyncio
from datetime import datetime
import logging
import os
import qrcode
from fpdf import FPDF
from PIL import Image
import requests
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import database as db
import state
from texts import TEXTS, PDF_CONVERTER_BUTTONS, BUTTON_MAPPINGS, CITY_NAMES_TRANSLATED, SOCIAL_MEDIA_LINKS
from config import OPENWEATHERMAP_API_KEY, FONT_PATH
from utils import get_input_back_keyboard_markup, get_main_keyboard_markup
from rate_limiter import rate_limit

# --- YARDIMCI FONKSİYONLAR ---
def get_pdf_keyboard_markup(lang):
    buttons = PDF_CONVERTER_BUTTONS.get(lang, PDF_CONVERTER_BUTTONS["en"])
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

# --- ZAMAN KOMUTU ---
async def time_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
    now = datetime.now().strftime("%H:%M:%S")
    await update.message.reply_text(f"🕒 Saat: {now}")

# --- QR KOD ---
@rate_limit("heavy")
async def qrcode_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    # DB İŞLEMİ: Asenkron
    lang = await asyncio.to_thread(db.get_user_lang, user_id)
    
    if context.args:
        data = ' '.join(context.args)
        await generate_and_send_qr(update, context, data)
    else:
        state.clear_user_states(user_id)
        state.waiting_for_qr_data.add(user_id)
        # DÜZELTME: QR kod moduna girince sadece Geri butonu görünsün
        await update.message.reply_text(
            TEXTS["qrcode_prompt_input"][lang],
            reply_markup=get_input_back_keyboard_markup(lang)
        )

async def generate_and_send_qr(update: Update, context: ContextTypes.DEFAULT_TYPE, data):
    user_id = update.effective_user.id
    # DB İŞLEMİ: Asenkron
    lang = await asyncio.to_thread(db.get_user_lang, user_id)

    # --- GERİ TUŞU KONTROLÜ (EKLENEN KISIM) ---
    data_lower = data.lower().strip()
    # Eğer gelen veri "Geri" butonu veya benzeri ise menüye dön
    if data_lower in BUTTON_MAPPINGS["menu"] or "geri" in data_lower or "back" in data_lower or "назад" in data_lower:
        from handlers.general import tools_menu_command
        state.waiting_for_qr_data.discard(user_id)
        await tools_menu_command(update, context)
        return
    # ------------------------------------------

    file_path = f"qr_{user_id}.png"
    
    try:
        img = qrcode.make(data)
        img.save(file_path)
        
        # LOGLAMA (YENİ)
        # Asenkron çağrılmalı ama db fonksiyonu senkron. to_thread kullanabiliriz veya direkt çağırabiliriz
        # db.log_qr_usage içinde try-except var, hata verirse botu durdurmaz.
        # Hız için thread içinde çağıralım.
        await asyncio.to_thread(db.log_qr_usage, user_id, data)
        
        with open(file_path, 'rb') as photo:
            await update.message.reply_photo(photo, caption=TEXTS["qrcode_generated"][lang].format(data=data), reply_markup=get_main_keyboard_markup(lang))
            
    except Exception as e:
        await update.message.reply_text(TEXTS["error_occurred"][lang] + str(e))
        
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)
    
    state.waiting_for_qr_data.discard(user_id)

# --- PDF DÖNÜŞTÜRÜCÜ ---
@rate_limit("heavy")
async def pdf_converter_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    # DB İŞLEMİ: Asenkron
    lang = await asyncio.to_thread(db.get_user_lang, user_id)
    state.clear_user_states(user_id)
    
    await update.message.reply_text(
        TEXTS["pdf_converter_menu_prompt"][lang],
        reply_markup=get_pdf_keyboard_markup(lang)
    )

async def prompt_text_for_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    # DB İŞLEMİ: Asenkron
    lang = await asyncio.to_thread(db.get_user_lang, user_id)
    state.clear_user_states(user_id)
    state.waiting_for_pdf_conversion_input.add(user_id)
    context.user_data['pdf_mode'] = 'text'
    await update.message.reply_text(
        TEXTS["prompt_text_for_pdf"][lang],
        reply_markup=get_input_back_keyboard_markup(lang)
    )

async def prompt_file_for_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    # DB İŞLEMİ: Asenkron
    lang = await asyncio.to_thread(db.get_user_lang, user_id)
    state.clear_user_states(user_id)
    state.waiting_for_pdf_conversion_input.add(user_id)
    context.user_data['pdf_mode'] = 'file'
    await update.message.reply_text(
        TEXTS["prompt_file_for_pdf"][lang],
        reply_markup=get_input_back_keyboard_markup(lang)
    )

async def handle_pdf_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    # DB İŞLEMİ: Asenkron
    lang = await asyncio.to_thread(db.get_user_lang, user_id)
    mode = context.user_data.get('pdf_mode')
    
    text_content = update.message.text.lower() if update.message.text else ""
    if text_content in BUTTON_MAPPINGS["menu"] or "geri" in text_content or "back" in text_content:
        from handlers.general import tools_menu_command
        state.waiting_for_pdf_conversion_input.discard(user_id)
        await tools_menu_command(update, context)
        return

    output_filename = f"document_{str(user_id)}.pdf"
    temp_files = [] 

    try:
        processing_msg = await update.message.reply_text("⏳ PDF hazırlanıyor...")

        pdf = FPDF()
        pdf.add_page()
        
        # Unicode desteği için DejaVuSans fontu (Türkçe + Kiril karakterler)
        if os.path.exists(FONT_PATH):
            pdf.add_font("DejaVu", "", FONT_PATH)
            pdf.set_font("DejaVu", size=12)
        else:
            # Fallback: Helvetica (Unicode desteksiz)
            pdf.set_font("Helvetica", size=12)

        # --- İÇERİK TÜRÜNE GÖRE İŞLEM (Smart Handling) ---
        # Kullanıcının hangi modda olduğuna bakmaksızın, gönderdiği veriyi işle
        
        if update.message.text:
            text = update.message.text
            pdf.multi_cell(w=pdf.epw, h=10, text=text)
            pdf.output(output_filename)

        elif update.message.photo:
            photo_file = await update.message.photo[-1].get_file()
            photo_path = f"temp_img_{str(user_id)}.jpg"
            temp_files.append(photo_path)
            
            await photo_file.download_to_drive(photo_path)
            
            cover = Image.open(photo_path)
            pdf.image(photo_path, x=10, y=10, w=190)
            pdf.output(output_filename)
            
        elif update.message.document:
            doc = update.message.document
            
            # 1. Metin Dosyası (.txt)
            if doc.mime_type == 'text/plain':
                doc_path = f"temp_doc_{str(user_id)}.txt"
                temp_files.append(doc_path)
                
                doc_file = await doc.get_file()
                await doc_file.download_to_drive(doc_path)
                
                with open(doc_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    pdf.multi_cell(w=pdf.epw, h=10, text=content)
                pdf.output(output_filename)
            
            # 2. Resim Dosyası (PNG, JPG vb. dosya olarak gönderilmiş)
            elif doc.mime_type and doc.mime_type.startswith('image/'):
                img_path = f"temp_doc_img_{str(user_id)}"
                temp_files.append(img_path)
                
                doc_file = await doc.get_file()
                await doc_file.download_to_drive(img_path)
                
                try:
                    # Görüntüyü aç ve PDF'e ekle
                    cover = Image.open(img_path)
                    
                    # Eğer PNG ve transparan ise, beyaz arka plana çevir (FPDF hatasını önlemek için)
                    if img_path.lower().endswith('.png') or doc.mime_type == 'image/png':
                         if cover.mode in ('RGBA', 'LA') or (cover.mode == 'P' and 'transparency' in cover.info):
                             alpha = cover.convert('RGBA').split()[-1]
                             bg = Image.new("RGB", cover.size, (255, 255, 255))
                             bg.paste(cover, mask=alpha)
                             cover = bg
                             # Geçici olarak JPG kaydet
                             cover.save(img_path + ".jpg", "JPEG", quality=90)
                             img_path = img_path + ".jpg"
                             temp_files.append(img_path)

                    pdf.image(img_path, x=10, y=10, w=190)
                    pdf.output(output_filename)
                except Exception as e:
                    await processing_msg.delete()
                    await update.message.reply_text(f"Resim işlenirken hata: {e}")
                    return

            else:
                await processing_msg.delete()
                await update.message.reply_text(TEXTS["unsupported_file_type"][lang])
                return
        
        else:
            await processing_msg.delete()
            await update.message.reply_text(TEXTS["unsupported_file_type"][lang])
            return

        with open(output_filename, 'rb') as f:
            await update.message.reply_document(f, caption=TEXTS["pdf_conversion_success"][lang])
            
        # LOGLAMA (YENİ)
        log_type = "text" if update.message.text else ("image" if (update.message.photo or (update.message.document and update.message.document.mime_type.startswith('image/'))) else "document")
        await asyncio.to_thread(db.log_pdf_usage, user_id, log_type)
        
        await processing_msg.delete()

    except Exception as e:
        await update.message.reply_text(TEXTS["pdf_conversion_error"][lang].format(error=str(e)))
        
    finally:
        if os.path.exists(output_filename):
            os.remove(output_filename)
        for temp in temp_files:
            if os.path.exists(temp):
                os.remove(temp)

    state.waiting_for_pdf_conversion_input.discard(user_id)
    # İşlem bitince PDF menüsüne geri dön
    await pdf_converter_menu(update, context)

# --- HAVA DURUMU ---
@rate_limit("heavy")
async def weather_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    # DB İŞLEMİ: Asenkron
    lang = await asyncio.to_thread(db.get_user_lang, user_id)
    
    if context.args:
        city = ' '.join(context.args)
        await get_weather_data(update, context, city)
    else:
        state.clear_user_states(user_id)
        state.waiting_for_weather_city.add(user_id)
        
        # 1. Adım: Alttaki klavyeyi sadece "Geri" butonu olacak şekilde güncelle
        await update.message.reply_text(
            TEXTS["weather_prompt_city"][lang],
            reply_markup=get_input_back_keyboard_markup(lang)
        )
        
        # 2. Adım: Şehir seçim butonlarını sun
        cities = CITY_NAMES_TRANSLATED.get(lang, CITY_NAMES_TRANSLATED["en"])
        keyboard = []
        row = []
        for city_key, city_name in cities.items():
            row.append(InlineKeyboardButton(city_name, callback_data=f"weather_{city_key}"))
            if len(row) == 2:
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(TEXTS["weather_select_city"][lang], reply_markup=reply_markup)

async def get_weather_data(update: Update, context: ContextTypes.DEFAULT_TYPE, city_name):
    user_id = update.effective_user.id
    # DB İŞLEMİ: Asenkron
    lang = await asyncio.to_thread(db.get_user_lang, user_id)

    # --- GERİ TUŞU KONTROLÜ (EKLENEN KISIM) ---
    city_name_lower = city_name.lower().strip()
    # "Geri" butonuna basıldığında gelen metni kontrol ediyoruz
    if city_name_lower in BUTTON_MAPPINGS["menu"] or "geri" in city_name_lower or "back" in city_name_lower or "назад" in city_name_lower:
        from handlers.general import tools_menu_command
        state.waiting_for_weather_city.discard(user_id)
        # Menüye dön
        await tools_menu_command(update, context)
        return
    # ------------------------------------------
    
    api_key = OPENWEATHERMAP_API_KEY
    if not api_key:
        target_message = update.message if update.message else update.callback_query.message
        await target_message.reply_text("API Key eksik! (Config dosyasını kontrol edin)")
        state.waiting_for_weather_city.discard(user_id)
        return

    weather_lang = lang 
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city_name}&appid={api_key}&units=metric&lang={weather_lang}"
    
    # Callback query veya normal mesajdan hangisi varsa onu kullan
    target_message = update.message if update.message else update.callback_query.message

    try:
        # Non-blocking request with asyncio
        response = await asyncio.to_thread(
            lambda: requests.get(url, timeout=10)
        )
        data = response.json()

        if data["cod"] == 200:
            weather_desc = data["weather"][0]["description"]
            temp = data["main"]["temp"]
            feels_like = data["main"]["feels_like"]
            humidity = data["main"]["humidity"]
            wind_speed = data["wind"]["speed"]
            city = data["name"]
            
            msg = TEXTS["weather_current"][lang].format(
                city=city,
                temp=temp,
                feels_like=feels_like,
                description=weather_desc.title(),
                humidity=humidity,
                wind_speed=wind_speed
            )
            # BAŞARILI SONUÇ: Ana menü klavyesini geri getir
            await target_message.reply_text(msg, reply_markup=get_main_keyboard_markup(lang))
        else:
            await target_message.reply_text(TEXTS["weather_city_not_found"][lang].format(city=city_name))

    except requests.exceptions.Timeout:
        await target_message.reply_text(TEXTS["weather_api_error"][lang])
    except requests.exceptions.ConnectionError:
        await target_message.reply_text(TEXTS["weather_api_error"][lang])
    except Exception as e:
        logging.getLogger(__name__).error(f"Weather Error: {e}")
        await target_message.reply_text(TEXTS["weather_api_error"][lang])
    
    state.waiting_for_weather_city.discard(user_id)

async def weather_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    # DB İŞLEMİ: Asenkron
    lang = await asyncio.to_thread(db.get_user_lang, user_id)
    
    await query.answer()
    
    if query.data.startswith("weather_"):
        city_key = query.data.split("_")[1]
        # Şehir adını (Key olarak İngilizcesini) kullanarak hava durumunu çek
        await get_weather_data(update, context, city_key)

# --- GELİŞTİRİCİ ---
async def show_developer_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    # DB İŞLEMİ: Asenkron
    lang = await asyncio.to_thread(db.get_user_lang, user_id)
    

    
    keyboard = [
        [InlineKeyboardButton(TEXTS["my_website"][lang], url=SOCIAL_MEDIA_LINKS["website"])],
        [InlineKeyboardButton("Instagram", url=SOCIAL_MEDIA_LINKS["instagram"]),
         InlineKeyboardButton("Telegram", url=SOCIAL_MEDIA_LINKS["telegram"])],
        [InlineKeyboardButton("LinkedIn", url=SOCIAL_MEDIA_LINKS["linkedin"])],
        [InlineKeyboardButton(TEXTS["back_button_inline"][lang], callback_data="back_to_main_menu")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(TEXTS["developer_info_prompt"][lang], reply_markup=reply_markup)

async def handle_social_media_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "back_to_main_menu":
        await query.message.delete()