import { useCodeStore } from "@/stores/code";
import { motion } from "framer-motion";
import { tapProps } from "@/lib/motion";
import { Play, Square, Eraser } from "lucide-react";
import { useEffect, useRef } from "react";

export function Terminal() {
  const terminal = useCodeStore((s) => s.terminal);
  const running = useCodeStore((s) => s.running);
  const run = useCodeStore((s) => s.runCode);
  const stop = useCodeStore((s) => s.stopCode);
  const clear = useCodeStore((s) => s.clearTerminal);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    ref.current?.scrollTo({ top: ref.current.scrollHeight });
  }, [terminal.length]);

  return (
    <div className="flex h-full flex-col overflow-hidden rounded-xl border border-border bg-[#0a0a0a]">
      <div className="flex items-center justify-between border-b border-white/5 px-3 py-2">
        <div className="flex items-center gap-1.5">
          <span className="h-2.5 w-2.5 rounded-full bg-[#ff5f57]" />
          <span className="h-2.5 w-2.5 rounded-full bg-[#febc2e]" />
          <span className="h-2.5 w-2.5 rounded-full bg-[#28c840]" />
          <span className="ml-3 font-mono text-[10px] uppercase tracking-widest text-white/50">
            sandbox — bash
          </span>
        </div>
        <div className="flex items-center gap-1">
          <motion.button
            {...tapProps}
            onClick={run}
            disabled={running}
            className="flex h-7 items-center gap-1 rounded-md bg-emerald-500/15 px-2 text-[11px] text-emerald-400 disabled:opacity-50"
          >
            <Play className="h-3 w-3" /> Run
          </motion.button>
          <motion.button
            {...tapProps}
            onClick={stop}
            disabled={!running}
            className="flex h-7 items-center gap-1 rounded-md bg-destructive/15 px-2 text-[11px] text-destructive disabled:opacity-50"
          >
            <Square className="h-3 w-3" /> Stop
          </motion.button>
          <motion.button
            {...tapProps}
            onClick={clear}
            className="flex h-7 items-center gap-1 rounded-md bg-white/5 px-2 text-[11px] text-white/70"
          >
            <Eraser className="h-3 w-3" /> Clear
          </motion.button>
        </div>
      </div>
      <div ref={ref} className="flex-1 overflow-y-auto p-3 font-mono text-[12px] leading-relaxed text-white/85">
        {terminal.map((l, i) => (
          <div key={i} className={l.startsWith("✗") ? "text-destructive" : l.startsWith("✓") ? "text-emerald-400" : l.startsWith("→") ? "text-white/50" : ""}>
            {l}
          </div>
        ))}
        {running && <div className="mt-1 h-3 w-1.5 animate-pulse bg-white/70" />}
      </div>
    </div>
  );
}
