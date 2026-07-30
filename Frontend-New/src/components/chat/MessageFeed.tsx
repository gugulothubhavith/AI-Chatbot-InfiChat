import { useEffect, useRef, useState } from "react";
import { useChatStore } from "@/stores/chat";
import { Markdown } from "./Markdown";
import { RefreshCw, Copy, Pencil, Check, X, Globe, Volume2, Square, Loader2 } from "lucide-react";
import { motion } from "framer-motion";
import { tapProps } from "@/lib/motion";
import { useModelStore, MODELS } from "@/stores/model";
import { toast } from "sonner";
import { Logo } from "@/components/brand/Logo";
import { useTtsStore, resolveVoiceId } from "@/stores/tts";
import { useSettingsStore } from "@/stores/settings";

export function MessageFeed({ streamSlot }: { streamSlot?: React.ReactNode }) {
  const conv = useChatStore((s) => s.conversations.find((c) => c.id === s.activeId));
  const pending = useChatStore((s) => s.pending);
  const regenerate = useChatStore((s) => s.regenerate);
  const editAndResend = useChatStore((s) => s.editAndResend);
  const model = useModelStore((s) => s.model);
  const modelName = MODELS.find((m) => m.id === model)?.name ?? "";

  const [editingId, setEditingId] = useState<string | null>(null);
  const [draft, setDraft] = useState("");

  const ttsActiveId = useTtsStore((s) => s.activeId);
  const ttsLoading = useTtsStore((s) => s.loading);
  const speak = useTtsStore((s) => s.speak);
  const stopTts = useTtsStore((s) => s.stop);
  const voiceProfile = useSettingsStore((s) => s.voiceProfile);

  // Stop any in-flight speech when the feed unmounts (route change / logout) so
  // audio never outlives the view that started it.
  useEffect(() => stopTts, [stopTts]);

  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    ref.current?.scrollTo({ top: ref.current.scrollHeight, behavior: "smooth" });
  }, [conv?.messages.length, pending, streamSlot]);

  const copyText = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      toast("Copied to clipboard");
    } catch {
      toast("Copy failed");
    }
  };

  if ((!conv || conv.messages.length === 0) && !streamSlot) return <EmptyState />;

  return (
    <div ref={ref} className="h-full overflow-y-auto pt-24 pb-48">
      <div className="mx-auto max-w-[845px] px-6 space-y-8">
        {conv?.messages.map((m, i) => {
          const isLastAssistant = m.role === "assistant" && i === (conv?.messages.length ?? 0) - 1;
          return m.role === "user" ? (
            <div key={m.id} className="group flex flex-col items-end gap-1.5">
              {editingId === m.id ? (
                <div className="w-full max-w-[80%] rounded-2xl border border-border bg-surface-2 p-2">
                  <textarea
                    value={draft}
                    onChange={(e) => setDraft(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" && !e.shiftKey) {
                        e.preventDefault();
                        const v = draft.trim();
                        if (!v) return;
                        setEditingId(null);
                        if (v === m.content) return;
                        void editAndResend(m.id, v);
                        toast("Sending to AI…");
                      } else if (e.key === "Escape") {
                        setEditingId(null);
                      }
                    }}
                    rows={Math.min(8, Math.max(2, draft.split("\n").length))}
                    className="w-full resize-none bg-transparent px-2 py-1 text-sm outline-none"
                    autoFocus
                  />
                  <div className="mt-1 flex items-center justify-between">
                    <span className="pl-2 text-[10px] text-muted-foreground">⏎ send · ⇧⏎ newline · Esc cancel</span>
                    <div className="flex gap-1">
                      <motion.button
                        {...tapProps}
                        onClick={() => setEditingId(null)}
                        className="flex items-center gap-1 rounded-md px-2 py-1 text-[11px] text-muted-foreground hover:bg-surface hover:text-foreground"
                      >
                        <X className="h-3 w-3" /> Cancel
                      </motion.button>
                      <motion.button
                        {...tapProps}
                        onClick={() => {
                          const v = draft.trim();
                          if (!v) return;
                          setEditingId(null);
                          if (v === m.content) return;
                          void editAndResend(m.id, v);
                          toast("Sending to AI…");
                        }}
                        className="flex items-center gap-1 rounded-md bg-primary px-2 py-1 text-[11px] font-medium text-primary-foreground"
                      >
                        <Check className="h-3 w-3" /> Send
                      </motion.button>
                    </div>
                  </div>
                </div>


              ) : (
                <div className="max-w-[80%] rounded-2xl bg-surface-2 px-4 py-2.5 text-sm leading-relaxed whitespace-pre-wrap">
                  {m.content}
                </div>
              )}
              {editingId !== m.id && (
                <div className="flex items-center gap-1 opacity-0 transition-opacity group-hover:opacity-100">
                  <motion.button
                    {...tapProps}
                    onClick={() => copyText(m.content)}
                    aria-label="Copy message"
                    className="flex h-6 w-6 items-center justify-center rounded-md text-muted-foreground hover:bg-surface-2 hover:text-foreground"
                  >
                    <Copy className="h-3 w-3" />
                  </motion.button>
                  <motion.button
                    {...tapProps}
                    onClick={() => {
                      setDraft(m.content);
                      setEditingId(m.id);
                    }}
                    aria-label="Edit message"
                    className="flex h-6 w-6 items-center justify-center rounded-md text-muted-foreground hover:bg-surface-2 hover:text-foreground"
                  >
                    <Pencil className="h-3 w-3" />
                  </motion.button>
                </div>
              )}
            </div>
          ) : (

            <div key={m.id} className="flex gap-3">
              <div className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-brand/70 to-brand/30 text-[10px] font-medium text-brand-foreground">
                AI
              </div>
              <div className="min-w-0 flex-1">
                {m.autoSearched && (
                  <div className="mb-1.5 inline-flex items-center gap-1.5 rounded-full border border-brand/30 bg-brand/5 px-2 py-0.5 text-[11px] font-medium text-brand">
                    <Globe className="h-3 w-3" />
                    Searched the web automatically
                  </div>
                )}
                <Markdown content={m.content} />
                <div className="mt-2 flex items-center gap-3 text-[11px] text-muted-foreground">
                  <span>{modelName}</span>
                  {typeof m.tokens === "number" && <span>· {m.tokens} tokens</span>}
                  {typeof m.latencyMs === "number" && <span>· {(m.latencyMs / 1000).toFixed(1)}s</span>}
                  <motion.button
                    {...tapProps}
                    onClick={() => speak(m.id, m.content, resolveVoiceId(voiceProfile))}
                    className={`ml-1 flex items-center gap-1 rounded px-1.5 py-0.5 hover:bg-surface-2 hover:text-foreground ${
                      ttsActiveId === m.id ? "text-brand" : ""
                    }`}
                    aria-label={ttsActiveId === m.id ? "Stop reading" : "Read aloud"}
                  >
                    {ttsActiveId === m.id && ttsLoading ? (
                      <>
                        <Loader2 className="h-3 w-3 animate-spin" /> Loading
                      </>
                    ) : ttsActiveId === m.id ? (
                      <>
                        <Square className="h-3 w-3 fill-current" /> Stop
                      </>
                    ) : (
                      <>
                        <Volume2 className="h-3 w-3" /> Read
                      </>
                    )}
                  </motion.button>
                  {isLastAssistant && (
                    <motion.button
                      {...tapProps}
                      onClick={() => regenerate()}
                      className="ml-1 flex items-center gap-1 rounded px-1.5 py-0.5 hover:bg-surface-2 hover:text-foreground"
                    >
                      <RefreshCw className="h-3 w-3" /> Regenerate
                    </motion.button>
                  )}
                </div>
              </div>
            </div>
          );
        })}
        {streamSlot && (
          <div className="flex gap-3">
            <div className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-brand/70 to-brand/30 text-[10px] font-medium text-brand-foreground">
              AI
            </div>
            <div className="min-w-0 flex-1">{streamSlot}</div>
          </div>
        )}
        {pending && (
          <div className="flex gap-3">
            <div className="mt-0.5 h-7 w-7 shrink-0 rounded-full shimmer" />
            <div className="flex-1 space-y-2">
              <div className="h-3 w-3/4 rounded shimmer" />
              <div className="h-3 w-2/3 rounded shimmer" />
              <div className="h-3 w-1/2 rounded shimmer" />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function EmptyState() {
  return (
    <div className="flex h-full items-center justify-center px-6">
      <div className="max-w-md text-center">
        <div className="mx-auto mb-5 flex items-center justify-center">
          <Logo size={34} animated />
        </div>
        <h1 className="text-2xl font-medium tracking-tight">How can I help today?</h1>
        <p className="mt-2 text-sm text-muted-foreground">
          Ask anything — code, writing, research, or brainstorming. Attach a file with the + button.
        </p>
      </div>
    </div>
  );
}
