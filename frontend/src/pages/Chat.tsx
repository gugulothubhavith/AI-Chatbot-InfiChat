import React, { useState, useRef, useEffect } from "react";
import { Logo } from "../components/Logo";
import { useAuth } from "../hooks/useAuth";
import { useParams, useNavigate } from "react-router-dom";
import axios from "axios";
import ReactMarkdown from "react-markdown";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { atomDark } from "react-syntax-highlighter/dist/esm/styles/prism";
import {
  Send,
  Bot,
  User,
  RefreshCw,
  Mic,
  FileText,
  Square,
  Plus,
  Volume2,
  Loader2,
  Copy,
  Check,
  ThumbsUp,
  ThumbsDown,
  Share2,
  Pencil,
} from "lucide-react";
import { Button } from "../components/ui/Button";
import { Input } from "../components/ui/Input";
import { TypingIndicator } from "../components/ui/TypingIndicator";
import { cn } from "../lib/utils";

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

const MODELS = [
  {
    id: "llama-3.3-70b-versatile",
    name: "Llama 3.3 (70B) - Groq",
    description: "Ultra-fast general intelligence",
  },
  {
    id: "planner_agent",
    name: "Multi-Agent Squad",
    description: "Planner -> Coder -> Reviewer workflow",
  },
  {
    id: "gemini-3-flash-preview",
    name: "Gemini 3 (Flash) - Google",
    description: "Latest Vision-capable model",
  },
  {
    id: "deepseek/deepseek-chat",
    name: "DeepSeek V3",
    description: "Advanced reasoning and coding",
  },
  {
    id: "llama-3.1-8b-instant",
    name: "Llama 3.1 (8B)",
    description: "Instant responses",
  },
];

function DocumentCard({ name, type, isUser }: { name: string; type: string; isUser: boolean }) {
  return (
    <div className={cn(
      "flex items-center gap-3 p-3 rounded-[18px] border max-w-[300px] transition-all",
      isUser 
        ? "bg-white dark:bg-gray-900 border-gray-200 dark:border-gray-700 shadow-sm"
        : "bg-gray-50 dark:bg-gray-800 border-gray-200 dark:border-gray-700"
    )}>
      <div className="h-10 w-10 rounded-xl bg-red-500/10 flex items-center justify-center shrink-0">
        <FileText className="h-5 w-5 text-red-500" />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-[13px] font-semibold text-gray-900 dark:text-gray-100 truncate">{name}</p>
        <p className="text-[11px] text-gray-500 dark:text-gray-400 font-medium uppercase">{type.split("/")[1]?.toUpperCase() || "FILE"}</p>
      </div>
    </div>
  );
}

export default function Chat() {
  const { token, user } = useAuth();
  const { sessionId } = useParams();
  const navigate = useNavigate();

  console.log("DEBUG: Chat component user data:", user);

  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [selectedImage, setSelectedImage] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<{ name: string; type: string } | null>(null);
  const [loading, setLoading] = useState(false);
  const [selectedModel, setSelectedModel] = useState(MODELS[0].id);
  const [useRag, setUseRag] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [isTtsPlaying, setIsTtsPlaying] = useState(false);
  const [isTtsLoading, setIsTtsLoading] = useState(false);
  const [settings, setSettings] = useState<any>({
    textToSpeech: false,
    autoSendVoice: true,
    selectedVoice: "en_professional_male",
    theme: "system",
  });

  const [copiedMsgIdx, setCopiedMsgIdx] = useState<number | null>(null);
  const [likedMsgIdx, setLikedMsgIdx] = useState<number | null>(null);
  const [dislikedMsgIdx, setDislikedMsgIdx] = useState<number | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const utteranceRef = useRef<SpeechSynthesisUtterance | null>(null);
  const loadedSessionIdRef = useRef<string | null>(null);
  const ttsAbortRef = useRef<AbortController | null>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    inputRef.current?.focus();
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      const res = await axios.get("/api/settings", {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.data) {
        setSettings((prev: any) => ({ ...prev, ...res.data }));
      }
    } catch (err) {
      console.error("Failed to fetch settings", err);
    }
  };

  // Sync with URL sessionId
  useEffect(() => {
    if (sessionId) {
      if (sessionId !== loadedSessionIdRef.current) {
        loadMessages(sessionId);
      }
    } else {
      setMessages([]);
      loadedSessionIdRef.current = null;
    }
  }, [sessionId]);

  const loadMessages = async (sid: string) => {
    setLoading(true);
    try {
      const res = await axios.get(`/api/chat/sessions/${sid}/messages`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setMessages(
        res.data.map((m: any) => ({
          ...m,
          timestamp: new Date(m.created_at),
        })),
      );

      loadedSessionIdRef.current = sid;

    } catch (err) {
      console.error("Failed to load messages", err);
    } finally {
      setLoading(false);
    }
  };

  const toggleRecording = async () => {
    if (isRecording) {
      mediaRecorderRef.current?.stop();
      setIsRecording(false);
    } else {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          audio: true,
        });
        const mediaRecorder = new MediaRecorder(stream);
        mediaRecorderRef.current = mediaRecorder;
        const chunks: Blob[] = [];

        mediaRecorder.ondataavailable = (e) => chunks.push(e.data);
        mediaRecorder.onstop = async () => {
          const mimeType = mediaRecorder.mimeType || "audio/webm";
          const blob = new Blob(chunks, { type: mimeType });

          // Determine realistic file extension
          let ext = "webm";
          if (mimeType.includes("mp4")) ext = "mp4";
          if (mimeType.includes("ogg")) ext = "ogg";

          const formData = new FormData();
          formData.append("file", blob, `recording.${ext}`);

          setLoading(true);
          try {
            const res = await axios.post("/api/voice/transcribe", formData, {
              headers: { Authorization: `Bearer ${token}` },
            });

            const text = res.data.text;
            const storedSettings = localStorage.getItem("chatSettings");
            const settings = storedSettings ? JSON.parse(storedSettings) : {};

            if (settings.autoSendVoice) {
              // If auto-send is on, send immediately without updating input field state (avoid conflict)
              // Use current input state + transcribed text
              handleSendMessage({
                overrideText: input ? input + " " + text : text,
              });
            } else {
              setInput((prev) => (prev ? prev + " " + text : text));
            }
          } catch (err: any) {
            console.error("Transcription failed", err);
          } finally {
            setLoading(false);
            stream.getTracks().forEach((track) => track.stop());
          }
        };

        mediaRecorder.start();
        setIsRecording(true);
      } catch (err) {
        console.error("Microphone access denied", err);
        alert("Could not access microphone.");
      }
    }
  };

  const handleSendMessage = async (customConfig?: {
    overrideModel?: string;
    overrideText?: string;
  }) => {
    // Stop any ongoing TTS before sending new message
    stopTts();

    const textToSend = customConfig?.overrideText || input;

    if ((!textToSend.trim() && !selectedImage) || loading) return;

    const storedSettings = localStorage.getItem("chatSettings");
    const settings = storedSettings ? JSON.parse(storedSettings) : {};

    // Explicit model from UI selector or Settings
    const activeModel =
      customConfig?.overrideModel ||
      selectedModel ||
      settings.activeModel ||
      "llama-3.1-8b-instant";

    const userMessage: Message = {
      role: "user",
      content: textToSend,
      timestamp: new Date(),
      image: selectedImage || undefined,
      file_name: selectedFile?.name || undefined,
      file_type: selectedFile?.type || undefined,
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setSelectedImage(null);
    setSelectedFile(null);
    setLoading(true);

    try {
      const response = await fetch("/api/chat/stream", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          messages: messages.concat(userMessage).map((m) => ({
            role: m.role,
            content: m.content,
            image: m.image,
            file_name: m.file_name,
            file_type: m.file_type,
          })),
          conversation_id:
            sessionId && sessionId !== "undefined" ? sessionId : null,
          system_prompt: settings.systemPrompt,
          temperature: settings.temperature,
          max_tokens: settings.maxTokens,
          top_p: settings.topP,
          frequency_penalty: settings.frequencyPenalty,
          presence_penalty: settings.presencePenalty,
          history_limit:
            settings.historyLimit === 0 ? null : settings.historyLimit,

          model: activeModel, // Pass the selected model
          use_rag: useRag,
          workspace: localStorage.getItem("activeWorkspace") || "personal",
        }),
      });

      // Clear RAG flag after one use if it was active
      if (useRag) setUseRag(false);

      if (!response.ok) {
        const errorText = await response.text();
        let errorMessage = `Stream request failed: ${response.status} ${response.statusText}`;
        try {
          const errorJson = JSON.parse(errorText);
          errorMessage += ` - ${JSON.stringify(errorJson, null, 2)}`;
        } catch {
          errorMessage += ` - ${errorText}`;
        }
        throw new Error(errorMessage);
      }

      // Get session ID from header (important for first message)
      const newSid = response.headers.get("X-Chat-Session-ID");
      if (newSid && newSid !== sessionId) {
        loadedSessionIdRef.current = newSid;
        navigate(`/${newSid}`, { replace: true });
      }

      const reader = response.body?.getReader();
      if (!reader) throw new Error("No reader");

      const assistantMessage: Message = {
        role: "assistant",
        content: "",
        model: activeModel,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, assistantMessage]);

      const decoder = new TextDecoder();
      let fullContent = "";
      let streamBuffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        streamBuffer += decoder.decode(value, { stream: true });

        // SSE events are separated by double newlines (\n\n)
        const parts = streamBuffer.split("\n\n");
        // Keep the last partial event in the buffer
        streamBuffer = parts.pop() || "";

        for (const line of parts) {
          const trimmedLine = line.trim();
          if (trimmedLine.startsWith("data: ")) {
            const text = trimmedLine.slice(6);
            try {
              const data = JSON.parse(text);
              if (data && typeof data.content === "string") {
                fullContent += data.content;
              } else if (typeof data === "string") {
                fullContent += data;
              }
            } catch (e) {
              // Fallback for non-JSON or partial JSON (though buffer should prevent this)
              console.warn("Failed to parse SSE chunk", text);
            }

            setMessages((prev) => {
              const newMsgs = [...prev];
              newMsgs[newMsgs.length - 1].content = fullContent;
              return newMsgs;
            });
          }
        }
      }

      // Final flush for any remaining data in the buffer
      if (streamBuffer.trim().startsWith("data: ")) {
        const text = streamBuffer.trim().slice(6);
        try {
          const data = JSON.parse(text);
          if (data && typeof data.content === "string") {
            fullContent += data.content;
          } else if (typeof data === "string") {
            fullContent += data;
          }
        } catch (e) {
          console.warn("Dangling stream buffer failed to parse", text);
        }

        setMessages((prev) => {
          const newMsgs = [...prev];
          newMsgs[newMsgs.length - 1].content = fullContent;
          return newMsgs;
        });
      }

          // Text-to-Speech (Unreal Speech V8 Backend)
      if (settings.textToSpeech && fullContent) {
        try {
          // Initialize AudioContext immediately to satisfy browser auto-play gesture requirements
          const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)({ sampleRate: 24000 });
          if (audioContext.state === 'suspended') {
              audioContext.resume();
          }

          const ttsRes = await fetch("/api/voice/tts", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              "Authorization": `Bearer ${token}`
            },
            body: JSON.stringify({ text: fullContent, voice_id: settings.selectedVoice || "af_sky" })
          });
          
          if (!ttsRes.ok) throw new Error("Auto TTS streaming failed");

          setIsTtsPlaying(true);
          const reader = ttsRes.body?.getReader();
          if (!reader) throw new Error("Stream unreachable");

          let nextStartTime = audioContext.currentTime;
          let byteBuffer = new Uint8Array(0);

          const playChunk = (chunkBytes: Uint8Array) => {
              const floats = new Float32Array(chunkBytes.buffer, chunkBytes.byteOffset, chunkBytes.byteLength / 4);
              const audioBuffer = audioContext.createBuffer(1, floats.length, 24000);
              audioBuffer.getChannelData(0).set(floats);
              
              const source = audioContext.createBufferSource();
              source.buffer = audioBuffer;
              source.connect(audioContext.destination);
              
              if (nextStartTime < audioContext.currentTime) {
                  nextStartTime = audioContext.currentTime + 0.01; // Tiny buffer if we are underrunning
              }
              source.start(nextStartTime);
              nextStartTime += audioBuffer.duration;
              
              audioRef.current = { pause: () => { 
                  if (audioContext.state !== 'closed') audioContext.close(); 
              } } as unknown as HTMLAudioElement;
          };

          while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            
            const newBuffer = new Uint8Array(byteBuffer.length + value.length);
            newBuffer.set(byteBuffer);
            newBuffer.set(value, byteBuffer.length);
            byteBuffer = newBuffer;

            // Stream in extremely fast ~50ms chunks (4800 bytes = 1200 floats) for near zero latency
            // But respond even faster for the FIRST chunk (25ms = 2400 bytes)
            const minChunkSize = byteBuffer.length === value.length ? 2400 : 4800;
            while (byteBuffer.length >= minChunkSize) {
              playChunk(byteBuffer.slice(0, minChunkSize));
              byteBuffer = byteBuffer.slice(minChunkSize);
            }
          }

          // Play remainder bytes properly aligned to float32 bounds
          const remainder = byteBuffer.length - (byteBuffer.length % 4);
          if (remainder > 0) {
              playChunk(byteBuffer.slice(0, remainder));
          }

          setTimeout(() => {
              setIsTtsPlaying(false);
              audioRef.current = null;
              if (audioContext.state !== 'closed') {
                  audioContext.close();
              }
          }, Math.max(0, (nextStartTime - audioContext.currentTime) * 1000));

        } catch (ttsErr) {
          console.error(
            "Backend TTS failed, falling back to browser...",
            ttsErr,
          );
          const utterance = new SpeechSynthesisUtterance(fullContent);
          utteranceRef.current = utterance;
          setIsTtsPlaying(true);

          utterance.onend = () => {
            setIsTtsPlaying(false);
            utteranceRef.current = null;
          };

          utterance.onerror = () => {
            setIsTtsPlaying(false);
            utteranceRef.current = null;
          };

          window.speechSynthesis.speak(utterance);
        }
      }
    } catch (err: any) {
      console.error("Chat error", err);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "Error: " + err.message,
          timestamp: new Date(),
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const playMessageTts = async (text: string) => {
    if (isTtsPlaying) {
      stopTts();
      return;
    }

    // Show loading spinner immediately on button click
    setIsTtsLoading(true);
    
    // Create abort controller for this request so user can cancel mid-loading
    const abortController = new AbortController();
    ttsAbortRef.current = abortController;
    
    try {
        const ttsRes = await fetch("/api/voice/tts", {
          method: "POST",
          signal: abortController.signal,
          headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${token}`
          },
          body: JSON.stringify({ text, voice_id: settings.selectedVoice || "en_professional_male" })
        });

        if (!ttsRes.ok) throw new Error("TTS streaming failed");

        // High-fidelity MP3 Streaming implementation
        const mediaSource = new MediaSource();
        const url = URL.createObjectURL(mediaSource);
        const audio = new Audio(url);
        audioRef.current = audio;
        
        setIsTtsLoading(false);
        setIsTtsPlaying(true);

        mediaSource.addEventListener("sourceopen", async () => {
            const sourceBuffer = mediaSource.addSourceBuffer("audio/mpeg");
            const reader = ttsRes.body?.getReader();
            if (!reader) return;

            try {
                // Initial buffer to start playback quickly
                let hasStarted = false;
                
                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;
                    
                    // Add chunk to source buffer
                    // We must wait for the buffer to not be updating before appending
                    await new Promise<void>((resolve) => {
                        if (!sourceBuffer.updating) {
                            sourceBuffer.appendBuffer(value);
                            resolve();
                        } else {
                            const onUpdateEnd = () => {
                                sourceBuffer.removeEventListener("updateend", onUpdateEnd);
                                sourceBuffer.appendBuffer(value);
                                resolve();
                            };
                            sourceBuffer.addEventListener("updateend", onUpdateEnd);
                        }
                    });

                    if (!hasStarted && audio.paused) {
                        try {
                            await audio.play();
                            hasStarted = true;
                        } catch (playErr) {
                            // Interaction required or other play error
                            console.warn("Auto-play blocked, waiting for chunk", playErr);
                        }
                    }
                }
                
                // Signal end of stream when fully read
                if (mediaSource.readyState === "open") {
                    mediaSource.endOfStream();
                }
            } catch (err) {
                console.error("Streaming error", err);
                if (mediaSource.readyState === "open") mediaSource.endOfStream();
            }
        });

        audio.onended = () => {
            setIsTtsPlaying(false);
            audioRef.current = null;
            URL.revokeObjectURL(url);
        };

        audio.onerror = (e) => {
            console.error("Audio element error", e);
            setIsTtsPlaying(false);
            audioRef.current = null;
            URL.revokeObjectURL(url);
        };

    } catch (ttsErr: any) {
      setIsTtsLoading(false);
      setIsTtsPlaying(false);
      
      // If was cancelled intentionally by user, don't fall back to browser TTS
      if (ttsErr?.name === 'AbortError') {
        console.log("TTS cancelled by user.");
        return;
      }
      
      console.error("Backend TTS failed, falling back to browser...", ttsErr);
      const utterance = new SpeechSynthesisUtterance(text);
      utteranceRef.current = utterance;
      setIsTtsPlaying(true);

      utterance.onend = () => {
        setIsTtsPlaying(false);
        utteranceRef.current = null;
      };

      utterance.onerror = () => {
        setIsTtsPlaying(false);
        utteranceRef.current = null;
      };

      window.speechSynthesis.speak(utterance);
    }
  };

  const stopTts = () => {
    // Abort any in-flight TTS fetch (cancels loading phase)
    if (ttsAbortRef.current) {
      ttsAbortRef.current.abort();
      ttsAbortRef.current = null;
    }
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current = null;
    }
    if (window.speechSynthesis.speaking) {
      window.speechSynthesis.cancel();
      utteranceRef.current = null;
    }
    setIsTtsPlaying(false);
    setIsTtsLoading(false);
  };

  const handleCopy = (text: string, idx: number) => {
    navigator.clipboard.writeText(text);
    setCopiedMsgIdx(idx);
    setTimeout(() => setCopiedMsgIdx(null), 2000);
  };

  const handleShare = (text: string) => {
    if (navigator.share) {
      navigator.share({ text });
    } else {
      navigator.clipboard.writeText(text);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="flex flex-col h-full bg-white dark:bg-[#0B0B0B] text-gray-900 dark:text-gray-100 overflow-hidden transition-colors duration-300">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 bg-white/80 dark:bg-[#0B0B0B]/50 backdrop-blur-md sticky top-0 z-10">
        <div className="flex items-center gap-3">
          <Logo hideIcon={true} nameSize={22} />
        </div>

        <div className="flex items-center gap-4">
          <select
            value={selectedModel}
            onChange={(e) => setSelectedModel(e.target.value)}
            className="bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 text-sm rounded-lg block px-3 py-2 focus:ring-cyan-500 focus:border-cyan-500 text-gray-900 dark:text-white outline-none"
          >
            {MODELS.map((m) => (
              <option key={m.id} value={m.id}>
                {m.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div
        className={cn(
          "flex flex-col flex-1 overflow-hidden",
          messages.length === 0 ? "justify-center" : "",
        )}
      >
        {/* Messages Area */}
        <div
          className={cn(
            "overflow-y-auto p-4 md:p-6 space-y-6 scrollbar-thin scrollbar-thumb-gray-200 dark:scrollbar-thumb-gray-800 scrollbar-track-transparent",
            messages.length === 0 ? "flex-none h-auto !p-0" : "flex-1",
          )}
        >
          {messages.length === 0 ? (
            <div
              className="flex flex-col items-center justify-center text-center px-8 opacity-0 animate-in fade-in slide-in-from-bottom-4 duration-500 fill-mode-forwards"
              style={{ animationDelay: "0.1s", opacity: 1 }}
            >
              <h2 className="text-3xl md:text-4xl font-normal tracking-tight text-gray-900 dark:text-gray-100 font-sans mb-[1cm]">
                What can I help with?
              </h2>
            </div>
          ) : (
            messages.filter(msg => msg.role !== "system").map((msg, idx) => (
                <div
                  key={idx}
                  className={cn(
                    "flex gap-4 max-w-4xl mx-auto group animate-in fade-in slide-in-from-bottom-2 duration-300",
                    msg.role === "user" ? "flex-row-reverse" : "flex-row",
                  )}
                >
                  <div
                    className={cn(
                      "h-8 w-8 rounded-full flex items-center justify-center shrink-0 mt-1 shadow-md overflow-hidden",
                      msg.role === "user"
                        ? "bg-gray-100 dark:bg-gray-800"
                        : "bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-gray-700",
                    )}
                  >
                    {msg.role === "user" ? (
                      user?.picture ? (
                        <img
                          src={user.picture}
                          alt="User"
                          className="h-full w-full object-cover"
                        />
                      ) : (
                        <User className="h-5 w-5 text-gray-500" />
                      )
                    ) : (
                      <Bot className="h-5 w-5 text-gray-600 dark:text-gray-400" />
                    )}
                  </div>

                  <div
                    className={cn(
                      "flex flex-col max-w-[85%]",
                      msg.role === "user" ? "items-end" : "items-start",
                    )}
                  >
                    <div
                      className={cn(
                        "px-4 py-2.5 rounded-2xl text-sm leading-relaxed relative",
                        msg.role === "user"
                          ? "bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-gray-100"
                          : "bg-transparent text-gray-800 dark:text-gray-200",
                      )}
                    >
                      {msg.image && (
                        <div className="mb-4 -mx-1 p-2 bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm">
                          <img
                            src={msg.image}
                            alt="Uploaded"
                            className="rounded-lg max-h-[320px] w-auto transition-shadow duration-200"
                          />
                        </div>
                      )}

                      {msg.file_name && (
                        <div className="mb-4">
                          <DocumentCard 
                            name={msg.file_name} 
                            type={msg.file_type || "file"} 
                            isUser={msg.role === "user"}
                          />
                        </div>
                      )}
                      {msg.content ? (
                        <ReactMarkdown
                          components={{
                            code(props) {
                              const { children, className, node, ...rest } =
                                props;
                              const match = /language-(\w+)/.exec(
                                className || "",
                              );
                              return match ? (
                                <div className="rounded-md overflow-hidden my-3 border border-gray-700/50 bg-[#1e1e1e]">
                                  <div className="bg-[#2d2d2d] px-3 py-1 text-xs text-gray-400 border-b border-gray-700/50 flex justify-between items-center">
                                    <span>{match[1]}</span>
                                  </div>
                                  <SyntaxHighlighter
                                    style={atomDark}
                                    language={match[1]}
                                    PreTag="div"
                                    customStyle={{
                                      margin: 0,
                                      padding: "1rem",
                                      background: "transparent",
                                    }}
                                    {...(rest as any)}
                                  >
                                    {String(children).replace(/\n$/, "")}
                                  </SyntaxHighlighter>
                                </div>
                              ) : (
                                <code
                                  className={cn(
                                    "bg-gray-700/50 px-1.5 py-0.5 rounded text-xs font-mono text-cyan-200",
                                    className,
                                  )}
                                  {...rest}
                                >
                                  {children}
                                </code>
                              );
                            },
                          }}
                        >
                          {msg.content}
                        </ReactMarkdown>
                      ) : (
                        <TypingIndicator />
                      )}
                    </div>
                    {msg.role === "user" && msg.content && (
                      <div className="flex justify-end w-full mt-1.5 mr-1 gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity">
                        <button
                          onClick={() => handleCopy(msg.content, idx)}
                          className="p-1 text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800/60 rounded-md transition-colors"
                          title="Copy"
                        >
                          {copiedMsgIdx === idx ? (
                            <Check className="w-3.5 h-3.5 text-green-500" />
                          ) : (
                            <Copy className="w-3.5 h-3.5" />
                          )}
                        </button>
                        <button
                          onClick={() => {
                            setInput(msg.content);
                            inputRef.current?.focus();
                          }}
                          className="p-1 text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800/60 rounded-md transition-colors"
                          title="Edit"
                        >
                          <Pencil className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    )}
                    {msg.role === "assistant" && msg.content && idx === messages.length - 1 && !loading && (
                        <div className="flex justify-start w-full mt-1.5 ml-1 gap-0.5">
                          {/* Copy */}
                          <button
                            onClick={() => handleCopy(msg.content, idx)}
                            className="p-1.5 text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800/60 rounded-md transition-colors"
                            title="Copy"
                          >
                            {copiedMsgIdx === idx ? (
                              <Check className="w-4 h-4 text-green-500" />
                            ) : (
                              <Copy className="w-4 h-4" />
                            )}
                          </button>

                          {/* Thumbs Up */}
                          <button
                            onClick={() => setLikedMsgIdx(likedMsgIdx === idx ? null : idx)}
                            className={cn(
                              "p-1.5 rounded-md transition-colors",
                              likedMsgIdx === idx
                                ? "text-green-500 bg-green-500/10"
                                : "text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800/60"
                            )}
                            title="Good response"
                          >
                            <ThumbsUp className={cn("w-4 h-4", likedMsgIdx === idx && "fill-current")} />
                          </button>

                          {/* Thumbs Down */}
                          <button
                            onClick={() => setDislikedMsgIdx(dislikedMsgIdx === idx ? null : idx)}
                            className={cn(
                              "p-1.5 rounded-md transition-colors",
                              dislikedMsgIdx === idx
                                ? "text-red-500 bg-red-500/10"
                                : "text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800/60"
                            )}
                            title="Bad response"
                          >
                            <ThumbsDown className={cn("w-4 h-4", dislikedMsgIdx === idx && "fill-current")} />
                          </button>

                          {/* Share */}
                          <button
                            onClick={() => handleShare(msg.content)}
                            className="p-1.5 text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800/60 rounded-md transition-colors"
                            title="Share"
                          >
                            <Share2 className="w-4 h-4" />
                          </button>

                          {/* Regenerate — only on last assistant message */}
                          {idx === messages.length - 1 && !loading && (
                            <button
                              onClick={() => handleSendMessage({ overrideText: messages.filter(m => m.role === "user").slice(-1)[0]?.content || "" })}
                              className="p-1.5 text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800/60 rounded-md transition-colors"
                              title="Regenerate response"
                            >
                              <RefreshCw className="w-4 h-4" />
                            </button>
                          )}

                          {/* TTS — only on last assistant message */}
                          {idx === messages.length - 1 && !loading && (
                            <button
                              onClick={() =>
                                (isTtsLoading || isTtsPlaying)
                                  ? stopTts()
                                  : playMessageTts(msg.content)
                              }
                              className="p-1.5 text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800/60 rounded-md transition-colors"
                              title={isTtsLoading ? "Cancel" : isTtsPlaying ? "Stop reading" : "Read aloud"}
                            >
                              {isTtsLoading ? (
                                <span className="relative flex items-center justify-center w-4 h-4">
                                  <Loader2 className="w-4 h-4 animate-spin text-blue-500 absolute" />
                                  <span className="text-[7px] font-bold text-blue-500">✕</span>
                                </span>
                              ) : isTtsPlaying ? (
                                <Square className="w-4 h-4 fill-current" />
                              ) : (
                                <Volume2 className="w-4 h-4" />
                              )}
                            </button>
                          )}
                        </div>
                      )}
                  </div>
                </div>
              ),
            )
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div
          className={cn(
            "p-4 w-full",
            messages.length === 0
              ? "bg-transparent !py-0"
              : "bg-white dark:bg-[#0B0B0B]",
          )}
        >
          <div className="max-w-4xl mx-auto relative flex justify-center">
            <div className="w-[85%] relative flex flex-col">
              {/* Attachment Preview (Above Input) */}
              {(selectedImage || selectedFile) && (
                <div className="flex px-4 py-2 animate-in fade-in slide-in-from-bottom-2 duration-200">
                  {selectedImage ? (
                    <div className="relative group p-2 bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm">
                      <div className="h-14 w-14 rounded-lg overflow-hidden relative">
                        <img
                          src={selectedImage}
                          alt="Preview"
                          className="h-full w-full object-cover transition-transform group-hover:scale-110 duration-300"
                        />
                      </div>
                      <button
                        onClick={() => setSelectedImage(null)}
                        className="absolute -top-1.5 -right-1.5 bg-gray-900 dark:bg-gray-100 text-white dark:text-gray-900 rounded-full p-1 shadow-md hover:scale-110 active:scale-95 transition-all z-10"
                        title="Remove attachment"
                      >
                        <Plus className="h-3 w-3 rotate-45" />
                      </button>
                    </div>
                  ) : (
                    <div className="relative group">
                      <DocumentCard name={selectedFile!.name} type={selectedFile!.type} isUser={true} />
                      <button
                        onClick={() => setSelectedFile(null)}
                        className="absolute -top-1.5 -right-1.5 bg-gray-900 dark:bg-gray-100 text-white dark:text-gray-900 rounded-full p-1 shadow-md hover:scale-110 active:scale-95 transition-all z-10"
                        title="Remove attachment"
                      >
                        <Plus className="h-3 w-3 rotate-45" />
                      </button>
                    </div>
                  )}
                </div>
              )}

              <div className="relative">
                <Input
                  ref={inputRef}
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  disabled={loading}
                  placeholder="Send a message..."
                  className="w-full pl-12 pr-[92px] py-3 bg-gray-50 dark:bg-gray-900/50 border-gray-200 dark:border-gray-700 text-sm shadow-sm rounded-full focus:ring-gray-400/50 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500"
                />

                <div className="absolute left-2 top-2 bottom-2 flex items-center gap-1">
                  <input
                    type="file"
                    id="chat-upload"
                    className="hidden"
                    accept="image/*,.pdf,.txt,.doc,.docx"
                    onChange={async (e) => {
                      if (e.target.files && e.target.files[0]) {
                        const file = e.target.files[0];

                        // 1. Handle Image Upload (Vision)
                        if (file.type.startsWith("image/")) {
                          const reader = new FileReader();
                          reader.onloadend = () =>
                            setSelectedImage(reader.result as string);
                          reader.readAsDataURL(file);
                          e.target.value = "";
                          return;
                        }

                        // 2. Handle Document Upload (RAG)
                        setLoading(true);
                        let activeSid = sessionId;

                        if (!activeSid || activeSid === "undefined") {
                          try {
                            const sessRes = await axios.post(
                              "/api/chat/sessions",
                              {},
                              {
                                headers: { Authorization: `Bearer ${token}` },
                              },
                            );
                            activeSid = sessRes.data.id;
                            navigate(`/${activeSid}`, { replace: true });
                            loadedSessionIdRef.current = activeSid ?? null;
                          } catch (err) {
                            console.error(
                              "Failed to create session for document upload",
                              err,
                            );
                          }
                        }

                        const formData = new FormData();
                        formData.append("file", file);
                        if (activeSid)
                          formData.append("conversation_id", activeSid);

                        try {
                          await axios.post("/api/rag/upload", formData, {
                            headers: { Authorization: `Bearer ${token}` },
                          });
                          setSelectedFile({ name: file.name, type: file.type });
                          if (activeSid) await loadMessages(activeSid);
                        } catch (err: any) {
                          console.error("Upload failed", err);
                          alert(
                            `Failed to upload document: ${err.response?.data?.detail || err.message}`,
                          );
                        } finally {
                          setLoading(false);
                          e.target.value = "";
                        }
                      }
                    }}
                  />
                  <label
                    htmlFor="chat-upload"
                    className={cn(
                      "h-8 w-8 flex items-center justify-center rounded-full cursor-pointer transition-all",
                      selectedImage || useRag
                        ? "text-gray-900 dark:text-white bg-gray-200 dark:bg-gray-700"
                        : "text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 hover:bg-gray-200 dark:hover:bg-gray-800",
                    )}
                  >
                    <Plus className="h-5 w-5" />
                  </label>
                </div>

                <div className="absolute right-2 top-1.5 bottom-1.5 flex items-center gap-1">
                  <button
                    onClick={toggleRecording}
                    className={cn(
                      "h-8 w-8 flex items-center justify-center rounded-full",
                      isRecording
                        ? "text-red-500 bg-red-500/10 animate-pulse"
                        : "text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-800",
                    )}
                  >
                    <Mic className="h-4 w-4" />
                  </button>
                  <Button
                    size="icon"
                    variant={input.trim() || selectedImage ? "premium" : "ghost"}
                    className="h-9 w-9 rounded-full"
                    disabled={(!input.trim() && !selectedImage) || loading}
                    onClick={() => handleSendMessage()}
                  >
                    {loading ? (
                      <RefreshCw className="h-4 w-4 animate-spin" />
                    ) : (
                      <Send className="h-4 w-4" />
                    )}
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
