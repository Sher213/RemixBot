export interface ArrangementSection {
  section: string;
  description: string;
}

export interface RemixPlan {
  remix_concept: string;
  genre: string;
  bpm: number;
  key: string;
  energy_level: "low" | "medium" | "high" | "peak-time";
  arrangement: ArrangementSection[];
  production_notes: string[];
  instrumentation: string[];
  effects_chain: string[];
  mixing_recommendations: string[];
  mastering_recommendations: string[];
  lyric_ideas?: string[];
  ai_music_generation_prompt: string;
  copyright_note: string;
}
