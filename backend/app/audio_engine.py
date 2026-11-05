"""
Renders actual audio from RemixBot's Gemini-generated plan, using the Eleven Music API
(https://elevenlabs.io/docs/api-reference/music/compose) — a model purpose-built for
text-to-music generation, trained on licensed data and cleared for commercial use.

This keeps Gemini and the audio model cleanly separated:
- Gemini (gemini_client.py) writes the *plan* — concept, arrangement, production notes,
  and a tuned natural-language prompt for a music model.
- This module takes that prompt (plus a few structured fields) and renders the *audio*.

Eleven Music enforces its own copyright screening independently of RemixBot's system prompt
(see `RemixAudioBlocked` below) — if a prompt is judged too close to an existing copyrighted
work, the API refuses and returns a suggested rewrite instead of generating anything.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

from elevenlabs.client import ElevenLabs
from elevenlabs.core.api_error import ApiError

DEFAULT_MODEL_ID = os.getenv("ELEVENLABS_MUSIC_MODEL", "music_v2")

# Eleven Music accepts 3_000–600_000 ms. We default low and cap the top end so a stray
# request can't rack up a huge bill; raise MAX_DURATION_MS deliberately if you need longer.
MIN_DURATION_MS = 3_000
DEFAULT_DURATION_MS = 30_000
MAX_DURATION_MS = 120_000


class RemixAudioBlocked(Exception):
    """Raised when the music model itself refuses a prompt (e.g. too close to a real song)."""

    def __init__(self, message: str, suggestion: Optional[str] = None):
        super().__init__(message)
        self.suggestion = suggestion


@dataclass
class RenderedTrack:
    audio_bytes: bytes
    content_type: str = "audio/mpeg"


class AudioEngine:
    def __init__(self, api_key: Optional[str] = None, model_id: str = DEFAULT_MODEL_ID):
        api_key = api_key or os.getenv("ELEVENLABS_API_KEY")
        if not api_key:
            raise RuntimeError(
                "ELEVENLABS_API_KEY is not set. Add it to your environment or backend/.env"
            )
        self.client = ElevenLabs(api_key=api_key)
        self.model_id = model_id

    def render(
        self,
        prompt: str,
        duration_ms: int = DEFAULT_DURATION_MS,
        force_instrumental: bool = False,
    ) -> RenderedTrack:
        duration_ms = max(MIN_DURATION_MS, min(duration_ms, MAX_DURATION_MS))

        try:
            chunks = self.client.music.compose(
                prompt=prompt,
                music_length_ms=duration_ms,
                model_id=self.model_id,
                force_instrumental=force_instrumental,
            )
            audio_bytes = b"".join(chunks)
        except ApiError as exc:
            detail = _extract_detail(exc)
            if detail and detail.get("status") in ("bad_prompt", "bad_composition_plan"):
                suggestion = (detail.get("data") or {}).get(
                    "prompt_suggestion"
                ) or (detail.get("data") or {}).get("composition_plan_suggestion")
                raise RemixAudioBlocked(
                    "The music model flagged this prompt as too close to existing copyrighted "
                    "material and declined to render it.",
                    suggestion=suggestion if isinstance(suggestion, str) else None,
                ) from exc
            raise

        return RenderedTrack(audio_bytes=audio_bytes)


def _extract_detail(exc: ApiError) -> Optional[dict]:
    """Best-effort extraction of the {"status": ..., "data": {...}} error body Eleven Music sends."""
    body = getattr(exc, "body", None)
    if isinstance(body, dict):
        return body.get("detail") if isinstance(body.get("detail"), dict) else body
    return None
