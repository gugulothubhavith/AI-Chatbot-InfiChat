import React, { useRef } from "react";
import { m, LazyMotion, domAnimation, AnimatePresence } from "framer-motion";
import {
  PaperPlaneRight, Microphone, Plus, PencilSimple, FadersHorizontal, Globe, Image, Brain,
  BookOpen, CaretDown, ArrowsClockwise, FileText,
} from "@phosphor-icons/react";
import { cn } from "../lib/utils";
import { TokenUsageBadge } from "./TokenUsageBadge";

const MODELS = [
  { id: "nvidia/nemotron-3-ultra-550b-a55b", name: "Nemotron 3 Ultra (550B)", description: "Advanced reasoning with thinking capability" },
  { id: "meta/llama-3.1-70b-instruct", name: "Llama 3.1 (70B) Instruct", description: "Advanced conversational model" },
  { id: "openai/gpt-oss-120b", name: "GPT OSS (120B)", description: "High-speed reasoning and coding" },
];

interface ChatInputProps {
  input: string;
  setInput: (val: string) => void;
  loading: boolean;
  isWebSearch: boolean;
  isDeepResearch: boolean;
  isDeepThinking: boolean;
  isImageGen: boolean;
  useRag: boolean;
  selectedImage: string | null;
  selectedFile: { name: string; type: string } | null;
  selectedModel: string;
  showModelDropdown: boolean;
  showToolsMenu: boolean;
  isRecording: boolean;
  onSend: (config?: any) => void;
  onKeyDown: (e: React.KeyboardEvent) => void;
  onToggleWebSearch: () => void;
  onToggleResearch: () => void;
  onToggleThinking: () => void;
  onToggleImageGen: () => void;
  onToggleRag: () => void;
  onToggleModelDropdown: () => void;
  onToggleToolsMenu: () => void;
  onToggleRecording: () => void;
  onSelectModel: (id: string) => void;
  onRemoveImage: () => void;
  onRemoveFile: () => void;
  onFileSelected: (file: File) => void;
  setShowToolsMenu: (val: boolean) => void;
  setShowModelDropdown: (val: boolean) => void;
}

function DocumentCard({ name, type, isUser }: { name: string; type: string; isUser: boolean }) {
  return (
    <div className={cn("flex items-center gap-3 p-3 rounded-[18px] border max-w-[300px] transition-all",
      isUser ? "bg-white dark:bg-gray-900 border-gray-200 dark:border-gray-700 shadow-sm" : "bg-gray-50 dark:bg-gray-800 border-gray-200 dark:border-gray-700"
    )}>
      <div className="h-10 w-10 rounded-xl bg-red-500/10 flex items-center justify-center shrink-0"><FileText className="h-5 w-5 text-red-500" weight="fill" /></div>
      <div className="flex-1 min-w-0">
        <p className="text-[13px] font-semibold text-gray-900 dark:text-gray-100 truncate">{name}</p>
        <p className="text-[11px] text-gray-500 dark:text-gray-400 font-medium uppercase">{type.split("/")[1]?.toUpperCase() || "FILE"}</p>
      </div>
    </div>
  );
}

export function ChatInput({
  input, setInput, loading,
  isWebSearch,
  isDeepResearch,
  isDeepThinking,
  isImageGen,
  useRag,
  selectedImage,
  selectedFile,
  selectedModel,
  showModelDropdown,
  showToolsMenu,
  isRecording,
  onSend,
  onKeyDown,
  onToggleWebSearch,
  onToggleResearch,
  onToggleThinking, onToggleImageGen, onToggleRag,
  onToggleModelDropdown, onToggleToolsMenu, onToggleRecording, onSelectModel,
  onRemoveImage, onRemoveFile, onFileSelected, setShowToolsMenu, setShowModelDropdown,
}: ChatInputProps) {
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const activeModeShadow = isDeepResearch
    ? "0 0 0 1.5px oklch(0.600 0.200 300), 0 8px 32px -8px oklch(0.600 0.200 300 / 0.5)"
    : isDeepThinking
      ? "0 0 0 1.5px oklch(0.600 0.200 150), 0 8px 32px -8px oklch(0.600 0.200 150 / 0.5)"
      : isImageGen
        ? "0 0 0 1.5px oklch(0.650 0.250 15), 0 8px 32px -8px oklch(0.650 0.250 15 / 0.5)"
        : useRag
          ? "0 0 0 1.5px var(--color-info), 0 8px 32px -8px var(--color-info)"
          : "0 20px 40px -10px rgba(0,0,0,0.1), var(--shadow-island)";

  const selectedModelName = MODELS.find((m) => m.id === selectedModel)?.name || "Select Model";

  return (
<LazyMotion features={domAnimation}>
    <div className="absolute bottom-0 left-0 right-0 p-4 pb-6 w-full md:pb-8 pointer-events-none z-50 flex flex-col items-center justify-end"
      style={{ background: "linear-gradient(to top, var(--color-bg) 60%, transparent 100%)" }}>
      <div className="w-full max-w-3xl relative flex flex-col pointer-events-auto">

          {/* Attachments Preview */}
          <AnimatePresence>
            {(selectedImage || selectedFile) && (
              <m.div initial={{ opacity: 0, y: 15, scale: 0.95 }} animate={{ opacity: 1, y: 0, scale: 1 }} exit={{ opacity: 0, y: 15, scale: 0.95 }}
                className="flex px-4 py-3 mb-2 mx-2 rounded-2xl border backdrop-blur-xl shadow-lg"
                style={{ background: "color-mix(in srgb, var(--color-surface) 80%, transparent)", borderColor: "var(--color-border)" }}>
                {selectedImage ? (
                  <div className="relative group p-1.5 rounded-xl shadow-sm" style={{ background: "var(--color-surface)", border: "1px solid var(--color-border)" }}>
                    <div className="h-16 w-16 rounded-lg overflow-hidden relative">
                      <img src={selectedImage} alt="Preview" className="h-full w-full object-cover" />
                    </div>
                    <button onClick={onRemoveImage}
                      className="absolute -top-2 -right-2 rounded-full p-1.5 press-scale shadow-md"
                      style={{ background: "var(--color-text-primary)", color: "var(--color-bg)" }}>
                      <Plus className="h-3.5 w-3.5 rotate-45" weight="bold" />
                    </button>
                  </div>
                ) : (
                  <div className="relative group">
                    <DocumentCard name={selectedFile!.name} type={selectedFile!.type} isUser={true} />
                    <button onClick={onRemoveFile}
                      className="absolute -top-2 -right-2 rounded-full p-1.5 press-scale shadow-md"
                      style={{ background: "var(--color-text-primary)", color: "var(--color-bg)" }}>
                      <Plus className="h-3.5 w-3.5 rotate-45" weight="bold" />
                    </button>
                  </div>
                )}
              </m.div>
            )}
          </AnimatePresence>

          {/* Input Container */}
          <div className="rounded-[28px] transition-all duration-500 mx-2 shadow-2xl relative overflow-visible" 
            style={{ 
              background: "color-mix(in srgb, var(--color-surface) 85%, transparent)",
              backdropFilter: "blur(24px)",
              WebkitBackdropFilter: "blur(24px)",
              border: `1.5px solid ${isWebSearch || isDeepResearch || isDeepThinking || isImageGen || useRag ? "transparent" : "var(--color-border)"}`,
              boxShadow: activeModeShadow 
            }}>

              {/* Mode Indicators */}
              <AnimatePresence>
                {(isWebSearch || isDeepResearch || isDeepThinking || useRag || isImageGen) && (
                  <m.div initial={{ height: 0, opacity: 0 }} animate={{ height: "auto", opacity: 1 }} exit={{ height: 0, opacity: 0 }} className="flex items-center gap-2 px-4 pt-2.5 overflow-hidden">
                    {isWebSearch && <ModeChip icon={Globe} label="Web Search" color="oklch(0.600 0.200 250)" onClose={onToggleWebSearch} />}
                    {isDeepResearch && <ModeChip icon={Globe} label="Deep Research" color="oklch(0.600 0.200 300)" onClose={onToggleResearch} />}
                    {isDeepThinking && <ModeChip icon={Brain} label="Deep Thinking" color="oklch(0.600 0.200 150)" onClose={onToggleThinking} />}
                    {isImageGen && <ModeChip icon={Image} label="Image Generation" color="oklch(0.650 0.250 15)" onClose={onToggleImageGen} />}
                    {useRag && <ModeChip icon={BookOpen} label="Knowledge Base" color="var(--color-info)" onClose={onToggleRag} />}
                  </m.div>
                )}
              </AnimatePresence>

              {/* Textarea */}
              <textarea ref={inputRef} value={input} onChange={(e) => { setInput(e.target.value); e.target.style.height = "auto"; e.target.style.height = Math.min(e.target.scrollHeight, 200) + "px"; }}
                onKeyDown={onKeyDown} disabled={loading} placeholder="Ask anything..." rows={1}
                className="w-full bg-transparent text-base px-5 pt-4 pb-1 resize-none focus:outline-none focus:ring-0 focus:border-transparent border-none outline-none min-h-[48px] max-h-[200px]"
                style={{ color: "var(--color-text-primary)", fontFamily: "var(--font-sans)" }} />

              {/* Toolbar */}
              <div className="flex items-center justify-between px-3 pb-3 pt-1">
                <div className="flex items-center gap-1">
                  {/* File Upload */}
                  <input ref={fileInputRef} type="file" className="hidden" accept="image/*,.pdf,.txt,.doc,.docx"
                    onChange={(e) => { if (e.target.files?.[0]) onFileSelected(e.target.files[0]); }} />
                  <label htmlFor="chat-upload" onClick={() => fileInputRef.current?.click()}
                    className="h-8 w-8 flex items-center justify-center rounded-full cursor-pointer press-scale"
                    style={{ color: (selectedImage || useRag) ? "var(--color-text-on-accent)" : "var(--color-text-secondary)", background: (selectedImage || useRag) ? "var(--color-accent)" : "transparent" }}>
                    <Plus className="h-5 w-5" weight="bold" />
                  </label>

                  {/* Tools Menu */}
                  <div className="relative">
                    <button onClick={onToggleToolsMenu}
                      className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-xl press-scale"
                      style={{ color: (showToolsMenu || isDeepResearch || useRag) ? "var(--color-text-primary)" : "var(--color-text-secondary)" }}>
                      <FadersHorizontal className="h-4 w-4" weight="bold" /><span className="text-sm font-medium">Tools</span>
                    </button>
                    <AnimatePresence>
                      {showToolsMenu && (
                        <>
                          <div className="fixed inset-0 z-40" onClick={() => setShowToolsMenu(false)} />
                          <m.div initial={{ opacity: 0, y: 8, scale: 0.96 }} animate={{ opacity: 1, y: 0, scale: 1 }} exit={{ opacity: 0, y: 8, scale: 0.96 }}
                            className="absolute bottom-full left-0 mb-2 w-72 rounded-2xl z-50 py-2 glass-heavy"
                            style={{ border: "1px solid var(--color-border)", boxShadow: "var(--shadow-xl)" }}>
                            <div className="px-4 py-1.5 text-xs font-semibold uppercase tracking-wider" style={{ color: "var(--color-text-tertiary)" }}>Tools</div>
                            <ToolItem icon={Globe} label="Web Search" desc="Live agentic web search" active={isWebSearch} onClick={() => { onToggleWebSearch(); setShowToolsMenu(false); }} />
                            <ToolItem icon={Globe} label="Deep Research" desc="Multi-agent web research" active={isDeepResearch} onClick={() => { onToggleResearch(); setShowToolsMenu(false); }} />
                            <ToolItem icon={Brain} label="Deep Thinking" desc="Chain-of-thought reasoning" active={isDeepThinking} onClick={() => { onToggleThinking(); setShowToolsMenu(false); }} />
                            <ToolItem icon={Image} label="Create Image" desc="Generate images inline" active={isImageGen} onClick={() => { onToggleImageGen(); setShowToolsMenu(false); }} />
                          </m.div>
                        </>
                      )}
                    </AnimatePresence>
                  </div>
                </div>

                <div className="flex items-center gap-1">
                  <TokenUsageBadge />

                  {/* Model Selector */}
                  <div className="relative">
                    <button onClick={onToggleModelDropdown} 
                      className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-medium press-scale transition-all" 
                      style={{ 
                        background: "var(--color-surface-hover)", 
                        color: "var(--color-text-secondary)",
                        border: "1px solid var(--color-border)"
                      }}>
                      <span className="truncate max-w-[120px]">{selectedModelName}</span>
                      <CaretDown className={cn("h-3.5 w-3.5 transition-transform", showModelDropdown && "rotate-180")} weight="bold" />
                    </button>
                    <AnimatePresence>
                      {showModelDropdown && (
                        <>
                          <div className="fixed inset-0 z-40" onClick={() => setShowModelDropdown(false)} />
                          <m.div 
                            initial={{ opacity: 0, y: 12, scale: 0.96 }} 
                            animate={{ opacity: 1, y: 0, scale: 1 }} 
                            exit={{ opacity: 0, y: 12, scale: 0.96 }}
                            transition={{ type: "spring", damping: 25, stiffness: 300 }}
                            className="absolute bottom-full right-0 mb-3 w-72 rounded-[20px] z-50 p-1.5 backdrop-blur-2xl"
                            style={{ 
                              background: "color-mix(in srgb, var(--color-surface) 80%, transparent)",
                              border: "1px solid color-mix(in srgb, var(--color-border) 80%, transparent)", 
                              boxShadow: "0 20px 40px -10px rgba(0,0,0,0.2), var(--shadow-xl)"
                            }}>
                            <div className="px-3 py-2 text-[11px] font-bold uppercase tracking-widest" style={{ color: "var(--color-text-tertiary)" }}>
                              Intelligence Models
                            </div>
                            <div className="flex flex-col gap-1">
                              {MODELS.map((model) => (
                                <button key={model.id} onClick={() => { onSelectModel(model.id); setShowModelDropdown(false); }}
                                  className="w-full text-left px-3 py-2.5 rounded-xl flex items-center justify-between transition-all duration-200 group"
                                  style={{ 
                                    background: selectedModel === model.id ? "var(--color-accent-subtle)" : "transparent", 
                                    color: selectedModel === model.id ? "var(--color-accent)" : "var(--color-text-primary)"
                                  }}>
                                  <div className="flex flex-col">
                                    <span className="text-[13px] font-bold group-hover:translate-x-0.5 transition-transform">{model.name}</span>
                                    <span className="text-[11px] opacity-80">{model.description}</span>
                                  </div>
                                  {selectedModel === model.id && (
                                    <m.div layoutId="activeModelIndicator" className="h-2 w-2 rounded-full" style={{ background: "var(--color-accent)", boxShadow: "0 0 8px var(--color-accent)" }} />
                                  )}
                                </button>
                              ))}
                            </div>
                          </m.div>
                        </>
                      )}
                    </AnimatePresence>
                  </div>

                  {/* Mic */}
                  <button onClick={onToggleRecording}
                    className={cn("h-8 w-8 flex items-center justify-center rounded-full press-scale", isRecording && "animate-recording-pulse")}
                    style={{ color: isRecording ? "var(--color-error)" : "var(--color-text-secondary)", background: isRecording ? "var(--color-error-subtle)" : "transparent" }}>
                    <Microphone className="h-4 w-4" weight="fill" />
                  </button>

                  {/* Send */}
                  <button disabled={(!input.trim() && !selectedImage) || loading} onClick={() => onSend()}
                    className="h-8 w-8 flex items-center justify-center rounded-full press-scale"
                    style={{ background: (input.trim() || selectedImage) && !loading ? "var(--color-text-primary)" : "var(--color-surface-hover)", color: (input.trim() || selectedImage) && !loading ? "var(--color-bg)" : "var(--color-text-tertiary)" }}>
                    {loading ? <ArrowsClockwise className="h-4 w-4 animate-spin" weight="bold" /> : <PaperPlaneRight className="h-4 w-4" weight="fill" />}
                  </button>
              </div>
            </div>

        </div>
      </div>
      </div>
    </LazyMotion>
  );
}

function ModeChip({ icon: Icon, label, color, onClose }: { icon: any; label: string; color: string; onClose: () => void }) {
  return (
    <m.div initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }}
      className="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold"
      style={{ background: `${color}15`, color }}>
      <Icon className="h-3 w-3" />{label}
      <button onClick={onClose} className="ml-0.5 hover:opacity-70 press-scale"><Plus className="h-3 w-3 rotate-45" weight="bold" /></button>
    </m.div>
  );
}

function ToolItem({ icon: Icon, label, desc, active, onClick }: { icon: any; label: string; desc: string; active: boolean; onClick: () => void }) {
  return (
    <button onClick={onClick} className="w-full text-left px-3 py-2.5 flex items-center gap-3 transition-colors press-scale"
      style={{ background: active ? "oklch(0.600 0.200 300 / 0.08)" : "transparent", color: active ? "oklch(0.600 0.200 300)" : "var(--color-text-primary)" }}>
      <div className="h-9 w-9 rounded-xl flex items-center justify-center shrink-0" style={{ background: active ? "oklch(0.600 0.200 300 / 0.15)" : "var(--color-surface-hover)" }}>
        <Icon className="h-4.5 w-4.5" />
      </div>
      <div className="flex-1 min-w-0">
        <div className="text-sm font-semibold">{label}</div>
        <div className="text-xs" style={{ color: "var(--color-text-tertiary)" }}>{desc}</div>
      </div>
      {active && <div className="h-2 w-2 rounded-full animate-pulse shrink-0" style={{ background: "oklch(0.600 0.200 300)" }} />}
    </button>
  );
}
