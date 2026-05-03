# tests/test_call_llm.py
"""
Tests for utils/call_llm.py.

Tests the LLM client with:
- Successful calls
- Rate limit handling (429) with retries
- Exponential backoff timing
- Max retries exhaustion
- Other error handling
"""

import pytest
import tempfile
import os
from unittest.mock import MagicMock, patch
import time


class TestCallLLM:
    """Tests for call_llm function."""

    def test_successful_call_returns_text(self):
        """Test that a successful call returns the LLM response text."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_choice.message.content = "Respuesta del LLM"
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response

        with patch("utils.call_llm._get_deepseek_client", return_value=mock_client):
            from utils.call_llm import call_llm
            result = call_llm("un prompt de prueba")

        assert result == "Respuesta del LLM"
        mock_client.chat.completions.create.assert_called_once()

    def test_client_is_singleton(self):
        """Test that DeepSeek client is created only once."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_choice.message.content = "test"
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response

        with patch("utils.call_llm.OpenAI", return_value=mock_client):
            from utils.call_llm import call_llm, _get_deepseek_client
            
            # Reset singleton for test
            import utils.call_llm
            utils.call_llm._deepseek_client = None

            # Get client twice
            client1 = _get_deepseek_client()
            client2 = _get_deepseek_client()

            # Should be the same instance
            assert client1 is client2, "Client should be singleton"
            # And only created once
            from utils.call_llm import OpenAI
            assert OpenAI.call_count == 1

    @patch("utils.call_llm.time.sleep")
    def test_retries_on_rate_limit_and_succeeds(self, mock_sleep):
        """Test that it retries on 429 and eventually succeeds."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_choice.message.content = "Respuesta exitosa"
        mock_response.choices = [mock_choice]
        
        # First two calls fail with 429, third succeeds
        error_429 = Exception("429 Too Many Requests")
        mock_client.chat.completions.create.side_effect = [
            error_429,
            error_429,
            mock_response,
        ]

        with patch("utils.call_llm._get_deepseek_client", return_value=mock_client):
            from utils.call_llm import call_llm
            result = call_llm("prompt de prueba", max_retries=3)

        assert result == "Respuesta exitosa"
        assert mock_client.chat.completions.create.call_count == 3
        # Check retry delays were called (10s, 20s)
        assert mock_sleep.call_count == 2

    @patch("utils.call_llm.time.sleep")
    def test_returns_empty_string_after_max_retries(self, mock_sleep):
        """Test that it returns empty string when all retries are exhausted."""
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("429 Too Many Requests")

        with patch("utils.call_llm._get_deepseek_client", return_value=mock_client):
            from utils.call_llm import call_llm
            result = call_llm("prompt de prueba", max_retries=5)

        assert result == ""
        assert mock_client.chat.completions.create.call_count == 5
        # Should have slept 5 times
        assert mock_sleep.call_count == 5

    @patch("utils.call_llm.time.sleep")
    def test_exponential_backoff_timing(self, mock_sleep):
        """Test that backoff intervals are: 10s, 20s, 30s, 60s."""
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("429 Too Many Requests")

        with patch("utils.call_llm._get_deepseek_client", return_value=mock_client):
            from utils.call_llm import call_llm
            result = call_llm("prompt", max_retries=4)

        assert result == ""
        assert mock_client.chat.completions.create.call_count == 4
        # Check exponential increase: 10, 20, 30 seconds (4th retry uses last delay: 60)
        mock_sleep.assert_any_call(10)
        mock_sleep.assert_any_call(20)
        mock_sleep.assert_any_call(30)

    @patch("utils.call_llm.time.sleep")
    def test_handles_non_rate_limit_errors(self, mock_sleep):
        """Test that non-429 errors are logged and return empty string immediately."""
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("Network error")

        with patch("utils.call_llm._get_deepseek_client", return_value=mock_client):
            from utils.call_llm import call_llm
            result = call_llm("prompt")

        assert result == ""
        mock_client.chat.completions.create.assert_called_once()
        mock_sleep.assert_not_called()  # No sleep for non-429 errors

    @patch("utils.call_llm.time.sleep")
    def test_respects_max_retries_parameter(self, mock_sleep):
        """Test that max_retries parameter controls retry count."""
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("429 Too Many Requests")

        with patch("utils.call_llm._get_deepseek_client", return_value=mock_client):
            from utils.call_llm import call_llm
            result = call_llm("prompt", max_retries=2)

        assert result == ""
        assert mock_client.chat.completions.create.call_count == 2


class TestTranscribeAudioWithLLM:
    """Tests for transcribe_audio_with_llm function."""

    @patch("utils.call_llm.sr.Recognizer")
    @patch("utils.call_llm.AudioSegment.from_file")
    def test_transcribes_audio_successfully(self, mock_audio_segment, mock_recognizer_class):
        """Test successful audio transcription."""
        # Mock AudioSegment conversion
        mock_audio = MagicMock()
        mock_audio_segment.return_value = mock_audio
        
        # Mock recognizer
        mock_recognizer = MagicMock()
        mock_recognizer_class.return_value = mock_recognizer
        mock_recognizer.recognize_google.return_value = "Transcripción del audio"
        
        # Mock context manager for sr.AudioFile
        mock_audio_file = MagicMock()
        mock_audio_file.__enter__.return_value = mock_audio_file
        
        from utils.call_llm import transcribe_audio_with_llm
        
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            temp_path = f.name
            f.write(b"fake audio content")

        try:
            with patch("utils.call_llm.sr.AudioFile", return_value=mock_audio_file):
                result = transcribe_audio_with_llm(temp_path)

            assert result == "Transcripción del audio"
            mock_audio_segment.assert_called_once()
            mock_audio.export.assert_called_once()
            mock_recognizer.recognize_google.assert_called_once()
            # File should be deleted after processing
            assert not os.path.exists(temp_path)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            # Clean up converted file too
            converted = temp_path.rsplit('.', 1)[0] + '_converted.wav'
            if os.path.exists(converted):
                os.remove(converted)

    @patch("utils.call_llm.sr.Recognizer")
    @patch("utils.call_llm.AudioSegment.from_file")
    def test_deletes_audio_file_on_error(self, mock_audio_segment, mock_recognizer_class):
        """Test that temp audio file is deleted even on error."""
        mock_audio_segment.side_effect = Exception("Conversion failed")

        from utils.call_llm import transcribe_audio_with_llm

        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            temp_path = f.name
            f.write(b"fake audio content")

        try:
            result = transcribe_audio_with_llm(temp_path)

            assert result == ""
            # File should still be deleted even on error
            assert not os.path.exists(temp_path)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            # Clean up converted file too (it shouldn't exist but just in case)
            converted = temp_path.rsplit('.', 1)[0] + '_converted.wav'
            if os.path.exists(converted):
                os.remove(converted)


class TestAnalyzeImageWithLLM:
    """Tests for analyze_image_with_llm function."""

    @patch("utils.call_llm.base64.b64encode")
    @patch("builtins.open", new_callable=MagicMock)
    @patch("utils.call_llm.time.sleep")
    def test_analyzes_image_successfully(self, mock_sleep, mock_open, mock_b64encode):
        """Test successful image analysis."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_choice.message.content = "Análisis de la imagen"
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response

        # Mock base64 encoding
        mock_b64encode.return_value.decode.return_value = "fake_base64_data"

        # Mock file read
        mock_file = MagicMock()
        mock_file.__enter__.return_value = mock_file
        mock_open.return_value = mock_file

        with patch("utils.call_llm._get_deepseek_client", return_value=mock_client):
            from utils.call_llm import analyze_image_with_llm

            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
                temp_path = f.name
                f.write(b"fake image content")

            try:
                result = analyze_image_with_llm(temp_path, "Analiza esto")

                assert result == "Análisis de la imagen"
                mock_client.chat.completions.create.assert_called_once()
                # Verify the call included image_url content
                call_kwargs = mock_client.chat.completions.create.call_args[1]
                assert "messages" in call_kwargs
                content = call_kwargs["messages"][0]["content"]
                assert isinstance(content, list)
                assert content[1]["type"] == "image_url"
                # File should be deleted after processing
                assert not os.path.exists(temp_path)
            finally:
                if os.path.exists(temp_path):
                    os.remove(temp_path)

    @patch("utils.call_llm.time.sleep")
    def test_deletes_image_file_on_error(self, mock_sleep):
        """Test that temp image file is deleted even on error."""
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("API Error")

        with patch("utils.call_llm._get_deepseek_client", return_value=mock_client):
            from utils.call_llm import analyze_image_with_llm

            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
                temp_path = f.name
                f.write(b"fake image content")

            try:
                result = analyze_image_with_llm(temp_path, "Analiza")

                assert result == ""
                # File should be deleted even on error
                assert not os.path.exists(temp_path)
            finally:
                if os.path.exists(temp_path):
                    os.remove(temp_path)


class TestRateLimitIntegration:
    """Integration tests for rate limit handling in context."""

    @patch("utils.call_llm.time.sleep")
    def test_consecutive_rate_limited_calls_all_retried(self, mock_sleep):
        """Test that multiple consecutive calls each get their own retries."""
        mock_client = MagicMock()

        with patch("utils.call_llm._get_deepseek_client", return_value=mock_client):
            from utils.call_llm import call_llm

            # All calls fail with 429
            mock_client.chat.completions.create.side_effect = Exception("429 Too Many Requests")

            # First call exhausts retries
            result1 = call_llm("prompt1", max_retries=3)
            assert result1 == ""
            assert mock_client.chat.completions.create.call_count == 3

            # Reset and make another call - should also retry 3 times
            mock_client.chat.completions.create.reset_mock()
            mock_client.chat.completions.create.side_effect = Exception("429 Too Many Requests")

            result2 = call_llm("prompt2", max_retries=3)
            assert result2 == ""
            assert mock_client.chat.completions.create.call_count == 3

    @patch("utils.call_llm.time.sleep")
    def test_retry_count_is_per_call_not_cumulative(self, mock_sleep):
        """Test that retry count resets for each call to call_llm."""
        mock_client = MagicMock()

        with patch("utils.call_llm._get_deepseek_client", return_value=mock_client):
            from utils.call_llm import call_llm

            # Make 5 consecutive calls, each exhausting 3 retries
            for i in range(5):
                mock_client.chat.completions.create.side_effect = Exception("429 Too Many Requests")
                result = call_llm(f"prompt{i}", max_retries=3)
                assert result == ""

            # Each call should have made 3 attempts (not 15 cumulative)
            assert mock_client.chat.completions.create.call_count == 15


class TestRateLimiter:
    """Tests for RateLimiter class."""

    def test_acquire_grants_slot_when_available(self):
        """Test that acquire grants a slot when under limit."""
        from utils.call_llm import RateLimiter

        limiter = RateLimiter(max_requests=5)
        assert limiter.acquire() is True
        assert len(limiter.requests) == 1

    def test_acquire_denies_when_limit_reached(self):
        """Test that acquire denies when limit is reached."""
        from utils.call_llm import RateLimiter

        limiter = RateLimiter(max_requests=2)
        limiter.acquire()
        limiter.acquire()
        assert limiter.acquire() is False

    def test_acquire_is_thread_safe(self):
        """Test that acquire doesn't raise with concurrent access."""
        from utils.call_llm import RateLimiter
        import threading

        limiter = RateLimiter(max_requests=10)
        errors = []

        def worker():
            try:
                for _ in range(20):
                    limiter.acquire()
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0, f"Thread safety errors: {errors}"

    def test_acquire_sliding_window_clears_old_requests(self):
        """Test that old requests are removed from the window."""
        from utils.call_llm import RateLimiter
        import time

        limiter = RateLimiter(max_requests=2, window_seconds=1)

        # Make 2 requests
        assert limiter.acquire() is True
        assert limiter.acquire() is True
        assert limiter.acquire() is False  # Limit reached

        # Wait for window to expire
        time.sleep(1.1)

        # Should be able to acquire again
        assert limiter.acquire() is True

    @patch("utils.call_llm.time.sleep")
    def test_wait_for_slot_blocks_until_available(self, mock_sleep):
        """Test that wait_for_slot blocks and returns True when slot available."""
        from utils.call_llm import RateLimiter

        limiter = RateLimiter(max_requests=1)

        # Consume the slot
        limiter.acquire()

        # Mock sleep to return immediately
        mock_sleep.side_effect = lambda x: None

        # Add a mock acquire that returns True on second call
        call_count = [0]
        original_acquire = limiter.acquire

        def mock_acquire():
            call_count[0] += 1
            if call_count[0] > 1:
                return True
            return original_acquire()

        limiter.acquire = mock_acquire

        result = limiter.wait_for_slot(timeout=2)
        assert result is True


class TestRequestQueue:
    """Tests for RequestQueue class."""

    def test_enqueue_returns_true_when_space_available(self):
        """Test that enqueue returns True when queue has space."""
        from utils.call_llm import RequestQueue

        queue = RequestQueue(max_size=3)
        assert queue.enqueue(lambda: None) is True
        assert queue.size() == 1

    def test_enqueue_returns_false_when_full(self):
        """Test that enqueue returns False when queue is full."""
        from utils.call_llm import RequestQueue

        queue = RequestQueue(max_size=2)
        queue.enqueue(lambda: None)
        queue.enqueue(lambda: None)
        assert queue.enqueue(lambda: None) is False

    def test_is_full_works_correctly(self):
        """Test that is_full returns correct state."""
        from utils.call_llm import RequestQueue

        queue = RequestQueue(max_size=2)
        assert queue.is_full() is False
        queue.enqueue(lambda: None)
        queue.enqueue(lambda: None)
        assert queue.is_full() is True

    def test_size_returns_correct_count(self):
        """Test that size returns the correct number of items."""
        from utils.call_llm import RequestQueue

        queue = RequestQueue(max_size=5)
        assert queue.size() == 0
        queue.enqueue(lambda: None)
        queue.enqueue(lambda: None)
        assert queue.size() == 2


class TestRateLimiterIntegration:
    """Integration tests for rate limiter with call_llm."""

    @patch("utils.call_llm._rate_limiter.wait_for_slot")
    @patch("utils.call_llm._get_deepseek_client")
    def test_call_llm_waits_for_rate_limiter(self, mock_client_func, mock_wait):
        """Test that call_llm waits for rate limiter before making request."""
        mock_wait.return_value = True
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_choice.message.content = "Success"
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response
        mock_client_func.return_value = mock_client

        from utils.call_llm import call_llm
        result = call_llm("test prompt")

        assert result == "Success"
        mock_wait.assert_called_once()

    @patch("utils.call_llm._rate_limiter.wait_for_slot")
    @patch("utils.call_llm._get_deepseek_client")
    def test_call_llm_returns_empty_when_rate_limiter_timeout(self, mock_client_func, mock_wait):
        """Test that call_llm returns empty string when rate limiter times out."""
        mock_wait.return_value = False

        from utils.call_llm import call_llm
        result = call_llm("test prompt")

        assert result == ""

    @patch("utils.call_llm._request_queue.is_full")
    @patch("utils.call_llm._get_deepseek_client")
    def test_call_llm_returns_empty_when_queue_full(self, mock_client_func, mock_is_full):
        """Test that call_llm returns empty when request queue is full."""
        mock_is_full.return_value = True

        from utils.call_llm import call_llm
        result = call_llm("test prompt")

        assert result == ""
