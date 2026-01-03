import asyncio
import os
import qrcode
from fpdf import FPDF
from PIL import Image
from telegram import Update
from telegram.ext import ContextTypes
import database as db
import state
from texts import TEXTS, PDF_CONVERTER_BUTTONS, BUTTON_MAPPINGS
from config import FONT_PATH
from utils import get_input_back_keyboard_markup, get_main_keyboard_markup
from rate_limiter import rate_limit
import logging

def get_pdf_keyboard_markup(lang):
    buttons = PDF_CONVERTER_BUTTONS.get(lang, PDF_CONVERTER_BUTTONS["en"])
    from telegram import ReplyKeyboardMarkup
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

# --- PDF DÖNÜŞTÜRÜCÜ ---
@rate_limit("heavy")
async def pdf_converter_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    lang = await asyncio.to_thread(db.get_user_lang, user_id)
    state.clear_user_states(user_id)
    
    await update.message.reply_text(
        TEXTS["pdf_converter_menu_prompt"][lang],
        reply_markup=get_pdf_keyboard_markup(lang)
    )

async def prompt_text_for_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
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
        
        if os.path.exists(FONT_PATH):
            pdf.add_font("DejaVu", "", FONT_PATH)
            pdf.set_font("DejaVu", size=12)
        else:
            pdf.set_font("Helvetica", size=12)

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
            
            if doc.mime_type == 'text/plain':
                doc_path = f"temp_doc_{str(user_id)}.txt"
                temp_files.append(doc_path)
                
                doc_file = await doc.get_file()
                await doc_file.download_to_drive(doc_path)
                
                with open(doc_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    pdf.multi_cell(w=pdf.epw, h=10, text=content)
                pdf.output(output_filename)
            
            elif doc.mime_type and doc.mime_type.startswith('image/'):
                img_path = f"temp_doc_img_{str(user_id)}"
                temp_files.append(img_path)
                
                doc_file = await doc.get_file()
                await doc_file.download_to_drive(img_path)
                
                try:
                    cover = Image.open(img_path)
                    
                    if img_path.lower().endswith('.png') or doc.mime_type == 'image/png':
                         if cover.mode in ('RGBA', 'LA') or (cover.mode == 'P' and 'transparency' in cover.info):
                             alpha = cover.convert('RGBA').split()[-1]
                             bg = Image.new("RGB", cover.size, (255, 255, 255))
                             bg.paste(cover, mask=alpha)
                             cover = bg
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
    await pdf_converter_menu(update, context)
