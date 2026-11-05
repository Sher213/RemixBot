import type { RemixPlan } from "./types";

export async function requestRemix(prompt: string, ownAudioNote: string): Promise<RemixPlan> {
  const res = await fetch("/api/remix", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      prompt,
      has_own_audio: false,
      audio_context: ownAudioNote || null,
    }),
  });
  if (!res.ok) {
    const detail = await safeDetail(res);
    throw new Error(detail);
  }
  return res.json();
}

export async function requestRemixWithAudio(
  prompt: string,
  audioContext: string,
  file: File
): Promise<RemixPlan> {
  const form = new FormData();
  form.append("prompt", prompt);
  form.append("audio_context", audioContext);
  form.append("file", file);

  const res = await fetch("/api/remix-with-audio", {
    method: "POST",
    body: form,
  });
  if (!res.ok) {
    const detail = await safeDetail(res);
    throw new Error(detail);
  }
  return res.json();
}

async function safeDetail(res: Response): Promise<string> {
  try {
    const body = await res.json();
    return body.detail ?? `Request failed (${res.status})`;
  } catch {
    return `Request failed (${res.status})`;
  }
}
