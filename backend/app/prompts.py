"""
RemixBot's persona, instructions, and structured-output schema.

Keeping this in one module makes it easy to tune RemixBot's behavior
(tone, capabilities, copyright rules) without touching the API glue code.
"""

SYSTEM_PROMPT = """You are RemixBot, an expert AI music producer, songwriter, DJ, audio engineer, and sound designer.
Your mission is to turn user ideas into professional-quality musical remix PLANS: detailed, actionable
production concepts that a musician, producer, or AI music-generation tool could use to actually make the track.

You can help with:
- Completely original songs and instrumentals
- Remixing audio the user provides or owns
- Rearranging stems, extending songs, building intros/outros/transitions/drops
- Rewriting lyrics, generating hooks and harmonies
- Changing genres, mashing up user-owned content
- Cinematic scores and nearly any genre: EDM, hip-hop, orchestral, jazz, rock, metal, pop,
  lo-fi, trap, phonk, ambient, techno, house, synthwave, and more.

COPYRIGHT RULES (never break these):
- If the user references an existing song for INSPIRATION ("make something with the energy of..."),
  extract only high-level musical qualities: tempo, instrumentation, mood, era, and production style.
  Never reproduce or closely imitate the protected melody, lyrics, or recording of that song.
- If the user says they uploaded, wrote, or own the source material, treat that content as the only
  thing being remixed or transformed — do not blend in outside copyrighted material.
- Never generate lyrics that are, or closely imitate, an existing copyrighted song's lyrics.
- Never claim a remix "is" a specific commercial recording. Frame everything as an original
  transformation or an original composition in a given style.
- If a request cannot be fulfilled without imitating a specific copyrighted work, say so plainly,
  and instead offer a style/era/mood-based alternative that stays original.

For every request, determine (making reasonable creative assumptions when the user hasn't specified):
- genre, BPM, key, instrumentation, energy level, structure, vocal style, production style, target audience

When designing a remix, think like a Grammy-winning producer and consider: rhythm, groove, swing,
harmony, transitions, effects, vocal chops, bass design, layering, automation, mastering, and dynamics.

Always explain your creative reasoning briefly. Be creative, modern, and experimental, but keep
production choices coherent and commercially viable. Respond ONLY with the structured JSON described
by the response schema — no prose outside of it, no markdown fences.
"""

# Gemini structured-output schema (passed as response_schema in generation_config).
# This forces the model to return RemixBot's standard 9-part output as clean JSON
# the frontend can render as distinct "channel modules".
REMIX_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "remix_concept": {
            "type": "string",
            "description": "A short, vivid pitch for the overall creative direction.",
        },
        "genre": {"type": "string"},
        "bpm": {"type": "integer"},
        "key": {"type": "string"},
        "energy_level": {
            "type": "string",
            "enum": ["low", "medium", "high", "peak-time"],
        },
        "arrangement": {
            "type": "array",
            "description": "Ordered song sections, e.g. Intro, Verse, Build, Drop, Outro.",
            "items": {
                "type": "object",
                "properties": {
                    "section": {"type": "string"},
                    "description": {"type": "string"},
                },
                "required": ["section", "description"],
            },
        },
        "production_notes": {
            "type": "array",
            "items": {"type": "string"},
        },
        "instrumentation": {
            "type": "array",
            "items": {"type": "string"},
        },
        "effects_chain": {
            "type": "array",
            "items": {"type": "string"},
        },
        "mixing_recommendations": {
            "type": "array",
            "items": {"type": "string"},
        },
        "mastering_recommendations": {
            "type": "array",
            "items": {"type": "string"},
        },
        "lyric_ideas": {
            "type": "array",
            "description": "Optional short original lyric snippets or thematic ideas. Never copy existing lyrics.",
            "items": {"type": "string"},
        },
        "ai_music_generation_prompt": {
            "type": "string",
            "description": "A single, ready-to-use prompt for an AI music generation tool (e.g. Suno, Udio, Stable Audio).",
        },
        "copyright_note": {
            "type": "string",
            "description": "One sentence clarifying what was used as inspiration vs. user-owned/provided material.",
        },
    },
    "required": [
        "remix_concept",
        "genre",
        "bpm",
        "key",
        "energy_level",
        "arrangement",
        "production_notes",
        "instrumentation",
        "effects_chain",
        "mixing_recommendations",
        "mastering_recommendations",
        "ai_music_generation_prompt",
        "copyright_note",
    ],
}


def build_user_message(prompt: str, has_own_audio: bool, audio_context: str | None) -> str:
    """Wrap the raw user prompt with context about any uploaded audio."""
    parts = [f"User request: {prompt}"]
    if has_own_audio:
        parts.append(
            "The user has uploaded audio that they own or have permission to use. "
            "Treat it as the source material to remix/transform. "
            + (f"Context about the audio: {audio_context}" if audio_context else "")
        )
    else:
        parts.append(
            "No user-owned audio was provided. If the user referenced an existing artist/song, "
            "use it only as high-level style inspiration (tempo/mood/instrumentation) — do not "
            "imitate the specific melody, lyrics, or recording."
        )
    return "\n\n".join(parts)
