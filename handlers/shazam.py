
import os
import asyncio
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
# from shazamio import Shazam # Will import inside function to avoid import error if not installed yet
import database as db
from texts import TEXTS

async def recognize_file(file_path: str):
    """Recognize music from file using Shazam"""
    from shazamio import Shazam
    shazam = Shazam()
    out = await shazam.recognize(file_path)
    return out

def format_shazam_result(result, lang):
    """Format Shazam result for display"""
    track = result.get('track')
    if not track:
        return None
        
    title = track.get('title', 'Unknown')
    subtitle = track.get('subtitle', 'Unknown')
    images = track.get('images', {})
    cover_art = images.get('coverarthq') or images.get('coverart')
    
    sections = track.get('sections', [])
    lyrics = None
    for section in sections:
        if section.get('type') == 'LYRICS':
            lyrics = section.get('text')
            break
            
    # Basic formatting
    msg = f"🎵 *{title}*\n👤 {subtitle}\n"
    
    # Metadata shortcuts
    providers = track.get('hub', {}).get('providers', [])
    links = []
    for provider in providers:
        capt = provider.get('caption')
        actions = provider.get('actions', [])
        for action in actions:
            uri = action.get('uri')
            if uri and capt:
                links.append(f"[{capt}]({uri})")
                
    if links:
        msg += "\n" + " | ".join(links)
        
    return {"text": msg, "photo": cover_art}

    return {"text": msg, "photo": cover_art}


from utils import is_back_button
from handlers import tools
import state

async def start_shazam_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start Shazam mode"""
    user_id = update.effective_user.id
    lang = await asyncio.to_thread(db.get_user_lang, user_id)
    
    # Clean up trigger
    try:
        await update.message.delete()
    except: pass
    
    await state.clear_user_states(user_id)
    await state.set_state(user_id, state.WAITING_FOR_SHAZAM)
    
    from texts.strings import INPUT_BACK_BUTTONS
    kb = ReplyKeyboardMarkup(INPUT_BACK_BUTTONS[lang], resize_keyboard=True)
    
    msg = await update.message.reply_text(
        TEXTS["shazam_menu_prompt"][lang],
        reply_markup=kb,
        parse_mode="Markdown"
    )
    # Store message ID if needed for cleanup? (General policy doesn't restrict menu prompts usually)

async def handle_shazam_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle audio/video/voice/link input for Shazam"""
    user_id = update.effective_user.id
    lang = await asyncio.to_thread(db.get_user_lang, user_id)
    msg_obj = update.message
    text = msg_obj.text
    
    # Back check
    if is_back_button(text):
        await tools.tools_menu(update, context) # Return to tools
        return

    # Delete user input
    try:
        await update.message.delete()
    except: pass

    process_msg_text = TEXTS["shazam_processing"][lang]
    processing_msg = await update.message.reply_text(process_msg_text)
    
    file_path = None
    
    try:
        # 1. Check for Files
        file_id = None
        if msg_obj.audio: file_id = msg_obj.audio.file_id
        elif msg_obj.voice: file_id = msg_obj.voice.file_id
        elif msg_obj.video: file_id = msg_obj.video.file_id
        elif msg_obj.video_note: file_id = msg_obj.video_note.file_id
        elif msg_obj.document:
             mime = msg_obj.document.mime_type
             if mime and ('audio' in mime or 'video' in mime):
                 file_id = msg_obj.document.file_id
        
        if file_id:
            # Download file
            new_file = await context.bot.get_file(file_id)
            file_name = f"temp_shazam_{user_id}_{file_id[:10]}"
            file_path = f"/tmp/{file_name}"
            await new_file.download_to_drive(file_path)
            
        # 2. Check for Links
        elif text and ("http" in text) and any(x in text for x in ["instagram", "tiktok", "youtube", "youtu.be", "shorts"]):
            import yt_dlp
            file_path = f"/tmp/temp_shazam_link_{user_id}.mp3"
            
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': file_path,
                'noplaylist': True,
                'quiet': True,
                # Duration limit to avoid long downloads? Shazam only needs a snippet.
                # yt-dlp doesn't easily partial download. But we can use post-processor.
                # For now full download.
            }
            if os.path.exists(file_path):
                os.remove(file_path)
                
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([text])
        
        else:
            # Invalid input
            await processing_msg.delete()
            return # Ignore non-matching text (maybe random chat)
            
        # 3. Recognize
        if file_path and os.path.exists(file_path):
             result = await recognize_file(file_path)
             formatted = format_shazam_result(result, lang)
             
             await processing_msg.delete()
             
             if formatted:
                caption = TEXTS["shazam_result_caption"][lang].format(
                    title=result['track']['title'],
                    artist=result['track']['subtitle'],
                    album=result['track'].get('sections', [{}])[0].get('metadata', [{}])[0].get('text', 'Unknown') # Album fallback tricky
                )
                # Correction: format_shazam_result already does formatting, but I used a different key in TEXTS.
                # Let's rely on format_shazam_result's text logic or use the TEXTS key.
                # format_shazam_result returns "text" populated.
                
                if formatted["photo"]:
                    await update.message.reply_photo(photo=formatted["photo"], caption=formatted["text"], parse_mode="Markdown")
                else:
                    await update.message.reply_text(formatted["text"], parse_mode="Markdown")
             else:
                await update.message.reply_text(TEXTS["shazam_not_found"][lang])
                
             # Cleanup
             os.remove(file_path)
        else:
             await processing_msg.delete()
             await update.message.reply_text("❌ Download failed.")

    except Exception as e:
        try:
            await processing_msg.delete()
        except: pass
        await update.message.reply_text(f"❌ Error: {str(e)}")
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
