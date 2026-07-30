import { createFileRoute } from "@tanstack/react-router";
import { AnimatePresence, motion } from "framer-motion";
import { useMemo, useState } from "react";
import { AlertTriangle, ArrowLeft, ChevronRight, Cpu, GitBranch, Layers, MessageSquare, Network, Rocket, Terminal as TerminalIcon, Zap } from "lucide-react";


import { AgentTaskPlan } from "@/components/code/AgentTaskPlan";
import { AIAgentPipeline, AgentGraph } from "@/components/code/AIAgentPipeline";
import { FileExplorer } from "@/components/code/FileExplorer";
import { CodeEditor } from "@/components/code/CodeEditor";
import { useCodeSquad } from "@/hooks/useCodeSquad";
import { useCodeStore } from "@/stores/code";
import { MODELS, useModelStore } from "@/stores/model";
import { Markdown } from "@/components/chat/Markdown";
import { InputBar } from "@/components/chat/InputBar";

const MONO = "'JetBrains Mono', 'Geist Mono', ui-monospace, monospace";
const LIME = "#B4F03A";

export const Route = createFileRoute("/_app/code")({
  head: () => ({
    meta: [
      { title: "InfiBuild Studio — InfiChat" },
      { name: "description", content: "Multi-agent code generation studio streamed live over WebSocket." },
      { property: "og:title", content: "InfiBuild Studio — InfiChat" },
      { property: "og:description", content: "Multi-agent code generation studio streamed live over WebSocket." },
    ],
  }),
  component: CodePage,
});

const PROMPT_TEMPLATES = [
  { id: "PROMPT_01", title: "Scaffold microservices stack", sub: "Initialize k8s + gRPC skeleton" },
  { id: "PROMPT_02", title: "Optimize build pipeline", sub: "Reduce cold-start by 40%" },
  { id: "PROMPT_03", title: "Debug auth layer", sub: "Trace the JWT lifecycle end-to-end" },
];

const AGENT_ROSTER = [
  { name: "Planner", state: "idle" as const, note: "Awaiting brief" },
  { name: "Architect", state: "idle" as const, note: "Mesh topology cached" },
  { name: "Coder", state: "idle" as const, note: "Sandbox warm" },
  { name: "Reviewer", state: "idle" as const, note: "Rulepack v4.2 loaded" },
  { name: "Tester", state: "idle" as const, note: "vitest ready" },
  { name: "Deployer", state: "idle" as const, note: "edge/preview ready" },
];

function CodePage() {
  const { state, running, start, cancel, reset } = useCodeSquad();
  const [selected, setSelected] = useState<string | null>(null);
  const [flash, setFlash] = useState<string | null>(null);
  const [view, setView] = useState<"studio" | "chat">("studio");
  const model = useModelStore((s) => s.model);
  const setModel = useModelStore((s) => s.setModel);
  const activeModel = MODELS.find((m) => m.id === model) ?? MODELS[0];

  const sessions = useCodeStore((s) => s.sessions);
  const activeSessionId = useCodeStore((s) => s.activeId);
  const newSession = useCodeStore((s) => s.newSession);
  const setActiveSession = useCodeStore((s) => s.setActive);
  const activeSession = sessions.find((s) => s.id === activeSessionId) ?? null;

  const files = useMemo(() => Object.values(state.files), [state.files]);
  const started = files.length > 0 || state.plan.length > 0 || running;
  const activePath = selected ?? state.currentFilePath;
  const activeFile = activePath ? (state.files[activePath] ?? null) : null;

  const seen = useMemo(() => new Set<string>(), []);
  files.forEach((f) => {
    if (!seen.has(f.path)) {
      seen.add(f.path);
      if (started) {
        queueMicrotask(() => {
          setFlash(f.path);
          setTimeout(() => setFlash((cur) => (cur === f.path ? null : cur)), 900);
        });
      }
    }
  });

  const handleSubmit = (prompt: string) => {
    // ensure a code session exists for this iteration
    let sid = activeSessionId;
    if (!sid) sid = newSession();
    // append user prompt to the code session
    useCodeStore.setState((s) => ({
      sessions: s.sessions.map((c) =>
        c.id === sid
          ? {
              ...c,
              title: c.messages.length === 0 ? prompt.slice(0, 40) : c.title,
              messages: [...c.messages, { id: `${Date.now()}`, role: "user", content: prompt }],
            }
          : c,
      ),
    }));
    setSelected(null);
    setView("studio");
    reset();
    void start(prompt);
  };

  const handleBackToChat = () => {
    // append a status summary as an assistant message to the code session
    let sid = activeSessionId;
    if (!sid) {
      sid = newSession();
      setActiveSession(sid);
    }
    const planLines = state.plan
      .map((n) => {
        const children = (n.children ?? [])
          .map((c) => `  - [${c.status ?? "pending"}] ${c.title}`)
          .join("\n");
        return `- **${n.title}** — ${n.status ?? "pending"}${children ? `\n${children}` : ""}`;
      })
      .join("\n");
    const fileLines = files.map((f) => `- \`${f.path}\``).join("\n");
    const agentLines = Object.values(state.agents)
      .map((a) => `- #${a.agent_number} ${a.agent} — ${a.status}`)
      .join("\n");
    const summary =
      `### Build ${state.done ? "complete" : "snapshot"}\n\n` +
      `**Stats** — ${state.stats.workflows} workflows · ${state.stats.files} files · ${state.stats.agents} agents · ${(state.stats.latencyMs / 1000).toFixed(1)}s\n\n` +
      (agentLines ? `**Agent swarm**\n${agentLines}\n\n` : "") +
      (planLines ? `**Task plan**\n${planLines}\n\n` : "") +
      (fileLines ? `**Files generated**\n${fileLines}\n\n` : "") +
      `_Tell me what to change, add, or remove and I'll re-run the swarm._`;
    useCodeStore.setState((s) => ({
      sessions: s.sessions.map((c) =>
        c.id === sid
          ? { ...c, messages: [...c.messages, { id: `${Date.now()}`, role: "assistant", content: summary }] }
          : c,
      ),
    }));
    setView("chat");
  };



  return (
    <div className="relative flex h-full flex-col overflow-hidden bg-[#0A0A0A] text-[#F5F5F5]">
      {/* Top status strip */}
      <StatusStrip
        modelName={activeModel.name}
        provider={activeModel.provider}
        onModelClick={() => {
          const idx = MODELS.findIndex((m) => m.id === model);
          setModel(MODELS[(idx + 1) % MODELS.length].id);
        }}
        onBackToChat={handleBackToChat}
        running={running}
        showBackToChat={view === "studio"}
      />

      <AnimatePresence>
        {(state.connection === "error" || state.connection === "closed") &&
          running === false &&
          state.connection === "error" && (
            <motion.div
              initial={{ y: -30, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              exit={{ y: -30, opacity: 0 }}
              className="absolute inset-x-0 top-14 z-10 mx-auto flex w-fit items-center gap-2 rounded-full border border-amber-500/40 bg-amber-500/10 px-3 py-1 text-[11.5px] text-amber-400"
            >
              <AlertTriangle className="h-3 w-3" />
              WebSocket disconnected — retrying
            </motion.div>
          )}
      </AnimatePresence>

      <AnimatePresence mode="wait">
        {view === "chat" ? (
          <motion.div
            key="chat"
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="flex flex-1 flex-col overflow-hidden"
          >
            <div className="flex items-center justify-between border-b border-white/5 px-4 py-2">
              <div className="flex items-center gap-2 text-[11px] text-white/50" style={{ fontFamily: MONO }}>
                <MessageSquare className="h-3 w-3 text-[#B4F03A]" />
                Code agent chat · {activeSession?.title ?? "New session"}
              </div>
              {started && (
                <button
                  onClick={() => setView("studio")}
                  className="rounded-md border border-white/10 bg-white/[0.03] px-2.5 py-1 text-[10.5px] text-white/70 transition-colors hover:border-[#B4F03A]/40 hover:text-white"
                  style={{ fontFamily: MONO }}
                >
                  Open studio →
                </button>
              )}
            </div>
            <div className="flex-1 overflow-y-auto settings-scroll px-4 pb-6 pt-4">
              <div className="mx-auto flex max-w-3xl flex-col gap-4">
                {(activeSession?.messages ?? []).map((m) => (
                  <div
                    key={m.id}
                    className={
                      m.role === "user"
                        ? "self-end max-w-[85%] rounded-xl border border-white/10 bg-white/[0.04] px-3.5 py-2.5 text-[13px] text-white/90"
                        : "self-start w-full rounded-xl border border-white/8 bg-[#141414] px-4 py-3 text-[13px] text-white/85"
                    }
                  >
                    {m.role === "assistant" ? <Markdown content={m.content} /> : m.content}
                  </div>
                ))}
                {(activeSession?.messages.length ?? 0) === 0 && (
                  <div className="rounded-xl border border-dashed border-white/10 bg-white/[0.02] p-6 text-center text-[12px] text-white/40">
                    No history yet — send a prompt to start a build.
                  </div>
                )}
              </div>
            </div>
            <div className="border-t border-white/5 bg-[#0A0A0A] px-4 py-3">
              <div className="mx-auto max-w-3xl">
                <InputBar onSubmit={handleSubmit} pending={running} hideTools />
              </div>
            </div>
          </motion.div>
        ) : !started ? (

          <motion.div
            key="hero"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0, filter: "blur(12px)", y: -20 }}
            transition={{ duration: 0.4 }}
            className="flex min-h-0 flex-1"
          >
            {/* Center focus */}
            <div className="min-w-0 flex-1 overflow-y-auto settings-scroll border-r border-white/5">
              <div className="mx-auto flex min-h-full max-w-3xl flex-col gap-8 px-6 py-10 lg:px-10 lg:py-14">
                <header className="space-y-3">
                  <div
                    className="text-[10px] uppercase tracking-[0.25em] text-[#B4F03A]"
                    style={{ fontFamily: MONO }}
                  >
                    &gt; INFIBUILD_STUDIO_v4.2
                  </div>
                  <h1
                    className="text-[32px] font-semibold tracking-tight leading-[1.05]"
                    style={{ fontFamily: MONO }}
                  >
                    Initiate build sequence.
                  </h1>
                  <p className="max-w-xl text-sm leading-relaxed text-white/50">
                    Multi-agent orchestration environment. Describe the system, and a deterministic
                    swarm — Planner, Architect, Coder, Reviewer, Tester, Deployer — will synthesise,
                    verify, and ship a runnable project.
                  </p>
                </header>

                {/* Prompt templates */}
                <section className="space-y-3">
                  <SectionLabel icon={<Zap className="h-3 w-3" />} label="Suggested prompts" />
                  <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
                    {PROMPT_TEMPLATES.map((t) => (
                      <button
                        key={t.id}
                        onClick={() => handleSubmit(t.title)}
                        className="group flex flex-col rounded-lg border border-white/8 bg-[#141414] p-4 text-left transition-all hover:-translate-y-0.5 hover:border-[#B4F03A]/50 hover:bg-[#161819]"
                      >
                        <span
                          className="text-[10px] tracking-widest text-[#B4F03A]"
                          style={{ fontFamily: MONO }}
                        >
                          {t.id}
                        </span>
                        <span className="mt-1.5 text-[13px] font-medium text-white/90">
                          {t.title}
                        </span>
                        <span className="mt-2 text-[11px] text-white/40">{t.sub}</span>
                        <ChevronRight className="mt-3 h-3.5 w-3.5 text-white/20 transition-colors group-hover:text-[#B4F03A]" />
                      </button>
                    ))}
                  </div>
                </section>

                {/* Live code stream preview */}
                <section className="space-y-3">
                  <SectionLabel icon={<TerminalIcon className="h-3 w-3" />} label="Deterministic pipeline preview" />
                  <div className="overflow-hidden rounded-lg border border-white/8 bg-[#0D0D0D]">
                    <div className="flex items-center gap-2 border-b border-white/5 px-4 py-2">
                      <span className="h-2 w-2 rounded-full bg-red-500/40" />
                      <span className="h-2 w-2 rounded-full bg-yellow-500/40" />
                      <span className="h-2 w-2 rounded-full bg-emerald-500/40" />
                      <span
                        className="ml-3 text-[10px] uppercase tracking-widest text-white/40"
                        style={{ fontFamily: MONO }}
                      >
                        agent_architect · defining topology
                      </span>
                      <span className="ml-auto text-[10px] text-white/30" style={{ fontFamily: MONO }}>
                        utf-8 · typescript
                      </span>
                    </div>
                    <pre
                      className="overflow-x-auto p-4 text-[12px] leading-[1.7]"
                      style={{ fontFamily: MONO }}
                    >
                      <code>
                        <span className="text-purple-400">import</span>{" "}
                        <span className="text-white/80">{"{ Orchestrator }"}</span>{" "}
                        <span className="text-purple-400">from</span>{" "}
                        <span className="text-orange-300">"@infibuild/core"</span>;
                        {"\n"}
                        <span className="text-white/30">
                          {"// initializing high-concurrency node"}
                        </span>
                        {"\n"}
                        <span className="text-blue-400">const</span>{" "}
                        <span className="text-white/90">app</span> ={" "}
                        <span className="text-purple-400">new</span>{" "}
                        <span className="text-emerald-300">Orchestrator</span>({"{"}
                        {"\n  "}threads: <span className="text-orange-300">16</span>,
                        {"\n  "}sandbox: <span className="text-orange-300">true</span>,
                        {"\n  "}pipeline: <span className="text-orange-300">'deterministic'</span>,
                        {"\n  "}model: <span className="text-orange-300">'{activeModel.id}'</span>,
                        {"\n"}
                        {"}"});
                        {"\n"}
                        <span className="ml-0 inline-block h-[13px] w-[6px] translate-y-[2px] animate-pulse bg-[#B4F03A]" />
                      </code>
                    </pre>
                  </div>
                </section>

                <div className="rounded-xl border border-white/8 bg-[#141414] p-3">
                  <div
                    className="mb-2 text-[10px] font-medium uppercase tracking-widest text-white/40"
                    style={{ fontFamily: MONO }}
                  >
                    &gt; Prompt
                  </div>
                  <InputBar onSubmit={handleSubmit} pending={running} hideTools placeholder="Describe the system to build…" />
                </div>

                <div className="h-16" />
              </div>
            </div>

            {/* Right telemetry rail */}
            <TelemetryRail modelName={activeModel.name} />
          </motion.div>
        ) : (
          <motion.div
            key="studio"
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex flex-1 flex-col gap-3 overflow-y-auto settings-scroll p-4 pt-6 pb-6"
          >
            <div className="flex gap-2 overflow-x-auto settings-scroll">
              <div className="shrink-0"><AIAgentPipeline state={state} running={running} /></div>
              <div className="min-w-0 flex-1"><AgentGraph state={state} running={running} /></div>
            </div>

            {state.done && (
              <motion.div
                initial={{ opacity: 0, y: -8 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-[#B4F03A]/30 bg-[#B4F03A]/[0.06] px-4 py-3"
              >
                <div className="flex items-center gap-2.5">
                  <span className="flex h-6 w-6 items-center justify-center rounded-full bg-[#B4F03A]/20 text-[#B4F03A]">
                    <Rocket className="h-3 w-3" />
                  </span>
                  <div>
                    <div className="text-[12px] font-medium text-white/90" style={{ fontFamily: MONO }}>
                      Build complete
                    </div>
                    <div className="text-[11px] text-white/50">
                      Need changes? Head back to chat to refine, add, or remove features.
                    </div>
                  </div>
                </div>
                <button
                  onClick={handleBackToChat}
                  className="inline-flex items-center gap-1.5 rounded-md border border-[#B4F03A]/40 bg-[#B4F03A]/10 px-3 py-1.5 text-[11px] font-medium text-[#B4F03A] transition-colors hover:bg-[#B4F03A]/20"
                  style={{ fontFamily: MONO }}
                >
                  <MessageSquare className="h-3 w-3" />
                  Back to chat
                  <ArrowLeft className="h-3 w-3 rotate-180" />
                </button>
              </motion.div>
            )}


            <div className="grid min-h-0 grid-cols-1 gap-3 lg:flex-1 lg:grid-cols-[280px_260px_1fr]">
              <div className="max-h-[420px] min-h-0 overflow-y-auto settings-scroll rounded-xl border border-white/8 bg-[#141414] p-3 lg:max-h-none">
                <div
                  className="mb-2 text-[10px] font-medium uppercase tracking-widest text-white/40"
                  style={{ fontFamily: MONO }}
                >
                  Task plan
                </div>
                <AgentTaskPlan plan={state.plan} />
              </div>

              <div className="max-h-[420px] min-h-0 lg:max-h-none">
                <FileExplorer
                  files={files}
                  selectedPath={activePath}
                  onSelect={setSelected}
                  flashPath={flash}
                />
              </div>

              <div className="min-h-[420px] overflow-hidden lg:min-h-0">
                <CodeEditor file={activeFile} />
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>





      {running && (
        <button
          onClick={cancel}
          className="absolute bottom-24 right-6 z-20 rounded-full border border-white/10 bg-[#141414] px-3 py-1 text-[11px] text-white/70 hover:text-white"
          style={{ fontFamily: MONO }}
        >
          Stop swarm
        </button>
      )}
    </div>
  );
}

function StatusStrip({
  modelName,
  provider,
  onModelClick,
  onBackToChat,
  running,
  showBackToChat,
}: {
  modelName: string;
  provider: string;
  onModelClick: () => void;
  onBackToChat: () => void;
  running: boolean;
  showBackToChat: boolean;
}) {
  return (
    <div className="flex h-12 shrink-0 items-center gap-2 border-b border-white/5 bg-[#0A0A0A]/80 px-3 backdrop-blur sm:px-4">
      <div className="flex min-w-0 flex-1 items-center gap-2 overflow-hidden text-[11px] sm:gap-3" style={{ fontFamily: MONO }}>
        {showBackToChat && (
          <button
            onClick={onBackToChat}
            className="flex shrink-0 items-center gap-1.5 rounded-md border border-white/10 bg-white/[0.03] px-2 py-1 text-[10.5px] text-white/70 transition-colors hover:border-[#B4F03A]/40 hover:text-white"
            title="Back to code agent chat"
          >
            <ArrowLeft className="h-3 w-3" />
            <span className="hidden sm:inline">Back to chat</span>
          </button>
        )}
        <span className="hidden text-white/40 md:inline">PROJ /</span>
        <span className="truncate font-semibold tracking-tight text-white/90">INFIBUILD_STUDIO</span>
        <span className="hidden shrink-0 items-center gap-1 rounded bg-white/5 px-2 py-0.5 text-[10px] text-[#B4F03A] sm:inline-flex">
          <GitBranch className="h-3 w-3" /> main
        </span>
        <span className="hidden shrink-0 items-center gap-1 text-white/30 lg:inline-flex">
          <ChevronRight className="h-3 w-3" />
          <span>{running ? "orchestrating" : "idle"}</span>
        </span>
      </div>

      <div className="flex shrink-0 items-center gap-2">
        <button
          onClick={onModelClick}
          className="flex items-center gap-1.5 rounded-md border border-white/10 bg-white/[0.03] px-2.5 py-1 text-[10.5px] text-white/70 transition-colors hover:border-[#B4F03A]/40 hover:text-white"
          style={{ fontFamily: MONO }}
          title="Cycle model"
        >
          <span className="h-1.5 w-1.5 rounded-full" style={{ background: LIME }} />
          <span className="hidden text-white/40 lg:inline">{provider}</span>
          <span className="max-w-[100px] truncate sm:max-w-none">{modelName}</span>
        </button>
        <div
          className="hidden items-center gap-1.5 rounded-md border border-white/10 bg-white/[0.03] px-2.5 py-1 text-[10.5px] text-white/70 lg:inline-flex"
          style={{ fontFamily: MONO }}
        >
          <span className={`h-1.5 w-1.5 rounded-full ${running ? "animate-pulse bg-[#B4F03A]" : "bg-emerald-500"}`} />
          SANDBOX · node20 · 2vCPU
        </div>
      </div>
    </div>
  );
}


function SectionLabel({ icon, label }: { icon: React.ReactNode; label: string }) {
  return (
    <div
      className="flex items-center gap-1.5 text-[10px] uppercase tracking-[0.22em] text-white/35"
      style={{ fontFamily: MONO }}
    >
      <span className="text-[#B4F03A]">{icon}</span>
      {label}
    </div>
  );
}

function TelemetryRail({ modelName }: { modelName: string }) {
  return (
    <aside className="hidden w-[280px] shrink-0 flex-col gap-4 overflow-y-auto settings-scroll bg-[#0D0D0D] p-4 lg:flex">
      <div>
        <div
          className="mb-3 flex items-center justify-between text-[10px] uppercase tracking-[0.22em] text-white/35"
          style={{ fontFamily: MONO }}
        >
          <span className="flex items-center gap-1.5">
            <Layers className="h-3 w-3 text-[#B4F03A]" /> Agent roster
          </span>
          <span className="text-[#B4F03A]">6 idle</span>
        </div>
        <div className="space-y-2">
          {AGENT_ROSTER.map((a, i) => (
            <div
              key={a.name}
              className="rounded-lg border border-white/8 bg-[#141414] p-2.5"
            >
              <div className="flex items-center gap-2">
                <span className="h-1.5 w-1.5 rounded-full bg-white/40" />
                <span className="text-[12px] font-medium text-white/90" style={{ fontFamily: MONO }}>
                  {a.name}
                </span>
                <span className="ml-auto text-[10px] text-white/30" style={{ fontFamily: MONO }}>
                  0{i + 1}
                </span>
              </div>
              <p className="mt-1 text-[10.5px] text-white/40">{a.note}</p>
            </div>
          ))}
        </div>
      </div>

      <div>
        <div
          className="mb-2 flex items-center gap-1.5 text-[10px] uppercase tracking-[0.22em] text-white/35"
          style={{ fontFamily: MONO }}
        >
          <Network className="h-3 w-3 text-[#B4F03A]" /> Capabilities
        </div>
        <div className="flex flex-wrap gap-1.5">
          {["Deep Thinking", "Deep Research", "Web", "Image"].map((c) => (
            <span
              key={c}
              className="rounded-full border border-white/10 bg-white/[0.03] px-2 py-0.5 text-[10px] text-white/60"
              style={{ fontFamily: MONO }}
            >
              {c}
            </span>
          ))}
        </div>
      </div>

      <div>
        <div
          className="mb-2 flex items-center gap-1.5 text-[10px] uppercase tracking-[0.22em] text-white/35"
          style={{ fontFamily: MONO }}
        >
          <Cpu className="h-3 w-3 text-[#B4F03A]" /> Telemetry
        </div>
        <div className="rounded-lg border border-white/8 bg-[#141414] p-3" style={{ fontFamily: MONO }}>
          <TelemetryRow label="CPU" value="12%" accent />
          <TelemetryRow label="RAM" value="1.4 GB" />
          <TelemetryRow label="NET" value="42 ms" />
          <TelemetryRow label="MODEL" value={modelName} truncate />
        </div>
      </div>

      <div className="mt-auto rounded-lg border border-white/8 bg-[#141414] p-3">
        <div
          className="mb-1 flex items-center gap-1.5 text-[10px] uppercase tracking-[0.22em] text-[#B4F03A]"
          style={{ fontFamily: MONO }}
        >
          <Rocket className="h-3 w-3" /> Ready
        </div>
        <p className="text-[11px] leading-relaxed text-white/50">
          Sandbox warm. Deterministic pipeline armed. Submit a prompt to launch the swarm.
        </p>
      </div>
    </aside>
  );
}

function TelemetryRow({
  label,
  value,
  accent = false,
  truncate = false,
}: {
  label: string;
  value: string;
  accent?: boolean;
  truncate?: boolean;
}) {
  return (
    <div className="flex items-center justify-between py-1 text-[11px]">
      <span className="text-white/35">{label}</span>
      <span
        className={`${accent ? "text-[#B4F03A]" : "text-white/85"} ${truncate ? "max-w-[140px] truncate" : ""}`}
      >
        {value}
      </span>
    </div>
  );
}
