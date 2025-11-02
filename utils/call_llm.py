import os
import logging
import time 
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in the .env file")

genai.configure(api_key=GEMINI_API_KEY)

def call_llm(prompt: str, max_retries: int = 3) -> str:
    """
    Calls the language model to process the prompt, with retry logic.
    """
    model = genai.GenerativeModel('gemini-2.0-flash')
    attempts = 0
    while attempts < max_retries:
        try:
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            # Check for rate limit error (429)
            if "429" in str(e):
                attempts += 1
                wait_time = 5 * attempts 
                logger.info(f"-> API rate limit hit (429). Retrying in {wait_time} seconds... ({attempts}/{max_retries})")
                time.sleep(wait_time)
            else:
                logger.error(f"Error calling LLM: {e}")
                return ""
    
    logger.warning("-> Maximum number of retries for the LLM API exceeded.")
    return ""