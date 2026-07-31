import { useEffect, useState, useRef } from "react";
import { m, LazyMotion, domAnimation, AnimatePresence } from "framer-motion";

/* ─── Pipeline Variant Configurations ─── */

type PipelineVariant = "research" | "thinking" | "code";

interface PipelineConfig {
  title: string;
  agentCount: number;
  nodes: { label: string; sublabel: string; id: string }[];
  outputs: { label: string; status: "done" | "active" | "queued" }[];
  messages: string[];
  stats: { label: string; value: string }[];
  stack: string;
}

const VARIANT_CONFIGS: Record<PipelineVariant, PipelineConfig> = {
  research: {
    title: "DEEP RESEARCH PIPELINE",
    agentCount: 11,
    nodes: [
      { label: "User Query", sublabel: "TRIGGER", id: "node-01" },
      { label: "Web Crawl", sublabel: "SEARCH", id: "serper-api" },
      { label: "Synthesizer", sublabel: "LLM AGENT", id: "nemotron" },
    ],
    outputs: [
      { label: "Source Index", status: "done" },
      { label: "Fact Check", status: "active" },
      { label: "Report Gen", status: "queued" },
    ],
    messages: [
      "Initializing 12-agent pipeline...",
      "Dispatching 12 research agents in parallel",
      "Agent SearchMaster: Crawling 24 web sources...",
      "Agent FactChecker: Cross-referencing 8 claims",
      "Agent Synthesizer: Building citation graph (47 nodes)",
      "Vector search: 12 chunks, avg cosine sim 0.91",
      "Agent ReportWriter: Structuring executive summary",
      "Agent QualityReviewer: Confidence score 94.2%",
      "Final synthesis: 2,847 tokens, 24 sources cited",
      "Pipeline complete. Report ready for delivery.",
    ],
    stats: [
      { label: "WORKFLOWS", value: "342" },
      { label: "SOURCES", value: "24" },
      { label: "AGENTS", value: "12" },
      { label: "LATENCY", value: "4.2s" },
    ],
    stack: "Nemotron · Serper · RAG",
  },
  thinking: {
    title: "DEEP THINKING PIPELINE",
    agentCount: 5,
    nodes: [
      { label: "Problem", sublabel: "INPUT", id: "node-01" },
      { label: "Chain-of-Thought", sublabel: "REASONER", id: "cot-engine" },
      { label: "Verifier", sublabel: "LLM AGENT", id: "nemotron" },
    ],
    outputs: [
      { label: "Analysis", status: "done" },
      { label: "Verification", status: "active" },
      { label: "Synthesis", status: "queued" },
    ],
    messages: [
      'Received: "Prove that the sum of angles..."',
      "Decomposing problem into 4 sub-problems",
      "Step 1: Analyzing base assumptions → valid",
      "Step 2: Applying logical chain → 3 inferences",
      "Step 3: Verifying intermediate conclusions",
      "Confidence: 96.8% across all reasoning steps",
      "Cross-checking with adversarial counter-examples",
      "Synthesizing final proof with citations",
      "Quality gate passed: logical consistency 99.1%",
      "Reasoning complete. 4 steps, 0 contradictions.",
    ],
    stats: [
      { label: "WORKFLOWS", value: "891" },
      { label: "STEPS", value: "4" },
      { label: "CONFIDENCE", value: "96.8%" },
      { label: "LATENCY", value: "1.8s" },
    ],
    stack: "Nemotron · CoT · Verify",
  },
  code: {
    title: "INFIBUILD AGENT SWARM",
    agentCount: 6,
    nodes: [
      { label: "User Spec", sublabel: "TRIGGER", id: "node-01" },
      { label: "Architect", sublabel: "PLANNER", id: "architect" },
      { label: "Coder Swarm", sublabel: "LLM AGENTS", id: "coders" },
    ],
    outputs: [
      { label: "Frontend", status: "done" },
      { label: "Backend", status: "active" },
      { label: "Tests", status: "queued" },
    ],
    messages: [
      'Received: "Build a task management app with React..."',
      "Architect: Designing system components and tech stack",
      "SpecWriter: Detailing functional requirements and APIs",
      "TaskDecomposer: Breaking into 8 parallel coding tasks",
      "CoderSwarm: 4 agents generating source code",
      "Agent Coder-1: Writing React components (src/App.tsx)",
      "Agent Coder-2: Building FastAPI endpoints (api/routes.py)",
      "Agent Coder-3: Creating database models (models/task.py)",
      "Tester: Running automated test suite → 12/12 passed",
      "Build complete. 23 files generated in 8.4s.",
    ],
    stats: [
      { label: "WORKFLOWS", value: "1,247" },
      { label: "FILES", value: "23" },
      { label: "AGENTS", value: "6" },
      { label: "LATENCY", value: "8.4s" },
    ],
    stack: "Nemotron · Swarm · Tests",
  },
};

/* ─── Sub-components ─── */

function StatusIndicator({
  status,
}: {
  status: "done" | "active" | "queued" | string;
}) {
  if (status === "active" || status === "running") {
    return (
      <m.div
        className="w-[6px] h-[6px] rounded-full shrink-0"
        style={{ background: "var(--color-warning)" }}
        animate={{ opacity: [0.3, 1, 0.3] }}
        transition={{ duration: 1.5, repeat: Infinity, ease: "easeInOut" }}
      />
    );
  }
  if (status === "done" || status === "completed") {
    return <div className="w-[6px] h-[6px] rounded-full shrink-0" style={{ background: "var(--color-success)", opacity: 0.9 }} />;
  }
  if (status === "error") {
    return <div className="w-[6px] h-[6px] rounded-full shrink-0" style={{ background: "var(--color-error)", opacity: 0.9 }} />;
  }
  return <div className="w-[6px] h-[6px] rounded-full shrink-0" style={{ background: "var(--color-text-tertiary)", opacity: 0.3 }} />;
}

export interface DynamicNode {
  id: string;
  label: string;
  sublabel?: string;
  status?: "pending" | "running" | "completed" | "error";
}

/* ─── Main Component ─── */

export interface AgentPipelineProps {
  variant?: PipelineVariant;
  className?: string;
  dynamicStats?: { label: string; value: string | number }[];
  dynamicMessages?: string[];
  dynamicOutputs?: { label: string; status: "done" | "active" | "queued" }[];
  dynamicStack?: string;
  dynamicNodes?: DynamicNode[];
  agentCount?: number;
}

export default function AIAgentPipeline({ 
  variant = "code", 
  agentCount = 12,
  className = "", 
  dynamicStats, 
  dynamicMessages, 
  dynamicOutputs, 
  dynamicStack, 
  dynamicNodes 
}: AgentPipelineProps) {
  const config = VARIANT_CONFIGS[variant];
  const [messageLog, setMessageLog] = useState<string[]>([]);
  const [workflows, setWorkflows] = useState(1247);
  const logEndRef = useRef<HTMLDivElement>(null);

  // Manage terminal log scrolling
  useEffect(() => {
    if (dynamicMessages && dynamicMessages.length > 0) {
      setMessageLog(prev => {
        const newMsg = dynamicMessages[dynamicMessages.length - 1];
        if (prev[prev.length - 1] === newMsg) return prev; // Prevent duplicates
        const updated = [...prev, newMsg];
        return updated.slice(-10); // Keep last 10 messages for history
      });
    } else {
      // Fake ticker if no dynamic messages
      const interval = setInterval(() => {
        setMessageLog(prev => {
          const nextIdx = (prev.length % config.messages.length);
          const newMsg = config.messages[nextIdx];
          const updated = [...prev, newMsg];
          return updated.slice(-10);
        });
      }, 2700);
      return () => clearInterval(interval);
    }
  }, [dynamicMessages, config.messages]);

  useEffect(() => {
    if (logEndRef.current) {
      logEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messageLog]);

  // Fallback fake workflows increment
  useEffect(() => {
    const workflowInterval = setInterval(() => {
      setWorkflows((prev) => prev + 1);
    }, 7200);
    return () => clearInterval(workflowInterval);
  }, []);

  const nodesToRender = dynamicNodes || config.nodes.slice(1).map(n => ({ ...n, status: "running" as const }));

  return (
    <LazyMotion features={domAnimation}>
      <div
        className={`rounded-[14px] overflow-hidden font-sans w-full max-w-[640px] mx-auto flex flex-col ${className}`}
        style={{
          background: "var(--color-surface)",
          border: "1px solid var(--color-border)",
        }}
      >
        {/* Header */}
        <div
          className="px-[18px] py-[11px] flex items-center justify-between shrink-0"
          style={{ borderBottom: "1px solid var(--color-border)", background: "rgba(0,0,0,0.2)" }}
        >
          <div className="flex items-center gap-2">
            <m.div
              className="w-[8px] h-[8px] rounded-full"
              style={{ background: "var(--color-error)" }} // Red recording dot
              animate={{ opacity: [1, 0.2, 1], scale: [1, 1.2, 1] }}
              transition={{ duration: 1.5, repeat: Infinity, ease: "easeInOut" }}
            />
            <span
              className="text-[10px] tracking-[0.1em] font-mono font-bold"
              style={{ color: "var(--color-text-secondary)" }}
            >
              {config.title} <span style={{ color: "var(--color-text-tertiary)" }}>· LIVE</span>
            </span>
          </div>
          <span
            className="text-[10px] font-mono"
            style={{ color: "var(--color-text-tertiary)", opacity: 0.5 }}
          >
            {dynamicNodes ? dynamicNodes.length : config.agentCount} nodes · 0 errors
          </span>
        </div>

        {/* SVG Pipeline Visualization with Animated Dotted Lines */}
        <svg width="100%" viewBox="0 0 600 200" className="block" style={{ minHeight: 172 }}>
          <defs>
            {/* Arrow marker */}
            <marker
              id={`arrow-${variant}`}
              viewBox="0 0 10 10"
              refX="8" refY="5"
              markerWidth="5" markerHeight="5"
              orient="auto"
            >
              <path
                d="M2 1.5L7.5 5L2 8.5"
                fill="none"
                stroke="var(--color-accent)"
                strokeWidth="1.6"
                strokeLinecap="round"
                strokeLinejoin="round"
                opacity={0.5}
              />
            </marker>
            {/* Glow filter for active nodes */}
            <filter id={`glow-${variant}`}>
              <feGaussianBlur stdDeviation="3" result="blur" />
              <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
            </filter>
          </defs>

          {/* ── Connection Path: Trigger → Engine ── */}
          <path
            d="M116,100 L180,100"
            fill="none"
            stroke="var(--color-accent)"
            strokeWidth="1.5"
            strokeDasharray="4 6"
            opacity={0.25}
            markerEnd={`url(#arrow-${variant})`}
          />
          {/* Animated dots on Trigger→Engine */}
          <circle r={2.8} className="fill-[var(--color-accent)]" opacity={1}>
            <animateMotion dur="1.1s" repeatCount="indefinite" begin="0s" path="M116,100 L180,100" />
          </circle>
          <circle r={2} className="fill-[var(--color-accent)]" opacity={0.55}>
            <animateMotion dur="1.1s" repeatCount="indefinite" begin="0.4s" path="M116,100 L180,100" />
          </circle>
          <circle r={1.3} className="fill-[var(--color-accent)]" opacity={0.3}>
            <animateMotion dur="1.1s" repeatCount="indefinite" begin="0.75s" path="M116,100 L180,100" />
          </circle>

          {/* ── Connection Path: Engine → Output Top ── */}
          <path
            d="M420,100 C440,100 445,55 460,55"
            fill="none"
            stroke="var(--color-accent)"
            strokeWidth="1.5"
            strokeDasharray="4 6"
            opacity={0.2}
          />
          <circle r={2.2} className="fill-[var(--color-accent)]" opacity={0.9}>
            <animateMotion dur="1.3s" repeatCount="indefinite" begin="0.1s" path="M420,100 C440,100 445,55 460,55" />
          </circle>
          <circle r={1.4} className="fill-[var(--color-accent)]" opacity={0.45}>
            <animateMotion dur="1.3s" repeatCount="indefinite" begin="0.6s" path="M420,100 C440,100 445,55 460,55" />
          </circle>

          {/* ── Connection Path: Engine → Output Middle ── */}
          <path
            d="M420,100 L460,100"
            fill="none"
            stroke="var(--color-accent)"
            strokeWidth="1.5"
            strokeDasharray="4 6"
            opacity={0.2}
            markerEnd={`url(#arrow-${variant})`}
          />
          <circle r={2.2} className="fill-[var(--color-accent)]" opacity={0.9}>
            <animateMotion dur="1.0s" repeatCount="indefinite" begin="0.25s" path="M420,100 L460,100" />
          </circle>
          <circle r={1.4} className="fill-[var(--color-accent)]" opacity={0.45}>
            <animateMotion dur="1.0s" repeatCount="indefinite" begin="0.7s" path="M420,100 L460,100" />
          </circle>

          {/* ── Connection Path: Engine → Output Bottom ── */}
          <path
            d="M420,100 C440,100 445,145 460,145"
            fill="none"
            stroke="var(--color-accent)"
            strokeWidth="1.5"
            strokeDasharray="4 6"
            opacity={0.2}
          />
          <circle r={2.2} className="fill-[var(--color-accent)]" opacity={0.9}>
            <animateMotion dur="1.4s" repeatCount="indefinite" begin="0.4s" path="M420,100 C440,100 445,145 460,145" />
          </circle>
          <circle r={1.4} className="fill-[var(--color-accent)]" opacity={0.45}>
            <animateMotion dur="1.4s" repeatCount="indefinite" begin="0.9s" path="M420,100 C440,100 445,145 460,145" />
          </circle>

          {/* ── Node 1: Trigger ── */}
          <rect x="16" y="78" width="100" height="44" rx="8" fill="var(--color-bg)" stroke="var(--color-border)" strokeWidth="0.5" />
          <text x="66" y="95" textAnchor="middle" fontSize="9.5" fill="var(--color-text-tertiary)" fontFamily="system-ui" letterSpacing=".07em">
            {config.nodes[0].sublabel}
          </text>
          <text x="66" y="112" textAnchor="middle" fontSize="12" fill="var(--color-text-primary)" fontFamily="system-ui">
            {config.nodes[0].label}
          </text>

          {/* ── Node 2: Execution Engine (dynamic agents inside) ── */}
          <rect x="180" y="42" width="240" height="146" rx="12" fill="var(--color-bg)" stroke="var(--color-accent)" strokeWidth="1" opacity={0.9} />
          {/* Accent top bar */}
          <rect x="194" y="42.5" width="60" height="1" rx="0.5" fill="var(--color-accent)" opacity={0.5} />
          {/* Engine label */}
          <text x="196" y="58" fontSize="8" fill="var(--color-accent)" fontFamily="monospace" letterSpacing=".1em" opacity={0.7}>
            EXECUTION ENGINE
          </text>
          {/* Pulsing dot next to label */}
          <m.circle cx="280" cy="55" r={2.5} className="fill-[var(--color-accent)]"
            animate={{ opacity: [0.15, 1, 0.15] }}
            transition={{ duration: 1.2, repeat: Infinity, ease: "easeInOut" }}
          />

          {/* Dynamic node chips via foreignObject */}
          <foreignObject x="186" y="62" width="228" height="120">
            <div className="flex flex-wrap gap-[5px] justify-center p-1 overflow-y-auto" style={{ maxHeight: 118 }}>
              {nodesToRender.map((node) => (
                <div 
                  key={node.id} 
                  className="relative flex items-center gap-1.5 px-2 py-[3px] rounded border"
                  style={{ 
                    background: "rgba(0,0,0,0.5)",
                    borderColor: node.status === "running" ? "var(--color-accent)" : node.status === "completed" ? "var(--color-success)" : node.status === "error" ? "var(--color-error)" : "var(--color-border)",
                    opacity: node.status === "pending" ? 0.45 : 1
                  }}
                >
                  {node.status === "running" && (
                    <m.div 
                      className="absolute inset-0 rounded pointer-events-none"
                      style={{ background: "var(--color-accent)" }}
                      animate={{ opacity: [0.06, 0.18, 0.06] }}
                      transition={{ duration: 1.2, repeat: Infinity }}
                    />
                  )}
                  <StatusIndicator status={node.status || "active"} />
                  <span className="text-[8px] whitespace-nowrap truncate max-w-[60px] relative z-10" style={{ color: "var(--color-text-secondary)" }}>
                    {node.label}
                  </span>
                </div>
              ))}
            </div>
          </foreignObject>

          {/* ── Output Nodes ── */}
          {(dynamicOutputs || config.outputs).map((output, i) => {
            const y = 40 + i * 45;
            const isActive = output.status === "active";
            const isDone = output.status === "done";
            return (
              <g key={output.label}>
                <rect x="460" y={y} width="124" height="30" rx="7" fill="var(--color-bg)" stroke={isDone ? "var(--color-success)" : isActive ? "var(--color-warning)" : "var(--color-border)"} strokeWidth={isDone || isActive ? "0.8" : "0.5"} />
                <text x="502" y={y + 18.5} textAnchor="middle" fontSize="11" fill="var(--color-text-secondary)" fontFamily="system-ui">
                  {output.label}
                </text>
                {/* Status dot */}
                {isActive ? (
                  <m.circle cx="570" cy={y + 8} r={3.5} className="fill-[var(--color-warning)]"
                    animate={{ opacity: [0.3, 1, 0.3] }}
                    transition={{ duration: 1.8, delay: i * 0.3, repeat: Infinity, ease: "easeInOut" }}
                  />
                ) : isDone ? (
                  <circle cx="570" cy={y + 8} r={3.5} className="fill-[var(--color-success)]" opacity={0.9} />
                ) : (
                  <circle cx="570" cy={y + 8} r={3.5} className="fill-[var(--color-text-tertiary)]" opacity={0.3} />
                )}
              </g>
            );
          })}
        </svg>

        {/* ── Professional Terminal Trace Log ── */}
        <div
          className="flex flex-col"
          style={{ borderTop: "1px solid var(--color-border)" }}
        >
          {/* Terminal toolbar */}
          <div className="flex items-center justify-between px-[18px] py-[6px]" style={{ background: "rgba(0,0,0,0.4)", borderBottom: "1px solid var(--color-border)" }}>
            <div className="flex items-center gap-2">
              <div className="flex gap-[5px]">
                <div className="w-[7px] h-[7px] rounded-full" style={{ background: "#ff5f57" }} />
                <div className="w-[7px] h-[7px] rounded-full" style={{ background: "#febc2e" }} />
                <div className="w-[7px] h-[7px] rounded-full" style={{ background: "#28c840" }} />
              </div>
              <span className="text-[9px] font-mono tracking-widest uppercase ml-2" style={{ color: "var(--color-text-tertiary)", opacity: 0.6 }}>
                trace · telemetry
              </span>
            </div>
            <div className="flex items-center gap-1.5">
              <m.div
                className="w-[5px] h-[5px] rounded-full"
                style={{ background: "var(--color-success)" }}
                animate={{ opacity: [1, 0.3, 1] }}
                transition={{ duration: 1.5, repeat: Infinity }}
              />
              <span className="text-[8px] font-mono" style={{ color: "var(--color-text-tertiary)", opacity: 0.5 }}>
                {messageLog.length} events
              </span>
            </div>
          </div>
          {/* Terminal body */}
          <div className="h-[80px] overflow-y-auto custom-scrollbar font-mono text-[10px] leading-[1.7] bg-black/70 px-[18px] py-[8px]">
            {messageLog.length === 0 ? (
              <div className="flex items-center gap-2 opacity-40">
                <m.span
                  animate={{ opacity: [1, 0, 1] }}
                  transition={{ duration: 1, repeat: Infinity }}
                  style={{ color: "var(--color-accent)" }}
                >▋</m.span>
                <span style={{ color: "var(--color-text-tertiary)" }}>Awaiting pipeline telemetry...</span>
              </div>
            ) : (
              messageLog.map((msg, idx) => {
                const lineNum = String(idx + 1).padStart(3, "0");
                const isLatest = idx === messageLog.length - 1;
                return (
                  <m.div 
                    key={`log-${idx}`}
                    initial={{ opacity: 0, x: -8 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ duration: 0.2 }}
                    className="flex gap-0 items-start"
                  >
                    <span className="w-[28px] shrink-0 text-right mr-2 select-none" style={{ color: "var(--color-text-tertiary)", opacity: 0.2 }}>
                      {lineNum}
                    </span>
                    <span className="shrink-0 mr-1.5" style={{ color: isLatest ? "var(--color-accent)" : "var(--color-text-tertiary)", opacity: isLatest ? 0.9 : 0.3 }}>
                      {isLatest ? "▸" : "│"}
                    </span>
                    <span className="truncate" style={{ color: isLatest ? "var(--color-text-primary)" : "var(--color-text-tertiary)", opacity: isLatest ? 1 : 0.55 }}>
                      {msg}
                    </span>
                    {isLatest && (
                      <m.span
                        animate={{ opacity: [1, 0, 1] }}
                        transition={{ duration: 0.8, repeat: Infinity }}
                        className="ml-1"
                        style={{ color: "var(--color-accent)" }}
                      >▋</m.span>
                    )}
                  </m.div>
                );
              })
            )}
            <div ref={logEndRef} />
          </div>
        </div>

        {/* Stats Footer */}
        <div
          className="px-[18px] py-[10px] flex gap-[22px] items-center shrink-0 bg-black/40"
          style={{ borderTop: "1px solid var(--color-border)" }}
        >
          {config.stats.map(stat => {
            const dyn = dynamicStats?.find(d => d.label === stat.label);
            return dyn ? { ...stat, value: String(dyn.value) } : stat;
          }).map((stat) => (
            <div key={stat.label}>
              <div className="text-[9px] tracking-[0.09em] mb-[3px]" style={{ color: "var(--color-text-tertiary)", opacity: 0.6 }}>
                {stat.label}
              </div>
              <div className="text-[14px] font-mono" style={{ color: "var(--color-text-secondary)" }}>
                {stat.value}
              </div>
            </div>
          ))}
          <div className="ml-auto text-right">
            <div className="text-[9px] tracking-[0.09em] mb-[3px]" style={{ color: "var(--color-text-tertiary)", opacity: 0.4 }}>
              STACK
            </div>
            <div className="text-[10px] font-mono" style={{ color: "var(--color-text-tertiary)", opacity: 0.8 }}>
              {dynamicStack || config.stack}
            </div>
          </div>
        </div>
      </div>
    </LazyMotion>
  );
}
