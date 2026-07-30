import { create } from "zustand";
import { nanoid } from "@/lib/nanoid";
import { api } from "@/lib/api";

export type CodeMsg = {
  id: string;
  role: "user" | "assistant";
  content: string;
  plan?: { step: string; status: "done" | "active" | "pending" }[];
};
export type CodeSession = {
  id: string;
  title: string;
  createdAt: number;
  messages: CodeMsg[];
};

type CodeState = {
  sessions: CodeSession[];
  activeId: string | null;
  pending: boolean;
  terminal: string[];
  running: boolean;
  _ws: WebSocket | null;
  setActive: (id: string | null) => void;
  newSession: () => string;
  rename: (id: string, title: string) => void;
  remove: (id: string) => void;
  send: (content: string) => Promise<void>;
  runCode: () => Promise<void>;
  stopCode: () => void;
  clearTerminal: () => void;
};

export const useCodeStore = create<CodeState>((set, get) => ({
  sessions: [],
  activeId: null,
  pending: false,
  terminal: [],
  running: false,
  _ws: null,
  setActive: (activeId) => set({ activeId }),
  newSession: () => {
    const id = nanoid();
    set((s) => ({
      sessions: [{ id, title: "New session", createdAt: Date.now(), messages: [] }, ...s.sessions],
      activeId: id,
    }));
    return id;
  },
  rename: (id, title) =>
    set((s) => ({ sessions: s.sessions.map((c) => (c.id === id ? { ...c, title } : c)) })),
  remove: (id) =>
    set((s) => ({
      sessions: s.sessions.filter((c) => c.id !== id),
      activeId: s.activeId === id ? (s.sessions[0]?.id ?? null) : s.activeId,
    })),
  send: async (content) => {
    let id = get().activeId;
    if (!id) id = get().newSession();
    const userMsg: CodeMsg = { id: nanoid(), role: "user", content };
    set((s) => ({
      sessions: s.sessions.map((c) =>
        c.id === id
          ? { ...c, title: c.messages.length === 0 ? content.slice(0, 40) : c.title, messages: [...c.messages, userMsg] }
          : c,
      ),
      pending: true,
    }));

    // Connect to WebSocket code agent
    try {
      const ws = api.connectWS(`/ws/code?session_id=${id}`);
      set({ _ws: ws });

      const assistantId = nanoid();
      set((s) => ({
        sessions: s.sessions.map((c) =>
          c.id === id
            ? { ...c, messages: [...c.messages, { id: assistantId, role: "assistant" as const, content: "" }] }
            : c,
        ),
      }));

      ws.onopen = () => {
        ws.send(JSON.stringify({ message: content }));
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === "terminal") {
            set((s) => ({ terminal: [...s.terminal, data.content] }));
          } else if (data.type === "plan") {
            set((s) => ({
              sessions: s.sessions.map((c) => ({
                ...c,
                messages: c.messages.map((m) =>
                  m.id === assistantId ? { ...m, plan: data.tasks } : m,
                ),
              })),
            }));
          } else if (data.content) {
            set((s) => ({
              sessions: s.sessions.map((c) => ({
                ...c,
                messages: c.messages.map((m) =>
                  m.id === assistantId ? { ...m, content: m.content + data.content } : m,
                ),
              })),
            }));
          }
        } catch {
          // Non-JSON message
        }
      };

      ws.onclose = () => {
        set({ pending: false, _ws: null });
      };

      ws.onerror = () => {
        set((s) => ({
          sessions: s.sessions.map((c) => ({
            ...c,
            messages: c.messages.map((m) =>
              m.id === assistantId && !m.content
                ? { ...m, content: "⚠️ Connection to code agent failed. Please check the backend is running." }
                : m,
            ),
          })),
          pending: false,
          _ws: null,
        }));
      };
    } catch {
      set({ pending: false });
    }
  },
  runCode: async () => {
    set({ terminal: ["$ Running code..."], running: true });
    // The real code execution happens through the WebSocket
    // Terminal output comes via ws.onmessage with type "terminal"
    setTimeout(() => set({ running: false }), 1000);
  },
  stopCode: () => {
    const ws = get()._ws;
    if (ws) {
      ws.close();
      set({ _ws: null });
    }
    set((s) => ({ running: false, pending: false, terminal: [...s.terminal, "✗ stopped by user"] }));
  },
  clearTerminal: () => set({ terminal: [] }),
}));

