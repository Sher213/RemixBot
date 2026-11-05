from __future__ import annotations

import logging
import os
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .gemini_client import RemixBotClient

load_dotenv()

# ----------------------------------------------------
# Logging
# ----------------------------------------------------
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger("remixbot.api")

app = FastAPI(title="RemixBot API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)

_client: Optional[RemixBotClient] = None


def get_client() -> RemixBotClient:
    global _client

    if _client is None:
        logger.info("Initializing RemixBotClient...")
        _client = RemixBotClient()

    return _client


class RemixRequest(BaseModel):
    prompt: str
    has_own_audio: bool = False
    audio_context: Optional[str] = None


@app.get("/api/health")
def health():
    logger.info("Health check requested.")
    return {"status": "ok"}


@app.post("/api/remix")
def remix_text_only(req: RemixRequest):
    """Generate a remix plan from a text prompt alone (no audio upload)."""

    logger.info("Received text remix request.")

    if not req.prompt.strip():
        logger.warning("Empty prompt received.")
        raise HTTPException(status_code=400, detail="prompt must not be empty")

    logger.info(
        "Prompt length=%d | has_audio=%s",
        len(req.prompt),
        req.has_own_audio,
    )

    try:
        result = get_client().generate_remix(
            prompt=req.prompt,
            has_own_audio=req.has_own_audio,
            audio_context=req.audio_context,
        )

        logger.info("Successfully generated remix.")
        return result

    except Exception:
        logger.exception("Failed generating remix.")
        raise HTTPException(status_code=502, detail="Failed to generate remix")


@app.post("/api/remix-with-audio")
async def remix_with_audio(
    prompt: str = Form(...),
    audio_context: Optional[str] = Form(None),
    file: UploadFile = File(...),
):
    """Generate a remix plan grounded in user-provided audio."""

    logger.info(
        "Received audio remix request. filename=%s mime=%s",
        file.filename,
        file.content_type,
    )

    if not prompt.strip():
        logger.warning("Empty prompt received.")
        raise HTTPException(status_code=400, detail="prompt must not be empty")

    audio_bytes = await file.read()

    logger.info(
        "Uploaded file size: %.2f MB",
        len(audio_bytes) / (1024 * 1024),
    )

    max_bytes = 20 * 1024 * 1024

    if len(audio_bytes) > max_bytes:
        logger.warning(
            "Upload exceeded size limit (%.2f MB).",
            len(audio_bytes) / (1024 * 1024),
        )
        raise HTTPException(
            status_code=413,
            detail="Audio file too large (20MB limit)",
        )

    try:
        result = get_client().generate_remix(
            prompt=prompt,
            has_own_audio=True,
            audio_context=audio_context,
            audio_bytes=audio_bytes,
            audio_mime_type=file.content_type or "audio/mpeg",
        )

        logger.info("Successfully generated audio remix.")
        return result

    except Exception:
        logger.exception("Failed generating audio remix.")
        raise HTTPException(status_code=502, detail="Failed to generate remix")