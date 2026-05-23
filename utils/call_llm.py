# utils/call_llm.py
"""
Utility module for interacting with the DeepSeek API (OpenAI-compatible).
Wraps the client with a rate limiter, a request queue, and retry logic for robustness.
"""

import os
import logging
import time 
import threading
import queue
import base64
from openai import OpenAI
import speech_recognition as sr
from pydub import AudioSegment
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

# ============================================================
# SINGLETON - Cliente creado una sola vez
# ============================================================

_deepseek_client = None

def _get_deepseek_client():
    """Get or create singleton DeepSeek/OpenAI client instance."""
    global _deepseek_client
    if _deepseek_client is None:
        if not DEEPSEEK_API_KEY:
            raise ValueError(
                "DEEPSEEK_API_KEY not found. Set it in .env or as an environment variable."
            )
        _deepseek_client = OpenAI(
            api_key=DEEPSEEK_API_KEY,
            base_url="https://api.deepseek.com"
        )
        logger.info("Initialized DeepSeek client")
    return _deepseek_client


# ============================================================
# RATE LIMITING GLOBAL - Token Bucket (Sliding Window)
# ============================================================

class RateLimiter:
    """
    Token bucket rate limiter with sliding window approach.
    Thread-safe implementation for limiting API requests.
    
    Configuration: 15 requests per minute (safe for DeepSeek API)
    """
    
    MAX_REQUESTS_PER_MINUTE = 15
    WINDOW_SIZE_SECONDS = 60
    
    def __init__(self, max_requests: int = MAX_REQUESTS_PER_MINUTE, 
                 window_seconds: int = WINDOW_SIZE_SECONDS):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = []  # timestamps of recent requests
        self._lock = threading.Lock()
    
    def acquire(self) -> bool:
        """
        Acquire a slot for making a request.
        Returns True if slot is available, False otherwise.
        """
        with self._lock:
            now = time.time()
            # Remove requests outside the sliding window
            self.requests = [ts for ts in self.requests if now - ts < self.window_seconds]
            
            if len(self.requests) < self.max_requests:
                self.requests.append(now)
                return True
            return False
    
    def wait_for_slot(self, timeout: float = 120.0) -> bool:
        """
        Wait until a slot is available.
        Returns True if slot acquired, False if timeout reached.
        """
        start_time = time.time()
        while True:
            if self.acquire():
                return True
            
            if time.time() - start_time > timeout:
                return False
            
            # Wait a bit before checking again
            time.sleep(1)
    
    def time_until_available(self) -> float:
        """Returns seconds until a slot might be available."""
        with self._lock:
            if len(self.requests) < self.max_requests:
                return 0.0
            
            # Calculate when the oldest request will expire
            oldest = min(self.requests)
            return max(0.0, self.window_seconds - (time.time() - oldest))


# Global rate limiter instance
_rate_limiter = RateLimiter()


# ============================================================
# REQUEST QUEUE
# ============================================================

class RequestQueue:
    """
    Simple FIFO queue for requests.
    Maximum 5 requests can be enqueued waiting for processing.
    """
    
    MAX_QUEUE_SIZE = 5
    
    def __init__(self, max_size: int = MAX_QUEUE_SIZE):
        self.max_size = max_size
        self._queue = queue.Queue(maxsize=max_size)
        self._lock = threading.Lock()
    
    def enqueue(self, item: callable) -> bool:
        """
        Try to add a request to the queue.
        Returns True if enqueued, False if queue is full.
        """
        try:
            self._queue.put(item, block=False)
            return True
        except queue.Full:
            return False
    
    def dequeue(self, timeout: float = None) -> callable:
        """Get next item from queue. Blocks if empty."""
        return self._queue.get(block=True, timeout=timeout)
    
    def size(self) -> int:
        """Current queue size."""
        return self._queue.qsize()
    
    def is_full(self) -> bool:
        """Check if queue is at capacity."""
        return self._queue.full()


# Global request queue
_request_queue = RequestQueue()


# ============================================================
# EXPONENTIAL BACKOFF CONFIGURATION
# ============================================================

# Backoff delays: 10, 20, 30, 60 seconds (4 retries with escalating delays)
BACKOFF_DELAYS = [10, 20, 30, 60]
MAX_RETRIES = 5  # Maximum 5 retries (initial attempt + 5 retries = 6 calls max)


def _process_queue_worker():
    """
    Worker that processes queued requests in order.
    Runs in a background thread.
    """
    while True:
        try:
            request_info = _request_queue.dequeue(timeout=1)
            if request_info is None:
                continue
            
            prompt, callback = request_info
            try:
                result = call_llm_impl(prompt)
                callback((True, result))
            except Exception as e:
                callback((False, str(e)))
        except queue.Empty:
            continue
        except Exception as e:
            logger.error(f"Queue worker error: {e}")


# Start queue processing in background thread
_queue_thread = threading.Thread(target=_process_queue_worker, daemon=True)
_queue_thread.start()


# ============================================================
# MAIN LLM CALL FUNCTIONS
# ============================================================

def call_llm(prompt: str, max_retries: int = None) -> str:
    """
    Calls the language model to process the prompt, with retry logic,
    rate limiting, and request queue support.
    
    Args:
        prompt: The prompt to send to the LLM
        max_retries: Maximum number of retries (defaults to MAX_RETRIES)
    
    Returns:
        The LLM response text, or empty string on failure
    """
    if max_retries is None:
        max_retries = MAX_RETRIES
    
    # Check queue availability first
    if _request_queue.is_full():
        logger.warning("Request queue is full - service temporarily unavailable")
        return ""
    
    # Wait for rate limiter slot
    if not _rate_limiter.wait_for_slot(timeout=120):
        logger.warning("Rate limiter timeout - too many requests")
        return ""
    
    # Process the request
    return call_llm_impl(prompt, max_retries)


def call_llm_impl(prompt: str, max_retries: int = MAX_RETRIES) -> str:
    """
    Internal implementation of LLM call with retry logic.
    """
    client = _get_deepseek_client()
    attempts = 0
    
    while attempts < max_retries:
        try:
            response = client.chat.completions.create(
                model="deepseek-v4-flash",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                stream=False
            )
            return response.choices[0].message.content
        except Exception as e:
            if "429" in str(e):
                attempts += 1
                if attempts < len(BACKOFF_DELAYS):
                    wait_time = BACKOFF_DELAYS[attempts - 1]
                else:
                    wait_time = BACKOFF_DELAYS[-1]
                
                logger.info(f"-> API rate limit hit (429). Retrying in {wait_time} seconds... ({attempts}/{max_retries})")
                time.sleep(wait_time)
            else:
                logger.error(f"Error calling LLM: {e}")
                return ""
    
    logger.warning("-> Maximum number of retries for the LLM API exceeded.")
    return ""

def transcribe_audio_with_llm(audio_path: str) -> str:
    """
    Transcribes an audio file using speech recognition.
    Uses pydub for format conversion and Google Web Speech API (free) for recognition.
    """
    wav_path = None
    try:
        logger.info(f"Converting audio file: {audio_path}...")
        
        # Convert to WAV using pydub (handles various formats)
        wav_path = audio_path.rsplit('.', 1)[0] + '_converted.wav'
        audio = AudioSegment.from_file(audio_path)
        audio.export(wav_path, format="wav")
        
        logger.info("-> Audio converted to WAV. Transcribing...")
        
        recognizer = sr.Recognizer()
        with sr.AudioFile(wav_path) as source:
            audio_data = recognizer.record(source)
        
        text = recognizer.recognize_google(audio_data, language="es-ES")
        logger.info("-> Transcription successful")
        
        return text
    except sr.UnknownValueError:
        logger.error("Speech recognition could not understand audio")
        return ""
    except sr.RequestError as e:
        logger.error(f"Could not request results from speech recognition service: {e}")
        return ""
    except Exception as e:
        logger.error(f"Error during audio transcription: {e}")
        return ""
    finally:
        # Clean up all temp files
        for path in [audio_path, wav_path]:
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                except OSError:
                    pass

def analyze_image_with_llm(image_path: str, prompt: str) -> str:
    """
    Sends a local image to DeepSeek for analysis via vision API.
    """
    client = _get_deepseek_client()
    
    try:
        logger.info(f"Reading image at {image_path}...")
        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")
        
        # Determine image type from extension
        ext = os.path.splitext(image_path)[1].lower()
        mime_type = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".webp": "image/webp",
        }.get(ext, "image/jpeg")
        
        logger.info("Sending image to DeepSeek vision...")
        response = client.chat.completions.create(
            model="deepseek-v4-flash",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{image_data}"
                            }
                        }
                    ]
                }
            ],
            stream=False
        )
        
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Error analyzing image: {e}")
        return ""
    finally:
        # Always clean up the image file
        if os.path.exists(image_path):
            try:
                os.remove(image_path)
            except OSError:
                pass