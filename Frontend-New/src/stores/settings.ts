import { create } from "zustand";
import { persist } from "zustand/middleware";

export type Theme = "light" | "dark" | "system";
export type AccentKey = "vercel" | "stripe" | "linear" | "amber" | "rose";

export const ACCENTS: Record<AccentKey, { label: string; oklch: string; swatch: string }> = {
  vercel: { label: "Vercel Blue", oklch: "oklch(0.6 0.2 255)", swatch: "#0070F3" },
  stripe: { label: "Stripe Blurple", oklch: "oklch(0.58 0.22 285)", swatch: "#635BFF" },
  linear: { label: "Linear Green", oklch: "oklch(0.7 0.18 155)", swatch: "#5E6AD2" },
  amber: { label: "Amber", oklch: "oklch(0.75 0.17 70)", swatch: "#F5A524" },
  rose: { label: "Rose", oklch: "oklch(0.65 0.22 15)", swatch: "#F31260" },
};

export type AppLang = "auto" | "en" | "hi" | "ja";
export type SpokenLang = "auto" | "en" | "hi";
export type VoiceProfile = "pro-en-male" | "corp-hi-female" | "empathetic-te-male" | "alert-hi-fast";

export type NotifChannels = { push: boolean; email: boolean };
export type NotifKey = "responses" | "recommendations" | "usage";

type SettingsState = {
  // General
  theme: Theme;
  accent: AccentKey;
  appLang: AppLang;
  spokenLang: SpokenLang;
  voiceProfile: VoiceProfile;
  voiceFullscreen: boolean;

  // Notifications
  notifications: Record<NotifKey, NotifChannels>;

  // Personalization
  customInstructions: string;
  nickname: string;
  occupation: string;
  interests: string;
  personalizeResponses: boolean;
  conversationMemory: boolean;
  pythonInterpreter: boolean;
  voiceTTS: boolean;

  // Security
  piiScrubbing: boolean;

  // Web
  autoWebSearch: boolean;

  // Legacy chat prefs
  enterToSend: boolean;
  streaming: boolean;

  set: <K extends keyof SettingsState>(k: K, v: SettingsState[K]) => void;
  setNotif: (k: NotifKey, channel: keyof NotifChannels, v: boolean) => void;
  hydrate: () => Promise<void>;
};

export const useSettingsStore = create<SettingsState>()(
  persist(
    (set) => ({
      theme: "dark",
      accent: "vercel",
      appLang: "auto",
      spokenLang: "auto",
      voiceProfile: "pro-en-male",
      voiceFullscreen: false,

      notifications: {
        responses: { push: true, email: false },
        recommendations: { push: false, email: true },
        usage: { push: true, email: true },
      },

      customInstructions: "",
      nickname: "",
      occupation: "",
      interests: "",
      personalizeResponses: true,
      conversationMemory: true,
      pythonInterpreter: true,
      voiceTTS: false,

      piiScrubbing: true,

      autoWebSearch: true,

      enterToSend: true,
      streaming: true,

      set: (k, v) => {
        set({ [k]: v } as Partial<SettingsState>);
        // Fire and forget update to backend. Skipped when unauthenticated —
        // the theme switcher is reachable from /login, where this would only
        // produce 401 noise. localStorage still holds the preference.
        import("@/lib/api").then(({ api, hasAuthToken }) => {
          if (!hasAuthToken()) return;
          if (k === "nickname" || k === "occupation" || k === "interests" || k === "customInstructions" || k === "theme" || k === "accent") {
            api.updateSettings({ [k]: v }).catch(console.error);
          }
        });
      },
      setNotif: (k, channel, v) =>
        set((s) => ({
          notifications: { ...s.notifications, [k]: { ...s.notifications[k], [channel]: v } },
        })),
        
      hydrate: async () => {
        try {
          const { api } = await import("@/lib/api");
          const s = (await api.getSettings()) as Record<string, unknown> | null;
          if (!s) return;

          // `theme` and `accent` are per-device preferences owned by
          // localStorage. The backend copy is write-only from the client's
          // perspective — reading it back lets a stale row (or a response that
          // raced an in-flight POST) overwrite the user's current choice.
          set((prev) => ({
            ...prev,
            customInstructions: (s.customInstructions as string) ?? prev.customInstructions,
            nickname: (s.nickname as string) ?? prev.nickname,
            occupation: (s.occupation as string) ?? prev.occupation,
            interests: (s.moreAboutYou as string) ?? prev.interests,
            enterToSend: (s.sendOnEnter as boolean) ?? prev.enterToSend,
            voiceTTS: (s.textToSpeech as boolean) ?? prev.voiceTTS,
            conversationMemory: (s.enableMemory as boolean) ?? prev.conversationMemory,
            pythonInterpreter: (s.enableCodeInterpreter as boolean) ?? prev.pythonInterpreter,
          }));
        } catch (e) {
          console.error("Failed to hydrate settings", e);
        }
      }
    }),
    {
      name: "infichat-settings",
      version: 2,
      partialize: (s) => ({
        theme: s.theme,
        accent: s.accent,
        appLang: s.appLang,
        spokenLang: s.spokenLang,
        voiceProfile: s.voiceProfile,
        voiceFullscreen: s.voiceFullscreen,
        notifications: s.notifications,
        customInstructions: s.customInstructions,
        nickname: s.nickname,
        occupation: s.occupation,
        interests: s.interests,
        personalizeResponses: s.personalizeResponses,
        conversationMemory: s.conversationMemory,
        pythonInterpreter: s.pythonInterpreter,
        voiceTTS: s.voiceTTS,
        piiScrubbing: s.piiScrubbing,
        autoWebSearch: s.autoWebSearch,
        enterToSend: s.enterToSend,
        streaming: s.streaming,
      }),
      // v1 could hold a `theme` corrupted by the old force-dark/hydrate race,
      // plus backend-shaped keys from the previous blind spread. Drop both.
      migrate: (state, from) => {
        if (from >= 2) return state as SettingsState;
        const s = (state ?? {}) as Partial<SettingsState>;
        const valid = s.theme === "light" || s.theme === "dark" || s.theme === "system";
        return { ...s, theme: valid ? s.theme : "dark" } as SettingsState;
      },
    },
  ),
);

// Backwards-compat helpers used in existing components
export const settingsSetters = {
  setTheme: (t: Theme) => useSettingsStore.getState().set("theme", t),
  setAccent: (a: AccentKey) => useSettingsStore.getState().set("accent", a),
  setEnterToSend: (v: boolean) => useSettingsStore.getState().set("enterToSend", v),
  setVoiceTTS: (v: boolean) => useSettingsStore.getState().set("voiceTTS", v),
  setStreaming: (v: boolean) => useSettingsStore.getState().set("streaming", v),
};
