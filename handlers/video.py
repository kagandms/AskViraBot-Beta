import asyncio
import os
import logging
import aiohttp
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
import database as db
import state
from texts import TEXTS, VIDEO_DOWNLOADER_BUTTONS, FORMAT_SELECTION_BUTTONS, BUTTON_MAPPINGS
from utils import get_input_back_keyboard_markup, get_tools_keyboard_markup, is_back_button
from rate_limiter import rate_limit

def get_video_downloader_keyboard_markup(lang):
    buttons = VIDEO_DOWNLOADER_BUTTONS.get(lang, VIDEO_DOWNLOADER_BUTTONS["en"])
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

def get_format_selection_keyboard_markup(lang):
    buttons = FORMAT_SELECTION_BUTTONS.get(lang, FORMAT_SELECTION_BUTTONS["en"])
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

@rate_limit("heavy")
async def video_downloader_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    lang = await asyncio.to_thread(db.get_user_lang, user_id)
    await state.clear_user_states(user_id)
    
    await update.message.reply_text(
        TEXTS["video_downloader_menu_prompt"][lang],
        reply_markup=get_video_downloader_keyboard_markup(lang)
    )

async def set_video_platform(update: Update, context: ContextTypes.DEFAULT_TYPE, platform: str):
    user_id = update.effective_user.id
    lang = await asyncio.to_thread(db.get_user_lang, user_id)
    
    await state.clear_user_states(user_id)
    # Store platform in persistent state data
    await state.set_state(user_id, state.WAITING_FOR_FORMAT_SELECTION, {"platform": platform})
    
    await update.message.reply_text(
        TEXTS["format_selection_prompt"][lang],
        reply_markup=get_format_selection_keyboard_markup(lang)
    )

async def set_download_format(update: Update, context: ContextTypes.DEFAULT_TYPE, download_format: str):
    user_id = update.effective_user.id
    lang = await asyncio.to_thread(db.get_user_lang, user_id)
    
    # Retrieve platform from persistent state
    state_data = await state.get_data(user_id)
    platform = state_data.get("platform")
    
    if not platform:
        await video_downloader_menu(update, context)
        return
    
    # Update to next state with accumulated data
    await state.clear_user_states(user_id)
    await state.set_state(user_id, state.WAITING_FOR_VIDEO_LINK, {"platform": platform, "format": download_format})
    
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
    user_id = update.effective_user.id
    lang = await asyncio.to_thread(db.get_user_lang, user_id)
    
    # State zaten main.py'de kontrol edildi

    download_info = await state.get_data(user_id)
    if not download_info:
        return False
    
    platform = download_info.get("platform")
    download_format = download_info.get("format", "video")
    url = update.message.text.strip()
    
    url_lower = url.lower()
    if is_back_button(url_lower):
        await state.clear_user_states(user_id)
        await video_downloader_menu(update, context)
        return True
    
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
    
    if download_format == "audio":
        status_msg = await update.message.reply_text(TEXTS["audio_downloading"][lang])
    else:
        status_msg = await update.message.reply_text(TEXTS["video_downloading"][lang])
    
    output_path = f"media_{user_id}"
    downloaded_file = None
    
    try:
        import yt_dlp
        
        if download_format == "audio":
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
            ydl_opts = {
                'outtmpl': output_path + '.%(ext)s',
                'format': 'best[filesize<50M]/best',
                'noplaylist': True,
                'quiet': True,
                'no_warnings': True,
                'socket_timeout': 30,
            }
        
        def download_media():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                if download_format == "audio":
                    return output_path + '.mp3'
                return ydl.prepare_filename(info)
        
        downloaded_file = await asyncio.to_thread(download_media)
        
        if not os.path.exists(downloaded_file):
            for ext in ['.mp3', '.mp4', '.webm', '.m4a']:
                alt_file = output_path + ext
                if os.path.exists(alt_file):
                    downloaded_file = alt_file
                    break
        
        if not os.path.exists(downloaded_file):
            await status_msg.edit_text(TEXTS["video_download_error"][lang].format(error="Dosya bulunamadı"))
            return True
        
        file_size = os.path.getsize(downloaded_file)
        if file_size > 50 * 1024 * 1024:
            await status_msg.edit_text(TEXTS["video_file_too_large"][lang])
            return True
        
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
        await state.clear_user_states(user_id)
        if downloaded_file and os.path.exists(downloaded_file):
            os.remove(downloaded_file)
        for ext in ['.mp4', '.webm', '.mkv', '.mp4.part', '.mp3', '.m4a', '.opus']:
            temp_file = output_path + ext
            if os.path.exists(temp_file):
                os.remove(temp_file)
    
    return True
