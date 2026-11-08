"""Gnani Prisma STT (Speech-to-Text) Service Module.

Endpoint: POST https://api.vachana.ai/stt/v3
Authentication Header: X-API-Key-ID: API_KEY
Model: prisma-v2.5 (default for single-language, robust conversational speech)

Supported container formats: WAV, MP3, OGG, FLAC, AAC, M4A
Primary languages: mr-IN (Marathi), hi-IN (Hindi), en-IN (English)
"""

import io
import logging
from typing import Any, Dict, Optional, Tuple
import requests
from backend.config import get_settings

logger = logging.getLogger("warkari.services.speech")

PRISMA_STT_ENDPOINT = "https://api.vachana.ai/stt/v3"

# Recognized locale mappings
LANGUAGE_CODE_MAP = {
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

SUPPORTED_MIME_TYPES = {
    "audio/wav": "wav",
    "audio/x-wav": "wav",
    "audio/wave": "wav",
    "audio/mp3": "mp3",
    "audio/mpeg": "mp3",
    "audio/ogg": "ogg",
    "audio/flac": "flac",
    "audio/x-flac": "flac",
    "audio/aac": "aac",
    "audio/m4a": "m4a",
    "audio/x-m4a": "m4a",
    "audio/webm": "webm",
}

MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB limit for short-form audio clip


class SpeechServiceError(Exception):
    """Custom exception raised for STT processing errors."""
    def __init__(self, message: str, status_code: int = 502, error_code: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code


class SpeechService:
    def __init__(self, api_key: Optional[str] = None):
        self.endpoint = PRISMA_STT_ENDPOINT
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
        """Normalizes and validates target language code."""
        normalized = (lang_input or "mr-IN").strip().lower()
        if normalized in LANGUAGE_CODE_MAP:
            return LANGUAGE_CODE_MAP[normalized]
        # Check standard casing
        if lang_input in ["mr-IN", "hi-IN", "en-IN"]:
            return lang_input
        raise ValueError(
            f"Unsupported language code '{lang_input}'. Supported languages: Marathi (mr-IN), Hindi (hi-IN), English (en-IN)."
        )

    def validate_audio(
        self,
        audio_bytes: bytes,
        content_type: Optional[str] = None,
        filename: Optional[str] = None
    ) -> Tuple[str, str]:
        """Validates payload size and resolves filename and MIME type."""
        if not audio_bytes or len(audio_bytes) == 0:
            raise SpeechServiceError("Audio payload is empty.", status_code=400, error_code="EMPTY_AUDIO")

        if len(audio_bytes) > MAX_FILE_SIZE_BYTES:
            raise SpeechServiceError(
                f"Audio file exceeds {MAX_FILE_SIZE_BYTES // (1024 * 1024)}MB size limit.",
                status_code=400,
                error_code="AUDIO_TOO_LARGE"
            )

        # Detect audio format
        detected_mime = (content_type or "").split(";")[0].strip().lower()
        ext = None

        if detected_mime in SUPPORTED_MIME_TYPES:
            ext = SUPPORTED_MIME_TYPES[detected_mime]
        elif filename and "." in filename:
            file_ext = filename.rsplit(".", 1)[-1].lower()
            ext_map = {"wav": "audio/wav", "mp3": "audio/mpeg", "ogg": "audio/ogg", "flac": "audio/flac", "aac": "audio/aac", "m4a": "audio/m4a", "webm": "audio/webm"}
            if file_ext in ext_map:
                ext = file_ext
                detected_mime = ext_map[file_ext]

        # Check RIFF header for WAV if undetermined
        if not ext and len(audio_bytes) >= 12:
            if audio_bytes[:4] == b"RIFF" and audio_bytes[8:12] == b"WAVE":
                detected_mime = "audio/wav"
                ext = "wav"

        if not ext:
            raise SpeechServiceError(
                f"Unsupported audio type '{content_type or 'unknown'}'. Please provide WAV, MP3, OGG, FLAC, AAC, or M4A.",
                status_code=400,
                error_code="UNSUPPORTED_AUDIO_FORMAT"
            )

        safe_filename = filename or f"recording.{ext}"
        return safe_filename, detected_mime

    def transcribe_audio(
        self,
        audio_bytes: bytes,
        language: str = "mr-IN",
        content_type: Optional[str] = "audio/wav",
        filename: Optional[str] = "recording.wav",
        timeout: int = 12
    ) -> Dict[str, Any]:
        """Sends audio to Gnani Prisma v2.5 STT endpoint with a bounded timeout.

        Args:
            audio_bytes: Raw binary bytes of the recorded speech.
            language: Target language code ('mr-IN', 'hi-IN', 'en-IN').
            content_type: MIME type of the uploaded audio.
            filename: Original or synthesized filename.
            timeout: Network timeout in seconds (default: 12s).

        Returns:
            Dict containing success status, recognized transcript, and metadata.
        """
        if not self.is_configured:
            raise SpeechServiceError(
                "SpeechService is unconfigured. GNANI_API_KEY is missing from environment.",
                status_code=503,
                error_code="MISSING_API_KEY"
            )

        target_lang = self.resolve_language_code(language)
        resolved_filename, resolved_mime = self.validate_audio(audio_bytes, content_type, filename)

        headers = {
            "X-API-Key-ID": self.api_key.strip()
        }

        form_data = {
            "language_code": target_lang,
            "model": "prisma-v2.5",
            "format": "transcribe"
        }

        files = {
            "audio_file": (resolved_filename, io.BytesIO(audio_bytes), resolved_mime)
        }

        try:
            response = requests.post(
                self.endpoint,
                headers=headers,
                data=form_data,
                files=files,
                timeout=timeout
            )
        except requests.Timeout:
            logger.error("Timeout connecting to Gnani STT endpoint (%s s)", timeout)
            raise SpeechServiceError("Gnani STT service request timed out.", status_code=504, error_code="STT_TIMEOUT")
        except requests.RequestException as exc:
            logger.error("Network error communicating with Gnani STT: %s", str(exc))
            raise SpeechServiceError("Unable to reach Gnani STT service.", status_code=502, error_code="STT_NETWORK_ERROR")

        if response.status_code == 401:
            logger.error("Gnani STT returned 401 Unauthorized.")
            raise SpeechServiceError("Invalid or unauthorized Gnani API key.", status_code=401, error_code="INVALID_API_KEY")

        if response.status_code == 429:
            logger.warning("Gnani STT rate limited: 429.")
            raise SpeechServiceError("Gnani API rate limit reached. Please wait a moment and try again.", status_code=429, error_code="RATE_LIMITED")

        if not response.ok:
            error_msg = f"Gnani STT API failed with status {response.status_code}"
            try:
                err_data = response.json()
                if "error" in err_data and isinstance(err_data["error"], dict):
                    error_msg = err_data["error"].get("message", error_msg)
                elif "detail" in err_data:
                    error_msg = str(err_data["detail"])
            except Exception:
                pass
            logger.error("Gnani STT returned error HTTP %s: %s", response.status_code, error_msg)
            raise SpeechServiceError(error_msg, status_code=response.status_code, error_code="STT_API_ERROR")

        try:
            res_json = response.json()
        except Exception:
            raise SpeechServiceError("Invalid JSON received from Gnani STT service.", status_code=502, error_code="INVALID_RESPONSE")

        # Official format: {"success": true, "transcript": "...", ...}
        transcript = res_json.get("transcript", "")
        detected_lang = res_json.get("detected_language_code") or target_lang

        return {
            "success": True,
            "transcript": transcript,
            "language": target_lang,
            "detected_language": detected_lang,
            "model": res_json.get("model", "prisma-v2.5"),
            "request_id": res_json.get("request_id")
        }


speech_service = SpeechService()
