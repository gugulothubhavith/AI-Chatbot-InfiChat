import { useCallback, useEffect, useRef, useState } from "react";
import { runWebSearchStream, type WebSearchEvent } from "@/lib/streams";

export type WebSearchSource = { title: string; url: string; favicon?: string; snippet?: string };
export type WebSearchCitation = { index: number; title: string; url: string };

export type WebSearchState = {
  statuses: string[];
  currentStatus: string;
  sources: WebSearchSource[];
  report?: { content: string; citations: WebSearchCitation[] };
  error?: string;
  complete: boolean;
};

const empty: WebSearchState = {
  statuses: [],
  currentStatus: "",
  sources: [],
  complete: false,
};

export function useWebSearchStream() {
  const [state, setState] = useState<WebSearchState>(empty);
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
      await runWebSearchStream(prompt, (e: WebSearchEvent) => {
        setState((prev) => {
          switch (e.type) {
            case "status":
              return { ...prev, currentStatus: e.message, statuses: [...prev.statuses, e.message] };
            case "source":
              return { ...prev, sources: [...prev.sources, e.source] };
            case "report":
              return { ...prev, report: { content: e.content, citations: e.citations }, currentStatus: "" };
            case "error":
              return { ...prev, error: e.message, currentStatus: "" };
            case "done":
              return { ...prev, complete: true, currentStatus: "" };
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
