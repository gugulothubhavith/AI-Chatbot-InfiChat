import { useCallback, useEffect, useRef, useState } from "react";
import { runThinkingStream, type ThinkingEvent } from "@/lib/streams";

export type ReasoningStep = {
  step_number: number;
  title: string;
  content: string;
  confidence: number;
  status: "pending" | "verified";
};

export type ThinkingProgress = {
  stage: string;
  message: string;
  confidence: number;
  sub_problems: string[];
  steps: ReasoningStep[];
  complete: boolean;
  report?: { executive_summary: string; reasoning_chain: { title: string; content: string }[] };
};

const empty: ThinkingProgress = {
  stage: "idle",
  message: "",
  confidence: 0,
  sub_problems: [],
  steps: [],
  complete: false,
};

export function useThinkingStream() {
  const [state, setState] = useState<ThinkingProgress>(empty);
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
      await runThinkingStream(prompt, (e: ThinkingEvent) => {
        setState((prev) => {
          if (e.type === "thinking_progress") {
            return { ...prev, stage: e.stage, message: e.message, confidence: e.confidence, sub_problems: e.sub_problems ?? prev.sub_problems };
          }
          if (e.type === "reasoning_step") {
            const existing = prev.steps.find((s) => s.step_number === e.step_number);
            const next: ReasoningStep = { step_number: e.step_number, title: e.title, content: e.content, confidence: e.confidence, status: e.status };
            return {
              ...prev,
              steps: existing ? prev.steps.map((s) => (s.step_number === e.step_number ? next : s)) : [...prev.steps, next],
            };
          }
          if (e.type === "thinking_complete") {
            return { ...prev, complete: true, report: e.report, confidence: 1 };
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
