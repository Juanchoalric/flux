import os
import logging
import time 
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("No se encontró la GEMINI_API_KEY en el archivo .env")

genai.configure(api_key=GEMINI_API_KEY)

def call_llm(prompt: str, max_retries: int = 3) -> str:
    """
    Llama al modelo de lenguaje para procesar el prompt, con lógica de reintentos.
    """
    model = genai.GenerativeModel('gemini-2.0-flash')
    attempts = 0
    while attempts < max_retries:
        try:
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            if "429" in str(e):
                attempts += 1
                wait_time = 5 * attempts 
                logger.info(f"-> Límite de API alcanzado (429). Reintentando en {wait_time} segundos... ({attempts}/{max_retries})")
                time.sleep(wait_time)
            else:
                logger.error(f"Error al llamar al LLM: {e}")
                return ""
    
    logger.warning("-> Se superó el número máximo de reintentos para la API del LLM.")
    return ""