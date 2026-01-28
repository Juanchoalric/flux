import os
import logging
import time 
import PIL.Image
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

def transcribe_audio_with_llm(audio_path: str) -> str:
    """
    Uploads an audio file and asks the multimodal LLM to transcribe it.
    """
    logger.info(f"Uploading audio file: {audio_path} to Gemini...")
    model = genai.GenerativeModel('gemini-2.0-flash') 
    
    try:
        # 1. Upload the file to the Gemini API
        audio_file = genai.upload_file(path=audio_path)
        logger.info("-> Audio file uploaded successfully.")
        
        # 2. Send the file and a prompt to the model
        prompt = "Transcribe este audio a texto. Responde únicamente con el texto transcrito."
        response = model.generate_content([prompt, audio_file])
        
        # 3. Clean up the local audio file after processing
        os.remove(audio_path)
        
        return response.text.strip()
    except Exception as e:
        logger.error(f"Error during audio transcription: {e}")
        if os.path.exists(audio_path):
            os.remove(audio_path)
        return ""
    
def analyze_image_with_llm(image_path: str, prompt: str) -> str:
    """
    Envía una imagen local a Gemini para análisis junto con un prompt.
    """
    model = genai.GenerativeModel('gemini-2.0-flash')
    
    try:
        logger.info(f"Opening image at {image_path}...")
        img = PIL.Image.open(image_path)
        
        logger.info("Sending image to Gemini...")
        response = model.generate_content([prompt, img])
        
        os.remove(image_path) 
        
        return response.text
    except Exception as e:
        logger.error(f"Error analyzing image: {e}")
        return ""