import { useCallback, useEffect, useRef, useState } from "react";
import { runCodeSquad, type CodeEvent } from "@/lib/streams";

export type PlanNode = { id: number; title: string; status?: "pending" | "running" | "completed"; children?: PlanNode[] };
export type AgentSlot = { agent_number: number; agent: string; status: "queued" | "running" | "completed" | "error"; message: string };
export type GenFile = { path: string; content: string; generating?: boolean };
export type ConnectionState = "idle" | "connecting" | "open" | "closed" | "error";

export type CodeSquadState = {
  plan: PlanNode[];
  agents: Record<number, AgentSlot>;
  files: Record<string, GenFile>;
  rawStream: string;
  currentFilePath: string | null;
  stats: { workflows: number; files: number; agents: number; latencyMs: number };
  done: boolean;
  connection: ConnectionState;
};

const empty: CodeSquadState = {
  plan: [],
  agents: {},
  files: {},
  rawStream: "",
  currentFilePath: null,
  stats: { workflows: 0, files: 0, agents: 0, latencyMs: 0 },
  done: false,
  connection: "idle",
};

// Regex to detect "// filepath: <path>" markers inside streaming markdown chunks.
const FILEPATH_RE = /\/\/\s*filepath:\s*([^\n\r]+)/i;

export function useCodeSquad() {
  const [state, setState] = useState<CodeSquadState>(empty);
  const [running, setRunning] = useState(false);
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => () => abortRef.current?.abort(), []);

  const setStatusForTask = (plan: PlanNode[], taskId: number, status: PlanNode["status"]): PlanNode[] =>
    plan.map((n) => ({
      ...n,
      status: n.id === taskId ? status : n.status,
      children: n.children ? setStatusForTask(n.children, taskId, status) : undefined,
    }));

  const start = useCallback(async (prompt: string) => {
    abortRef.current?.abort();
    const ctrl = new AbortController();
    abortRef.current = ctrl;
    setState({ ...empty, connection: "connecting" });
    setRunning(true);

    // Simulated WebSocket handshake
    await new Promise((r) => setTimeout(r, 300));
    setState((s) => ({ ...s, connection: "open" }));

    try {
      await runCodeSquad(prompt, (e: CodeEvent) => {
        setState((prev) => {
          switch (e.type) {
            case "plan":
              return { ...prev, plan: e.tree.map((n) => ({ ...n, status: "pending", children: n.children?.map((c) => ({ ...c, status: c.status as PlanNode["status"] })) })) };
            case "agent_status":
              return { ...prev, agents: { ...prev.agents, [e.agent_number]: { agent_number: e.agent_number, agent: e.agent, status: e.status, message: e.message } } };
            case "code_progress":
              return { ...prev, plan: setStatusForTask(prev.plan, Number(e.task_id), e.status === "running" ? "running" : "completed") };
            case "code_chunk": {
              const raw = prev.rawStream + e.chunk;
              const match = e.chunk.match(FILEPATH_RE);
              let currentFilePath = prev.currentFilePath;
              const files = { ...prev.files };
              if (match) {
                currentFilePath = match[1].trim();
                files[currentFilePath] = { path: currentFilePath, content: "", generating: true };
                return { ...prev, rawStream: raw, currentFilePath, files };
              }
              if (currentFilePath) {
                const cur = files[currentFilePath] ?? { path: currentFilePath, content: "" };
                // strip stray fence remnants so on-disk content stays clean
                const cleaned = e.chunk.replace(/```[a-z]*\n?/gi, "");
                files[currentFilePath] = { ...cur, content: cur.content + cleaned, generating: true };
              }
              return { ...prev, rawStream: raw, files };
            }
            case "code_generated": {
              const files = { ...prev.files, [e.file.path]: { path: e.file.path, content: e.file.content, generating: false } };
              return { ...prev, files, currentFilePath: e.file.path };
            }
            case "stats":
              return { ...prev, stats: { workflows: e.workflows, files: e.files, agents: e.agents, latencyMs: e.latencyMs } };
            case "done":
              return { ...prev, done: true, connection: "closed" };
          }
          return prev;
        });
      }, ctrl.signal);
    } catch {
      setState((s) => ({ ...s, connection: "error" }));
    } finally {
      setRunning(false);
    }
  }, []);

  const cancel = useCallback(() => {
    abortRef.current?.abort();
    setState((s) => ({ ...s, connection: "closed" }));
  }, []);

  const reset = useCallback(() => setState(empty), []);

  return { state, running, start, cancel, reset };
}
