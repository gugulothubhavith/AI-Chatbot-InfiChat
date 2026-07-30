import { create } from "zustand";
import { api } from "@/lib/api";

/**
 * Global text-to-speech playback controller.
 *
 * Exactly one utterance plays at a time across the whole app, so this lives in
 * a single store rather than per-component state — every "Read aloud" button
 * reads `activeId` to decide whether to show Play or Stop, and calling `speak`
 * on a new message implicitly stops the previous one.
 *
 * Two engines, in order of preference:
 *   1. Backend `/voice/tts` (Edge-TTS) → streamed MP3 into an HTMLAudioElement.
 *      Higher quality and consistent across browsers. Fully abortable.
 *   2. Browser `speechSynthesis` fallback when the backend is unavailable or
 *      the fetch fails. Also fully stoppable via `cancel()`.
 *
 * Both engines are torn down on `stop()`, on navigation away (see the
 * `beforeunload` guard in the hook), and before starting a new utterance, so
 * audio never leaks past the user pressing Stop.
 */

type Engine = "backend" | "browser" | null;

type TtsState = {
  /** id of the message currently playing, or null when idle */
  activeId: string | null;
  /** true between the click and the first audio frame (backend fetch latency) */
  loading: boolean;

  // Internal handles — not for component use.
  _audio: HTMLAudioElement | null;
  _objectUrl: string | null;
  _abort: AbortController | null;
  _engine: Engine;

  speak: (id: string, text: string, voiceId: string) => Promise<void>;
  stop: () => void;
};

// Map the app's voice-profile keys to backend voice ids. Kept permissive: an
// unknown profile falls through to the professional English default rather
// than failing synthesis.
const VOICE_MAP: Record<string, string> = {
  "pro-en-male": "en_professional_male",
  "corp-hi-female": "hi_corporate_female",
  "empathetic-te-male": "te_empathetic_male",
  "alert-hi-fast": "hi_alert_fast",
};

export function resolveVoiceId(profile: string | undefined): string {
  if (!profile) return "en_professional_male";
  return VOICE_MAP[profile] ?? "en_professional_male";
}

export const useTtsStore = create<TtsState>((set, get) => ({
  activeId: null,
  loading: false,
  _audio: null,
  _objectUrl: null,
  _abort: null,
  _engine: null,

  stop: () => {
    const { _audio, _objectUrl, _abort, _engine } = get();
    // Abort any in-flight backend fetch first so its .then() can't resurrect
    // playback after we've reset state.
    if (_abort) {
      try {
        _abort.abort();
      } catch {
        /* already settled */
      }
    }
    if (_audio) {
      _audio.pause();
      _audio.src = "";
      _audio.load();
    }
    if (_objectUrl) {
      URL.revokeObjectURL(_objectUrl);
    }
    if (_engine === "browser" && typeof window !== "undefined" && "speechSynthesis" in window) {
      window.speechSynthesis.cancel();
    }
    set({
      activeId: null,
      loading: false,
      _audio: null,
      _objectUrl: null,
      _abort: null,
      _engine: null,
    });
  },

  speak: async (id, text, voiceId) => {
    // Toggle semantics: clicking the currently-playing message stops it.
    if (get().activeId === id) {
      get().stop();
      return;
    }
    // Always tear down any prior playback before starting a new one.
    get().stop();

    const trimmed = text.trim();
    if (!trimmed) return;

    const controller = new AbortController();
    set({ activeId: id, loading: true, _abort: controller, _engine: "backend" });

    try {
      const res = await api.voice.tts(trimmed, voiceId, controller.signal);
      // If the user hit stop (or started another message) while the request
      // was in flight, this request is no longer the active one — bail without
      // touching state.
      if (get()._abort !== controller) return;

      if (!res.ok) throw new Error(`tts ${res.status}`);

      const blob = await res.blob();
      if (get()._abort !== controller) return;

      const objectUrl = URL.createObjectURL(blob);
      const audio = new Audio(objectUrl);

      const cleanup = () => {
        // Only clear if we're still the active utterance — a newer speak()
        // may have already taken over.
        if (get()._audio === audio) {
          URL.revokeObjectURL(objectUrl);
          set({
            activeId: null,
            loading: false,
            _audio: null,
            _objectUrl: null,
            _abort: null,
            _engine: null,
          });
        }
      };
      audio.onended = cleanup;
      audio.onerror = cleanup;

      set({ _audio: audio, _objectUrl: objectUrl, loading: false });
      await audio.play();
    } catch (err) {
      // Aborts are expected (user pressed stop) — swallow them silently.
      if (controller.signal.aborted) return;
      // Backend unavailable → fall back to the browser engine.
      speakWithBrowser(id, trimmed, set, get);
    }
  },
}));

// Browser SpeechSynthesis fallback. Kept out of the store body to keep `speak`
// readable; it mutates the same store via the passed set/get.
function speakWithBrowser(
  id: string,
  text: string,
  set: (partial: Partial<TtsState>) => void,
  get: () => TtsState,
) {
  if (typeof window === "undefined" || !("speechSynthesis" in window)) {
    set({ activeId: null, loading: false, _abort: null, _engine: null });
    return;
  }
  // Guard against a stop() that fired between the fetch failure and here.
  if (get().activeId !== id) return;

  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  const cleanup = () => {
    if (get().activeId === id) {
      set({ activeId: null, loading: false, _abort: null, _engine: null });
    }
  };
  utterance.onend = cleanup;
  utterance.onerror = cleanup;
  set({ activeId: id, loading: false, _engine: "browser", _abort: null });
  window.speechSynthesis.speak(utterance);
}
