import { motion, AnimatePresence } from "framer-motion";
import {
  Telescope,
  Globe,
  FileText,
  Check,
  Activity,
  Cpu,
  Gauge,
  ShieldCheck,
  AlertTriangle,
  ChevronRight,
  Sparkles,
  Network,
} from "lucide-react";
import type { ResearchProgress, AgentState } from "@/hooks/useResearchStream";
import { Markdown } from "@/components/chat/Markdown";

const STATUS_COLOR: Record<AgentState["status"], string> = {
  queued: "text-muted-foreground",
  running: "text-brand",
  completed: "text-emerald-400",
  error: "text-rose-400",
};

const STATUS_DOT: Record<AgentState["status"], string> = {
  queued: "bg-muted-foreground/40",
  running: "bg-brand shadow-[0_0_12px] shadow-brand/60",
  completed: "bg-emerald-400",
  error: "bg-rose-400",
};

function formatTs(ts: number) {
  const d = new Date(ts);
  return `${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}:${String(d.getSeconds()).padStart(2, "0")}`;
}

export function DeepResearchProgress({ state }: { state: ResearchProgress }) {
  const stagePct = state.totalStages ? Math.round((state.stage / state.totalStages) * 100) : 0;
  const agentList = Object.values(state.agents);
  const running = agentList.filter((a) => a.status === "running").length;
  const done = agentList.filter((a) => a.status === "completed").length;
  const gate = state.gates[state.gates.length - 1];
  const avgConf =
    state.findings.length > 0
      ? state.findings.reduce((s, f) => s + f.confidence, 0) / state.findings.length
      : 0;

  return (
    <div className="relative overflow-hidden rounded-2xl border border-border/70 bg-[#08090b] p-4 text-foreground shadow-[0_0_0_1px_rgba(255,255,255,0.02)_inset]">
      {/* Ambient glow */}
      <div className="pointer-events-none absolute -top-24 left-1/2 h-56 w-[70%] -translate-x-1/2 rounded-full bg-brand/10 blur-3xl" />
      <div className="pointer-events-none absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.03)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.03)_1px,transparent_1px)] bg-[size:32px_32px] [mask-image:radial-gradient(ellipse_at_top,black,transparent_70%)]" />

      {/* Header */}
      <div className="relative flex items-center gap-3">
        <div className="relative flex h-10 w-10 items-center justify-center rounded-xl bg-brand/10 ring-1 ring-brand/30">
          <motion.div
            className="absolute inset-0 rounded-xl bg-brand/30 blur-md"
            animate={{ opacity: state.complete ? 0 : [0.25, 0.75, 0.25] }}
            transition={{ duration: 2, repeat: state.complete ? 0 : Infinity }}
          />
          <Telescope className="relative h-4 w-4 text-brand" />
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2 text-[10px] font-medium uppercase tracking-[0.18em] text-muted-foreground">
            <span>Deep Research</span>
            <span className="rounded-full bg-brand/15 px-1.5 py-px font-mono text-[9.5px] text-brand">
              12-STAGE MULTI-AGENT
            </span>
          </div>
          <div className="mt-0.5 flex items-center gap-2 text-[13px]">
            <motion.span
              key={state.stageMessage}
              initial={{ opacity: 0, y: 3 }}
              animate={{ opacity: 1, y: 0 }}
              className="truncate"
            >
              {state.stageMessage || "Booting research swarm…"}
            </motion.span>
            {!state.complete && (
              <motion.span
                className="inline-block h-1.5 w-1.5 rounded-full bg-brand"
                animate={{ opacity: [0.2, 1, 0.2] }}
                transition={{ duration: 1.1, repeat: Infinity }}
              />
            )}
          </div>
        </div>
        <div className="hidden shrink-0 items-center gap-1.5 rounded-lg border border-white/5 bg-white/[0.02] px-2 py-1 font-mono text-[10.5px] text-muted-foreground sm:flex">
          <Activity className="h-3 w-3 text-brand" /> STAGE
          <span className="text-foreground">{String(state.stage).padStart(2, "0")}</span>
          <span className="opacity-40">/</span>
          <span>{String(state.totalStages).padStart(2, "0")}</span>
        </div>
      </div>

      {/* Stage stepper */}
      <div className="relative mt-4">
        <div className="flex gap-1">
          {Array.from({ length: state.totalStages || 12 }).map((_, i) => {
            const idx = i + 1;
            const isDone = idx < state.stage;
            const isActive = idx === state.stage;
            return (
              <div key={i} className="relative h-1.5 flex-1 overflow-hidden rounded-full bg-white/5">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: isDone ? "100%" : isActive ? "60%" : "0%" }}
                  transition={{ type: "spring", stiffness: 140, damping: 24 }}
                  className={`h-full ${isDone ? "bg-brand" : "bg-gradient-to-r from-brand/70 to-brand"}`}
                />
                {isActive && (
                  <motion.div
                    className="absolute inset-y-0 -left-4 w-8 bg-white/40 blur-sm"
                    animate={{ x: ["-20%", "220%"] }}
                    transition={{ duration: 1.4, repeat: Infinity, ease: "easeInOut" }}
                  />
                )}
              </div>
            );
          })}
        </div>
        <div className="mt-1.5 flex justify-between font-mono text-[9.5px] uppercase tracking-widest text-muted-foreground">
          <span>{state.stageKey || "…"}</span>
          <span>{stagePct}% complete</span>
        </div>
      </div>

      {/* Bento */}
      <div className="relative mt-4 grid gap-3 lg:grid-cols-3">
        {/* LEFT — Report / Live discoveries */}
        <div className="space-y-3 lg:col-span-2">
          {/* Live discoveries */}
          <div className="rounded-xl border border-white/5 bg-white/[0.02]">
            <div className="flex items-center justify-between border-b border-white/5 px-3 py-2">
              <div className="flex items-center gap-2 font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
                <Sparkles className="h-3 w-3 text-brand" /> Live discoveries
                <span className="rounded-full bg-white/5 px-1.5 text-[9.5px] text-foreground/80">
                  {state.findings.length}
                </span>
              </div>
              <div className="font-mono text-[10px] text-muted-foreground">
                avg conf <span className="text-foreground">{(avgConf * 100).toFixed(0)}%</span>
              </div>
            </div>
            <div className="max-h-56 space-y-2 overflow-y-auto p-3">
              {state.findings.length === 0 && (
                <div className="py-6 text-center font-mono text-[11px] text-muted-foreground">
                  Awaiting cross-validated findings…
                </div>
              )}
              <AnimatePresence initial={false}>
                {state.findings.map((f, i) => {
                  const pct = Math.round(f.confidence * 100);
                  const tone =
                    f.confidence > 0.85 ? "emerald" : f.confidence > 0.7 ? "brand" : "amber";
                  const toneRing =
                    tone === "emerald"
                      ? "ring-emerald-400/40"
                      : tone === "brand"
                        ? "ring-brand/40"
                        : "ring-amber-400/40";
                  const toneText =
                    tone === "emerald" ? "text-emerald-400" : tone === "brand" ? "text-brand" : "text-amber-400";
                  return (
                    <motion.div
                      key={i}
                      layout
                      initial={{ opacity: 0, y: 6, scale: 0.98 }}
                      animate={{ opacity: 1, y: 0, scale: 1 }}
                      exit={{ opacity: 0 }}
                      className={`group relative rounded-lg border border-white/5 bg-black/30 p-2.5 ring-1 ${toneRing}/0 transition-shadow hover:${toneRing}`}
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div className="text-[12.5px] leading-relaxed">{f.claim}</div>
                        <div className={`shrink-0 font-mono text-[10.5px] ${toneText}`}>{pct}%</div>
                      </div>
                      <div className="mt-1.5 flex items-center gap-3 font-mono text-[10px] text-muted-foreground">
                        <span className="inline-flex items-center gap-1">
                          <Network className="h-3 w-3" /> {f.source_count} sources
                        </span>
                        <div className="relative h-1 flex-1 overflow-hidden rounded-full bg-white/5">
                          <motion.div
                            initial={{ width: 0 }}
                            animate={{ width: `${pct}%` }}
                            className={`h-full ${
                              tone === "emerald"
                                ? "bg-emerald-400"
                                : tone === "brand"
                                  ? "bg-brand"
                                  : "bg-amber-400"
                            }`}
                          />
                        </div>
                      </div>
                    </motion.div>
                  );
                })}
              </AnimatePresence>
            </div>
          </div>

          {/* Report */}
          <AnimatePresence>
            {state.complete && state.report && (
              <motion.div
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                className="rounded-xl border border-white/5 bg-white/[0.02] p-4"
              >
                <div className="mb-3 flex items-center justify-between">
                  <div className="flex items-center gap-2 font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
                    <FileText className="h-3 w-3 text-brand" /> Final report
                  </div>
                  <div className="flex items-center gap-2 font-mono text-[10px] text-muted-foreground">
                    <span>{state.report.fact_count} facts</span>
                    <span className="opacity-40">·</span>
                    <span>{state.report.citations.length} citations</span>
                  </div>
                </div>
                <div className="mb-3 rounded-lg border border-brand/20 bg-brand/5 p-3 text-[12.5px] leading-relaxed">
                  <div className="mb-1 font-mono text-[9.5px] uppercase tracking-widest text-brand">
                    Executive summary
                  </div>
                  {state.report.executive_summary}
                </div>
                <Markdown content={state.report.content} />
                {state.report.citations.length > 0 && (
                  <div className="mt-4 border-t border-white/5 pt-3">
                    <div className="mb-2 font-mono text-[9.5px] uppercase tracking-widest text-muted-foreground">
                      References
                    </div>
                    <ol className="list-decimal space-y-1 pl-4 text-[12px]">
                      {state.report.citations.map((c) => (
                        <li key={c.url}>
                          <a href={c.url} target="_blank" rel="noreferrer" className="text-brand hover:underline">
                            {c.title}
                          </a>
                        </li>
                      ))}
                    </ol>
                  </div>
                )}
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* RIGHT — Telemetry */}
        <div className="space-y-3">
          {/* Metrics */}
          <div className="grid grid-cols-3 gap-2">
            <Metric icon={<Cpu className="h-3 w-3 text-brand" />} label="Agents" value={`${running}/${agentList.length || "–"}`} sub="running" />
            <Metric icon={<Globe className="h-3 w-3 text-brand" />} label="Sources" value={String(state.sources.length)} sub="ingested" />
            <Metric icon={<Gauge className="h-3 w-3 text-brand" />} label="Facts" value={String(state.findings.length)} sub="verified" />
          </div>

          {/* Quality gauge */}
          <QualityGauge gate={gate} avgConfidence={avgConf} />

          {/* Agent terminal */}
          <div className="overflow-hidden rounded-xl border border-white/5 bg-black/50">
            <div className="flex items-center justify-between border-b border-white/5 bg-white/[0.02] px-3 py-1.5">
              <div className="flex items-center gap-2 font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
                <Activity className="h-3 w-3 text-brand" /> agent telemetry
              </div>
              <div className="flex items-center gap-1">
                {["#ff5f57", "#febc2e", "#28c840"].map((c) => (
                  <span key={c} className="h-2 w-2 rounded-full" style={{ background: c }} />
                ))}
              </div>
            </div>
            <div className="max-h-40 space-y-0.5 overflow-y-auto p-2.5 font-mono text-[11px] leading-relaxed">
              {state.logs.length === 0 && (
                <div className="py-4 text-center text-[10.5px] text-muted-foreground">no telemetry yet…</div>
              )}
              <AnimatePresence initial={false}>
                {state.logs.slice(-40).map((l, i) => (
                  <motion.div
                    key={`${l.ts}-${i}`}
                    initial={{ opacity: 0, x: -6 }}
                    animate={{ opacity: 1, x: 0 }}
                    className="flex items-start gap-2"
                  >
                    <span className="text-white/30">{formatTs(l.ts)}</span>
                    <span className={`inline-block h-1.5 w-1.5 shrink-0 translate-y-1.5 rounded-full ${STATUS_DOT[l.status]}`} />
                    <span className={`shrink-0 ${STATUS_COLOR[l.status]}`}>{l.agent}</span>
                    <span className="min-w-0 truncate text-white/70">› {l.message}</span>
                  </motion.div>
                ))}
              </AnimatePresence>
            </div>
          </div>

          {/* Plan tree */}
          {state.plan.length > 0 && (
            <div className="rounded-xl border border-white/5 bg-white/[0.02] p-3">
              <div className="mb-2 flex items-center gap-2 font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
                <ShieldCheck className="h-3 w-3 text-brand" /> Research plan
              </div>
              <ul className="space-y-1.5 text-[12px]">
                {state.plan.map((node) => (
                  <li key={node.id}>
                    <div className="flex items-center gap-1.5 font-medium">
                      <ChevronRight className="h-3 w-3 text-brand" />
                      {node.title}
                    </div>
                    {node.children && (
                      <ul className="ml-4 mt-1 space-y-0.5 border-l border-white/10 pl-3 text-[11.5px] text-muted-foreground">
                        {node.children.map((c) => (
                          <li key={c.id} className="flex items-center gap-1.5">
                            <span className="h-1 w-1 rounded-full bg-muted-foreground/60" />
                            {c.title}
                          </li>
                        ))}
                      </ul>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Sources */}
          {state.sources.length > 0 && (
            <div className="rounded-xl border border-white/5 bg-white/[0.02] p-3">
              <div className="mb-2 flex items-center gap-2 font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
                <Globe className="h-3 w-3 text-brand" /> Sources
                <span className="rounded-full bg-white/5 px-1.5 text-[9.5px] text-foreground/80">
                  {state.sources.length}
                </span>
              </div>
              <div className="max-h-36 space-y-1 overflow-y-auto pr-1">
                <AnimatePresence initial={false}>
                  {state.sources.map((s) => {
                    let host = s.url;
                    try {
                      host = new URL(s.url).hostname.replace(/^www\./, "");
                    } catch {
                      /* keep */
                    }
                    const favicon =
                      s.favicon ?? `https://www.google.com/s2/favicons?domain=${host}&sz=32`;
                    return (
                      <motion.a
                        key={s.url}
                        href={s.url}
                        target="_blank"
                        rel="noreferrer"
                        initial={{ opacity: 0, x: -6 }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ opacity: 0 }}
                        className="group flex items-center gap-2 rounded-md border border-transparent px-1.5 py-1 hover:border-white/5 hover:bg-white/[0.03]"
                      >
                        <img src={favicon} alt="" className="h-3.5 w-3.5 rounded-sm" />
                        <div className="min-w-0 flex-1">
                          <div className="truncate text-[11.5px] group-hover:text-brand">{s.title}</div>
                          <div className="truncate font-mono text-[9.5px] text-muted-foreground">
                            {host}
                          </div>
                        </div>
                      </motion.a>
                    );
                  })}
                </AnimatePresence>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function Metric({
  icon,
  label,
  value,
  sub,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  sub: string;
}) {
  return (
    <div className="rounded-xl border border-white/5 bg-white/[0.02] p-2.5">
      <div className="flex items-center gap-1.5 font-mono text-[9.5px] uppercase tracking-widest text-muted-foreground">
        {icon} {label}
      </div>
      <div className="mt-0.5 font-mono text-[18px] tabular-nums text-foreground">{value}</div>
      <div className="font-mono text-[9.5px] text-muted-foreground">{sub}</div>
    </div>
  );
}

function QualityGauge({
  gate,
  avgConfidence,
}: {
  gate: { iteration: number; verdict: "pass" | "fail"; confidence: number } | undefined;
  avgConfidence: number;
}) {
  const value = gate?.confidence ?? avgConfidence;
  const pct = Math.round(value * 100);
  const pass = gate?.verdict === "pass";
  const size = 96;
  const r = 40;
  const c = 2 * Math.PI * r;
  const dash = c * value;

  return (
    <div className="rounded-xl border border-white/5 bg-white/[0.02] p-3">
      <div className="mb-2 flex items-center justify-between">
        <div className="flex items-center gap-2 font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
          <Gauge className="h-3 w-3 text-brand" /> Quality gate
        </div>
        {gate && (
          <span
            className={`inline-flex items-center gap-1 rounded-full border px-1.5 py-0.5 font-mono text-[9.5px] uppercase ${
              pass
                ? "border-emerald-400/40 bg-emerald-400/10 text-emerald-400"
                : "border-amber-400/40 bg-amber-400/10 text-amber-400"
            }`}
          >
            {pass ? <Check className="h-3 w-3" /> : <AlertTriangle className="h-3 w-3" />}
            iter {gate.iteration} {gate.verdict}
          </span>
        )}
      </div>
      <div className="flex items-center gap-3">
        <div className="relative" style={{ width: size, height: size }}>
          <svg viewBox="0 0 100 100" className="h-full w-full -rotate-90">
            <circle cx="50" cy="50" r={r} stroke="rgba(255,255,255,0.08)" strokeWidth="8" fill="none" />
            <motion.circle
              cx="50"
              cy="50"
              r={r}
              stroke={pass ? "rgb(52,211,153)" : "rgb(56,145,255)"}
              strokeWidth="8"
              strokeLinecap="round"
              fill="none"
              initial={{ strokeDasharray: `0 ${c}` }}
              animate={{ strokeDasharray: `${dash} ${c}` }}
              transition={{ type: "spring", stiffness: 90, damping: 20 }}
            />
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <div className="font-mono text-[18px] tabular-nums">{pct}%</div>
            <div className="font-mono text-[9px] uppercase tracking-widest text-muted-foreground">
              conf
            </div>
          </div>
        </div>
        <div className="flex-1 space-y-1 font-mono text-[10.5px] text-muted-foreground">
          <div>
            iteration <span className="text-foreground">{gate?.iteration ?? "–"}</span>
          </div>
          <div>
            verdict{" "}
            <span className={pass ? "text-emerald-400" : "text-amber-400"}>
              {gate?.verdict ?? "pending"}
            </span>
          </div>
          <div>
            avg fact conf <span className="text-foreground">{(avgConfidence * 100).toFixed(0)}%</span>
          </div>
        </div>
      </div>
    </div>
  );
}
