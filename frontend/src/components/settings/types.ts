import { Sun, Moon, Monitor } from "@phosphor-icons/react";

// ─── Shared Settings Interface ───────────────────────────────────────────────
export interface Settings {
    theme: "light" | "dark" | "system";
    accentColor: string;
    language: string;
    spokenLanguage: string;
    selectedVoice: string;
    separateVoice: boolean;
    fontSize: "small" | "medium" | "large";
    showAvatars: boolean;
    sendOnEnter: boolean;
    model: string;
    temperature: number;
    maxTokens: number;
    topP: number;
    frequencyPenalty: number;
    presencePenalty: number;
    historyLimit: number;
    activeModel: string;
    autoSendVoice: boolean;
    textToSpeech: boolean;
    notifResponses: string[];
    notifRecommendations: string[];
    notifUsage: string[];
    customInstructions: string;
    nickname: string;
    occupation: string;
    moreAboutYou: string;
    enableMemory: boolean;
    enableChatHistory: boolean;
    enableCodeInterpreter: boolean;
    enableVoice: boolean;
}

export interface ArchivedSession {
    id: string;
    title: string;
    created_at: string;
}

export interface SharedLink {
    token: string;
    title: string;
    created_at: string;
}

// ─── Default Settings ────────────────────────────────────────────────────────
export const DEFAULT_SETTINGS: Settings = {
    theme: "system",
    accentColor: "default",
    language: "auto",
    spokenLanguage: "auto",
    selectedVoice: "en_professional_male",
    separateVoice: true,
    fontSize: "medium",
    showAvatars: true,
    sendOnEnter: true,
    model: "nvidia/nemotron-3-ultra-550b-a55b",
    temperature: 0.7,
    maxTokens: 2048,
    topP: 1.0,
    frequencyPenalty: 0.0,
    presencePenalty: 0.0,
    historyLimit: 0,
    activeModel: "nvidia/nemotron-3-ultra-550b-a55b",
    autoSendVoice: true,
    textToSpeech: false,
    notifResponses: ["push"],
    notifRecommendations: ["push"],
    notifUsage: ["push"],
    customInstructions: "",
    nickname: "",
    occupation: "",
    moreAboutYou: "",
    enableMemory: true,
    enableChatHistory: true,
    enableCodeInterpreter: true,
    enableVoice: true,
};

// ─── Theme Options ───────────────────────────────────────────────────────────
export const THEME_OPTIONS = [
    { id: "light" as const, label: "Light", icon: Sun, desc: "Clean & bright" },
    { id: "dark" as const, label: "Dark", icon: Moon, desc: "Easy on eyes" },
    { id: "system" as const, label: "System", icon: Monitor, desc: "Auto match" },
];

// ─── Accent Colors ──────────────────────────────────────────────────────────
export const ACCENT_COLORS = [
    { id: "default", label: "Indigo", color: "#6366f1" },
    { id: "sky", label: "Sky", color: "#0ea5e9" },
    { id: "teal", label: "Teal", color: "#14b8a6" },
    { id: "green", label: "Green", color: "#22c55e" },
    { id: "orange", label: "Orange", color: "#f97316" },
    { id: "rose", label: "Rose", color: "#f43f5e" },
    { id: "purple", label: "Purple", color: "#a855f7" },
];

// ─── Shared CSS class presets ────────────────────────────────────────────────
export const settingsStyles = {
    label: "text-sm font-medium text-gray-800 dark:text-gray-200",
    subtext: "text-xs text-gray-500 dark:text-gray-400 mt-0.5",
    sectionTitle: "text-xs uppercase tracking-wider text-gray-400 dark:text-gray-500 font-semibold mb-3",
    divider: "border-t border-gray-100 dark:border-white/5",
    pill: "bg-[#f0f0f0] dark:bg-white/10 px-3 py-1 rounded-full text-xs font-semibold hover:bg-gray-200 dark:hover:bg-white/20 transition-all",
    dangerPill: "bg-red-50 dark:bg-red-500/10 text-red-500 px-3 py-1 rounded-full text-xs font-semibold hover:bg-red-100 dark:hover:bg-red-500/20 transition-all",
} as const;

// ─── Shared Props ────────────────────────────────────────────────────────────
export interface SettingsTabProps {
    settings: Settings;
    setSettings: React.Dispatch<React.SetStateAction<Settings>>;
}
