# RemixBot

An AI remix-planning console: describe a remix (and optionally attach audio you own or have
permission to use), and RemixBot — powered by the Gemini API — returns a full production plan:
concept, arrangement, instrumentation, effects chain, mixing/mastering notes, optional lyric ideas,
and a ready-to-use prompt for an AI music-generation tool.

**What it generates is a structured production plan, not raw audio.** That plan is meant to be fed
into a DAW, a human producer, or an audio-generation model (Suno, Udio, Stable Audio, etc.) via the
`ai_music_generation_prompt` field it returns.

## Copyright approach

- If you reference an existing artist/song only for *inspiration*, RemixBot is instructed to use
  high-level qualities (tempo, mood, instrumentation, era) — not to imitate the specific melody,
  lyrics, or recording.
- If you upload audio, RemixBot treats it as content you own or have permission to use, and builds
  the remix plan around that material specifically.
- RemixBot will decline to imitate a specific copyrighted work closely, and will say so rather than
  quietly complying.

This is enforced via the system prompt in `backend/app/prompts.py` — tune it there if you need
stricter or different rules for your deployment.

## Project layout

```
remixbot/
├── backend/            FastAPI + Gemini API
│   ├── app/
│   │   ├── main.py         API routes
│   │   ├── gemini_client.py Gemini API wrapper
│   │   └── prompts.py      System prompt + JSON schema
│   ├── requirements.txt
│   └── .env.example
└── frontend/           Vite + TypeScript console UI
    ├── index.html
    └── src/
        ├── main.ts     App logic / rendering
        ├── api.ts      Fetch calls to the backend
        ├── types.ts    Shared TS types
        └── style.css   Visual design
```

## Backend setup

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# edit .env and add your GEMINI_API_KEY (https://aistudio.google.com/apikey)
uvicorn app.main:app --reload --port 8000
```

## Frontend setup

```bash
cd frontend
npm install
npm run dev
```

Visit http://localhost:5173 — the dev server proxies `/api/*` to the backend on port 8000
(see `vite.config.ts`).

## API

- `POST /api/remix` — `{ prompt, has_own_audio, audio_context }` → JSON remix plan (text-only).
- `POST /api/remix-with-audio` — multipart form: `prompt`, `audio_context`, `file` → JSON remix plan,
  grounded in the uploaded audio.
- `GET /api/health` — liveness check.

Both remix endpoints return the same shape, defined in `frontend/src/types.ts` /
`backend/app/prompts.py`'s `REMIX_RESPONSE_SCHEMA`.

## Extending toward actual audio rendering

RemixBot's Gemini-backed endpoints produce a *plan*, not a rendered audio file. To go from plan to
finished audio you'd wire the `ai_music_generation_prompt` (and structured production notes) into
an audio-generation pipeline — for example:

- Send the prompt to a text-to-music API, or
- Use it as a detailed brief for stem manipulation with `pydub`/`librosa`/a DAW scripting API when
  the user has supplied their own stems.

That audio-rendering step is intentionally left out of this scaffold since it depends heavily on
which audio engine/model you plan to integrate — this repo gives you the conversational + planning
layer to build on top of.

## Model note

`GEMINI_MODEL` defaults to `gemini-2.5-flash` in `backend/.env.example`. Check
[ai.google.dev/gemini-api/docs/models](https://ai.google.dev/gemini-api/docs/models) for the current
model lineup and adjust if needed.
