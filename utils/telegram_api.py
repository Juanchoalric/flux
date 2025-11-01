import os
import telegram
import logging
from telegram import Update
from dotenv import load_dotenv
import asyncio

load_dotenv()

logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TELEGRAM_TOKEN:
    raise ValueError("No se encontró el TELEGRAM_TOKEN en el archivo .env")

LAST_UPDATE_ID = None

async def initialize_bot():
    """
    Limpia los mensajes pendientes al arrancar el bot.
    Esto evita que el bot procese mensajes antiguos al reiniciar.
    """
    global LAST_UPDATE_ID
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    updates = await bot.get_updates(timeout=1)
    if updates:
        LAST_UPDATE_ID = updates[-1].update_id
        logger.info(f"-> Bot inicializado. Se han limpiado {len(updates)} mensajes pendientes.")

async def get_latest_updates():
    """
    Obtiene el último mensaje no procesado de un chat.
    """
    global LAST_UPDATE_ID
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    offset = LAST_UPDATE_ID + 1 if LAST_UPDATE_ID else None
    updates = await bot.get_updates(offset=offset, timeout=5)
    if updates:
        latest_update = updates[-1]
        LAST_UPDATE_ID = latest_update.update_id
        if latest_update.message and latest_update.message.text:
            return {
                "chat_id": latest_update.message.chat_id,
                "message_text": latest_update.message.text,
                "user_name": latest_update.message.from_user.first_name
            }
    return None

async def send_message(chat_id: int, text: str):
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    await bot.send_message(chat_id=chat_id, text=text)

async def send_message(chat_id: int, text: str):
    """
    Envía un mensaje a un chat específico de Telegram.
    """
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    await bot.send_message(chat_id=chat_id, text=text)