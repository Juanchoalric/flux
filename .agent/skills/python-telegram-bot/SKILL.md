---
name: python-telegram-bot
description: >
  Guía para python-telegram-bot. Manejo de updates, mensajes, callbacks, media.
  Trigger: Cuando se modifica nodes.py, telegram_api.py o se agrega funcionalidad al bot.
license: Apache-2.0
metadata:
  author: gentleman-programming
  version: "1.0"
---

## When to Use

- Proyecto usa python-telegram-bot
- Se agregan handlers de mensajes, callbacks, keyboards
- Necesitas enviar mensajes, fotos, audio, o recibir voice messages
- Troubleshooting de webhooks o polling

## Setup

```bash
pip install python-telegram-bot
```

## Patterns Usados en Este Proyecto

### 1. Receiving Updates (Async)

```python
# utils/telegram_api.py pattern
from telegram import Update
from telegram.ext import Application, ContextTypes

async def get_latest_updates():
    # Usar con polling o webhook
    application = Application.builder().token(TOKEN).build()
    # ...
```

### 2. Sending Messages

```python
async def send_message(chat_id: int, text: str, reply_markup=None):
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    
    await application.bot.send_message(
        chat_id=chat_id,
        text=text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
```

### 3. Inline Keyboards

```python
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

keyboard = [
    [InlineKeyboardButton("📊 Resumen", callback_data="resumen hoy")],
    [InlineKeyboardButton("❓ Ayuda", callback_data="ayuda")]
]
reply_markup = InlineKeyboardMarkup(keyboard)

await bot.send_message(chat_id, "Elige:", reply_markup=reply_markup)
```

### 4. Handling Different Message Types

```python
# En nodes.py - GetMessageNode
def post(self, shared, _, exec_res):
    msg_type = exec_res.get("type")  # "text", "audio", "photo"
    
    if msg_type == "audio":
        return "transcribe"
    elif msg_type == "text":
        return "detect_intent"
    elif msg_type == "photo":
        return "analyze_receipt"
```

### 5. Callback Query Handlers

```python
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data  # "resumen hoy", "ayuda", etc.
    # Process callback
```

## Common Patterns

### Keyboard con Emoji

```python
# Botones comunes
InlineKeyboardButton("✅ Confirmar", callback_data="confirm"),
InlineKeyboardButton("❌ Cancelar", callback_data="cancel"),
InlineKeyboardButton("📊 Resumen", callback_data="resumen"),
InlineKeyboardButton("❓ Ayuda", callback_data="ayuda"),
```

### Parse Modes

```python
# Markdown (limitado)
parse_mode="Markdown"

# HTML (más flexible)
parse_mode="HTML"

# Mensaje con bold e italic:
"*Negrita* y _italic_ y `code`"
"<b>Negrita</b> y <i>italic</i>"
```

### Handling Photos

```python
# Recibir photo
photo = update.message.photo[-1]  # La foto con mayor resolución
file = await bot.get_file(photo.file_id)
await file.download_to_drive("photo.jpg")

# Enviar photo
await bot.send_photo(chat_id=chat_id, photo=open("img.jpg", "rb"))
```

### Handling Voice/Audio

```python
# Recibir voice
voice = update.message.voice
file = await bot.get_file(voice.file_id)
await file.download_to_drive("audio.ogg")

# O usar audio directamente
audio = update.message.audio
```

## Webhook vs Polling

| Modo | Cuándo usarlo | Config |
|------|---------------|--------|
| **Polling** | Desarrollo local | `application.run_polling()` |
| **Webhook** | Producción | `application.run_webhook()` + nginx/cert |

### Webhook Setup

```python
app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

# Webhook config
await app.bot.set_webhook("https://tu-dominio.com/webhook")
app.run_webhook(
    listen="0.0.0.0",
    port=8443,
    url_path="webhook",
    cert="cert.pem"
)
```

## Errores Comunes

1. **No usar await con métodos async** → "coroutine was never awaited"
2. **No hacer answer() en callbacks** → el botón queda colgado
3. **Chat ID wrong** → verificar que sea integer, no string
4. **Message too long** → usar split o MarkdownV2

## Commands

```bash
# Test de bot
python -c "from telegram import Bot; print(Bot(token='TOKEN').get_me())"

# Webhook info
curl https://api.telegram.org/bot<TOKEN>/getWebhookInfo
```

## Resources

- **Docs**: https://docs.python-telegram-bot.org/
- **API Reference**: https://docs.python-telegram-bot.org/telegram.bot
- **Ejemplos**: https://github.com/python-telegram-bot/python-telegram-bot/tree/master/examples
