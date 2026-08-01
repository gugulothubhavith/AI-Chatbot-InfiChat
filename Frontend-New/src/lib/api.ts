/**
 * Centralized API client for the InfiChat backend.
 *
 * All authenticated requests go through `api.fetch()` which injects the JWT
 * token from the auth store. The `API_BASE` is resolved at build time via the
 * `VITE_API_URL` env var, falling back to the current origin (works behind
 * Docker reverse-proxy).
 */

import { reportConsentRequired, toConsentRequirement } from "./consent-gate";

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

// ── Errors ──────────────────────────────────────────────────

/** `detail.code` values the client branches on, rather than matching prose. */
export const API_ERROR_CODES = {
  consentRequired: "CONSENT_REQUIRED",
  consentIncomplete: "CONSENT_INCOMPLETE",
  versionMismatch: "VERSION_MISMATCH",
} as const;

/**
 * A failed HTTP response, with the backend's structured `detail` preserved.
 *
 * The API raises `HTTPException(detail={"code": ..., "message": ...})` for every
 * condition a caller might branch on — `CONSENT_REQUIRED`, `VERSION_MISMATCH`,
 * `CONSENT_INCOMPLETE`. Flattening that into an `Error` whose message was the
 * stringified JSON left callers regex-matching prose, and put raw JSON in front
 * of the user. `code` and `message` are lifted out so callers can branch on the
 * former and display the latter.
 */
export class ApiError extends Error {
  readonly status: number;
  readonly code?: string;
  readonly detail?: unknown;

  constructor(status: number, message: string, opts?: { code?: string; detail?: unknown }) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = opts?.code;
    this.detail = opts?.detail;
  }
}

/** FastAPI's `detail` is a string for simple aborts, an object for the coded
 *  errors above, and an array of `{loc, msg}` entries for 422 validation
 *  failures. Normalise all three into one displayable sentence. */
function detailToMessage(detail: unknown): string | undefined {
  if (typeof detail === "string") return detail || undefined;
  if (Array.isArray(detail)) {
    const parts = detail
      .map((entry) =>
        entry && typeof entry === "object" && typeof (entry as { msg?: unknown }).msg === "string"
          ? (entry as { msg: string }).msg
          : undefined,
      )
      .filter((msg): msg is string => Boolean(msg));
    return parts.length ? parts.join("; ") : undefined;
  }
  if (detail && typeof detail === "object") {
    const message = (detail as { message?: unknown }).message;
    if (typeof message === "string") return message;
  }
  return undefined;
}

function detailToCode(detail: unknown): string | undefined {
  if (detail && typeof detail === "object" && !Array.isArray(detail)) {
    const code = (detail as { code?: unknown }).code;
    if (typeof code === "string") return code;
  }
  return undefined;
}

/**
 * Turn a non-ok response into an `ApiError`. Consumes the body, so call it at
 * most once per response.
 *
 * The raw body deliberately never reaches the thrown message. A 500 can carry a
 * driver-level string — a failing SQL constraint, say — and that belongs in the
 * server log, not on screen. Shapes we do not recognise fall back to a generic
 * sentence keyed off the status.
 *
 * This is also where a consent refusal is published. Nine backend modules
 * depend on `require_consent`, so the 403 arrives from whichever feature the
 * user happens to touch first — and both transports funnel their failures
 * through here, which makes this the one place that sees all of them. It only
 * announces; it does not clear the session or navigate, because a stale user is
 * still authenticated and has to stay where they are for the modal to appear
 * over them.
 */
async function toApiError(res: Response): Promise<ApiError> {
  const raw = await res.text().catch(() => "");
  let detail: unknown;
  try {
    detail = (JSON.parse(raw) as { detail?: unknown }).detail;
  } catch {
    // Not JSON — a proxy error page, or an empty body. Leave `detail` unset.
  }
  const code = detailToCode(detail);
  if (res.status === 403 && code === API_ERROR_CODES.consentRequired) {
    reportConsentRequired(toConsentRequirement(detail));
  }
  const message =
    detailToMessage(detail) ??
    (res.status >= 500
      ? "The server ran into a problem. Please try again."
      : `Request failed (${res.status}).`);
  return new ApiError(res.status, message, { code, detail });
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
    throw new ApiError(401, "Your session has expired. Please sign in again.");
  }
  if (!res.ok) {
    throw await toApiError(res);
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
  // Streaming endpoints are consent-gated too, and they bypass `fetchJSON`, so
  // they need their own conversion for the gate to see a 403.
  if (!res.ok) {
    throw await toApiError(res);
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
  permissions?: string[];
};

async function login(email: string, password: string): Promise<AuthResult> {
  return fetchJSON<AuthResult>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

/**
 * Create an account.
 *
 * `consent` is a required argument, not an options bag with defaults: the
 * backend refuses registration unless both flags are explicitly true, and a
 * default here would let a caller omit consent and still look correct at the
 * call site. Making it required means the compiler asks the question.
 */
async function register(
  email: string,
  password: string,
  consent: { accept_terms: boolean; accept_privacy: boolean },
): Promise<AuthResult> {
  return fetchJSON<AuthResult>("/auth/register", {
    method: "POST",
    body: JSON.stringify({
      email,
      password,
      accept_terms: consent.accept_terms,
      accept_privacy: consent.accept_privacy,
    }),
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

// ── Legal / consent endpoints ───────────────────────────────

export type PolicyVersions = {
  terms_version: string;
  privacy_version: string;
};

export type ConsentStatus = {
  consent_current: boolean;
  accepted_terms_version: string | null;
  accepted_privacy_version: string | null;
  required_terms_version: string;
  required_privacy_version: string;
  consent_accepted_at: string | null;
};

/** Public — no token needed, so the auth screens can show which version they
 *  are asking about. */
async function getPolicyVersions(): Promise<PolicyVersions> {
  return fetchJSON<PolicyVersions>("/legal/versions");
}

async function getConsent(): Promise<ConsentStatus> {
  return fetchJSON<ConsentStatus>("/legal/consent");
}

/**
 * Accept the current policies.
 *
 * The versions are echoed back so the server can reject a client that is
 * displaying a policy which changed while the modal was open — it answers 409
 * `VERSION_MISMATCH` rather than silently recording consent to text the user
 * never saw. They are optional in the API for older clients; this client always
 * sends them.
 */
async function acceptConsent(versions: PolicyVersions): Promise<ConsentStatus> {
  return fetchJSON<ConsentStatus>("/legal/consent", {
    method: "POST",
    body: JSON.stringify({
      accept_terms: true,
      accept_privacy: true,
      terms_version: versions.terms_version,
      privacy_version: versions.privacy_version,
    }),
  });
}

/** GDPR Art. 7(3). Clears consent; does not delete the account. */
async function withdrawConsent(): Promise<ConsentStatus> {
  return fetchJSON<ConsentStatus>("/legal/consent/withdraw", { method: "POST" });
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

// ── Data rights (GDPR Art. 15 / 17, DPDP s.11–12) ───────────

/**
 * The archive `GET /chat/export` actually returns.
 *
 * Deliberately not `ChatSessionDTO[]` — `export_user_chat_history` builds its own
 * dicts, and they are narrower than the list endpoint's: no `updated_at`,
 * `workspace` or `is_pinned` on a session, no `id` or `model` on a message.
 * Reusing the DTOs would advertise fields the export never sends.
 */
export type ChatExport = {
  sessions: Array<{
    id: string;
    title: string;
    created_at: string;
    messages: Array<{ role: string; content: string; created_at: string }>;
  }>;
  generated_at: string;
};

/** Art. 15 / s.11 — a machine-readable copy of the user's chat history.
 *
 *  Consent-gated on the server (`chat.py` depends on `require_consent`), so a
 *  stale user gets a 403 and the re-consent modal rather than a download. */
async function exportChatHistory(): Promise<ChatExport> {
  return fetchJSON<ChatExport>("/chat/export");
}

/** Art. 17 / s.12 — erase every session and message, keeping the account. */
async function deleteChatHistory(): Promise<void> {
  await fetchJSON("/chat/history", { method: "DELETE" });
}

/**
 * Art. 17 / s.12 — erase the account itself.
 *
 * Sits on `auth`, not `chat`, for a reason that matters: `/auth/me` is not
 * consent-gated, so erasure stays reachable for a user whose consent has gone
 * stale. A right to be forgotten that required agreeing to new terms first would
 * not be a right. The server refuses admin accounts with a 403.
 */
async function deleteAccount(): Promise<void> {
  await fetchJSON("/auth/me", { method: "DELETE" });
}

// ── Exported API object ─────────────────────────────────────

export const api = {
  url,
  fetchJSON,
  fetchSSE,
  connectWS,
  auth: { login, register, getMe, refreshToken, googleLogin, logout, deleteAccount },
  chat: {
    listSessions,
    createSession,
    deleteSession,
    getMessages,
    renameSession,
    exportChatHistory,
    deleteChatHistory,
  },
  legal: { getPolicyVersions, getConsent, acceptConsent, withdrawConsent },

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
      // Same conversion as the other transports. Pressing the mic can be the
      // first thing a stale user does, so this path has to raise the consent
      // gate too — and echoing the raw body put `{"detail":{...}}` on screen.
      if (!res.ok) {
        throw await toApiError(res);
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
