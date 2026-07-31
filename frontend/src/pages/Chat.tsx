import React, { useState, useRef, useEffect, useCallback } from "react";
import { LazyMotion, m, domAnimation } from "framer-motion";
import { useParams, useNavigate } from "react-router-dom";
import axios from "axios";
import { Logo } from "../components/Logo";
import { useAuth } from "../hooks/useAuth";
import { useChatStream } from "../hooks/useChatStream";
import { useResearchStream } from "../hooks/useResearchStream";
import { useThinkingStream } from "../hooks/useThinkingStream";
import { useWebSearchStream } from "../hooks/useWebSearchStream";
import { DeepResearchProgress } from "../components/DeepResearchProgress";
import { WebSearchProgress } from "../components/WebSearchProgress";
import { ChatMessage } from "../components/ChatMessage";
import { ChatInput } from "../components/ChatInput";
import { Skeleton } from "../components/ui/Skeleton";
import { SubscriptionGate } from "../components/SubscriptionGate";
import { useAccentColor } from "../hooks/useAccentColor";
import { cn, formatNameFromEmail } from "../lib/utils";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8080";

const handleShare = (text: string) => { navigator.share?.({ text }) || navigator.clipboard.writeText(text); };

function getGreeting(): string {
  const h = new Date().getHours();
  if (h < 5) return "Late night coding?";
  if (h < 12) return "Good morning";
  if (h < 17) return "Good afternoon";
  if (h < 21) return "Good evening";
  return "Good evening";
}

const SUGGESTED_PROMPTS = [
  { icon: "💡", text: "Explain quantum computing", label: "Learn" },
  { icon: "✍️", text: "Write a Python web scraper", label: "Code" },
  { icon: "📊", text: "Analyze this data pattern", label: "Analyze" },
  { icon: "🎨", text: "Design a REST API schema", label: "Create" },
];

interface Message {
  id?: string;
  role: "user" | "assistant" | "system";
  content: string;
  model?: string;
  timestamp: Date;
  image?: string;
  file_name?: string;
  file_type?: string;
}

export default function Chat() {
  const { token, user } = useAuth();
  const { sessionId } = useParams();
  const navigate = useNavigate();

  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [selectedImage, setSelectedImage] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<{ name: string; type: string } | null>(null);
  const [loading, setLoading] = useState(false);
  const [selectedModel, setSelectedModel] = useState("nvidia/nemotron-3-ultra-550b-a55b");
  const [showModelDropdown, setShowModelDropdown] = useState(false);
  const [showToolsMenu, setShowToolsMenu] = useState(false);
  const [isDeepResearch, setIsDeepResearch] = useState(false);
  const [isDeepThinking, setIsDeepThinking] = useState(false);
  const [isWebSearch, setIsWebSearch] = useState(false);
  const [isImageGen, setIsImageGen] = useState(false);
  const [useRag, setUseRag] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [isTtsPlaying, setIsTtsPlaying] = useState(false);
  const [isTtsLoading, setIsTtsLoading] = useState(false);
  const [settings, setSettings] = useState<any>({ textToSpeech: false, selectedVoice: "en_professional_male" });
  const [imgError, setImgError] = useState(false);
  const [copiedMsgIdx, setCopiedMsgIdx] = useState<number | null>(null);
  const [likedMsgIdx, setLikedMsgIdx] = useState<number | null>(null);
  const [dislikedMsgIdx, setDislikedMsgIdx] = useState<number | null>(null);

  const { sendStreamingMessage, cancelStream, isStreaming } = useChatStream();
  const { startResearch, cancelResearch, progress: researchProgress, isResearching } = useResearchStream();
  const { startThinking, cancelThinking, progress: thinkingProgress, isThinking } = useThinkingStream();
  const { startWebSearch, cancelWebSearch, progress: webSearchProgress, isWebSearching } = useWebSearchStream();

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const utteranceRef = useRef<SpeechSynthesisUtterance | null>(null);
  const loadedSessionIdRef = useRef<string | null>(null);
  const ttsAbortRef = useRef<AbortController | null>(null);

  // Sync accent color from settings to CSS variables
  useAccentColor(settings.accentColor || 'default');

  const scrollToBottom = () => messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  useEffect(() => { scrollToBottom(); }, [messages]);
  useEffect(() => { inputRef.current?.focus(); fetchSettings(); }, []);

  const fetchSettings = async () => {
    try {
      const res = await axios.get("/settings", { headers: { Authorization: `Bearer ${token}` } });
      if (res.data) setSettings((p: any) => ({ ...p, ...res.data }));
    } catch {}
  };

  useEffect(() => {
    if (sessionId && sessionId !== loadedSessionIdRef.current) loadMessages(sessionId);
    else if (!sessionId) { setMessages([]); loadedSessionIdRef.current = null; }
  }, [sessionId]);

  useEffect(() => {
    const handleReset = () => {
      setMessages([]); loadedSessionIdRef.current = null; setInput("");
      setSelectedFile(null); setSelectedImage(null);
      setIsDeepResearch(false); setIsDeepThinking(false);
      cancelResearch(); cancelThinking();
      setShowToolsMenu(false); stopTts();
    };
    window.addEventListener("reset-chat", handleReset);
    return () => window.removeEventListener("reset-chat", handleReset);
  }, []);

  const loadMessages = async (sid: string) => {
    setLoading(true);
    try {
      const res = await axios.get(`/chat/sessions/${sid}/messages`, { headers: { Authorization: `Bearer ${token}` } });
      setMessages(res.data.map((m: any) => ({ ...m, image: m.image_url, timestamp: new Date(m.created_at) })));
      loadedSessionIdRef.current = sid;
    } catch (e) { console.error("Failed to load messages", e); }
    finally { setLoading(false); }
  };

  const stopTts = () => {
    ttsAbortRef.current?.abort();
    if (audioRef.current) { audioRef.current.pause(); audioRef.current = null; }
    if (window.speechSynthesis.speaking) window.speechSynthesis.cancel();
    setIsTtsPlaying(false); setIsTtsLoading(false);
  };

  const handleSendMessage = useCallback(async (customConfig?: any) => {
    stopTts();
    const textToSend = customConfig?.overrideText || input;
    if ((!textToSend.trim() && !selectedImage) || loading) return;

    const activeModel = customConfig?.overrideModel || selectedModel || "nvidia/nemotron-3-ultra-550b-a55b";
    const userMessage: Message = { role: "user", content: textToSend, timestamp: new Date(), image: selectedImage || undefined, file_name: selectedFile?.name, file_type: selectedFile?.type };
    setMessages(prev => [...prev, userMessage]);
    setInput(""); setSelectedImage(null); setSelectedFile(null);
    setLoading(true);

    // Track streaming state — replaces content on the LAST assistant message
    // during streaming, only creates new message for calls outside a stream.
    let streamingActive = false;

    const addAssistantMessage = (content: string, model?: string) => {
      setMessages(prev => {
        const newMsgs = [...prev];
        const last = newMsgs[newMsgs.length - 1];
        // If the last message is an assistant message AND we're in streaming mode,
        // update it in-place. Otherwise push a new message.
        if (streamingActive && last && last.role === "assistant") {
          newMsgs[newMsgs.length - 1] = { ...last, content, model: model || last.model };
        } else {
          newMsgs.push({ role: "assistant", content, model: model || activeModel, timestamp: new Date() });
          streamingActive = true; // Once we create a placeholder, all subsequent calls update it
        }
        return newMsgs;
      });
    };

    if (isImageGen) {
      setIsImageGen(false);
      addAssistantMessage("🎨 **Generating your image...**");
      try {
        const res = await axios.post("/image/generate", { prompt: textToSend, session_id: sessionId }, { headers: { Authorization: `Bearer ${token}` } });
        const sid = res.headers["x-chat-session-id"];
        if (sid && sid !== sessionId) navigate(`/${sid}`, { replace: true });
        setMessages(prev => { const n = [...prev]; n[n.length - 1] = { role: "assistant", content: "Here is your generated image:", image: res.data.image_url, timestamp: new Date() }; return n; });
      } catch (err: any) {
        addAssistantMessage(`Failed to generate image: ${err.message}`);
      }
      setLoading(false);
      return;
    }

    if (isDeepResearch) {
      setIsDeepResearch(false);
      addAssistantMessage("", "deep-research");
      await startResearch(textToSend, token || "", sessionId, activeModel, navigate, (report) => { addAssistantMessage(report, "deep-research"); });
      setLoading(false);
      window.dispatchEvent(new Event("chat-updated"));
      return;
    }

    if (isWebSearch) {
      setIsWebSearch(false);
      addAssistantMessage("", "web-search");
      await startWebSearch(textToSend, token || "", sessionId, activeModel, navigate, (report) => { addAssistantMessage(report, "web-search"); });
      setLoading(false);
      window.dispatchEvent(new Event("chat-updated"));
      return;
    }

    if (isDeepThinking) {
      setIsDeepThinking(false);
      addAssistantMessage("", "deep-thinking");
      await startThinking(textToSend, token || "", sessionId, activeModel, navigate, (report) => { addAssistantMessage(report, "deep-thinking"); });
      setLoading(false);
      window.dispatchEvent(new Event("chat-updated"));
      return;
    }

    await sendStreamingMessage(`${API_URL}/chat/stream`, {
      messages: messages.concat(userMessage).map(m => ({ role: m.role, content: m.content, image: m.image, file_name: m.file_name, file_type: m.file_type })),
      conversation_id: sessionId || null, model: activeModel, use_rag: useRag,
      workspace: localStorage.getItem("activeWorkspace") || "personal",
    }, {
      onToken: (text) => addAssistantMessage(text),
      onError: (err) => addAssistantMessage(`⚠️ **Error:** ${err}`),
      onDone: () => {},
      onStatus: (code) => { if (code === 401) alert("Session expired. Please refresh."); },
    }, token || undefined);
    if (useRag) setUseRag(false);
    setLoading(false);
    window.dispatchEvent(new Event("chat-updated"));

    if (settings.textToSpeech) {
      try {
        const ttsRes = await fetch(`${API_URL}/voice/tts`, { method: "POST", headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` }, body: JSON.stringify({ text: "Done", voice_id: settings.selectedVoice }) });
        if (ttsRes.ok) { const blob = await ttsRes.blob(); const audio = new Audio(URL.createObjectURL(blob)); audio.play(); }
      } catch {}
    }
  }, [input, selectedImage, selectedFile, loading, selectedModel, isImageGen, isDeepResearch, isDeepThinking, isWebSearch, useRag, messages, token, sessionId, settings]);

  const toggleRecording = async () => {
    if (isRecording) { mediaRecorderRef.current?.stop(); setIsRecording(false); return; }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mr = new MediaRecorder(stream);
      mediaRecorderRef.current = mr;
      const chunks: Blob[] = [];
      mr.ondataavailable = (e) => chunks.push(e.data);
      mr.onstop = async () => {
        const blob = new Blob(chunks);
        const formData = new FormData(); formData.append("file", blob, "recording.webm");
        const resp = await fetch(`${API_URL}/voice/transcribe`, { method: "POST", headers: { Authorization: `Bearer ${token}` }, body: formData });
        const data = await resp.json();
        setInput(prev => prev ? prev + " " + data.text : data.text);
        stream.getTracks().forEach(t => t.stop());
      };
      mr.start();
      setIsRecording(true);
    } catch { alert("Could not access microphone."); }
  };

  const handleCopy = (text: string, idx: number) => { navigator.clipboard.writeText(text); setCopiedMsgIdx(idx); setTimeout(() => setCopiedMsgIdx(null), 2000); };
  const handleKeyDown = (e: React.KeyboardEvent) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleSendMessage(); } };

  const playMessageTts = async (text: string) => {
    if (isTtsPlaying) { stopTts(); return; }
    setIsTtsLoading(true);
    const ac = new AbortController(); ttsAbortRef.current = ac;
    try {
      const res = await fetch(`${API_URL}/voice/tts`, { method: "POST", signal: ac.signal, headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` }, body: JSON.stringify({ text, voice_id: settings.selectedVoice }) });
      if (!res.ok) throw new Error("TTS failed");
      const blob = await res.blob(); const url = URL.createObjectURL(blob);
      const audio = new Audio(url); audioRef.current = audio;
      setIsTtsLoading(false); setIsTtsPlaying(true);
      audio.onended = () => { setIsTtsPlaying(false); URL.revokeObjectURL(url); };
      audio.onerror = () => { setIsTtsPlaying(false); URL.revokeObjectURL(url); };
      await audio.play();
    } catch {
      setIsTtsLoading(false);
      const u = new SpeechSynthesisUtterance(text);
      utteranceRef.current = u; setIsTtsPlaying(true);
      u.onend = () => setIsTtsPlaying(false);
      window.speechSynthesis.speak(u);
    }
  };

  return (
    <LazyMotion features={domAnimation}>
    <div className="absolute inset-0 flex flex-col overflow-hidden" style={{ background: "var(--color-bg)", color: "var(--color-text-primary)" }}>
      {messages.length === 0 && (
        <div className="absolute inset-0 pointer-events-none overflow-hidden">
          <div className="ambient-orb" style={{ top: "-15%", left: "50%", transform: "translateX(-50%)" }} />
        </div>
      )}
      <div className="flex items-center justify-between px-6 pt-4 pb-2 sticky top-0 z-10" style={{ background: messages.length > 0 ? "var(--color-bg)" : "transparent" }}>
        <Logo hideIcon={true} nameSize={48} className="ml-[-4px] animate-fade-in" />
      </div>

      <div className="flex flex-col flex-1 overflow-hidden">
        <div data-lenis-prevent="true" className={cn("overflow-y-auto p-4 md:p-6 space-y-6 pb-32 md:pb-40", messages.length === 0 ? "flex-1 flex flex-col justify-center" : "flex-1")}>
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center text-center px-4 relative mt-8 md:mt-16 w-full max-w-4xl mx-auto">
              <div className="relative z-10 flex flex-col items-center w-full">
                <m.div initial={{ opacity: 0, scale: 0.9, filter: "blur(10px)" }} animate={{ opacity: 1, scale: 1, filter: "blur(0px)" }} transition={{ duration: 0.7, ease: [0.16, 1, 0.3, 1] }}
                  className="mb-6 flex flex-col items-center">
                  <h2 className="text-3xl md:text-4xl font-semibold tracking-tight mb-4 text-center leading-tight"
                    style={{ color: "var(--color-text-primary)" }}>
                    {getGreeting()}{user ? `, ${formatNameFromEmail((user as any).email)}` : "."}
                  </h2>
                  <p className="text-lg md:text-xl font-medium" style={{ color: "var(--color-text-secondary)" }}>
                    How can I help you today?
                  </p>
                </m.div>
              </div>
            </div>
          ) : (
            messages.reduce((acc: React.ReactNode[], msg, idx) => {
              if (msg.role !== "system") {
                acc.push(
                  <ChatMessage key={idx + "-" + msg.content.substring(0, 10)} message={msg} index={idx} isLast={idx === messages.length - 1} loading={loading}
                    user={user ? { picture: (user as any).avatar_url || (user as any).picture } : undefined} imgError={imgError} setImgError={setImgError}
                    onCopy={handleCopy} onEdit={(t) => setInput(t)} onRegenerate={(t) => handleSendMessage({ overrideText: t })}
                    onShare={handleShare} onPlayTts={playMessageTts} onStopTts={stopTts}
                    onLike={(i) => setLikedMsgIdx(i)} onDislike={(i) => setDislikedMsgIdx(i)}
                    copiedMsgIdx={copiedMsgIdx} likedMsgIdx={likedMsgIdx} dislikedMsgIdx={dislikedMsgIdx}
                    isTtsPlaying={isTtsPlaying} isTtsLoading={isTtsLoading}
                    researchProgress={researchProgress} thinkingProgress={thinkingProgress} />
                );
              }
              return acc;
            }, [])
          )}
          
          {/* Display active live streams at the bottom */}
          {isWebSearching && (
            <div className="w-full max-w-4xl mx-auto px-4 flex justify-start">
              <WebSearchProgress status={webSearchProgress} />
            </div>
          )}
          {loading && !isStreaming && !isResearching && !isThinking && (
            <div className="flex w-full animate-in fade-in max-w-4xl mx-auto px-4">
              <div className="h-8 w-8 rounded-full bg-gray-500/10 mr-4 flex-shrink-0" />
              <div className="flex-1 space-y-3 mt-1">
                <Skeleton className="h-4 w-[60%]" />
                <Skeleton className="h-4 w-[80%]" />
                <Skeleton className="h-4 w-[40%]" />
              </div>
            </div>
          )}
          <div ref={messagesEndRef} className="h-4" />
        </div>

        <ChatInput input={input} setInput={setInput} loading={loading}
          isWebSearch={isWebSearch} isDeepResearch={isDeepResearch} isDeepThinking={isDeepThinking}
          isImageGen={isImageGen} useRag={useRag}
          selectedImage={selectedImage} selectedFile={selectedFile}
          selectedModel={selectedModel}
          showModelDropdown={showModelDropdown} showToolsMenu={showToolsMenu}
          isRecording={isRecording}
          onSend={handleSendMessage} onKeyDown={handleKeyDown}
          onToggleWebSearch={() => setIsWebSearch(!isWebSearch)}
          onToggleResearch={() => setIsDeepResearch(!isDeepResearch)}
          onToggleThinking={() => setIsDeepThinking(!isDeepThinking)}
          onToggleImageGen={() => setIsImageGen(!isImageGen)}
          onToggleRag={() => setUseRag(!useRag)}
          onToggleModelDropdown={() => setShowModelDropdown(!showModelDropdown)}
          onToggleToolsMenu={() => setShowToolsMenu(!showToolsMenu)}
          onToggleRecording={toggleRecording}
          onSelectModel={setSelectedModel}
          onRemoveImage={() => setSelectedImage(null)}
          onRemoveFile={() => setSelectedFile(null)}
          onFileSelected={(file) => {
            if (file.type.startsWith("image/")) {
              const reader = new FileReader();
              reader.onloadend = () => setSelectedImage(reader.result as string);
              reader.readAsDataURL(file);
            } else {
              const formData = new FormData(); formData.append("file", file);
              axios.post("/rag/upload", formData, { headers: { Authorization: `Bearer ${token}` } }).then(() => { setSelectedFile({ name: file.name, type: file.type }); setUseRag(true); }).catch(e => alert("Upload failed"));
            }
          }}
          setShowToolsMenu={setShowToolsMenu} setShowModelDropdown={setShowModelDropdown}
        />
      </div>
      <SubscriptionGate isOpen={false} onClose={() => {}} />
    </div>
    </LazyMotion>
  );
}

