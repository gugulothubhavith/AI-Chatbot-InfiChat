import { useState, useEffect, useRef, ChangeEvent } from "react";
import { createPortal } from "react-dom";
import {
    Gear as SettingsIcon,
    Check,
    X,
    Plus,
    Bell,
    Play,
    FileText,
    ShieldCheck,
    UserCircle as CircleUser,
    CaretDown as ChevronDown,
    Spinner as Loader2,
    Sparkle as Sparkles,
    Database,
    Question as HelpCircle,
    Trash as Trash2,
    ArrowsClockwise as RefreshCw,
    DownloadSimple as Download,
    Sun,
    Moon,
    Monitor,
    CreditCard,
} from "@phosphor-icons/react";
import { cn } from "../lib/utils";
import axios from "axios";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8080";
import { useAuth } from "../hooks/useAuth";
import { useTheme } from "../context/ThemeContext";
import { useAccentColor } from "../hooks/useAccentColor";
import { toast } from "sonner";
import { ThemePreviewCards, AccentColorPicker, SecuritySection, AccountSection, THEME_OPTIONS, ACCENT_COLORS, settingsStyles } from "./settings";

interface Settings {
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
    // Personalization
    customInstructions: string;
    nickname: string;
    occupation: string;
    moreAboutYou: string;
    enableMemory: boolean;
    enableChatHistory: boolean;
    enableCodeInterpreter: boolean;
    enableVoice: boolean;
}

interface SettingsModalProps {
    isOpen: boolean;
    onClose: () => void;
}

function CustomSelect({ value, options, onChange }: { value: string, options: { value: string, label: string }[], onChange: (v: string) => void }) {
    const [isOpen, setIsOpen] = useState(false);
    const containerRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        const handleClick = (e: MouseEvent) => {
            if (containerRef.current && !containerRef.current.contains(e.target as Node)) setIsOpen(false);
        };
        document.addEventListener("mousedown", handleClick);
        return () => document.removeEventListener("mousedown", handleClick);
    }, []);

    const selectedOption = options.find(o => o.value === value) || options[0];

    return (
        <div className="relative" ref={containerRef}>
            <button
                onClick={() => setIsOpen(!isOpen)}
                className="flex items-center gap-1 text-[13px] text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors"
            >
                {selectedOption.label}
                <ChevronDown size={14} className={cn("transition-transform opacity-50", isOpen && "rotate-180")} />
            </button>
            {isOpen && (
                <div className="absolute right-0 top-full mt-2 min-w-[140px] bg-white dark:bg-[#171717] border border-gray-200 dark:border-gray-700 rounded-2xl shadow-xl py-1.5 z-[100]">
                    {options.map(opt => (
                        <button
                            key={opt.value}
                            onClick={() => { onChange(opt.value); setIsOpen(false); }}
                            className="w-full flex items-center justify-between px-3 py-2 text-[13px] hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors text-left"
                        >
                            <span className={cn(opt.value === value ? "text-gray-900 dark:text-gray-100 font-medium" : "text-gray-500 dark:text-gray-400")}>
                                {opt.label}
                            </span>
                            {opt.value === value && <Check size={14} className="text-gray-900 dark:text-gray-100" />}
                        </button>
                    ))}
                </div>
            )}
        </div>
    );
}


function NotifChannelPicker({ channels, onChange }: { channels: string[], onChange: (next: string[]) => void }) {
    const [open, setOpen] = useState(false);
    const ref = useRef<HTMLDivElement>(null);

    useEffect(() => {
        const h = (e: MouseEvent) => { if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false); };
        document.addEventListener('mousedown', h);
        return () => document.removeEventListener('mousedown', h);
    }, []);

    const hasPush = channels.includes('push');
    const hasEmail = channels.includes('email');
    const label = hasPush && hasEmail ? 'Push, Email' : hasPush ? 'Push' : hasEmail ? 'Email' : 'None';

    const toggle = async (ch: string) => {
        if (ch === 'push' && !hasPush) {
            if ('Notification' in window && Notification.permission !== 'granted' && Notification.permission !== 'denied') {
                await Notification.requestPermission();
            }
        }
        const next = channels.includes(ch) ? channels.filter(c => c !== ch) : [...channels, ch];
        onChange(next);
        if (next.length === 0) setOpen(false);
    };

    const toggleBase2 = 'w-10 h-[22px] rounded-full p-[2px] cursor-pointer transition-colors duration-300 flex-shrink-0 flex items-center';

    return (
        <div className="relative flex-shrink-0" ref={ref}>
            <button
                onClick={() => setOpen(o => !o)}
                className="flex items-center gap-1 text-[13px] text-gray-500 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200 transition-colors"
            >
                {label}
                <ChevronDown size={14} className={cn('opacity-50 transition-transform', open && 'rotate-180')} />
            </button>
            {open && (
                <div className="absolute right-0 top-full mt-2 w-[160px] bg-white dark:bg-[#171717] border border-gray-200 dark:border-gray-700 rounded-2xl shadow-xl py-2 z-[200]">
                    {/* Push row */}
                    <div className="flex items-center justify-between px-4 py-2">
                        <span className="text-[13px] text-gray-900 dark:text-gray-100 font-medium">Push</span>
                        <button
                            onClick={() => toggle('push')}
                            className={cn(toggleBase2, hasPush ? 'bg-[#10A37F] justify-end' : 'bg-gray-100 dark:bg-gray-800 justify-start')}
                        >
                            <div className="h-[18px] w-[18px] rounded-full bg-white shadow" />
                        </button>
                    </div>
                    {/* Email row */}
                    <div className="flex items-center justify-between px-4 py-2">
                        <span className="text-[13px] text-gray-900 dark:text-gray-100 font-medium">Email</span>
                        <button
                            onClick={() => toggle('email')}
                            className={cn(toggleBase2, hasEmail ? 'bg-[#10A37F] justify-end' : 'bg-gray-100 dark:bg-gray-800 justify-start')}
                        >
                            <div className="h-[18px] w-[18px] rounded-full bg-white shadow" />
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
}

interface ArchivedSession {
    id: string;
    title: string;
    updated_at: string;
}

interface SharedLink {
    token: string;
    title: string;
    created_at: string;
}

const tabs = [
    { id: "general", label: "General", icon: SettingsIcon },
    { id: "notifications", label: "Notifications", icon: Bell },
    { id: "personalization", label: "Personalization", icon: Sparkles },
    { id: "data", label: "Data controls", icon: Database },
    { id: "security", label: "Security", icon: ShieldCheck },
    { id: "updates", label: "Updates", icon: RefreshCw },
    { id: "account", label: "Account", icon: CircleUser },
    { id: "subscription", label: "Subscription", icon: CreditCard },
];

export function SettingsModal({ isOpen, onClose }: SettingsModalProps) {
    const { user, token, logout } = useAuth();
    const { theme: ctxTheme, setTheme: setCtxTheme } = useTheme();
    const [activeTab, setActiveTab] = useState("general");
    const [settings, setSettings] = useState<Settings>({
        theme: ctxTheme,
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
        // Personalization
        customInstructions: "",
        nickname: "",
        occupation: "",
        moreAboutYou: "",
        enableMemory: true,
        enableChatHistory: true,
        enableCodeInterpreter: true,
        enableVoice: true,
    });

    const [piiEnabled, setPiiEnabled] = useState(false);
    const [showRagManager, setShowRagManager] = useState(false);
    const [showArchivedManager, setShowArchivedManager] = useState(false);
    const [showSharedManager, setShowSharedManager] = useState(false);
    const [showPasswordForm, setShowPasswordForm] = useState(false);

    const [ragDocuments, setRagDocuments] = useState<string[]>([]);
    const [archivedSessions, setArchivedSessions] = useState<ArchivedSession[]>([]);
    const [sharedLinks, setSharedLinks] = useState<SharedLink[]>([]);

    const [isUploadingRag, setIsUploadingRag] = useState(false);
    const [passwordData, setPasswordData] = useState({ old: "", new: "", confirm: "" });
    const [passwordStatus, setPasswordStatus] = useState<{ type: 'success' | 'error', msg: string } | null>(null);
    const [isCheckingUpdate, setIsCheckingUpdate] = useState(false);
    const [updateResult, setUpdateResult] = useState<{ available: boolean, version?: string, url?: string } | null>(null);
    const [imgError, setImgError] = useState(false);

    const [accentOpen, setAccentOpen] = useState(false);
    const [isReading, setIsReading] = useState(false);
    const [readingId, setReadingId] = useState<string | null>(null);
    const accentRef = useRef<HTMLDivElement>(null);
    const audioRef = useRef<any>(null);

    // Sync accent color to CSS custom properties on :root
    useAccentColor(settings.accentColor);

    useEffect(() => {
        if (isOpen) {
            fetchSettings();
            const handleEsc = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); };
            window.addEventListener("keydown", handleEsc);
            return () => window.removeEventListener("keydown", handleEsc);
        }
    }, [isOpen]);

    useEffect(() => {
        const handleClick = (e: MouseEvent) => {
            if (accentRef.current && !accentRef.current.contains(e.target as Node)) {
                setAccentOpen(false);
            }
        };
        document.addEventListener("mousedown", handleClick);
        return () => document.removeEventListener("mousedown", handleClick);
    }, []);

    const fetchSettings = async () => {
        try {
            const res = await axios.get("/settings");
            if (res.data) {
                setSettings(prev => ({ ...prev, ...res.data, theme: ctxTheme }));
            }

            // Also fetch PII status
            const privacyRes = await axios.get("/admin/privacy/settings");
            if (privacyRes.data) setPiiEnabled(!!privacyRes.data.pii_scrubbing_enabled);

            fetchRagDocuments();
            fetchArchivedSessions();
            fetchSharedLinks();
        } catch { /* fail silently */ }
    };

    const fetchArchivedSessions = async () => {
        try {
            const res = await axios.get("/chat/archived");
            if (res.data) setArchivedSessions(res.data);
        } catch { /* fail */ }
    };

    const fetchSharedLinks = async () => {
        try {
            const res = await axios.get("/chat/shared");
            if (res.data) setSharedLinks(res.data);
        } catch { /* fail */ }
    };

    const handleUnarchive = async (id: string) => {
        try {
            await axios.patch(`/chat/sessions/${id}`, { is_archived: false });
            fetchArchivedSessions();
            toast.success("Chat unarchived");
        } catch { toast.error("Failed to unarchive"); }
    };

    const handleDeleteArchived = async (id: string) => {
        toast("Delete this chat permanently?", {
            action: {
                label: "Delete",
                onClick: async () => {
                    try {
                        await axios.delete(`/chat/sessions/${id}`);
                        fetchArchivedSessions();
                        toast.success("Chat deleted");
                    } catch { toast.error("Failed to delete"); }
                },
            },
        });
    };

    const handleUnshare = async (token: string) => {
        try {
            await axios.delete(`/chat/shared/${token}`);
            fetchSharedLinks();
            toast.success("Link removed");
        } catch { toast.error("Failed to unshare"); }
    };

    const handleCheckForUpdates = async () => {
        setIsCheckingUpdate(true);
        setUpdateResult(null);
        try {
            // @ts-ignore
            if (window.electronAPI?.checkForUpdates) {
                // @ts-ignore
                const result = await window.electronAPI.checkForUpdates();
                setUpdateResult(result);
            } else {
                // Fallback for browser
                const res = await axios.get("/system/latest-update");
                const currentVersion = "0.1.0"; // Should come from package.json or config
                setUpdateResult({
                    available: res.data.version !== currentVersion,
                    version: res.data.version,
                    url: res.data.download_url
                });
            }
        } catch (err) {
            console.error("Update check failed", err);
        } finally {
            setIsCheckingUpdate(false);
        }
    };

    const handlePasswordUpdate = async () => {
        if (passwordData.new !== passwordData.confirm) {
            setPasswordStatus({ type: 'error', msg: "New passwords don't match" });
            return;
        }
        if (passwordData.new.length < 6) {
            setPasswordStatus({ type: 'error', msg: "Password must be at least 6 characters" });
            return;
        }

        try {
            await axios.patch("/auth/password", {
                old_password: passwordData.old,
                new_password: passwordData.new
            });
            setPasswordStatus({ type: 'success', msg: "Password updated successfully" });
            setPasswordData({ old: "", new: "", confirm: "" });
            setTimeout(() => setShowPasswordForm(false), 2000);
        } catch (err: any) {
            setPasswordStatus({ type: 'error', msg: err.response?.data?.detail || "Update failed" });
        }
    };


    const handleSave = async (updatedSettings?: Settings) => {
        try {
            const finalSettings = updatedSettings || settings;
            await axios.post("/settings", finalSettings);
            if (finalSettings.theme && finalSettings.theme !== ctxTheme) {
                setCtxTheme(finalSettings.theme);
            }
        } catch (error) {
            console.error("Failed to save settings", error);
        }
    };

    const playPreview = async () => {
        if (isReading) {
            if (audioRef.current?.pause) audioRef.current.pause();
            setIsReading(false);
            setReadingId(null);
            return;
        }

        setIsReading(true);
        setReadingId("preview");

        const previewTexts: Record<string, string> = {
            "en_professional_male": "Hello! This is a professional English voice profile.",
            "hi_corporate_female": "नमस्ते। यह एक कॉर्पोरेट हिंदी आवाज़ है, जो बहुत ही स्पष्ट है।",
            "te_empathetic_male": "నమస్కారం. ఇది ఒక సానుభూతితో కూడిన తెలుగు స్వరం.",
            "hi_alert_female": "सावधान! यह एक तेज़ हिंदी सूचना है।"
        };

        const text = previewTexts[settings.selectedVoice] || "Hello! This is its preview.";

        try {
            const res = await fetch(`${API_URL}/voice/tts`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`
                },
                body: JSON.stringify({ text, voice_id: settings.selectedVoice })
            });

            if (!res.ok) throw new Error("TTS failed");

            const blob = await res.blob();
            const url = URL.createObjectURL(blob);
            const audio = new Audio(url);

            audioRef.current = audio;
            setIsReading(true);

            audio.onended = () => {
                setIsReading(false);
                setReadingId(null);
                URL.revokeObjectURL(url);
            };

            await audio.play();

        } catch (err) {
            console.error("Preview failed", err);
            setIsReading(false);
            setReadingId(null);
        }
    };

    // Removed applyTheme as it's handled by ThemeContext

    const togglePii = async () => {
        const next = !piiEnabled;
        setPiiEnabled(next);
        try { await axios.post("/admin/privacy/pii", { enabled: next }); } catch { /* fail silently */ }
    };

    const fetchRagDocuments = async () => {
        try {
            const res = await axios.get("/rag/documents");
            if (res.data?.documents) setRagDocuments(res.data.documents);
        } catch { /* fail silently */ }
    };

    const handleRagUpload = async (e: ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;

        setIsUploadingRag(true);
        const formData = new FormData();
        formData.append("file", file);

        try {
            await axios.post("/rag/upload", formData);
            await fetchRagDocuments();
            toast.success("File uploaded and indexed successfully.");
        } catch (err) {
            toast.error("Failed to upload file.");
        } finally {
            setIsUploadingRag(false);
        }
    };

    const handleRagDelete = async (filename: string) => {
        toast(`Delete "${filename}" from Knowledge Base?`, {
            action: {
                label: "Delete",
                onClick: async () => {
                    try {
                        await axios.delete(`/rag/documents/${filename}`);
                        await fetchRagDocuments();
                        toast.success("Document deleted");
                    } catch {
                        toast.error("Failed to delete document.");
                    }
                },
            },
        });
    };


    const currentAccent = ACCENT_COLORS.find(c => c.id === settings.accentColor) ?? ACCENT_COLORS[0];



    if (!isOpen) return null;

    // Shared row classes
    const row = "flex items-center justify-between py-3.5 border-b border-gray-200 dark:border-gray-700 last:border-0";
    const label = "text-[13px] text-gray-900 dark:text-gray-100 font-medium";
    const subtext = "text-xs text-gray-500 dark:text-gray-400 mt-1 leading-normal";
    const toggleBase = "w-11 h-6 rounded-full p-[3px] cursor-pointer transition-colors duration-300 flex-shrink-0";

    return createPortal(
        <div className="fixed inset-0 z-[300] flex items-center justify-center p-4">
            {/* Backdrop */}
            <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" onClick={onClose} />

            {/* Modal */}
            <div className="relative w-full max-w-[740px] h-[580px] bg-white dark:bg-[#212121] rounded-3xl shadow-2xl flex overflow-hidden z-10 border border-gray-200 dark:border-gray-700">

                {/* Close button - Top Left of container */}
                <button
                    onClick={onClose}
                    className="absolute top-4 left-4 z-20 p-1.5 rounded-lg text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-all font-bold"
                >
                    <X size={18} strokeWidth={2.5} />
                </button>
                {/* ── Left Sidebar ── */}
                <div className="w-[230px] flex-shrink-0 bg-white dark:bg-[#171717] border-r border-gray-200 dark:border-gray-700 flex flex-col pt-14 pb-3 px-2">

                    {/* Nav tabs */}
                    <nav className="flex-1 flex flex-col gap-0.5">
                        {tabs.map(tab => (
                            <button
                                key={tab.id}
                                onClick={() => setActiveTab(tab.id)}
                                className={cn(
                                    "flex items-center gap-2.5 px-3 py-2 rounded-lg text-[13px] font-medium transition-all text-left w-full",
                                    activeTab === tab.id
                                        ? "bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-gray-100 shadow-sm"
                                        : "text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 hover:text-gray-800 dark:hover:text-gray-200"
                                )}
                            >
                                <tab.icon size={15} className="flex-shrink-0" />
                                {tab.label}
                            </button>
                        ))}
                    </nav>

                </div>
                {/* ── Right Content ── */}
                <div className="flex-1 flex flex-col overflow-hidden">
                    {/* Header */}
                    <div className="px-8 pt-7 pb-1 flex-shrink-0">
                        <h2 className="text-base font-semibold text-gray-900 dark:text-gray-100">
                            {activeTab === "account" ? "Account" : tabs.find(t => t.id === activeTab)?.label ?? activeTab}
                        </h2>
                    </div>
                    {/* Scrollable body */}
                    <div className="flex-1 overflow-y-auto px-8 py-4">

                        {/* ────── GENERAL ────── */}
                        {activeTab === "general" && (
                            <div className="space-y-6">
                                <div>
                                    <h3 className={settingsStyles.sectionTitle}>Appearance</h3>
                                    <div className="space-y-5">
                                        <div className="space-y-3">
                                            <span className={label}>Theme</span>
                                            <ThemePreviewCards 
                                                value={settings.theme} 
                                                onChange={(t) => {
                                                    setSettings(s => {
                                                        const next = { ...s, theme: t };
                                                        handleSave(next);
                                                        return next;
                                                    });
                                                }} 
                                            />
                                        </div>
                                        
                                        <div className="space-y-3">
                                            <span className={label}>Accent Color</span>
                                            <AccentColorPicker
                                                value={settings.accentColor}
                                                onChange={(c) => {
                                                    setSettings(s => {
                                                        const next = { ...s, accentColor: c };
                                                        handleSave(next);
                                                        return next;
                                                    });
                                                }}
                                            />
                                        </div>
                                    </div>
                                </div>
                                <div className="space-y-0 divide-y divide-gray-100 dark:divide-white/[0.06]">

                                <div className={row}>
                                    <span className={label}>Language</span>
                                    <CustomSelect
                                        value={settings.language}
                                        options={[
                                            { value: "auto", label: "Auto detect" },
                                            { value: "en", label: "English (US)" },
                                            { value: "hi", label: "Hindi" },
                                            { value: "ja", label: "日本語" },
                                        ]}
                                        onChange={v => {
                                            setSettings(s => {
                                                const next = { ...s, language: v };
                                                handleSave(next);
                                                return next;
                                            });
                                        }}
                                    />
                                </div>

                                <div className="py-3.5 border-b border-gray-200 dark:border-gray-700">
                                    <div className="flex items-center justify-between">
                                        <span className={label}>Spoken language</span>
                                        <CustomSelect
                                            value={settings.spokenLanguage}
                                            options={[
                                                { value: "auto", label: "Auto-detect" },
                                                { value: "en", label: "English" },
                                                { value: "hi", label: "Hindi" },
                                            ]}
                                            onChange={v => {
                                                setSettings(s => {
                                                    const next = { ...s, spokenLanguage: v };
                                                    handleSave(next);
                                                    return next;
                                                });
                                            }}
                                        />
                                    </div>
                                    <p className={subtext}>
                                        For best results, select the language you mainly speak. If it’s not listed, it may still be supported via auto-detection.
                                    </p>
                                </div>

                                <div className={row}>
                                    <span className={label}>Voice</span>
                                    <div className="flex items-center gap-4">
                                        <button
                                            className="flex items-center gap-1 text-[13px] text-gray-900 dark:text-gray-100 font-medium hover:opacity-80 transition-opacity"
                                            onClick={playPreview}
                                            disabled={isReading && readingId !== "preview"}
                                        >
                                            {isReading && readingId === "preview" ? (
                                                <Loader2 size={13} className="animate-spin" />
                                            ) : (
                                                <Play size={11} className="fill-current" />
                                            )}
                                            Play
                                        </button>
                                        <CustomSelect
                                            value={settings.selectedVoice}
                                            options={[
                                                { value: "en_professional_male", label: "Professional - English (Male)" },
                                                { value: "hi_corporate_female", label: "Corporate - Hindi (Female)" },
                                                { value: "te_empathetic_male", label: "Empathetic - Telugu (Male)" },
                                                { value: "hi_alert_female", label: "Alert - Hindi (Fast)" },
                                            ]}
                                            onChange={v => {
                                                setSettings(s => {
                                                    const next = { ...s, selectedVoice: v };
                                                    handleSave(next);
                                                    return next;
                                                });
                                            }}
                                        />
                                    </div>
                                </div>

                                <div className="py-3.5">
                                    <div className="flex items-center justify-between">
                                        <span className={label}>Separate Voice</span>
                                        <div
                                            className={cn(toggleBase, settings.separateVoice ? "bg-[#10A37F]" : "bg-[#ccc] dark:bg-[#444]")}
                                            onClick={() => {
                                                setSettings(s => {
                                                    const next = { ...s, separateVoice: !s.separateVoice };
                                                    handleSave(next);
                                                    return next;
                                                });
                                            }}
                                        >
                                            <div className={cn("h-[18px] w-[18px] rounded-full bg-white shadow transition-transform duration-300", settings.separateVoice ? "translate-x-5" : "translate-x-0")} />
                                        </div>
                                    </div>
                                    <p className={subtext}>
                                        Keep ChatGPT Voice in a separate full screen, without real time transcripts and visuals.
                                    </p>
                                </div>
                            </div>
                            </div>
                        )}

                        {/* ────── NOTIFICATIONS ────── */}
                        {activeTab === "notifications" && (
                            <div className="divide-y divide-gray-100 dark:divide-white/[0.06]">
                                {([
                                    {
                                        key: "notifResponses" as keyof Settings,
                                        title: "Responses",
                                        desc: "Get notified when InfiChat finishes a response that takes time, like generating a long answer.",
                                    },
                                    {
                                        key: "notifRecommendations" as keyof Settings,
                                        title: "Recommendations",
                                        desc: "Stay in the loop on new tools, tips, and features from InfiChat.",
                                    },
                                    {
                                        key: "notifUsage" as keyof Settings,
                                        title: "Usage",
                                        desc: "We'll notify you when usage limits reset or when you're approaching your limits.",
                                    },
                                ] as { key: keyof Settings; title: string; desc: string }[]).map(item => (
                                    <div key={item.key as string} className="py-4">
                                        <div className="flex items-start justify-between gap-4">
                                            <div className="flex-1 min-w-0">
                                                <div className={label}>{item.title}</div>
                                                <p className={subtext}>{item.desc}</p>
                                            </div>
                                            <NotifChannelPicker
                                                channels={settings[item.key] as string[]}
                                                onChange={next => {
                                                    const updated = { ...settings, [item.key]: next };
                                                    setSettings(updated);
                                                    handleSave(updated);
                                                }}
                                            />
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}

                        {/* ────── PERSONALIZATION ────── */}
                        {activeTab === "personalization" && (
                            <div className="space-y-6">
                                {/* Custom Instructions */}
                                <div className="space-y-3">
                                    <div className={label}>Custom instructions</div>
                                    <textarea
                                        value={settings.customInstructions}
                                        onChange={e => {
                                            const next = { ...settings, customInstructions: e.target.value };
                                            setSettings(next);
                                            handleSave(next);
                                        }}
                                        placeholder="Additional behavior, style, and tone preferences"
                                        className="w-full h-24 bg-transparent border border-gray-200 dark:border-gray-700 rounded-xl px-4 py-3 text-[15px] focus:outline-none focus:ring-1 focus:ring-black/10 dark:focus:ring-white/20 resize-none placeholder-gray-400"
                                    />
                                    <p className={subtext}>These instructions will be applied to every new chat session.</p>
                                </div>

                                {/* About You (Simplified) */}
                                <div className="space-y-5 pt-2">
                                    <div className={label}>About you</div>

                                    <div className="space-y-4">
                                        <div className="flex gap-4">
                                            <div className="flex-1 space-y-2">
                                                <div className="text-sm font-medium dark:text-white/80">Nickname</div>
                                                <input
                                                    type="text"
                                                    value={settings.nickname}
                                                    onChange={e => {
                                                        const next = { ...settings, nickname: e.target.value };
                                                        setSettings(next);
                                                        handleSave(next);
                                                    }}
                                                    placeholder="InfiUser"
                                                    className="w-full bg-transparent border border-gray-200 dark:border-gray-700 rounded-xl px-3.5 py-2 text-[15px] focus:outline-none focus:ring-1 focus:ring-black/10 dark:focus:ring-white/20"
                                                />
                                            </div>
                                            <div className="flex-1 space-y-2">
                                                <div className="text-sm font-medium dark:text-white/80">Occupation</div>
                                                <input
                                                    type="text"
                                                    value={settings.occupation}
                                                    onChange={e => {
                                                        const next = { ...settings, occupation: e.target.value };
                                                        setSettings(next);
                                                        handleSave(next);
                                                    }}
                                                    placeholder="Developer"
                                                    className="w-full bg-transparent border border-gray-200 dark:border-gray-700 rounded-xl px-3.5 py-2 text-[15px] focus:outline-none focus:ring-1 focus:ring-black/10 dark:focus:ring-white/20"
                                                />
                                            </div>
                                        </div>

                                        <div className="space-y-2">
                                            <div className="text-sm font-medium dark:text-white/80">Interests & Context</div>
                                            <input
                                                type="text"
                                                value={settings.moreAboutYou}
                                                onChange={e => {
                                                    const next = { ...settings, moreAboutYou: e.target.value };
                                                    setSettings(next);
                                                    handleSave(next);
                                                }}
                                                placeholder="I like minimalist design and efficient code..."
                                                className="w-full bg-transparent border border-gray-200 dark:border-gray-700 rounded-xl px-3.5 py-2 text-[15px] focus:outline-none focus:ring-1 focus:ring-black/10 dark:focus:ring-white/20"
                                            />
                                        </div>
                                    </div>
                                </div>

                                {/* Memory */}
                                <div className="space-y-4 pt-4 border-t border-gray-200 dark:border-gray-700">
                                    <div className="flex items-center gap-1.5">
                                        <div className={label}>Memory & Context</div>
                                        <HelpCircle className="w-4 h-4 text-gray-400" />
                                        <button className="ml-auto bg-[#f0f0f0] dark:bg-white/10 px-3 py-1 rounded-full text-xs font-medium">Manage</button>
                                    </div>

                                    <div className="space-y-4">
                                        <div className="flex items-center justify-between">
                                            <div className="space-y-0.5">
                                                <div className="text-[14px] dark:text-white/90">Personalize responses</div>
                                                <p className={subtext}>Use my nickname, occupation, and context in chats.</p>
                                            </div>
                                            <div
                                                className={cn(toggleBase, settings.enableMemory ? "bg-green-500" : "bg-[#ccc] dark:bg-[#444]")}
                                                onClick={() => {
                                                    const next = { ...settings, enableMemory: !settings.enableMemory };
                                                    setSettings(next);
                                                    handleSave(next);
                                                }}
                                            >
                                                <div className={cn("h-[18px] w-[18px] rounded-full bg-white shadow transition-transform duration-300", settings.enableMemory ? "translate-x-5" : "translate-x-0")} />
                                            </div>
                                        </div>

                                        <div className="flex items-center justify-between">
                                            <div className="space-y-0.5">
                                                <div className="text-[14px] dark:text-white/90">Conversation memory</div>
                                                <p className={subtext}>Remember facts from previous conversations.</p>
                                            </div>
                                            <div
                                                className={cn(toggleBase, settings.enableChatHistory ? "bg-green-500" : "bg-[#ccc] dark:bg-[#444]")}
                                                onClick={() => {
                                                    const next = { ...settings, enableChatHistory: !settings.enableChatHistory };
                                                    setSettings(next);
                                                    handleSave(next);
                                                }}
                                            >
                                                <div className={cn("h-[18px] w-[18px] rounded-full bg-white shadow transition-transform duration-300", settings.enableChatHistory ? "translate-x-5" : "translate-x-0")} />
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                {/* Advanced */}
                                <div className="space-y-4 pt-4 border-t border-gray-200 dark:border-gray-700">
                                    <div className={label}>Advanced Features</div>
                                    <div className="space-y-4">
                                        {[
                                            { title: "Python Code Interpreter", desc: "Execute code in an isolated container.", key: "enableCodeInterpreter" },
                                            { title: "InfiChat Voice", desc: "Enable spoken responses and voice input.", key: "enableVoice" },
                                        ].map(item => (
                                            <div key={item.title} className="flex items-center justify-between">
                                                <div className="space-y-0.5">
                                                    <div className="text-[14px] dark:text-white/90">{item.title}</div>
                                                    <p className={subtext}>{item.desc}</p>
                                                </div>
                                                <div
                                                    className={cn(toggleBase, (settings as any)[item.key] ?? true ? "bg-green-500" : "bg-[#ccc] dark:bg-[#444]")}
                                                    onClick={() => {
                                                        const key = item.key as keyof Settings;
                                                        const next = { ...settings, [key]: !(settings as any)[key] };
                                                        setSettings(next);
                                                        handleSave(next);
                                                    }}
                                                >
                                                    <div className={cn("h-[18px] w-[18px] rounded-full bg-white shadow transition-transform duration-300", (settings as any)[item.key] ?? true ? "translate-x-5" : "translate-x-0")} />
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* ────── SECURITY ────── */}
                        {activeTab === "security" && (
                            <SecuritySection onShowPasswordChange={() => setShowPasswordForm(true)} />
                        )}

                        {/* ────── DATA CONTROLS ────── */}
                        {activeTab === "data" && !showRagManager && !showArchivedManager && !showSharedManager && (
                            <div className="space-y-1 divide-y divide-gray-100 dark:divide-white/[0.06]">
                                <div className="flex items-center justify-between py-4">
                                    <span className={label}>Shared links</span>
                                    <button
                                        onClick={() => setShowSharedManager(true)}
                                        className="bg-[#f0f0f0] dark:bg-white/10 px-3 py-1 rounded-full text-xs font-semibold hover:bg-gray-200 dark:hover:bg-white/20 transition-all"
                                    >Manage</button>
                                </div>

                                <div className="flex items-center justify-between py-4">
                                    <span className={label}>Archived chats</span>
                                    <button
                                        onClick={() => setShowArchivedManager(true)}
                                        className="bg-[#f0f0f0] dark:bg-white/10 px-3 py-1 rounded-full text-xs font-semibold hover:bg-gray-200 dark:hover:bg-white/20 transition-all"
                                    >Manage</button>
                                </div>

                                <div className="flex items-center justify-between py-4">
                                    <span className={label}>Knowledge Base (RAG)</span>
                                    <button
                                        className="bg-[#f0f0f0] dark:bg-white/10 px-3 py-1 rounded-full text-xs font-semibold hover:bg-gray-200 dark:hover:bg-white/20 transition-all"
                                        onClick={() => setShowRagManager(true)}
                                    >Manage</button>
                                </div>

                                <div className="flex items-center justify-between py-4">
                                    <span className={label}>Delete all chats</span>
                                    <button
                                        className="bg-red-50 dark:bg-red-500/10 text-red-500 px-3 py-1 rounded-full text-xs font-semibold hover:bg-red-100 dark:hover:bg-red-500/20 transition-all"
                                        onClick={() => {
                                            toast("Delete all chats permanently? This cannot be undone.", {
                                                action: {
                                                    label: "Delete All",
                                                    onClick: async () => {
                                                        try {
                                                            await axios.delete("/chat/history");
                                                            toast.success("All chat history deleted.");
                                                        } catch (err) {
                                                            toast.error("Failed to delete history.");
                                                        }
                                                    },
                                                },
                                            });
                                        }}
                                    >Delete all</button>
                                </div>

                                <div className="flex items-center justify-between py-4">
                                    <span className={label}>Export data</span>
                                    <button
                                        className="bg-[#f0f0f0] dark:bg-white/10 px-3 py-1 rounded-full text-xs font-semibold hover:bg-gray-200 dark:hover:bg-white/20 transition-all"
                                        onClick={async () => {
                                            try {
                                                const res = await axios.get("/chat/export", { responseType: 'blob' });
                                                const url = window.URL.createObjectURL(new Blob([res.data]));
                                                const link = document.createElement('a');
                                                link.href = url;
                                                link.setAttribute('download', `infichat-export-${new Date().toISOString().split('T')[0]}.json`);
                                                document.body.appendChild(link);
                                                link.click();
                                                link.remove();
                                            } catch (err) {
                                                toast.error("Export failed.");
                                            }
                                        }}
                                    >Export</button>
                                </div>
                            </div>
                        )}

                        {/* Knowledge Base Manager View */}
                        {activeTab === "data" && showRagManager && (
                            <div className="flex flex-col h-full">
                                <button
                                    onClick={() => setShowRagManager(false)}
                                    className="flex items-center gap-1.5 text-xs text-gray-500 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200 transition-colors mb-4"
                                >
                                    <ChevronDown className="rotate-90 w-3 h-3" /> Back to Data Controls
                                </button>

                                <div className="flex-1 flex flex-col min-h-0">
                                    <div className="flex items-center justify-between mb-4">
                                        <h3 className="text-sm font-semibold dark:text-white">Knowledge Base</h3>
                                        <label className="cursor-pointer bg-gray-900 dark:bg-white text-white dark:text-gray-900 px-3 py-1.5 rounded-lg text-xs font-medium hover:opacity-90 disabled:opacity-50">
                                            {isUploadingRag ? <Loader2 className="w-3 h-3 animate-spin inline mr-1" /> : <Plus className="w-3 h-3 inline mr-1" />}
                                            Upload File
                                            <input type="file" className="hidden" onChange={handleRagUpload} disabled={isUploadingRag} accept=".pdf,.txt,.docx" />
                                        </label>
                                    </div>

                                    <div className="flex-1 overflow-y-auto min-h-0 border border-gray-200 dark:border-gray-700 rounded-xl bg-gray-50/30 dark:bg-white/[0.02]">
                                        {ragDocuments.length === 0 ? (
                                            <div className="flex flex-col items-center justify-center h-full p-8 text-center">
                                                <FileText className="w-8 h-8 text-gray-300 dark:text-gray-700 mb-2" />
                                                <p className="text-xs text-gray-400">No documents indexed yet.</p>
                                            </div>
                                        ) : (
                                            <div className="divide-y divide-gray-100 dark:divide-white/[0.06]">
                                                {ragDocuments.map(doc => (
                                                    <div key={doc} className="flex items-center justify-between p-3 group">
                                                        <div className="flex items-center gap-2 min-w-0">
                                                            <FileText className="w-3.5 h-3.5 text-blue-500 flex-shrink-0" />
                                                            <span className="text-xs text-gray-900 dark:text-gray-100 truncate">{doc}</span>
                                                        </div>
                                                        <button
                                                            onClick={() => handleRagDelete(doc)}
                                                            className="text-gray-400 hover:text-red-500 transition-colors opacity-0 group-hover:opacity-100 p-1"
                                                        >
                                                            <X size={14} />
                                                        </button>
                                                    </div>
                                                ))}
                                            </div>
                                        )}
                                    </div>
                                    <p className="text-[10px] text-gray-400 mt-3 italic text-center">
                                        Uploaded files are used to improve chatbot responses using RAG.
                                    </p>
                                </div>
                            </div>
                        )}

                        {/* Shared Links Manager View */}
                        {activeTab === "data" && showSharedManager && (
                            <div className="flex flex-col h-full">
                                <button
                                    onClick={() => setShowSharedManager(false)}
                                    className="flex items-center gap-1.5 text-xs text-gray-500 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200 transition-colors mb-4"
                                >
                                    <ChevronDown className="rotate-90 w-3 h-3" /> Back
                                </button>

                                <div className="flex-1 flex flex-col min-h-0">
                                    <h3 className="text-sm font-semibold dark:text-white mb-4">Shared Links</h3>
                                    <div className="flex-1 overflow-y-auto border border-gray-200 dark:border-gray-700 rounded-xl bg-gray-50/30 dark:bg-white/[0.02]">
                                        {sharedLinks.length === 0 ? (
                                            <div className="flex flex-col items-center justify-center h-full p-8 text-center text-gray-400 text-xs">No shared links.</div>
                                        ) : (
                                            <div className="divide-y divide-gray-100 dark:divide-white/[0.06]">
                                                {sharedLinks.map(link => (
                                                    <div key={link.token} className="p-3 flex items-center justify-between gap-4">
                                                        <div className="min-w-0 flex-1">
                                                            <div className="text-xs font-medium dark:text-white truncate">{link.title}</div>
                                                            <div className="text-[10px] text-gray-400">Created {new Date(link.created_at).toLocaleDateString()}</div>
                                                        </div>
                                                        <div className="flex items-center gap-2">
                                                            <button
                                                                onClick={() => window.open(`/share/${link.token}`, '_blank')}
                                                                className="text-[11px] text-blue-500 hover:underline"
                                                            >View</button>
                                                            <button
                                                                onClick={() => handleUnshare(link.token)}
                                                                className="p-1 text-gray-400 hover:text-red-500"
                                                            ><X size={14} /></button>
                                                        </div>
                                                    </div>
                                                ))}
                                            </div>
                                        )}
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* Archived Chats Manager View */}
                        {activeTab === "data" && showArchivedManager && (
                            <div className="flex flex-col h-full">
                                <button
                                    onClick={() => setShowArchivedManager(false)}
                                    className="flex items-center gap-1.5 text-xs text-gray-500 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200 transition-colors mb-4"
                                >
                                    <ChevronDown className="rotate-90 w-3 h-3" /> Back
                                </button>

                                <div className="flex-1 flex flex-col min-h-0">
                                    <h3 className="text-sm font-semibold dark:text-white mb-4">Archived Chats</h3>
                                    <div className="flex-1 overflow-y-auto border border-gray-200 dark:border-gray-700 rounded-xl bg-gray-50/30 dark:bg-white/[0.02]">
                                        {archivedSessions.length === 0 ? (
                                            <div className="flex flex-col items-center justify-center h-full p-8 text-center text-gray-400 text-xs">No archived chats.</div>
                                        ) : (
                                            <div className="divide-y divide-gray-100 dark:divide-white/[0.06]">
                                                {archivedSessions.map(session => (
                                                    <div key={session.id} className="p-3 flex items-center justify-between gap-4">
                                                        <div className="min-w-0 flex-1">
                                                            <div className="text-xs font-medium dark:text-white truncate">{session.title}</div>
                                                            <div className="text-[10px] text-gray-400">{new Date(session.updated_at).toLocaleDateString()}</div>
                                                        </div>
                                                        <div className="flex items-center gap-2">
                                                            <button
                                                                onClick={() => handleUnarchive(session.id)}
                                                                className="text-[11px] text-gray-500 border border-gray-400/20 px-2 py-0.5 rounded-full hover:bg-gray-100 dark:hover:bg-gray-800"
                                                            >Unarchive</button>
                                                            <button
                                                                onClick={() => handleDeleteArchived(session.id)}
                                                                className="p-1 text-gray-400 hover:text-red-500"
                                                            ><Trash2 size={13} /></button>
                                                        </div>
                                                    </div>
                                                ))}
                                            </div>
                                        )}
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* ────── UPDATES ────── */}
                        {activeTab === "updates" && (
                            <div className="flex flex-col h-full">
                                <h3 className="text-sm font-semibold dark:text-white mb-4">Software Updates</h3>

                                <div className="bg-gray-50/50 dark:bg-white/[0.02] p-6 rounded-2xl border border-gray-200 dark:border-gray-700 flex flex-col items-center text-center">
                                    <div className="h-16 w-16 bg-indigo-50 dark:bg-indigo-500/10 rounded-full flex items-center justify-center mb-4">
                                        <RefreshCw className={cn("text-indigo-600 dark:text-indigo-400 w-8 h-8", isCheckingUpdate && "animate-spin")} />
                                    </div>

                                    <h4 className="text-base font-semibold dark:text-white mb-1">
                                        {updateResult?.available ? "Update Available!" : "Your App is Up to Date"}
                                    </h4>
                                    <p className="text-sm text-gray-500 dark:text-gray-400 mb-6">
                                        {updateResult?.available
                                            ? `Version ${updateResult.version} is now available for download.`
                                            : `You are currently using version 0.1.0.`}
                                    </p>

                                    {updateResult?.available ? (
                                        <button
                                            onClick={() => updateResult.url && window.open(updateResult.url, '_blank')}
                                            className="bg-indigo-600 hover:bg-indigo-700 text-white px-6 py-2.5 rounded-xl text-sm font-semibold transition-all flex items-center gap-2 shadow-lg shadow-indigo-500/20"
                                        >
                                            <Download className="w-4 h-4" />
                                            Download v{updateResult.version}
                                        </button>
                                    ) : (
                                        <button
                                            onClick={handleCheckForUpdates}
                                            disabled={isCheckingUpdate}
                                            className="bg-gray-900 dark:bg-white text-white dark:text-gray-900 px-6 py-2.5 rounded-xl text-sm font-semibold hover:opacity-90 transition-all disabled:opacity-50"
                                        >
                                            {isCheckingUpdate ? "Checking..." : "Check for Updates"}
                                        </button>
                                    )}
                                </div>

                                <div className="mt-8 space-y-4">
                                    <div className="p-4 bg-orange-50/30 dark:bg-orange-500/5 rounded-xl border border-orange-100/50 dark:border-orange-500/10">
                                        <p className="text-[11px] text-orange-700 dark:text-orange-400 leading-relaxed">
                                            <b>Note:</b> InfiChat is a self-hosted platform. Updates are provided directly through your admin's release channel. Always ensure you backup your local database before upgrading.
                                        </p>
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* ────── ACCOUNT ────── */}
                        {activeTab === "account" && (
                            <AccountSection onClose={onClose} />
                        )}

                        {/* ────── SUBSCRIPTION ────── */}
                        {activeTab === "subscription" && (
                            <div className="flex flex-col h-full overflow-y-auto pr-2 custom-scrollbar">
                                <h3 className="text-sm font-semibold dark:text-white mb-4">Subscription</h3>

                                <div className="divide-y divide-gray-100 dark:divide-white/[0.06]">
                                    <div className="flex items-center gap-4 py-4">
                                        <div className="h-12 w-12 rounded-2xl bg-indigo-500/10 flex items-center justify-center flex-shrink-0">
                                            <CreditCard className="h-6 w-6 text-indigo-500" />
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <div className="text-sm font-semibold text-gray-900 dark:text-gray-100 truncate">Enterprise Plan</div>
                                            <div className="text-xs text-green-500 font-medium mt-0.5">Active</div>
                                        </div>
                                    </div>

                                    <div className={row}>
                                        <span className={label}>Billing Cycle</span>
                                        <span className="text-[13px] text-gray-500 dark:text-gray-400">Monthly</span>
                                    </div>
                                    <div className={row}>
                                        <span className={label}>Next Invoice</span>
                                        <span className="text-[13px] text-gray-500 dark:text-gray-400">August 9, 2026</span>
                                    </div>
                                    <div className={row}>
                                        <div>
                                            <div className={label}>Manage Subscription</div>
                                            <div className={subtext}>Update payment methods and billing details.</div>
                                        </div>
                                        <button className="px-3 py-1.5 border border-gray-200 dark:border-white/[0.15] rounded-full text-xs font-semibold hover:bg-gray-100 dark:hover:bg-gray-800 transition-all text-gray-900 dark:text-gray-100">
                                            Manage
                                        </button>
                                    </div>
                                </div>
                            </div>
                        )}


                    </div>

                    {/* No Footer - Auto Save Pattern */}
                </div>
            </div>
        </div>,
        document.body
    );
}
