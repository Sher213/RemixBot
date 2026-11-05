"""
Thin wrapper around the Gemini API for RemixBot.

Uses Google's official `google-genai` SDK. Docs: https://ai.google.dev/gemini-api/docs
If you're on the older `google-generativeai` package, see the migration note in README.md.
"""
from __future__ import annotations

import json
import os
from typing import Optional

from google import genai
from google.genai import types

from .prompts import SYSTEM_PROMPT, REMIX_RESPONSE_SCHEMA, build_user_message

from dotenv import load_dotenv

load_dotenv()

# Check https://ai.google.dev/gemini-api/docs/models for the current model lineup
# and update this default if newer models are available.
DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")


class RemixBotClient:
    def __init__(self, api_key: Optional[str] = None, model: str = DEFAULT_MODEL):
        api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "GEMINI_API_KEY is not set. Add it to your environment or backend/.env"
            )
        self.client = genai.Client(api_key=api_key)
        self.model = model

    def generate_remix(
        self,
        prompt: str,
        has_own_audio: bool = False,
        audio_context: Optional[str] = None,
        audio_bytes: Optional[bytes] = None,
        audio_mime_type: Optional[str] = None,
    ) -> dict:
        """Call Gemini with RemixBot's system prompt and return a parsed remix plan."""
        user_message = build_user_message(prompt, has_own_audio, audio_context)

        contents: list = [user_message]

        # If the user uploaded audio they own, pass it in as multimodal context so
        # Gemini can describe/analyze it (tempo, key, mood) to ground the remix plan.
        # NOTE: Gemini itself does not output audio here — this powers the *plan*.
        # Actual audio rendering/stem manipulation should be done by an audio engine
        # (e.g. a DAW script, an audio-generation model, or ffmpeg/pydub pipeline)
        # using the `ai_music_generation_prompt` and production notes RemixBot returns.
        if audio_bytes and audio_mime_type:
            contents.append(
                types.Part.from_bytes(data=audio_bytes, mime_type=audio_mime_type)
            )

        response = self.client.models.generate_content(
            model=self.model,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                response_mime_type="application/json",
                response_schema=REMIX_RESPONSE_SCHEMA,
                temperature=0.9,
            ),
        )

        return json.loads(response.text)
