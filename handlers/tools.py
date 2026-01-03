import asyncio
from datetime import datetime
import logging
import os
import qrcode
from fpdf import FPDF
from PIL import Image
import aiohttp
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import database as db
import state
from texts import TEXTS, PDF_CONVERTER_BUTTONS, BUTTON_MAPPINGS, CITY_NAMES_TRANSLATED, SOCIAL_MEDIA_LINKS
from config import OPENWEATHERMAP_API_KEY, FONT_PATH
from utils import get_input_back_keyboard_markup, get_main_keyboard_markup, get_tools_keyboard_markup, get_weather_cities_keyboard
from rate_limiter import rate_limit

# --- YARDIMCI FONKSİYONLAR ---
def get_pdf_keyboard_markup(lang):
    buttons = PDF_CONVERTER_BUTTONS.get(lang, PDF_CONVERTER_BUTTONS["en"])
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

# --- ZAMAN KOMUTU ---
async def time_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    
    now = datetime.now().strftime("%H:%M:%S")
    await update.message.reply_text(f"🕒 Saat: {now}")

# --- QR KOD ---
@rate_limit("heavy")
async def qrcode_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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
    # Eğer gelen veri geri butonu ise menüye dön
    back_keywords = ["geri", "back", "назад", "araçlar menüsü", "tools menu", "меню инструментов"]
    if data_lower in BUTTON_MAPPINGS["menu"] or data_lower in BUTTON_MAPPINGS.get("back_to_tools", set()) or any(kw in data_lower for kw in back_keywords):
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
async def pdf_converter_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    # DB İŞLEMİ: Asenkron
    lang = await asyncio.to_thread(db.get_user_lang, user_id)
    state.clear_user_states(user_id)
    
    await update.message.reply_text(
        TEXTS["pdf_converter_menu_prompt"][lang],
        reply_markup=get_pdf_keyboard_markup(lang)
    )

async def prompt_text_for_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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

async def prompt_file_for_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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

async def handle_pdf_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    # DB İŞLEMİ: Asenkron
    lang = await asyncio.to_thread(db.get_user_lang, user_id)
    mode = context.user_data.get('pdf_mode')
    
    text_content = update.message.text.lower() if update.message.text else ""
    back_keywords = ["geri", "back", "назад", "araçlar menüsü", "tools menu", "меню инструментов"]
    if text_content in BUTTON_MAPPINGS["menu"] or text_content in BUTTON_MAPPINGS.get("back_to_tools", set()) or any(kw in text_content for kw in back_keywords):
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
async def weather_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    # DB İŞLEMİ: Asenkron
    lang = await asyncio.to_thread(db.get_user_lang, user_id)
    
    # API Key kontrolü - en başta yap
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
        state.clear_user_states(user_id)
        state.waiting_for_weather_city.add(user_id)
        
        # TEK MESAJ: Şehir seçim klavyesini (Reply Keyboard) gönder
        await update.message.reply_text(
            TEXTS["weather_prompt_city"][lang],
            reply_markup=get_weather_cities_keyboard(lang)
        )

async def get_weather_data(update: Update, context: ContextTypes.DEFAULT_TYPE, city_name):
    user_id = update.effective_user.id
    # DB İŞLEMİ: Asenkron
    lang = await asyncio.to_thread(db.get_user_lang, user_id)

    # --- ŞEHİR ADI DÖNÜŞTÜRME (BAYRAKLI İSİMLERDEN API İSİMLERİNE) ---
    # Kullanıcı "🇹🇷 İstanbul" gibi butona bastığında, API için "Istanbul" gerekiyor
    original_city_name = city_name
    for lang_code, cities in CITY_NAMES_TRANSLATED.items():
        for english_name, translated_name in cities.items():
            if city_name.strip() == translated_name.strip():
                city_name = english_name
                break
        if city_name != original_city_name:
            break

    # --- GERİ TUŞU KONTROLÜ (EKLENEN KISIM) ---
    city_name_lower = city_name.lower().strip()
    # Geri butonu kontrolü - tüm varyasyonları içerir
    back_keywords = ["geri", "back", "назад", "araçlar menüsü", "tools menu", "меню инструментов"]
    if city_name_lower in BUTTON_MAPPINGS["menu"] or city_name_lower in BUTTON_MAPPINGS.get("back_to_tools", set()) or any(kw in city_name_lower for kw in back_keywords):
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
        # Async HTTP request with aiohttp
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as response:
                data = await response.json()

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
            
            # 5 Günlük Tahmin butonu ekle (Inline Button)
            forecast_keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton(TEXTS["weather_forecast_button"][lang], callback_data=f"forecast_{city}")]
            ])
            
            # BAŞARILI SONUÇ: Şehir seçim klavyesini + Inline buton gönder
            await target_message.reply_text(msg, reply_markup=get_weather_cities_keyboard(lang))
            await target_message.reply_text(
                "👆",
                reply_markup=forecast_keyboard
            )
        else:
            await target_message.reply_text(TEXTS["weather_city_not_found"][lang].format(city=city_name))

    except asyncio.TimeoutError:
        await target_message.reply_text(TEXTS["weather_api_error"][lang])
    except aiohttp.ClientError:
        await target_message.reply_text(TEXTS["weather_api_error"][lang])
    except Exception as e:
        logging.getLogger(__name__).error(f"Weather Error: {e}")
        await target_message.reply_text(TEXTS["weather_api_error"][lang])
    
    # State'i silmiyoruz - kullanıcı başka şehir seçebilir veya Geri'ye basabilir
    # state.waiting_for_weather_city.discard(user_id)  # KALDIRILDI

async def weather_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user_id = query.from_user.id
    # DB İŞLEMİ: Asenkron
    lang = await asyncio.to_thread(db.get_user_lang, user_id)
    
    await query.answer()
    
    # 5 Günlük Tahmin butonu
    if query.data.startswith("forecast_"):
        city = query.data.replace("forecast_", "")
        await get_forecast_data(update, context, city, lang)
        return
    
    if query.data.startswith("weather_"):
        city_key = query.data.split("_")[1]
        
        # Inline butonları sil
        try:
            await query.message.delete()
        except Exception:
            pass
        
        # Şehir adını (Key olarak İngilizcesini) kullanarak hava durumunu çek
        await get_weather_data(update, context, city_key)

async def get_forecast_data(update: Update, context: ContextTypes.DEFAULT_TYPE, city: str, lang: str):
    """5 günlük hava durumu tahmini çeker ve gösterir"""
    from config import OPENWEATHERMAP_API_KEY
    from datetime import datetime as dt
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
        
        # Günlere göre grupla
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
        
        # İkon mapping
        icon_map = {
            "Clear": "☀️", "Clouds": "☁️", "Rain": "🌧️", "Drizzle": "🌦️",
            "Thunderstorm": "⛈️", "Snow": "❄️", "Mist": "🌫️", "Fog": "🌫️",
            "Haze": "🌫️", "Dust": "🌫️", "Smoke": "🌫️"
        }
        
        # Her gün için max/min hesapla
        lines = [TEXTS["weather_forecast_title"][lang].format(city=city)]
        
        for i, (day_key, items) in enumerate(sorted(daily_data.items())[:5]):
            temps = [item["temp"] for item in items]
            max_temp = round(max(temps))
            min_temp = round(min(temps))
            
            # Öğlen saatine en yakın veya ortadaki durumu al
            mid_item = items[len(items) // 2]
            desc = mid_item["desc"].title()
            icon = icon_map.get(mid_item["icon"], "🌡️")
            
            # Gün adı
            day_date = mid_item["date"]
            day_name = day_names.get(lang, day_names["en"])[day_date.weekday()]
            
            # Bugün/Yarın özel isimlendirme
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
        
        # Güncelle (inline mesajı düzenle)
        try:
            await query.message.edit_text(
                forecast_msg,
                parse_mode="Markdown"
            )
        except Exception:
            await query.message.reply_text(forecast_msg, parse_mode="Markdown")
        
    except Exception as e:
        logging.getLogger(__name__).error(f"Forecast Error: {e}")
        await query.message.reply_text(TEXTS["weather_api_error"][lang])


# --- GELİŞTİRİCİ ---
def get_developer_keyboard(lang):
    """Geliştirici menü klavyesi"""
    labels = {
        "tr": [["🌐 Web Sitem", "📸 Instagram"], ["✈️ Telegram", "💼 LinkedIn"], ["🔙 Geri"]],
        "en": [["🌐 My Website", "📸 Instagram"], ["✈️ Telegram", "💼 LinkedIn"], ["🔙 Back"]],
        "ru": [["🌐 Мой Сайт", "📸 Instagram"], ["✈️ Telegram", "💼 LinkedIn"], ["🔙 Назад"]]
    }
    return ReplyKeyboardMarkup(labels.get(lang, labels["en"]), resize_keyboard=True)

async def show_developer_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    lang = await asyncio.to_thread(db.get_user_lang, user_id)
    
    # State başlat
    import state
    state.clear_user_states(user_id)
    state.developer_menu_active.add(user_id)
    
    dev_text = {
        "tr": "👨‍💻 *Geliştirici Bilgileri*\n\nSosyal medya hesaplarıma aşağıdaki bağlantılardan ulaşabilirsiniz:",
        "en": "👨‍💻 *Developer Info*\n\nYou can reach my social media accounts through the links below:",
        "ru": "👨‍💻 *Информация о разработчике*\n\nВы можете связаться со мной через соцсети по ссылкам ниже:"
    }
    
    await update.message.reply_text(
        dev_text.get(lang, dev_text["en"]),
        reply_markup=get_developer_keyboard(lang),
        parse_mode="Markdown"
    )

async def handle_developer_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Geliştirici menüsü buton işleyicisi"""
    import state
    user_id = update.effective_user.id
    
    if user_id not in state.developer_menu_active:
        return False
    
    text = update.message.text.lower()
    lang = await asyncio.to_thread(db.get_user_lang, user_id)
    
    # Geri butonu
    if "geri" in text or "back" in text or "назад" in text:
        state.developer_menu_active.discard(user_id)
        # Önceki link mesajını temizle
        if "developer_last_link_msg" in context.user_data:
            try:
                await context.user_data["developer_last_link_msg"].delete()
            except Exception:
                pass
            del context.user_data["developer_last_link_msg"]
        from handlers.general import menu_command
        await menu_command(update, context)
        return True
    
    # Sosyal medya linkleri
    link = None
    if "web" in text or "сайт" in text:
        link = SOCIAL_MEDIA_LINKS["website"]
    elif "instagram" in text:
        link = SOCIAL_MEDIA_LINKS["instagram"]
    elif "telegram" in text:
        link = SOCIAL_MEDIA_LINKS["telegram"]
    elif "linkedin" in text:
        link = SOCIAL_MEDIA_LINKS["linkedin"]
    
    if link:
        # Önceki link mesajını sil
        if "developer_last_link_msg" in context.user_data:
            try:
                await context.user_data["developer_last_link_msg"].delete()
            except Exception:
                pass
        
        # Yeni mesajı gönder ve kaydet
        msg = await update.message.reply_text(f"🔗 {link}", reply_markup=get_developer_keyboard(lang))
        context.user_data["developer_last_link_msg"] = msg
        return True
    
    return False

async def handle_social_media_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    if query.data == "back_to_main_menu":
        await query.message.delete()

# --- VIDEO DOWNLOADER ---
from texts import VIDEO_DOWNLOADER_BUTTONS, FORMAT_SELECTION_BUTTONS

def get_video_downloader_keyboard_markup(lang):
    buttons = VIDEO_DOWNLOADER_BUTTONS.get(lang, VIDEO_DOWNLOADER_BUTTONS["en"])
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

def get_format_selection_keyboard_markup(lang):
    buttons = FORMAT_SELECTION_BUTTONS.get(lang, FORMAT_SELECTION_BUTTONS["en"])
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

@rate_limit("heavy")
async def video_downloader_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Video indirme platform seçim menüsü"""
    user_id = update.effective_user.id
    lang = await asyncio.to_thread(db.get_user_lang, user_id)
    state.clear_user_states(user_id)
    
    await update.message.reply_text(
        TEXTS["video_downloader_menu_prompt"][lang],
        reply_markup=get_video_downloader_keyboard_markup(lang)
    )

async def set_video_platform(update: Update, context: ContextTypes.DEFAULT_TYPE, platform: str):
    """Platform seçildi, format sorulsun"""
    user_id = update.effective_user.id
    lang = await asyncio.to_thread(db.get_user_lang, user_id)
    
    state.clear_user_states(user_id)
    state.waiting_for_format_selection[user_id] = platform
    
    await update.message.reply_text(
        TEXTS["format_selection_prompt"][lang],
        reply_markup=get_format_selection_keyboard_markup(lang)
    )

async def set_download_format(update: Update, context: ContextTypes.DEFAULT_TYPE, download_format: str):
    """Format seçildi, link iste"""
    user_id = update.effective_user.id
    lang = await asyncio.to_thread(db.get_user_lang, user_id)
    
    platform = state.waiting_for_format_selection.get(user_id)
    if not platform:
        # Format seçimi beklenmiyor, menüye yönlendir
        await video_downloader_menu(update, context)
        return
    
    state.waiting_for_format_selection.pop(user_id, None)
    state.waiting_for_video_link[user_id] = {"platform": platform, "format": download_format}
    
    platform_names = {
        "tiktok": "TikTok",
        "twitter": "Twitter/X", 
        "instagram": "Instagram"
    }
    platform_display = platform_names.get(platform, platform)
    
    await update.message.reply_text(
        TEXTS["video_downloader_prompt_link"][lang].format(platform=platform_display),
        reply_markup=get_input_back_keyboard_markup(lang)
    )

async def download_and_send_media(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Video/Ses linkini al, indir ve gönder"""
    user_id = update.effective_user.id
    lang = await asyncio.to_thread(db.get_user_lang, user_id)
    
    download_info = state.waiting_for_video_link.get(user_id)
    if not download_info:
        return False
    
    platform = download_info.get("platform")
    download_format = download_info.get("format", "video")
    url = update.message.text.strip()
    
    # Geri butonu kontrolü - Platform seçim menüsüne dön
    url_lower = url.lower()
    if url_lower in BUTTON_MAPPINGS.get("menu", set()) or url_lower in BUTTON_MAPPINGS.get("back_to_platform", set()) or "geri" in url_lower or "back" in url_lower or "назад" in url_lower:
        state.waiting_for_video_link.pop(user_id, None)
        await video_downloader_menu(update, context)
        return True
    
    # Platform-specific URL validation
    valid_domains = {
        "tiktok": ["tiktok.com", "vm.tiktok.com"],
        "twitter": ["twitter.com", "x.com", "t.co"],
        "instagram": ["instagram.com", "instagr.am"]
    }
    
    is_valid = any(domain in url.lower() for domain in valid_domains.get(platform, []))
    if not is_valid:
        platform_names = {"tiktok": "TikTok", "twitter": "Twitter/X", "instagram": "Instagram"}
        await update.message.reply_text(
            TEXTS["video_invalid_link"][lang].format(platform=platform_names.get(platform, platform))
        )
        return True
    
    # İndirme başladı mesajı
    if download_format == "audio":
        status_msg = await update.message.reply_text(TEXTS["audio_downloading"][lang])
    else:
        status_msg = await update.message.reply_text(TEXTS["video_downloading"][lang])
    
    output_path = f"media_{user_id}"
    downloaded_file = None
    
    try:
        import yt_dlp
        
        if download_format == "audio":
            # Ses indirme ayarları (MP3)
            ydl_opts = {
                'outtmpl': output_path + '.%(ext)s',
                'format': 'bestaudio/best',
                'noplaylist': True,
                'quiet': True,
                'no_warnings': True,
                'socket_timeout': 30,
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            }
        else:
            # Video indirme ayarları (MP4)
            ydl_opts = {
                'outtmpl': output_path + '.%(ext)s',
                'format': 'best[filesize<50M]/best',
                'noplaylist': True,
                'quiet': True,
                'no_warnings': True,
                'socket_timeout': 30,
            }
        
        # yt-dlp ile indir (blocking, thread içinde çalıştır)
        def download_media():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                if download_format == "audio":
                    # MP3 dosyasının yolunu döndür
                    return output_path + '.mp3'
                return ydl.prepare_filename(info)
        
        downloaded_file = await asyncio.to_thread(download_media)
        
        # Dosya var mı kontrol et
        if not os.path.exists(downloaded_file):
            # Alternatif uzantıları dene
            for ext in ['.mp3', '.mp4', '.webm', '.m4a']:
                alt_file = output_path + ext
                if os.path.exists(alt_file):
                    downloaded_file = alt_file
                    break
        
        if not os.path.exists(downloaded_file):
            await status_msg.edit_text(TEXTS["video_download_error"][lang].format(error="Dosya bulunamadı"))
            return True
        
        # Dosya boyutu kontrolü
        file_size = os.path.getsize(downloaded_file)
        if file_size > 50 * 1024 * 1024:  # 50MB
            await status_msg.edit_text(TEXTS["video_file_too_large"][lang])
            return True
        
        # Formatına göre gönder
        with open(downloaded_file, 'rb') as media_file:
            if download_format == "audio":
                await update.message.reply_audio(
                    media_file,
                    caption=TEXTS["audio_download_success"][lang],
                    reply_markup=get_tools_keyboard_markup(lang)
                )
            else:
                await update.message.reply_video(
                    media_file,
                    caption=TEXTS["video_download_success"][lang],
                    reply_markup=get_tools_keyboard_markup(lang)
                )
        
        await status_msg.delete()
        
    except Exception as e:
        error_msg = str(e)
        if len(error_msg) > 100:
            error_msg = error_msg[:100] + "..."
        await status_msg.edit_text(TEXTS["video_download_error"][lang].format(error=error_msg))
        logging.getLogger(__name__).error(f"Media download error: {e}")
        
    finally:
        state.waiting_for_video_link.pop(user_id, None)
        # Geçici dosyaları temizle
        if downloaded_file and os.path.exists(downloaded_file):
            os.remove(downloaded_file)
        # Olası diğer uzantılar
        for ext in ['.mp4', '.webm', '.mkv', '.mp4.part', '.mp3', '.m4a', '.opus']:
            temp_file = output_path + ext
            if os.path.exists(temp_file):
                os.remove(temp_file)
    
    return True