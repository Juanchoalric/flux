import os
import logging
import time 
import threading
import queue
import PIL.Image
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in the .env file")

genai.configure(api_key=GEMINI_API_KEY)

# ============================================================
# SINGLETON - Modelo creado una sola vez
# ============================================================

_GEMINI_MODEL_NAME = 'gemini-2.0-flash'
_gemini_model = None

def _get_gemini_model():
    """Get or create singleton Gemini model instance."""
    global _gemini_model
    if _gemini_model is None:
        _gemini_model = genai.GenerativeModel(_GEMINI_MODEL_NAME)
        logger.info(f"Initialized Gemini model: {_GEMINI_MODEL_NAME}")
    return _gemini_model


# ============================================================
# RATE LIMITING GLOBAL - Token Bucket (Sliding Window)
# ============================================================

class RateLimiter:
    """
    Token bucket rate limiter with sliding window approach.
    Thread-safe implementation for limiting API requests.
    
    Configuration: 15 requests per minute (safe for Gemini free tier)
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
    model = _get_gemini_model()
    attempts = 0
    
    while attempts < max_retries:
        try:
            response = model.generate_content(prompt)
            return response.text
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
    Uploads an audio file and asks the multimodal LLM to transcribe it.
    """
    logger.info(f"Uploading audio file: {audio_path} to Gemini...")
    model = _get_gemini_model() 
    
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
        return ""
    finally:
        # Always clean up the audio file
        if os.path.exists(audio_path):
            try:
                os.remove(audio_path)
            except OSError:
                pass

def analyze_image_with_llm(image_path: str, prompt: str) -> str:
    """
    Envía una imagen local a Gemini para análisis junto con un prompt.
    """
    model = _get_gemini_model()
    
    try:
        logger.info(f"Opening image at {image_path}...")
        img = PIL.Image.open(image_path)
        
        logger.info("Sending image to Gemini...")
        response = model.generate_content([prompt, img])
        
        return response.text
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