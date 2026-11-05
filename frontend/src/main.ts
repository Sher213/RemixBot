import "./style.css";
import { requestRemix, requestRemixWithAudio } from "./api";
import type { RemixPlan } from "./types";

const app = document.getElementById("app")!;

app.innerHTML = `
  <header class="topbar">
    <div class="brand">
      <div class="brand-mark">Remix<span>Bot</span></div>
      <div class="brand-tag">AI Remix Console</div>
    </div>
    <div class="meter" id="meter">
      ${Array.from({ length: 14 }, () => `<div class="bar"></div>`).join("")}
    </div>
  </header>

  <main class="console">
    <section class="channel-strip">
      <h2>Input Channel</h2>

      <label class="field-label" for="prompt">Describe the remix</label>
      <textarea id="prompt" rows="5" placeholder="e.g. Turn this into a driving synthwave track with a rising key change in the final chorus"></textarea>

      <label class="field-label">Source audio (optional — must be yours to use)</label>
      <label class="audio-drop" id="drop">
        <span id="drop-text">Click to attach audio you own or have permission to remix</span>
        <input type="file" id="file" accept="audio/*" />
      </label>
      <div class="own-audio-note">
        RemixBot only transforms audio you provide here. Referencing another artist by name in the
        prompt above will be treated as style inspiration only — not reproduced.
      </div>

      <label class="field-label" for="context">Notes about the audio (optional)</label>
      <input type="text" id="context" placeholder="e.g. acoustic guitar + scratch vocal, 90 BPM" />

      <button class="submit-btn" id="submit">Generate Remix Plan</button>
      <div id="error-slot"></div>
    </section>

    <section class="session" id="session">
      <div class="empty-state">
        <h3>No session loaded</h3>
        <p>Describe what you want above and hit "Generate Remix Plan" to fill this view.</p>
      </div>
    </section>
  </main>
`;

const promptEl = document.getElementById("prompt") as HTMLTextAreaElement;
const fileEl = document.getElementById("file") as HTMLInputElement;
const dropEl = document.getElementById("drop") as HTMLLabelElement;
const dropTextEl = document.getElementById("drop-text") as HTMLSpanElement;
const contextEl = document.getElementById("context") as HTMLInputElement;
const submitBtn = document.getElementById("submit") as HTMLButtonElement;
const sessionEl = document.getElementById("session") as HTMLElement;
const errorSlot = document.getElementById("error-slot") as HTMLDivElement;
const meterEl = document.getElementById("meter") as HTMLDivElement;

fileEl.addEventListener("change", () => {
  const file = fileEl.files?.[0];
  dropEl.classList.toggle("has-file", !!file);
  dropTextEl.textContent = file ? `Attached: ${file.name}` : "Click to attach audio you own or have permission to remix";
});

submitBtn.addEventListener("click", async () => {
  const prompt = promptEl.value.trim();
  errorSlot.innerHTML = "";

  if (!prompt) {
    errorSlot.innerHTML = `<div class="error-banner">Describe what you want RemixBot to create first.</div>`;
    return;
  }

  setLoading(true);
  try {
    const file = fileEl.files?.[0];
    const plan = file
      ? await requestRemixWithAudio(prompt, contextEl.value.trim(), file)
      : await requestRemix(prompt, contextEl.value.trim());
    renderPlan(plan);
  } catch (err) {
    errorSlot.innerHTML = `<div class="error-banner">${escapeHtml(
      err instanceof Error ? err.message : "Something went wrong talking to RemixBot."
    )}</div>`;
  } finally {
    setLoading(false);
  }
});

function setLoading(loading: boolean) {
  submitBtn.disabled = loading;
  submitBtn.textContent = loading ? "Mixing…" : "Generate Remix Plan";
  meterEl.classList.toggle("live", loading);
}

function renderPlan(plan: RemixPlan) {
  sessionEl.innerHTML = `
    <div class="headline">
      <p class="concept">${escapeHtml(plan.remix_concept)}</p>
      <div class="readouts">
        <div class="readout"><span class="label">Genre</span>${escapeHtml(plan.genre)}</div>
        <div class="readout"><span class="label">BPM</span>${plan.bpm}</div>
        <div class="readout"><span class="label">Key</span>${escapeHtml(plan.key)}</div>
        <div class="readout"><span class="label">Energy</span>${escapeHtml(plan.energy_level)}</div>
      </div>
    </div>

    ${module("01", "Arrangement", arrangementHtml(plan))}
    ${module("02", "Production Notes", listHtml(plan.production_notes))}
    ${module("03", "Instrumentation", listHtml(plan.instrumentation))}
    ${module("04", "Effects Chain", listHtml(plan.effects_chain))}
    ${module("05", "Mixing Recommendations", listHtml(plan.mixing_recommendations))}
    ${module("06", "Mastering Recommendations", listHtml(plan.mastering_recommendations))}
    ${plan.lyric_ideas?.length ? module("07", "Lyric Ideas", listHtml(plan.lyric_ideas)) : ""}
    ${module(
      plan.lyric_ideas?.length ? "08" : "07",
      "AI Music Generation Prompt",
      promptBoxHtml(plan.ai_music_generation_prompt)
    )}

    <div class="module">
      <div class="copyright-note">${escapeHtml(plan.copyright_note)}</div>
    </div>
  `;

  const copyBtn = sessionEl.querySelector<HTMLButtonElement>(".copy-btn");
  copyBtn?.addEventListener("click", () => {
    navigator.clipboard.writeText(plan.ai_music_generation_prompt);
    copyBtn.textContent = "Copied";
    setTimeout(() => (copyBtn.textContent = "Copy"), 1200);
  });
}

function module(tag: string, title: string, bodyHtml: string): string {
  return `
    <div class="module">
      <div class="module-header">
        <span class="led"></span>
        <span class="tag">${tag}</span>
        <h3>${escapeHtml(title)}</h3>
      </div>
      ${bodyHtml}
    </div>
  `;
}

function listHtml(items: string[]): string {
  if (!items?.length) return `<p>—</p>`;
  return `<ul>${items.map((i) => `<li>${escapeHtml(i)}</li>`).join("")}</ul>`;
}

function arrangementHtml(plan: RemixPlan): string {
  return plan.arrangement
    .map(
      (row) => `
      <div class="arrangement-row">
        <div class="section-name">${escapeHtml(row.section)}</div>
        <div>${escapeHtml(row.description)}</div>
      </div>`
    )
    .join("");
}

function promptBoxHtml(text: string): string {
  return `
    <div class="prompt-box">
      <button class="copy-btn">Copy</button>
      ${escapeHtml(text)}
    </div>
  `;
}

function escapeHtml(value: string): string {
  const div = document.createElement("div");
  div.textContent = value;
  return div.innerHTML;
}
