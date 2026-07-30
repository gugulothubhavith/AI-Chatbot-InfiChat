/**
 * Real SSE / WebSocket streaming utilities for InfiChat.
 *
 * Each function opens a real connection to the backend and calls `onEvent`
 * with typed payloads as they arrive.  If the backend is unreachable (no
 * VITE_API_URL set, CORS, or server down) the caller gets an error event.
 */

import { api } from "@/lib/api";

// ── Shared SSE parser ──────────────────────────────────────

async function parseSSE<E>(
  response: Response,
  onEvent: (e: E) => void,
  signal: AbortSignal,
): Promise<void> {
  const reader = response.body?.getReader();
  if (!reader) return;
  const decoder = new TextDecoder();
  let buffer = "";

  try {
    while (!signal.aborted) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() ?? "";
      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed.startsWith("data:")) continue;
        const dataStr = trimmed.slice(5).trim();
        if (!dataStr || dataStr === "[DONE]") continue;
        try {
          onEvent(JSON.parse(dataStr) as E);
        } catch {
          // malformed JSON, skip
        }
      }
    }
  } finally {
    reader.releaseLock();
  }
}

// ── Event types ────────────────────────────────────────────

export type ThinkingEvent =
  | { type: "thinking_progress"; stage: string; message: string; confidence: number; sub_problems?: string[] }
  | { type: "reasoning_step"; step_number: number; title: string; content: string; confidence: number; status: "pending" | "verified" }
  | { type: "thinking_complete"; report: { executive_summary: string; reasoning_chain: { title: string; content: string }[] } }
  | { type: "error"; message: string }
  | { type: "done" };

export type ResearchEvent =
  | { type: "research_stage"; stage: string; stage_number: number; total_stages: number; message: string }
  | { type: "agent_status"; agent: string; status: "queued" | "running" | "completed" | "error"; message: string; agent_number?: number; data?: Record<string, unknown> }
  | { type: "plan"; tree: { id: number; title: string; priority?: string; status?: string; children?: { id: number; title: string }[] }[] }
  | { type: "source_found"; source: { id?: string; title: string; url: string; favicon?: string | null; snippet?: string; domain?: string; authority?: number; source_type?: string } }
  | { type: "partial_finding"; claim: string; confidence: number; source_count: number; stance?: string }
  | { type: "quality_gate"; iteration: number; verdict: "pass" | "fail"; raw_verdict?: string; confidence: number; feedback?: string; checks?: unknown[] }
  | { type: "report"; content: string; executive_summary: string; citations: { title: string; url: string }[]; fact_count: number; confidence?: number; source_count?: number; entity_count?: number }
  | { type: "done"; research_id?: string; total_sources?: number; verified_facts?: number; iterations?: number }
  | { type: "error"; message: string };

export type WebSearchEvent =
  | { type: "status"; message: string }
  | { type: "source"; source: { title: string; url: string; favicon?: string; snippet?: string } }
  | { type: "report"; content: string; citations: { index: number; title: string; url: string }[] }
  | { type: "error"; message: string }
  | { type: "done" };

export type CodeEvent =
  | { type: "plan"; tree: { id: number; title: string; children?: { id: number; title: string; status?: string }[] }[] }
  | { type: "agent_status"; agent_number: number; agent: string; status: "queued" | "running" | "completed" | "error"; message: string; data?: Record<string, unknown> }
  | { type: "code_progress"; task_id: string; title?: string; status: "running" | "completed" | "failed" | "error"; files?: { path: string; language: string }[]; error?: string; message?: string }
  | { type: "code_chunk"; chunk: string; task_id?: string }
  | { type: "code_generated"; file: { path: string; content: string; language?: string } }
  | { type: "report"; content: string; files: { path: string; content: string; language: string; description?: string }[]; architecture?: Record<string, unknown>; tasks?: { id: string; title: string; status: string }[] }
  | { type: "stats"; workflows: number; files: number; agents: number; latencyMs: number }
  | { type: "done"; session_id?: string; total_files?: number; total_tasks?: number }
  | { type: "error"; message: string };

// ── Thinking stream ────────────────────────────────────────

export async function runThinkingStream(
  prompt: string,
  onEvent: (e: ThinkingEvent) => void,
  signal: AbortSignal,
): Promise<void> {
  try {
    const res = await api.fetchSSE("/thinking/stream", { query: prompt }, signal);
    await parseSSE<ThinkingEvent>(res, onEvent, signal);
  } catch (e) {
    if ((e as Error).name !== "AbortError") {
      onEvent({ type: "error", message: (e as Error).message });
    }
  }
}

// ── Research stream ────────────────────────────────────────

export async function runResearchStream(
  prompt: string,
  onEvent: (e: ResearchEvent) => void,
  signal: AbortSignal,
): Promise<void> {
  try {
    const res = await api.fetchSSE("/research/stream", { query: prompt }, signal);
    await parseSSE<ResearchEvent>(res, onEvent, signal);
  } catch (e) {
    if ((e as Error).name !== "AbortError") {
      onEvent({ type: "error", message: (e as Error).message });
    }
  }
}

// ── Web search stream ──────────────────────────────────────

export async function runWebSearchStream(
  prompt: string,
  onEvent: (e: WebSearchEvent) => void,
  signal: AbortSignal,
): Promise<void> {
  try {
    const res = await api.fetchSSE("/web_search/stream", { query: prompt }, signal);
    await parseSSE<WebSearchEvent>(res, onEvent, signal);
  } catch (e) {
    if ((e as Error).name !== "AbortError") {
      onEvent({ type: "error", message: (e as Error).message });
    }
  }
}

// ── Code squad (WebSocket) ─────────────────────────────────

export async function runCodeSquad(
  prompt: string,
  onEvent: (e: CodeEvent) => void,
  signal: AbortSignal,
): Promise<void> {
  return new Promise<void>((resolve, reject) => {
    const ws = api.connectWS("/ws/code/squad");

    const cleanup = () => {
      try { ws.close(); } catch { /* noop */ }
    };

    signal.addEventListener("abort", cleanup, { once: true });

    ws.onopen = () => {
      ws.send(JSON.stringify({ prompt }));
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as CodeEvent;
        onEvent(data);
        if (data.type === "done") {
          cleanup();
          resolve();
        }
      } catch {
        // Non-JSON frame — ignore
      }
    };

    ws.onerror = () => {
      onEvent({ type: "error", message: "WebSocket connection failed" });
      cleanup();
      reject(new Error("WebSocket error"));
    };

    ws.onclose = () => {
      resolve();
    };
  });
}
