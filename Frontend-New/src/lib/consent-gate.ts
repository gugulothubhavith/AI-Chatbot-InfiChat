/**
 * The channel between "some request was refused for want of consent" and "show
 * the re-consent modal".
 *
 * Nine backend modules depend on `require_consent`, so the 403 can arrive from
 * chat, the code agent, image, RAG, research, snippets, thinking, voice or web
 * search — whichever the user happens to touch first. Catching it per call site
 * would mean nine copies of the same handling, each easy to forget on the next
 * endpoint added. Instead `toApiError` in `lib/api.ts` publishes here once, and
 * the modal mounted in the app shell subscribes.
 *
 * This module imports nothing. `stores/auth.ts` already imports `lib/api.ts`,
 * so anything `api.ts` pulls in must not reach back into the store — a
 * dependency-free notifier keeps that impossible rather than merely avoided.
 */

/** Reported to subscribers so the modal can name the versions being asked for. */
export type ConsentRequirement = {
  requiredTermsVersion?: string;
  requiredPrivacyVersion?: string;
  acceptedTermsVersion?: string | null;
  acceptedPrivacyVersion?: string | null;
};

type Listener = (requirement: ConsentRequirement) => void;

const listeners = new Set<Listener>();

/**
 * The last requirement seen, kept so a 403 that lands before the modal has
 * mounted is not lost.
 *
 * The order is genuinely racy: `_app.tsx` fires `hydrate()` and
 * `loadSessions()` from an effect, and `loadSessions()` hits a consent-gated
 * endpoint. Whether that 403 resolves before or after the modal's own effect
 * subscribes is not something the component tree guarantees. Holding the value
 * turns "did we subscribe in time" into a non-question.
 */
let pending: ConsentRequirement | null = null;

/** Read the string at `key` if the server sent one. */
function readString(source: Record<string, unknown>, key: string): string | undefined {
  const value = source[key];
  return typeof value === "string" ? value : undefined;
}

/**
 * Pull the version fields out of the 403's `detail`.
 *
 * The payload is server-supplied, but it is still untrusted input as far as
 * types go — a shape change should degrade to "no versions shown" rather than
 * putting a non-string into the DOM.
 */
export function toConsentRequirement(detail: unknown): ConsentRequirement {
  if (!detail || typeof detail !== "object" || Array.isArray(detail)) return {};
  const source = detail as Record<string, unknown>;
  return {
    requiredTermsVersion: readString(source, "required_terms_version"),
    requiredPrivacyVersion: readString(source, "required_privacy_version"),
    // `null` is meaningful here — it is what a user who has never consented
    // looks like, as opposed to a field the server omitted.
    acceptedTermsVersion: source.accepted_terms_version === null
      ? null
      : readString(source, "accepted_terms_version"),
    acceptedPrivacyVersion: source.accepted_privacy_version === null
      ? null
      : readString(source, "accepted_privacy_version"),
  };
}

/** Announce that the API refused a request until consent is renewed. */
export function reportConsentRequired(requirement: ConsentRequirement): void {
  pending = requirement;
  for (const listener of listeners) listener(requirement);
}

/**
 * Subscribe to consent refusals. Replays a refusal that arrived before this
 * call, then returns an unsubscribe function.
 */
export function onConsentRequired(listener: Listener): () => void {
  listeners.add(listener);
  if (pending) listener(pending);
  return () => {
    listeners.delete(listener);
  };
}

/**
 * Forget the outstanding refusal, after consent has been recorded.
 *
 * Without this, a later subscribe — a remount, or a second modal instance
 * during development hot-reload — would replay a requirement the user has
 * already satisfied and block them again.
 */
export function clearConsentRequired(): void {
  pending = null;
}
