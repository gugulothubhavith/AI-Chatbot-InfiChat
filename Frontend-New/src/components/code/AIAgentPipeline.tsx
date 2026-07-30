import { motion } from "framer-motion";
import { useEffect, useState } from "react";
import type { CodeSquadState } from "@/hooks/useCodeSquad";
import { Activity, FileCode, Users, Timer } from "lucide-react";

export function AIAgentPipeline({ state, running }: { state: CodeSquadState; running: boolean }) {
  const [now, setNow] = useState(0);
  useEffect(() => {
    if (!running) return;
    const t = setInterval(() => setNow((n) => n + 1), 100);
    return () => clearInterval(t);
  }, [running]);

  const seconds = state.stats.latencyMs > 0 ? state.stats.latencyMs / 1000 : now / 10;
  const agentCount = Object.keys(state.agents).length;

  const stats = [
    { label: "Workflows", value: state.stats.workflows || state.plan.length, icon: Activity },
    { label: "Files", value: Object.keys(state.files).length, icon: FileCode },
    { label: "Agents", value: agentCount, icon: Users },
    { label: "Latency", value: `${seconds.toFixed(1)}s`, icon: Timer, live: true },
  ];

  return (
    <div className="flex gap-2 overflow-x-auto settings-scroll">
      {stats.map((s) => (
        <div key={s.label} className="relative min-w-[110px] shrink-0 overflow-hidden rounded-xl border border-border bg-surface-2/40 p-3">
          {running && s.live && (
            <motion.span
              className="absolute inset-x-0 top-0 h-px bg-brand"
              animate={{ scaleX: [0, 1, 0], transformOrigin: ["0% 0%", "100% 0%", "100% 0%"] }}
              transition={{ duration: 1.4, repeat: Infinity }}
            />
          )}
          <div className="flex items-center gap-1.5 text-[10px] font-medium uppercase tracking-widest text-muted-foreground">
            <s.icon className="h-3 w-3 shrink-0" />
            <span className="truncate">{s.label}</span>
          </div>
          <div className="mt-1 truncate font-mono text-lg tracking-tight">{s.value}</div>
        </div>
      ))}
    </div>
  );
}


export function AgentGraph({ state, running }: { state: CodeSquadState; running: boolean }) {
  const agents = Object.values(state.agents);
  if (agents.length === 0) return null;
  return (
    <div className="rounded-xl border border-border bg-surface-2/40 p-3">
      <div className="mb-2 text-[10px] font-medium uppercase tracking-widest text-muted-foreground">Agent swarm</div>
      <div className="flex gap-2 overflow-x-auto settings-scroll">
        {agents.map((a) => (
          <motion.div
            key={a.agent_number}
            layout
            className={`relative shrink-0 overflow-hidden whitespace-nowrap rounded-lg border px-2.5 py-1.5 text-[11.5px] ${
              a.status === "running"
                ? "border-brand/40 bg-brand/10 text-foreground"
                : a.status === "completed"
                  ? "border-emerald-500/30 bg-emerald-500/5 text-emerald-500"
                  : "border-border bg-surface/60 text-muted-foreground"
            }`}
          >
            {a.status === "running" && running && (
              <motion.span
                className="absolute inset-0 -z-0 bg-brand/15"
                animate={{ opacity: [0.2, 0.6, 0.2] }}
                transition={{ duration: 1.4, repeat: Infinity }}
              />
            )}
            <span className="relative font-medium">#{a.agent_number} {a.agent}</span>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
