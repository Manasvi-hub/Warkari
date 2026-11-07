"""Warkari Voice Assistant Routes.

Handles:
- POST /api/assistant/transcribe : Speech-to-Text using Gnani Prisma v2.5
- POST /api/assistant/speak      : Text-to-Speech using Gnani Timbre v2.5
- POST /api/assistant/voice      : End-to-end voice pipeline (STT -> Test Response -> TTS)
"""

import base64
import logging
from typing import Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.schemas import SpeakRequest, TranscribeResponse, VoiceInteractionResponse
from backend.services.assistant_service import assistant_service
from backend.services.speech_service import SpeechServiceError, speech_service
from backend.services.voice_service import VoiceServiceError, voice_service

logger = logging.getLogger("warkari.routes.assistant")

router = APIRouter(prefix="/api/assistant", tags=["Assistant Voice Pipeline"])


def generate_initial_response(transcript: str, language: str) -> str:
    """Generates initial polite response in the speaker's language without RAG/Intent engine."""
    clean_text = (transcript or "").strip()
    if not clean_text:
        if language.startswith("mr"):
            return "माफ करा, मला तुमचा आवाज स्पष्ट ऐकू आला नाही. कृपया पुन्हा बोला."
        elif language.startswith("hi"):
            return "क्षमा करें, मुझे आपकी आवाज़ स्पष्ट सुनाई नहीं दी। कृपया पुनः बोलें।"
        else:
            return "Pardon me, I could not hear your voice clearly. Please speak again."

    if language.startswith("mr"):
        return f"जय हरी विठ्ठल! आपल्याला '{clean_text}' याबद्दल सहाय्य करत आहोत. वारकरी सेवेत आपले स्वागत आहे."
    elif language.startswith("hi"):
        return f"जय श्री विठ्ठल! हम '{clean_text}' के बारे में आपकी सहायता कर रहे हैं। वारकरी सेवा में आपका स्वागत है।"
    else:
        return f"Jai Hari Vitthal! We received your request: '{clean_text}'. Welcome to Warkari assistance."


@router.post(
    "/transcribe",
    response_model=TranscribeResponse,
    summary="Transcribe speech to text using Gnani Prisma v2.5",
    description="Accepts an uploaded audio recording (WAV, MP3, OGG, WebM) and returns the recognized transcription."
)
async def transcribe_audio_endpoint(
    audio: UploadFile = File(..., description="Recorded audio file"),
    language: str = Form("mr-IN", description="Language code: mr-IN, hi-IN, en-IN")
) -> TranscribeResponse:
    if not speech_service.is_configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Gnani STT service is unconfigured. Please set GNANI_API_KEY in backend/.env"
        )

    try:
        audio_bytes = await audio.read()
        result = speech_service.transcribe_audio(
            audio_bytes=audio_bytes,
            language=language,
            content_type=audio.content_type,
            filename=audio.filename
        )
        return TranscribeResponse(
            success=result["success"],
            transcript=result["transcript"],
            language=result["language"],
            detected_language=result.get("detected_language"),
            model=result.get("model", "prisma-v2.5"),
            request_id=result.get("request_id")
        )
    except ValueError as val_err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(val_err))
    except SpeechServiceError as s_err:
        raise HTTPException(status_code=s_err.status_code, detail=s_err.message)
    except Exception as exc:
        logger.exception("Unexpected error in /transcribe endpoint")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to process audio transcription.")


@router.post(
    "/speak",
    summary="Synthesize speech from text using Gnani Timbre v2.5",
    description="Generates spoken binary WAV audio stream from input text."
)
async def speak_text_endpoint(request: SpeakRequest):
    if not voice_service.is_configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Gnani TTS service is unconfigured. Please set GNANI_API_KEY in backend/.env"
        )

    try:
        audio_bytes, content_type = voice_service.synthesize_speech(
            text=request.text,
            language=request.language,
            voice=request.voice,
            speed=request.speed or 1.0
        )
        return Response(
            content=audio_bytes,
            media_type=content_type,
            headers={
                "Content-Disposition": 'inline; filename="response.wav"',
                "Content-Length": str(len(audio_bytes))
            }
        )
    except ValueError as val_err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(val_err))
    except VoiceServiceError as v_err:
        raise HTTPException(status_code=v_err.status_code, detail=v_err.message)
    except Exception as exc:
        logger.exception("Unexpected error in /speak endpoint")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to synthesize speech audio.")


@router.post(
    "/voice",
    response_model=VoiceInteractionResponse,
    summary="End-to-end voice pipeline (STT -> Contextual Response -> TTS)",
    description="Receives recorded speech, performs transcription via Prisma v2.5, routes through intelligence engine, synthesizes audio via Timbre v2.5, and returns structured data."
)
async def voice_interaction_endpoint(
    audio: UploadFile = File(..., description="Recorded audio file from user"),
    language: str = Form("mr-IN", description="Language code: mr-IN, hi-IN, en-IN"),
    user_lat: Optional[float] = Form(None, description="Optional GPS latitude"),
    user_lon: Optional[float] = Form(None, description="Optional GPS longitude"),
    db: Session = Depends(get_db)
) -> VoiceInteractionResponse:
    if not speech_service.is_configured or not voice_service.is_configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Gnani AI services are unconfigured. Please set GNANI_API_KEY in backend/.env"
        )

    try:
        audio_bytes = await audio.read()
        # 1. Transcribe through Prisma STT
        stt_result = speech_service.transcribe_audio(
            audio_bytes=audio_bytes,
            language=language,
            content_type=audio.content_type,
            filename=audio.filename
        )
        transcript = stt_result.get("transcript", "").strip()
        resolved_lang = stt_result.get("language", language)

        if not transcript:
            fallback_text = (
                "आवाज ऐकू आला नाही. कृपया पुन्हा बोला."
                if resolved_lang == "mr-IN"
                else "आवाज सुनाई नहीं दिया। कृपया दोबारा बोलें।"
                if resolved_lang == "hi-IN"
                else "Could not hear audio clearly. Please try speaking again."
            )
            return VoiceInteractionResponse(
                success=False,
                transcript="",
                language=resolved_lang,
                response_text=fallback_text,
                intent="UNKNOWN",
                confidence=0.0,
                facilities=[],
                incident=None
            )

        # 2. Process via Intelligence & Contextual Response Engine
        intel = assistant_service.process_chat(
            db=db,
            message=transcript,
            language=resolved_lang,
            user_lat=user_lat,
            user_lon=user_lon
        )
        display_text = intel.get("response_text", "")
        speech_text = intel.get("speech_text") or display_text

        # 3. Synthesize normalized speech_text through Timbre TTS
        tts_audio_bytes, tts_mime = voice_service.synthesize_speech(
            text=speech_text,
            language=resolved_lang
        )

        # Format audio for immediate playback in React
        b64_audio = base64.b64encode(tts_audio_bytes).decode("ascii")
        audio_data_url = f"data:{tts_mime};base64,{b64_audio}"

        incident_data = intel.get("incident")
        ticket_id = incident_data.get("id") if incident_data else None

        return VoiceInteractionResponse(
            success=True,
            transcript=transcript,
            language=resolved_lang,
            detected_language=stt_result.get("detected_language"),
            response_text=display_text,
            speech_text=speech_text,
            intent=intel.get("intent"),
            confidence=intel.get("confidence"),
            facilities=intel.get("facilities", []),
            incident=incident_data,
            ticket_id=ticket_id,
            audio_url=audio_data_url,
            audio_base64=audio_data_url
        )
    except ValueError as val_err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(val_err))
    except (SpeechServiceError, VoiceServiceError) as s_err:
        raise HTTPException(status_code=s_err.status_code, detail=s_err.message)
    except Exception as exc:
        logger.exception("Unexpected error in /voice pipeline")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Voice pipeline execution failed.")

