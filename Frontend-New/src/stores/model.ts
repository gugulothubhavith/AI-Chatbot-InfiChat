import { create } from "zustand";
import { persist } from "zustand/middleware";

export type ModelId = string;

export type ModelEntry = {
  id: ModelId;
  name: string;
  provider: string;
  desc: string;
  custom?: boolean;
  endpoint?: string;
  apiKeyMasked?: string;
};

export const BUILTIN_MODELS: ModelEntry[] = [
  { id: "nvidia/nemotron-3-ultra-550b-a55b", name: "Nemotron 3 Ultra (550B)", provider: "NVIDIA", desc: "Advanced reasoning with thinking capability" },
  { id: "meta/llama-3.1-70b-instruct", name: "Llama 3.1 (70B) Instruct", provider: "Meta", desc: "Advanced conversational model" },
  { id: "openai/gpt-oss-120b", name: "GPT OSS (120B)", provider: "OpenAI", desc: "High-speed reasoning and coding" },
];

// Back-compat export used across the app.
export const MODELS = BUILTIN_MODELS;

export type ToolId = "web" | "image" | "research" | "thinking";

type ModelState = {
  model: ModelId;
  tools: Record<ToolId, boolean>;
  customModels: ModelEntry[];
  setModel: (m: ModelId) => void;
  toggleTool: (t: ToolId) => void;
  addCustomModel: (m: Omit<ModelEntry, "id" | "custom" | "apiKeyMasked"> & { apiKey?: string }) => ModelEntry;
  removeCustomModel: (id: ModelId) => void;
  allModels: () => ModelEntry[];
};

const maskKey = (k?: string) => {
  if (!k) return undefined;
  const trimmed = k.trim();
  if (trimmed.length <= 8) return "•".repeat(trimmed.length);
  return `${trimmed.slice(0, 4)}${"•".repeat(6)}${trimmed.slice(-4)}`;
};

export const useModelStore = create<ModelState>()(
  persist(
    (set, get) => ({
      model: "nvidia/nemotron-3-ultra-550b-a55b",
      tools: { web: false, image: false, research: false, thinking: false },
      customModels: [],
      setModel: (model) => set({ model }),
      toggleTool: (t) =>
        set((s) => {
          const wasActive = s.tools[t];
          const cleared = { web: false, image: false, research: false, thinking: false } as Record<ToolId, boolean>;
          return { tools: { ...cleared, [t]: !wasActive } };
        }),
      addCustomModel: (m) => {
        const id = `custom-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 6)}`;
        const entry: ModelEntry = {
          id,
          name: m.name.trim() || "Custom Model",
          provider: m.provider.trim() || "Custom",
          desc: m.desc?.trim() || m.endpoint || "User-configured endpoint",
          custom: true,
          endpoint: m.endpoint?.trim(),
          apiKeyMasked: maskKey(m.apiKey),
        };
        set((s) => ({ customModels: [...s.customModels, entry], model: id }));
        return entry;
      },
      removeCustomModel: (id) =>
        set((s) => {
          const next = s.customModels.filter((m) => m.id !== id);
          const model = s.model === id ? BUILTIN_MODELS[2].id : s.model;
          return { customModels: next, model };
        }),
      allModels: () => [...BUILTIN_MODELS, ...get().customModels],
    }),
    {
      name: "infichat-models",
      partialize: (s) => ({ model: s.model, customModels: s.customModels }),
    },
  ),
);
