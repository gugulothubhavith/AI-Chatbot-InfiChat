import { useCallback, useEffect, useRef, useState } from "react";
import { runResearchStream, type ResearchEvent } from "@/lib/streams";

export type AgentState = {
  name: string;
  status: "queued" | "running" | "completed" | "error";
  message: string;
  ts: number;
};
export type Source = { title: string; url: string; favicon?: string | null; snippet?: string };
export type Finding = { claim: string; confidence: number; source_count: number };
export type QualityGate = { iteration: number; verdict: "pass" | "fail"; confidence: number };
export type LogEntry = { ts: number; agent: string; status: AgentState["status"]; message: string };

export type ResearchProgress = {
  stageKey: string;
  stage: number;
  totalStages: number;
  stageMessage: string;
  plan: { id: number; title: string; children?: { id: number; title: string }[] }[];
  agents: Record<string, AgentState>;
  logs: LogEntry[];
  sources: Source[];
  findings: Finding[];
  gates: QualityGate[];
  complete: boolean;
  report?: {
    content: string;
    executive_summary: string;
    citations: { title: string; url: string }[];
    fact_count: number;
  };
};

const empty: ResearchProgress = {
  stageKey: "",
  stage: 0,
  totalStages: 12,
  stageMessage: "",
  plan: [],
  agents: {},
  logs: [],
  sources: [],
  findings: [],
  gates: [],
  complete: false,
};

export function useResearchStream() {
  const [state, setState] = useState<ResearchProgress>(empty);
  const [running, setRunning] = useState(false);
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => () => abortRef.current?.abort(), []);

  const start = useCallback(async (prompt: string) => {
    abortRef.current?.abort();
    const ctrl = new AbortController();
    abortRef.current = ctrl;
    setState(empty);
    setRunning(true);
    try {
      await runResearchStream(prompt, (e: ResearchEvent) => {
        setState((prev): ResearchProgress => {
          switch (e.type) {
            case "research_stage":
              return { ...prev, stageKey: e.stage, stage: e.stage_number, totalStages: e.total_stages, stageMessage: e.message };
            case "plan":
              return { ...prev, plan: e.tree };
            case "agent_status": {
              const ts = Date.now();
              return {
                ...prev,
                agents: { ...prev.agents, [e.agent]: { name: e.agent, status: e.status, message: e.message, ts } },
                logs: [...prev.logs, { ts, agent: e.agent, status: e.status, message: e.message }].slice(-200),
              };
            }
            case "source_found":
              return { ...prev, sources: [...prev.sources, e.source] };
            case "partial_finding":
              return { ...prev, findings: [...prev.findings, { claim: e.claim, confidence: e.confidence, source_count: e.source_count }] };
            case "quality_gate":
              return { ...prev, gates: [...prev.gates, { iteration: e.iteration, verdict: e.verdict, confidence: e.confidence }] };
            case "report":
              return {
                ...prev,
                complete: true,
                report: { content: e.content, executive_summary: e.executive_summary, citations: e.citations, fact_count: e.fact_count },
              };
            case "done":
              return { ...prev, complete: true };
          }
          return prev;
        });
      }, ctrl.signal);
    } finally {
      setRunning(false);
    }
  }, []);

  const cancel = useCallback(() => abortRef.current?.abort(), []);
  const reset = useCallback(() => setState(empty), []);

  return { state, running, start, cancel, reset };
}
