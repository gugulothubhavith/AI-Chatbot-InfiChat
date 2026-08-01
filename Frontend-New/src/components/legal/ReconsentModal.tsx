import * as DialogPrimitive from "@radix-ui/react-dialog";
import { Link, useNavigate } from "@tanstack/react-router";
import { AlertCircle, Loader2, ShieldCheck } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import {
  ConsentCheckbox,
  consentGapMessage,
  consentLinkClass,
} from "@/components/legal/ConsentCheckbox";
import { LEGAL_DOCS } from "@/content/legal";
import { api, ApiError, API_ERROR_CODES, type PolicyVersions } from "@/lib/api";
import {
  clearConsentRequired,
  onConsentRequired,
  type ConsentRequirement,
} from "@/lib/consent-gate";
import { useAuthStore } from "@/stores/auth";
import { cn } from "@/lib/utils";

/**
 * The re-consent gate: a blocking dialog raised when the API refuses a request
 * for want of current consent.
 *
 * Policies change, and a user who agreed to version 1.0.0 has not agreed to
 * 1.1.0 — continued use is not consent to new terms. The backend enforces that
 * with `require_consent`, which answers 403 CONSENT_REQUIRED on nine modules.
 * This dialog is what turns that refusal into something the user can act on.
 *
 * It is deliberately not dismissable. There is no close button, Escape does
 * nothing, and clicking the backdrop does nothing — the two ways out are to
 * accept, or to sign out. Anything else would leave the user in an app where
 * every feature answers 403 with no explanation.
 *
 * The dialog is presentation only. It renders over a session that is still
 * authenticated, and hiding UI is not access control: the gate that actually
 * holds is the backend dependency, which keeps refusing whatever this renders.
 */

/** Fall back to the versions compiled into the bundled documents when neither
 *  the 403 nor `/legal/versions` has told us what is required yet. */
const BUNDLED_VERSIONS: PolicyVersions = {
  terms_version: LEGAL_DOCS.terms.version,
  privacy_version: LEGAL_DOCS.privacy.version,
};

function versionsFrom(requirement: ConsentRequirement): PolicyVersions {
  return {
    terms_version: requirement.requiredTermsVersion ?? BUNDLED_VERSIONS.terms_version,
    privacy_version: requirement.requiredPrivacyVersion ?? BUNDLED_VERSIONS.privacy_version,
  };
}

/** Whether this is a first-time acceptance or a policy update. A user with no
 *  recorded consent needs different wording from one whose consent went stale —
 *  telling a brand-new account that "our policies have been updated" is a lie,
 *  and the 13 accounts predating the consent columns all land here. */
function isUpdate(requirement: ConsentRequirement): boolean {
  return Boolean(requirement.acceptedTermsVersion ?? requirement.acceptedPrivacyVersion);
}

export function ReconsentModal() {
  const [requirement, setRequirement] = useState<ConsentRequirement | null>(null);
  const [versions, setVersions] = useState<PolicyVersions>(BUNDLED_VERSIONS);
  const [consent, setConsent] = useState({ terms: false, privacy: false });
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const signOut = useAuthStore((s) => s.signOut);
  const navigate = useNavigate();

  // Subscribe once. `onConsentRequired` replays a requirement that arrived
  // before this effect ran — `loadSessions()` in the app shell can trigger the
  // 403 from its own effect, and effect ordering across the tree is not
  // something to rely on — so the unsubscribe is the only cleanup needed.
  useEffect(() => {
    return onConsentRequired((next) => {
      setRequirement((current) => {
        // Ignore repeats while the dialog is already up: several gated requests
        // fail together on first load, and re-setting state on each would reset
        // boxes the user has just ticked.
        if (current) return current;
        setVersions(versionsFrom(next));
        return next;
      });
    });
  }, []);

  // Confirm the required versions against the server rather than trusting the
  // error body alone. The 403 detail carries what the gate knew at refusal
  // time; `/legal/versions` is the authority, and the POST is rejected with a
  // 409 if we submit anything else.
  useEffect(() => {
    if (!requirement) return;
    let cancelled = false;
    api.legal
      .getPolicyVersions()
      .then((fresh) => {
        if (!cancelled) setVersions(fresh);
      })
      .catch(() => {
        // Keep the versions from the 403. Failing to refine them is not worth
        // blocking the user over — the 409 path below is the real backstop.
      });
    return () => {
      cancelled = true;
    };
  }, [requirement]);

  const toggle = useCallback((key: "terms" | "privacy", value: boolean) => {
    setError(null);
    setConsent((c) => ({ ...c, [key]: value }));
  }, []);

  async function accept() {
    const gap = consentGapMessage(consent.terms, consent.privacy);
    if (gap) {
      setError(gap);
      return;
    }

    setSubmitting(true);
    setError(null);
    try {
      await api.legal.acceptConsent(versions);
      // Drop the held requirement, or a later subscribe — a remount, or a
      // second 403 already in flight — would raise the dialog again over a
      // user who has just satisfied it.
      clearConsentRequired();
      setRequirement(null);
      setConsent({ terms: false, privacy: false });
    } catch (err) {
      if (err instanceof ApiError && err.code === API_ERROR_CODES.versionMismatch) {
        // The policy changed while the dialog was open. The server raises one
        // 409 per policy, each naming only its own version, so re-fetch both
        // rather than patching a single field out of the error.
        const fresh = await api.legal.getPolicyVersions().catch(() => null);
        if (fresh) setVersions(fresh);
        setConsent({ terms: false, privacy: false });
        setError(
          "The policies were updated while this was open. Please review the current versions and accept again.",
        );
      } else {
        setError(
          err instanceof Error ? err.message : "Could not record your consent. Please try again.",
        );
      }
    } finally {
      setSubmitting(false);
    }
  }

  function declineAndSignOut() {
    // Consent that cannot be refused is not freely given, so there has to be a
    // way out that is not acceptance. `signOut` clears state and revokes the
    // refresh cookie but does not navigate, so do that here rather than waiting
    // for a route resolution that may not come while a modal holds focus.
    clearConsentRequired();
    setRequirement(null);
    signOut();
    void navigate({ to: "/login" });
  }

  if (!requirement) return null;

  const update = isUpdate(requirement);

  return (
    <DialogPrimitive.Root open modal>
      <DialogPrimitive.Portal>
        <DialogPrimitive.Overlay className="data-[state=open]:animate-in data-[state=open]:fade-in-0 fixed inset-0 z-50 bg-black/80 backdrop-blur-sm" />
        <DialogPrimitive.Content
          // Every dismissal route is refused: no close button is rendered, and
          // these three cover Escape, pointer-down outside, and the focus-based
          // interact-outside that Radix fires for assistive technology.
          onEscapeKeyDown={(e) => e.preventDefault()}
          onPointerDownOutside={(e) => e.preventDefault()}
          onInteractOutside={(e) => e.preventDefault()}
          aria-describedby={undefined}
          className={cn(
            "bg-surface border-border fixed top-[50%] left-[50%] z-50 w-full max-w-lg translate-x-[-50%] translate-y-[-50%]",
            "rounded-2xl border p-6 shadow-2xl sm:p-7",
            "data-[state=open]:animate-in data-[state=open]:fade-in-0 data-[state=open]:zoom-in-95",
          )}
        >
          <div className="bg-brand/10 text-brand mb-4 flex h-10 w-10 items-center justify-center rounded-xl">
            <ShieldCheck className="h-5 w-5" />
          </div>

          <DialogPrimitive.Title className="text-[17px] font-semibold tracking-[-0.01em]">
            {update ? "Our policies have been updated" : "Please review our policies"}
          </DialogPrimitive.Title>

          <p className="text-muted-foreground mt-2 text-[13px] leading-[1.6]">
            {update
              ? "We have published new versions of the documents that govern your account. Please review and accept them to continue."
              : "Before you continue, we need your agreement to the documents that govern your account."}
          </p>

          <div className="border-border/70 bg-surface-2/40 mt-5 space-y-3 rounded-xl border p-4">
            <ConsentCheckbox
              checked={consent.terms}
              onChange={(v) => toggle("terms", v)}
              invalid={Boolean(error) && !consent.terms}
              disabled={submitting}
            >
              I agree to the{" "}
              <Link
                to="/terms"
                target="_blank"
                rel="noopener noreferrer"
                className={consentLinkClass}
              >
                Terms of Service
              </Link>{" "}
              <span className="text-muted-foreground/70">(v{versions.terms_version})</span>
            </ConsentCheckbox>

            <ConsentCheckbox
              checked={consent.privacy}
              onChange={(v) => toggle("privacy", v)}
              invalid={Boolean(error) && !consent.privacy}
              disabled={submitting}
            >
              I have read the{" "}
              <Link
                to="/privacy"
                target="_blank"
                rel="noopener noreferrer"
                className={consentLinkClass}
              >
                Privacy Policy
              </Link>{" "}
              <span className="text-muted-foreground/70">(v{versions.privacy_version})</span> and
              consent to the processing of my data as described in it
            </ConsentCheckbox>
          </div>

          {/* Both policies open in a new tab: this dialog cannot be dismissed,
              so navigating the current one away would strand the user on a
              legal page with the gate waiting again on return. */}
          <p className="text-muted-foreground/70 mt-2 text-[11.5px]">
            Both documents open in a new tab.
          </p>

          {error && (
            <p
              role="alert"
              className="text-destructive mt-3 flex items-start gap-2 text-[12.5px] leading-snug"
            >
              <AlertCircle className="mt-px h-3.5 w-3.5 shrink-0" />
              <span>{error}</span>
            </p>
          )}

          <div className="mt-6 flex flex-col-reverse gap-2 sm:flex-row sm:items-center sm:justify-between">
            <button
              type="button"
              onClick={declineAndSignOut}
              disabled={submitting}
              className="text-muted-foreground hover:text-foreground cursor-pointer text-[12.5px] underline decoration-transparent underline-offset-2 transition-colors hover:decoration-current disabled:opacity-50"
            >
              Decline and sign out
            </button>

            <button
              type="button"
              onClick={accept}
              disabled={submitting}
              className="bg-primary text-primary-foreground flex h-10 items-center justify-center gap-2 rounded-xl px-5 text-[13.5px] font-medium transition-opacity disabled:opacity-65 sm:w-auto"
            >
              {submitting ? <Loader2 className="h-4 w-4 animate-spin" /> : "Accept and continue"}
            </button>
          </div>

          <p className="text-muted-foreground/60 mt-4 text-[11px] leading-relaxed">
            You can withdraw your consent at any time from Settings. Withdrawing does not delete
            your account — you can request deletion separately.
          </p>
        </DialogPrimitive.Content>
      </DialogPrimitive.Portal>
    </DialogPrimitive.Root>
  );
}
