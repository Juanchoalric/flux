---
name: gemini-api
description: >
  Guía para Google Generative AI (Gemini). Chat, Vision, Audio transcription.
  Trigger: Cuando se modifica call_llm.py, prompts.py o se agrega análisis con LLM.
license: Apache-2.0
metadata:
  author: gentleman-programming
  version: "1.0"
---

## When to Use

- Proyecto usa google-generativeai para Gemini
- Se necesitan llamadas a LLM (chat, vision, transcription)
- Agregar nuevos prompts o modificar existentes
- Troubleshooting de API calls, rate limits

## Setup

```bash
pip install google-generativeai
```

## Environment Variables

```bash
# .env
GOOGLE_API_KEY=tu_api_key_aqui
GEMINI_MODEL=gemini-2.0-flash
```

## Patterns Usados en Este Proyecto

### 1. Basic Chat Call

```python
# utils/call_llm.py
from google import genai

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

def call_llm(prompt: str, model: str = None) -> str:
    model = model or os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    
    response = client.models.generate_content(
        model=model,
        contents=[prompt]
    )
    return response.text
```

### 2. Chat con Historia

```python
def call_llm_with_history(messages: list, model: str = None) -> str:
    """Chat con conversation history."""
    model = model or os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    
    response = client.models.generate_content(
        model=model,
        contents=messages
    )
    return response.text

# Usage
messages = [
    {"role": "user", "content": "Hola, soy Juan"},
    {"role": "model", "content": "Hola Juan! Cómo te ayuda?"},
    {"role": "user", "content": "Cuánto gasté en comida?"}
]
```

### 3. Vision (Image Analysis)

```python
# utils/call_llm.py
def analyze_image_with_llm(image_path: str, prompt: str) -> str:
    """Analyze image with Gemini Vision."""
    import PIL.Image
    
    client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
    
    image = PIL.Image.open(image_path)
    
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=[prompt, image]
    )
    return response.text
```

### 4. Audio Transcription

```python
# utils/call_llm.py
def transcribe_audio_with_llm(audio_path: str) -> str:
    """Transcribe audio file using Gemini."""
    import pathlib
    
    client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
    
    audio_file = pathlib.Path(audio_path)
    
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=[
            "Transcribe this audio exactly as spoken. Return only the text.",
            genai.upload_file(audio_file)
        ]
    )
    return response.text
```

### 5. JSON Response

```python
# Para recibir JSON estructurado
def call_llm_json(prompt: str, schema: dict = None) -> dict:
    """Call LLM and parse JSON response."""
    from google.generativeai import types
    
    client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
    
    generation_config = {
        "response_mime_type": "application/json",
    }
    if schema:
        generation_config["response_schema"] = schema
    
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=[prompt],
        generation_config=generation_config
    )
    return json.loads(response.text)
```

## Prompts (utils/prompts.py)

### Estructura de Prompt

```python
def get_parse_expense_prompt(categories: str, message: str) -> str:
    return f"""
Eres un asistente que parsea mensajes de gastos.

Categorías válidas: {categories}

Mensaje del usuario: {message}

Retorna un JSON array con objetos:
[{{"amount": 5000, "category": "comida", "description": "almuerzo"}}]

Solo retorna el JSON, sin texto adicional.
"""
```

### Tips para Prompts

1. **Ser específico** sobre formato de salida
2. **Incluir ejemplos** cuando sea complejo
3. **Mentionar** "Return only JSON" o "Solo retorna JSON"
4. **Manejar errores** en el código, no en el prompt

## Modelos Disponibles

| Model | Use Case | Speed | Cost |
|-------|----------|-------|------|
| gemini-2.0-flash | General, fast | ⚡⚡⚡ | $ |
| gemini-2.0-flash-lite | Simple tasks | ⚡⚡⚡⚡ | $ |
| gemini-2.0-pro | Complex reasoning | ⚡⚡ | $$ |
| gemini-1.5-pro | Large context | ⚡⚡ | $$ |
| gemini-1.5-flash | Balanced | ⚡⚡ | $ |

## Errores Comunes

1. **API Key not set** → Verificar GOOGLE_API_KEY
2. **Rate limit** → Implementar exponential backoff
3. **Invalid image format** → Usar PIL y formatos soportados (JPEG, PNG, WebP)
4. **Audio too long** → Gemini tiene límites de duración
5. **JSON parse error** → El modelo a veces devuelve texto extra

## Retry Pattern

```python
import time

def call_llm_with_retry(prompt: str, max_retries: int = 3) -> str:
    for attempt in range(max_retries):
        try:
            return call_llm(prompt)
        except Exception as e:
            if attempt < max_retries - 1:
                wait = 2 ** attempt  # exponential backoff
                time.sleep(wait)
            else:
                raise e
```

## Configuration

```python
# Generation config opcional
generation_config = {
    "temperature": 0.7,        # 0.0-1.0 (creativity)
    "top_p": 0.95,            # nucleus sampling
    "top_k": 40,              # token filtering
    "max_output_tokens": 2048,
    "response_mime_type": "text/plain",
}
```

## Commands

```bash
# Test de API
python -c "
from google import genai
client = genai.Client(api_key='TU_KEY')
print(client.models.list())
"

# Ver modelos disponibles
python -c "
import os
os.environ['GOOGLE_API_KEY'] = 'TU_KEY'
from google import genai
client = genai.Client()
for m in client.models.list():
    print(m.name)
"
```

## Resources

- **Docs**: https://ai.google.dev/docs
- **API Reference**: https://ai.google.dev/api/generative-ai
- **Models**: https://ai.google.dev/models
- **Pricing**: https://ai.google.dev/pricing
