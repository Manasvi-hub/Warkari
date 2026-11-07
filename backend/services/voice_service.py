"""Gnani Timbre TTS (Text-to-Speech) Service Module.

Endpoint: POST https://api.vachana.ai/api/v1/tts/inference
Authentication Header: X-API-Key-ID: API_KEY
Model: timbre-v2.5 (10 Indian languages support)

Default voice mappings for timbre-v2.5:
- mr-IN (Marathi): Nalini (default / standard Indian neural voice)
- hi-IN (Hindi): Nalini
- en-IN (English): Nalini / Kaveri
"""

import logging
from typing import Any, Dict, Optional, Tuple
import requests
from backend.config import get_settings

logger = logging.getLogger("warkari.services.voice")

TIMBRE_TTS_ENDPOINT = "https://api.vachana.ai/api/v1/tts/inference"

# Supported language codes for Timbre v2.5
SUPPORTED_TTS_LANGUAGES = {
    "mr": "mr-IN",
    "mr-in": "mr-IN",
    "mr-IN": "mr-IN",
    "hi": "hi-IN",
    "hi-in": "hi-IN",
    "hi-IN": "hi-IN",
    "en": "en-IN",
    "en-in": "en-IN",
    "en-IN": "en-IN",
}

DEFAULT_VOICE_PER_LANG = {
    "mr-IN": "Nalini",
    "hi-IN": "Nalini",
    "en-IN": "Nalini",
}


class VoiceServiceError(Exception):
    """Custom exception raised for TTS processing errors."""
    def __init__(self, message: str, status_code: int = 502, error_code: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code


class VoiceService:
    def __init__(self, api_key: Optional[str] = None):
        self.endpoint = TIMBRE_TTS_ENDPOINT
        self._explicit_api_key = api_key

    @property
    def api_key(self) -> Optional[str]:
        return self._explicit_api_key or get_settings().GNANI_API_KEY

    @property
    def is_configured(self) -> bool:
        """Checks if the service has an API key configured."""
        key = self.api_key
        return bool(key and key.strip())

    def resolve_language_code(self, lang_input: str) -> str:
        """Normalizes and validates target TTS language code."""
        normalized = (lang_input or "mr-IN").strip().lower()
        if normalized in SUPPORTED_TTS_LANGUAGES:
            return SUPPORTED_TTS_LANGUAGES[normalized]
        if lang_input in ["mr-IN", "hi-IN", "en-IN"]:
            return lang_input
        raise ValueError(
            f"Unsupported language code '{lang_input}' for TTS. Supported: Marathi (mr-IN), Hindi (hi-IN), English (en-IN)."
        )

    def synthesize_speech(
        self,
        text: str,
        language: str = "mr-IN",
        voice: Optional[str] = None,
        speed: float = 1.0,
        timeout: int = 30
    ) -> Tuple[bytes, str]:
        """Synthesizes text into speech using Gnani Timbre v2.5.

        Args:
            text: Text to synthesize.
            language: Language code ('mr-IN', 'hi-IN', 'en-IN').
            voice: Voice name in timbre-v2.5 catalog (defaults to 'Nalini').
            speed: Playback speed multiplier (0.85 to 1.15).
            timeout: Network timeout in seconds.

        Returns:
            Tuple of (raw_audio_bytes, content_type)
        """
        if not self.is_configured:
            raise VoiceServiceError(
                "VoiceService is unconfigured. GNANI_API_KEY is missing from environment.",
                status_code=503,
                error_code="MISSING_API_KEY"
            )

        clean_text = (text or "").strip()
        if not clean_text:
            raise VoiceServiceError("Text to synthesize cannot be empty.", status_code=400, error_code="EMPTY_TEXT")

        target_lang = self.resolve_language_code(language)
        selected_voice = voice or DEFAULT_VOICE_PER_LANG.get(target_lang, "Nalini")

        headers = {
            "X-API-Key-ID": self.api_key.strip(),
            "Content-Type": "application/json"
        }

        # Timbre v2.5 configuration
        payload = {
            "text": clean_text,
            "voice": selected_voice,
            "model": "timbre-v2.5",
            "language": target_lang,
            "speed": max(0.85, min(1.15, float(speed))),
            "audio_config": {
                "sample_rate": 48000,
                "num_channels": 1,
                "sample_width": 2,
                "encoding": "linear_pcm",
                "container": "wav"
            }
        }

        try:
            response = requests.post(
                self.endpoint,
                headers=headers,
                json=payload,
                timeout=timeout
            )
        except requests.Timeout:
            logger.error("Timeout connecting to Gnani TTS endpoint (%s s)", timeout)
            raise VoiceServiceError("Gnani TTS service request timed out.", status_code=504, error_code="TTS_TIMEOUT")
        except requests.RequestException as exc:
            logger.error("Network error communicating with Gnani TTS: %s", str(exc))
            raise VoiceServiceError("Unable to reach Gnani TTS service.", status_code=502, error_code="TTS_NETWORK_ERROR")

        if response.status_code == 401:
            logger.error("Gnani TTS returned 401 Unauthorized.")
            raise VoiceServiceError("Invalid or unauthorized Gnani API key.", status_code=401, error_code="INVALID_API_KEY")

        if response.status_code == 429:
            logger.warning("Gnani TTS rate limited: 429.")
            raise VoiceServiceError("Gnani API rate limit reached. Please wait a moment and try again.", status_code=429, error_code="RATE_LIMITED")

        if not response.ok:
            error_msg = f"Gnani TTS API failed with status {response.status_code}"
            try:
                err_data = response.json()
                if "error" in err_data and isinstance(err_data["error"], dict):
                    error_msg = err_data["error"].get("message", error_msg)
                elif "message" in err_data:
                    error_msg = err_data["message"]
                elif "detail" in err_data:
                    error_msg = str(err_data["detail"])
            except Exception:
                pass
            logger.error("Gnani TTS returned error HTTP %s: %s", response.status_code, error_msg)
            raise VoiceServiceError(error_msg, status_code=response.status_code, error_code="TTS_API_ERROR")

        content_type = response.headers.get("Content-Type", "audio/wav")
        audio_bytes = response.content

        if not audio_bytes or len(audio_bytes) < 44:
            raise VoiceServiceError("Received invalid or truncated audio from Gnani TTS.", status_code=502, error_code="EMPTY_AUDIO_RESPONSE")

        return audio_bytes, content_type


voice_service = VoiceService()
