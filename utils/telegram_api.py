import os
import telegram
import logging
from telegram import Update
from dotenv import load_dotenv
import asyncio
from pydub import AudioSegment

load_dotenv()

logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_TOKEN not found in .env file.")

LAST_UPDATE_ID = None

async def initialize_bot():
    """
    Cleans up any pending messages when the bot starts.
    This prevents the bot from processing old messages when it restarts.
    """
    global LAST_UPDATE_ID
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    updates = await bot.get_updates(timeout=1)
    if updates:
        LAST_UPDATE_ID = updates[-1].update_id
        logger.info(f"-> Bot initialized. {len(updates)} pending messages have been cleaned.")

async def get_latest_updates():
    """
    Gets the latest un-processed message, handling text, voice, and button callbacks.
    """
    global LAST_UPDATE_ID
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    offset = LAST_UPDATE_ID + 1 if LAST_UPDATE_ID else None
    updates = await bot.get_updates(offset=offset, timeout=5)

    if not updates:
        return None

    latest_update = updates[-1]
    LAST_UPDATE_ID = latest_update.update_id
    
    # Case 1: It's a button press (callback_query)
    if latest_update.callback_query:
        callback_data = latest_update.callback_query.data
        user_name = latest_update.callback_query.from_user.first_name
        chat_id = latest_update.callback_query.message.chat_id
        
        logger.info(f"-> Button press received from '{user_name}': '{callback_data}'")
        
        # Acknowledge the button press to remove the "loading" icon
        await latest_update.callback_query.answer()
        
        # Treat the button's data as a new text message
        return {
            "type": "text",
            "chat_id": chat_id,
            "message_text": callback_data,
            "user_name": user_name
        }

    # If it's not a callback, check for a regular message
    if not latest_update.message:
        return None

    user_name = latest_update.message.from_user.first_name
    chat_id = latest_update.message.chat_id

    # Case 2: It's a text message
    if latest_update.message.text:
        return {
            "type": "text",
            "chat_id": chat_id,
            "message_text": latest_update.message.text,
            "user_name": user_name
        }

    # Case 3: It's a voice message
    if latest_update.message.voice:
        logger.info(f"-> Voice message received from '{user_name}'.")
        voice = latest_update.message.voice
        file = await bot.get_file(voice.file_id)
        
        os.makedirs("temp", exist_ok=True)
        ogg_path = f"temp/{voice.file_id}.ogg"
        wav_path = f"temp/{voice.file_id}.wav"

        await file.download_to_drive(ogg_path)
        
        audio = AudioSegment.from_ogg(ogg_path)
        audio.export(wav_path, format="wav")
        
        os.remove(ogg_path)

        return {
            "type": "audio",
            "chat_id": chat_id,
            "audio_path": wav_path,
            "user_name": user_name
        }

    return None

async def send_message(chat_id: int, text: str, reply_markup=None):
    """
    Sends a message to a specific Telegram chat.
    """
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    await bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup, parse_mode='Markdown')