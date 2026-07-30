import { create } from "zustand";
import { nanoid } from "@/lib/nanoid";
import { api } from "@/lib/api";

export type Msg = {
  id: string;
  role: "user" | "assistant";
  content: string;
  tokens?: number;
  latencyMs?: number;
};
export type Conversation = {
  id: string;
  title: string;
  createdAt: number;
  messages: Msg[];
};

type ChatState = {
  conversations: Conversation[];
  activeId: string | null;
  pending: boolean;
  _abortCtrl: AbortController | null;
  setActive: (id: string | null) => void;
  newChat: () => string;
  rename: (id: string, title: string) => void;
  remove: (id: string) => void;
  send: (content: string) => Promise<void>;
  regenerate: () => Promise<void>;
  stop: () => void;
  appendUser: (content: string) => string;
  appendAssistant: (content: string, meta?: { tokens?: number; latencyMs?: number }) => string | undefined;
  updateAssistant: (id: string, content: string) => void;
  editUserMessage: (id: string, content: string) => void;
  editAndResend: (id: string, content: string) => Promise<void>;
  setPending: (v: boolean) => void;
  loadSessions: () => Promise<void>;
  loadMessages: (sessionId: string) => Promise<void>;
};

/** Parse SSE stream line by line and call `onChunk` for each content delta. */
async function streamChat(
  content: string,
  sessionId: string,
  signal: AbortSignal,
  onChunk: (text: string) => void,
): Promise<void> {
  // Get current model from model store
  const modelId = (() => {
    try {
      const raw = localStorage.getItem("infichat-models");
      if (!raw) return "nvidia/nemotron-3-ultra-550b-a55b";
      return JSON.parse(raw)?.state?.model ?? "nvidia/nemotron-3-ultra-550b-a55b";
    } catch { return "nvidia/nemotron-3-ultra-550b-a55b"; }
  })();

  const res = await api.fetchSSE("/chat/stream", {
    message: content,
    session_id: sessionId,
    model: modelId,
    stream: true,
  }, signal);

  const reader = res.body?.getReader();
  if (!reader) return;
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
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
        const parsed = JSON.parse(dataStr);
        const chunk = parsed.content ?? parsed.delta ?? parsed.text ?? "";
        if (chunk) onChunk(chunk);
      } catch {
        // Non-JSON SSE frame — use raw
        if (dataStr) onChunk(dataStr);
      }
    }
  }
}

export const useChatStore = create<ChatState>((set, get) => ({
  conversations: [],
  activeId: null,
  pending: false,
  _abortCtrl: null,

  setActive: (activeId) => {
    set({ activeId });
    if (activeId) get().loadMessages(activeId);
  },

  newChat: () => {
    const id = nanoid();
    set((s) => ({
      conversations: [{ id, title: "New chat", createdAt: Date.now(), messages: [] }, ...s.conversations],
      activeId: id,
    }));
    // Also create on backend (fire-and-forget, the stream will use this session)
    api.chat.createSession("New chat").then((sess) => {
      set((s) => ({
        conversations: s.conversations.map((c) =>
          c.id === id ? { ...c, id: sess.id } : c,
        ),
        activeId: s.activeId === id ? sess.id : s.activeId,
      }));
    }).catch(() => {/* best-effort */});
    return id;
  },

  rename: (id, title) => {
    set((s) => ({
      conversations: s.conversations.map((c) => (c.id === id ? { ...c, title } : c)),
    }));
    api.chat.renameSession(id, title).catch(() => {});
  },

  remove: (id) => {
    set((s) => ({
      conversations: s.conversations.filter((c) => c.id !== id),
      activeId: s.activeId === id ? (s.conversations[0]?.id ?? null) : s.activeId,
    }));
    api.chat.deleteSession(id).catch(() => {});
  },

  stop: () => {
    const ctrl = get()._abortCtrl;
    ctrl?.abort();
    set({ _abortCtrl: null, pending: false });
  },

  send: async (content) => {
    let id = get().activeId;
    if (!id) id = get().newChat();

    const userMsg: Msg = { id: nanoid(), role: "user", content };
    set((s) => ({
      conversations: s.conversations.map((c) =>
        c.id === id
          ? {
              ...c,
              title: c.messages.length === 0 ? content.slice(0, 40) : c.title,
              messages: [...c.messages, userMsg],
            }
          : c,
      ),
      pending: true,
    }));

    const assistantId = nanoid();
    // Pre-insert empty assistant message for streaming
    set((s) => ({
      conversations: s.conversations.map((c) =>
        c.id === id
          ? { ...c, messages: [...c.messages, { id: assistantId, role: "assistant" as const, content: "" }] }
          : c,
      ),
    }));

    const ctrl = new AbortController();
    set({ _abortCtrl: ctrl });
    const t0 = Date.now();

    try {
      await streamChat(content, id!, ctrl.signal, (chunk) => {
        set((s) => ({
          conversations: s.conversations.map((c) => ({
            ...c,
            messages: c.messages.map((m) =>
              m.id === assistantId ? { ...m, content: m.content + chunk } : m,
            ),
          })),
        }));
      });
      // Mark final metadata
      set((s) => ({
        conversations: s.conversations.map((c) => ({
          ...c,
          messages: c.messages.map((m) =>
            m.id === assistantId
              ? { ...m, latencyMs: Date.now() - t0 }
              : m,
          ),
        })),
      }));
    } catch (e) {
      if ((e as Error).name === "AbortError") return;
      // On error, update the assistant message with an error note
      set((s) => ({
        conversations: s.conversations.map((c) => ({
          ...c,
          messages: c.messages.map((m) =>
            m.id === assistantId
              ? { ...m, content: m.content || `⚠️ Error: ${(e as Error).message}` }
              : m,
          ),
        })),
      }));
    } finally {
      set({ pending: false, _abortCtrl: null });
    }
  },

  regenerate: async () => {
    const id = get().activeId;
    if (!id) return;
    const conv = get().conversations.find((c) => c.id === id);
    if (!conv || conv.messages.length < 2) return;
    const lastUser = [...conv.messages].reverse().find((m) => m.role === "user");
    if (!lastUser) return;

    // Remove last assistant message
    set((s) => ({
      conversations: s.conversations.map((c) =>
        c.id === id ? { ...c, messages: c.messages.slice(0, -1) } : c,
      ),
    }));
    await get().send(lastUser.content);
  },

  appendUser: (content) => {
    let id = get().activeId;
    if (!id) id = get().newChat();
    const userMsg: Msg = { id: nanoid(), role: "user", content };
    set((s) => ({
      conversations: s.conversations.map((c) =>
        c.id === id
          ? {
              ...c,
              title: c.messages.length === 0 ? content.slice(0, 40) : c.title,
              messages: [...c.messages, userMsg],
            }
          : c,
      ),
    }));
    return id!;
  },

  appendAssistant: (content, meta) => {
    const id = get().activeId;
    if (!id) return undefined;
    const msgId = nanoid();
    const reply: Msg = { id: msgId, role: "assistant", content, ...meta };
    set((s) => ({
      conversations: s.conversations.map((c) =>
        c.id === id ? { ...c, messages: [...c.messages, reply] } : c,
      ),
    }));
    return msgId;
  },

  updateAssistant: (msgId, content) => {
    set((s) => ({
      conversations: s.conversations.map((c) => ({
        ...c,
        messages: c.messages.map((m) => (m.id === msgId ? { ...m, content } : m)),
      })),
    }));
  },

  editUserMessage: (msgId, content) => {
    set((s) => ({
      conversations: s.conversations.map((c) => ({
        ...c,
        messages: c.messages.map((m) => (m.id === msgId && m.role === "user" ? { ...m, content } : m)),
      })),
    }));
  },

  editAndResend: async (msgId, content) => {
    const id = get().activeId;
    if (!id) return;
    set((s) => ({
      conversations: s.conversations.map((c) => {
        if (c.id !== id) return c;
        const idx = c.messages.findIndex((m) => m.id === msgId);
        if (idx === -1) return c;
        const before = c.messages.slice(0, idx);
        const edited: Msg = { ...c.messages[idx], content };
        return { ...c, messages: [...before, edited] };
      }),
    }));
    await get().send(content);
  },

  setPending: (v) => set({ pending: v }),

  loadSessions: async () => {
    try {
      const sessions = await api.chat.listSessions();
      const convs: Conversation[] = sessions.map((s) => ({
        id: s.id,
        title: s.title || "Untitled",
        createdAt: s.created_at ? new Date(s.created_at).getTime() : Date.now(),
        messages: [],
      }));
      set({ conversations: convs, activeId: convs[0]?.id ?? null });
    } catch {
      // Backend unreachable — keep local state
    }
  },

  loadMessages: async (sessionId: string) => {
    try {
      const msgs = await api.chat.getMessages(sessionId);
      const mapped: Msg[] = msgs.map((m) => ({
        id: m.id,
        role: m.role,
        content: m.content,
      }));
      set((s) => ({
        conversations: s.conversations.map((c) =>
          c.id === sessionId ? { ...c, messages: mapped } : c,
        ),
      }));
    } catch {
      // Non-fatal
    }
  },
}));
