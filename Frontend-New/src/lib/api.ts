/**
 * Centralized API client for the InfiChat backend.
 *
 * All authenticated requests go through `api.fetch()` which injects the JWT
 * token from the auth store. The `API_BASE` is resolved at build time via the
 * `VITE_API_URL` env var, falling back to the current origin (works behind
 * Docker reverse-proxy).
 */

const API_BASE = (import.meta.env.VITE_API_URL as string) || "/api/v1";

// Build a fully-qualified URL. When VITE_API_URL is empty the browser's
// origin is used, which is the correct default behind an nginx/traefik proxy.
function url(path: string): string {
  const base = API_BASE.replace(/\/+$/, "");
  const clean = path.startsWith("/") ? path : `/${path}`;
  return `${base}${clean}`;
}

// Read the JWT from localStorage (the auth store persists here).
function getToken(): string | null {
  try {
    const raw = localStorage.getItem("infichat-auth");
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    return parsed?.state?.token ?? null;
  } catch {
    return null;
  }
}

/** True when a JWT is present. Lets callers skip authenticated
 *  fire-and-forget writes on public routes (login/register). */
export function hasAuthToken(): boolean {
  return getToken() !== null;
}

function authHeaders(): Record<string, string> {
  const headers: Record<string, string> = {};
  
  const token = getToken();
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  
  try {
    headers["X-Timezone"] = Intl.DateTimeFormat().resolvedOptions().timeZone;
  } catch (e) {
    // Ignore timezone error
  }
  
  return headers;
}

// ── Generic helpers ─────────────────────────────────────────

async function fetchJSON<T = unknown>(
  path: string,
  init?: RequestInit,
): Promise<T> {
  const res = await fetch(url(path), {
    ...init,
    // Send the httpOnly refresh cookie on auth calls (login/refresh/logout).
    // The refresh token is no longer stored in JS, so XSS cannot exfiltrate it.
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...authHeaders(),
      ...(init?.headers as Record<string, string>),
    },
  });
  if (res.status === 401) {
    // Token expired — clear auth and redirect to login
    localStorage.removeItem("infichat-auth");
    window.location.href = "/login";
    throw new Error("Unauthorized");
  }
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new Error(`API ${res.status}: ${body.slice(0, 300)}`);
  }
  return res.json() as Promise<T>;
}

// SSE streaming — returns the raw Response so the caller can use
// `response.body.getReader()` or EventSource-style parsing.
async function fetchSSE(
  path: string,
  body: Record<string, unknown>,
  signal?: AbortSignal,
): Promise<Response> {
  const res = await fetch(url(path), {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "text/event-stream",
      ...authHeaders(),
    },
    body: JSON.stringify(body),
    signal,
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`SSE ${res.status}: ${text.slice(0, 300)}`);
  }
  return res;
}

// WebSocket with token in query string (WS doesn't support headers).
function connectWS(path: string): WebSocket {
  const token = getToken();
  const proto = window.location.protocol === "https:" ? "wss:" : "ws:";
  const host = API_BASE
    ? new URL(API_BASE).host
    : window.location.host;
  const wsUrl = `${proto}//${host}${path}${token ? `?token=${token}` : ""}`;
  return new WebSocket(wsUrl);
}

// ── Auth endpoints ──────────────────────────────────────────

export type AuthResult = {
  access_token: string;
  refresh_token?: string;
  token_type: string;
  user_id: string;
  name: string;
  email: string;
  avatar_url?: string;
  is_new_user: boolean;
  role?: string;
};

async function login(email: string, password: string): Promise<AuthResult> {
  return fetchJSON<AuthResult>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

async function register(email: string, password: string): Promise<AuthResult> {
  return fetchJSON<AuthResult>("/auth/register", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

async function getMe(): Promise<AuthResult> {
  return fetchJSON<AuthResult>("/auth/me");
}

async function refreshToken(): Promise<AuthResult> {
  // The refresh token lives in an httpOnly cookie; the browser attaches it
  // automatically because fetchJSON sends credentials. No body needed.
  return fetchJSON<AuthResult>("/auth/refresh", {
    method: "POST",
    body: JSON.stringify({}),
  });
}

async function logout(): Promise<void> {
  // Clears the httpOnly refresh cookie server-side and revokes sessions.
  await fetchJSON("/auth/logout", { method: "POST" });
}

async function googleLogin(credential: string): Promise<AuthResult> {
  return fetchJSON<AuthResult>("/auth/google", {
    method: "POST",
    body: JSON.stringify({ credential }),
  });
}

// ── Chat endpoints ──────────────────────────────────────────

export type ChatSessionDTO = {
  id: string;
  title: string;
  workspace?: string;
  is_pinned?: boolean;
  is_archived?: boolean;
  created_at?: string;
  updated_at?: string;
};

export type ChatMessageDTO = {
  id: string;
  session_id: string;
  role: "user" | "assistant";
  content: string;
  model?: string;
  created_at?: string;
};

async function listSessions(workspace = "personal"): Promise<ChatSessionDTO[]> {
  return fetchJSON<ChatSessionDTO[]>(`/chat/sessions?workspace=${workspace}`);
}

async function createSession(title?: string): Promise<ChatSessionDTO> {
  return fetchJSON<ChatSessionDTO>("/chat/sessions", {
    method: "POST",
    body: JSON.stringify(title ? { title } : {}),
  });
}

async function deleteSession(id: string): Promise<void> {
  await fetchJSON(`/chat/sessions/${id}`, { method: "DELETE" });
}

async function getMessages(sessionId: string): Promise<ChatMessageDTO[]> {
  return fetchJSON<ChatMessageDTO[]>(`/chat/sessions/${sessionId}/messages`);
}

async function renameSession(
  id: string,
  title: string,
): Promise<ChatSessionDTO> {
  return fetchJSON<ChatSessionDTO>(`/chat/sessions/${id}`, {
    method: "PATCH",
    body: JSON.stringify({ title }),
  });
}

// ── Exported API object ─────────────────────────────────────

export const api = {
  url,
  fetchJSON,
  fetchSSE,
  connectWS,
  auth: { login, register, getMe, refreshToken, googleLogin, logout },
  chat: { listSessions, createSession, deleteSession, getMessages, renameSession },

  // Settings
  getSettings: () => fetchJSON("/settings"),
  updateSettings: (payload: any) => fetchJSON("/settings", { method: "POST", body: JSON.stringify(payload) }),

  // API Keys
  getApiKeys: () => fetchJSON("/api_keys/"),
  createApiKey: (name: string, scopes: string[]) => fetchJSON("/api_keys/", { method: "POST", body: JSON.stringify({ name, scopes }) }),
  deleteApiKey: (id: string) => fetchJSON(`/api_keys/${id}`, { method: "DELETE" }),

  // Voice — TTS returns raw streamed audio, so hand back the Response for the
  // caller to pipe into an HTMLAudioElement. Non-ok is surfaced to the caller
  // (it falls back to the browser SpeechSynthesis engine).
  voice: {
    tts: (text: string, voice_id: string, signal?: AbortSignal) =>
      fetch(url("/voice/tts"), {
        method: "POST",
        headers: { "Content-Type": "application/json", ...authHeaders() },
        body: JSON.stringify({ text, voice_id }),
        signal,
      }),
    // Multipart upload — do NOT set Content-Type, the browser adds the
    // multipart boundary. Returns the transcribed text.
    transcribe: async (blob: Blob, language?: string, signal?: AbortSignal): Promise<string> => {
      const form = new FormData();
      const ext = blob.type.includes("webm") ? "webm" : blob.type.includes("ogg") ? "ogg" : "wav";
      form.append("file", blob, `speech.${ext}`);
      if (language && language !== "auto") form.append("language", language);
      const res = await fetch(url("/voice/transcribe"), {
        method: "POST",
        headers: { ...authHeaders() },
        body: form,
        signal,
      });
      if (!res.ok) {
        const body = await res.text().catch(() => "");
        throw new Error(`transcribe ${res.status}: ${body.slice(0, 200)}`);
      }
      const data = (await res.json()) as { text?: string };
      return data.text ?? "";
    },
  },

  // Subscriptions
  getPlans: () => fetchJSON("/subscription/plans"),
  getMyPlan: () => fetchJSON("/subscription/my-plan"),
  checkout: (plan_id: string, billing_cycle: string) => fetchJSON("/subscription/checkout", { method: "POST", body: JSON.stringify({ plan_id, billing_cycle }) }),
  getPortalUrl: () => fetchJSON("/subscription/portal"),
  getInvoices: () => fetchJSON("/subscription/invoices"),
} as const;
