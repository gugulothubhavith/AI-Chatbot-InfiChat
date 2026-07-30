import { motion, AnimatePresence } from "framer-motion";
import { Brain, Check, Sparkles } from "lucide-react";
import type { ThinkingProgress } from "@/hooks/useThinkingStream";
import { Markdown } from "@/components/chat/Markdown";

export function DeepThinkingProgress({ state }: { state: ThinkingProgress }) {
  const pct = Math.round(state.confidence * 100);

  return (
    <div className="rounded-2xl border border-border bg-surface-2/40 p-4 backdrop-blur-sm">
      <div className="flex items-center gap-3">
        <div className="relative flex h-9 w-9 items-center justify-center rounded-xl bg-brand/10">
          <motion.div
            className="absolute inset-0 rounded-xl bg-brand/20 blur-md"
            animate={{ opacity: state.complete ? 0 : [0.3, 0.8, 0.3] }}
            transition={{ duration: 1.8, repeat: state.complete ? 0 : Infinity }}
          />
          {state.complete ? (
            <Sparkles className="relative h-4 w-4 text-brand" />
          ) : (
            <motion.div animate={{ rotate: 360 }} transition={{ duration: 6, repeat: Infinity, ease: "linear" }}>
              <Brain className="relative h-4 w-4 text-brand" />
            </motion.div>
          )}
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2 text-[11px] font-medium uppercase tracking-widest text-muted-foreground">
            <span>Deep Thinking</span>
            <span className="text-brand">{state.stage}</span>
          </div>
          <div className="truncate text-[13px] text-foreground">{state.message || "Preparing…"}</div>
        </div>
        <div className="text-right">
          <div className="font-mono text-[11px] text-muted-foreground">{pct}%</div>
          <div className="mt-1 h-1 w-24 overflow-hidden rounded-full bg-surface">
            <motion.div
              className="h-full bg-gradient-to-r from-brand/60 to-brand"
              animate={{ width: `${pct}%` }}
              transition={{ type: "spring", stiffness: 120, damping: 22 }}
            />
          </div>
        </div>
      </div>

      {state.steps.length > 0 && (
        <div className="mt-4 border-l border-border/60 pl-4">
          <AnimatePresence initial={false}>
            {state.steps.map((s) => (
              <motion.div
                key={s.step_number}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.25 }}
                className="relative mb-3"
              >
                <div className="absolute -left-[21px] top-1 flex h-4 w-4 items-center justify-center">
                  {s.status === "verified" ? (
                    <motion.div
                      initial={{ scale: 0 }}
                      animate={{ scale: 1 }}
                      className="flex h-4 w-4 items-center justify-center rounded-full bg-emerald-500/20 text-emerald-500"
                    >
                      <Check className="h-2.5 w-2.5" strokeWidth={3} />
                    </motion.div>
                  ) : (
                    <span className="relative flex h-2.5 w-2.5">
                      <span className="absolute inset-0 animate-ping rounded-full bg-brand/60" />
                      <span className="relative h-2.5 w-2.5 rounded-full bg-brand" />
                    </span>
                  )}
                </div>
                <div className="text-[12.5px] font-medium text-foreground">
                  Step {s.step_number}. {s.title}
                </div>
                <div className="mt-0.5 text-[12px] leading-relaxed text-muted-foreground">
                  {s.content}
                  {s.status === "pending" && <TypingDots />}
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
        </div>
      )}

      <AnimatePresence>
        {state.complete && state.report && (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.15 }}
            className="mt-4 rounded-xl border border-border/60 bg-surface/60 p-4"
          >
            <div className="mb-2 text-[10px] font-medium uppercase tracking-widest text-muted-foreground">
              Executive summary
            </div>
            <Markdown content={state.report.executive_summary} />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

function TypingDots() {
  return (
    <span className="ml-1 inline-flex gap-0.5 align-middle">
      {[0, 1, 2].map((i) => (
        <motion.span
          key={i}
          className="inline-block h-1 w-1 rounded-full bg-brand"
          animate={{ opacity: [0.2, 1, 0.2], y: [0, -1, 0] }}
          transition={{ duration: 0.9, repeat: Infinity, delay: i * 0.15 }}
        />
      ))}
    </span>
  );
}
