import { Link } from "@tanstack/react-router";
import { ExternalLink, Loader2, ShieldAlert, ShieldCheck } from "lucide-react";
import { useEffect, useState } from "react";
import { toast } from "sonner";

import { Block, Row, SectionTitle } from "./_primitives";
import { consentLinkClass } from "@/components/legal/ConsentCheckbox";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { Button } from "@/components/ui/button";
import { api, type ConsentStatus } from "@/lib/api";
import { cn } from "@/lib/utils";

/**
 * The standing record of what this account has agreed to, and the control to
 * take it back.
 *
 * GDPR Art. 7(3) and DPDP s.6(4) both require that withdrawing consent be as
 * easy as giving it. Registration takes two ticks, so withdrawal cannot be a
 * support ticket — it has to be a button, next to the record of what was
 * accepted and when. `ReconsentModal` already promises this surface exists;
 * this is it.
 *
 * Withdrawal is not deletion. It clears the consent columns, which makes the
 * account stale and sends the next gated request into the re-consent modal; the
 * data stays until erasure is asked for separately, below in the danger zone.
 */

/**
 * Parse `consent_accepted_at`, which arrives with no timezone designator.
 *
 * `record_consent` writes `datetime.now(timezone.utc)` into a naive
 * `Column(DateTime)`, so the wall-clock that comes back is UTC — but
 * `.isoformat()` on a naive datetime emits no offset, and JS reads an
 * offset-less date-time form as *local*. Rendered as-is the panel would report
 * the acceptance shifted by the viewer's own UTC offset. Appending `Z` states
 * what the value already means rather than changing it.
 */
function parseTimestamp(iso: string): Date {
  const hasZone = /(?:Z|[+-]\d{2}:?\d{2})$/.test(iso);
  return new Date(hasZone ? iso : `${iso}Z`);
}

/** Same reader-facing format as the legal pages, plus the time — this is an
 *  audit record, and the day alone is thin evidence. */
function formatTimestamp(iso: string): string {
  const parsed = parseTimestamp(iso);
  if (Number.isNaN(parsed.getTime())) return iso;
  return parsed.toLocaleString("en-GB", {
    day: "numeric",
    month: "long",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

/** What the account accepted against what it now needs to have accepted. The
 *  two differ for a stale user, and saying only one of them hides the gap. */
function versionLine(accepted: string | null, required: string): string {
  if (!accepted) return `Not accepted · v${required} required`;
  if (accepted !== required) return `Accepted v${accepted} · v${required} now required`;
  return `Accepted v${accepted} · current`;
}

type LoadState =
  | { status: "loading" }
  | { status: "error"; message: string }
  | { status: "ready"; consent: ConsentStatus };

export function ConsentPanel() {
  const [state, setState] = useState<LoadState>({ status: "loading" });
  const [withdrawing, setWithdrawing] = useState(false);
  // Bumped by the retry button; the effect owns the request either way, so a
  // retry gets the same cancellation guard as the initial load.
  const [reloadToken, setReloadToken] = useState(0);

  useEffect(() => {
    let cancelled = false;
    setState({ status: "loading" });
    // `GET /legal/consent` depends on `get_current_user`, not `require_consent`
    // — deliberately, per `legal.py`: a stale user has to be able to read their
    // own consent state to act on it. So this loads even behind the modal.
    api.legal
      .getConsent()
      .then((consent) => {
        if (!cancelled) setState({ status: "ready", consent });
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setState({
            status: "error",
            message:
              err instanceof Error ? err.message : "Could not load your consent record.",
          });
        }
      });
    return () => {
      cancelled = true;
    };
  }, [reloadToken]);

  async function withdraw() {
    setWithdrawing(true);
    try {
      // Returns the cleared status, so the panel re-renders from the server's
      // answer rather than a guess about what withdrawal did.
      const next = await api.legal.withdrawConsent();
      setState({ status: "ready", consent: next });
      toast.success("Consent withdrawn", {
        description:
          "Your account and data are untouched. You will be asked to accept the policies again before using the assistant.",
      });
    } catch (err) {
      toast.error("Could not withdraw consent", {
        description: err instanceof Error ? err.message : "Please try again.",
      });
    } finally {
      setWithdrawing(false);
    }
  }

  return (
    <>
      <SectionTitle
        title="Consent"
        description="What this account has agreed to, and the record we keep of it."
      />

      {state.status === "loading" && (
        <Block>
          <Row title="Consent record" description="Loading your consent record…">
            <Loader2 className="text-muted-foreground h-4 w-4 animate-spin" />
          </Row>
        </Block>
      )}

      {state.status === "error" && (
        <Block>
          <Row title="Consent record" description={state.message}>
            <Button
              size="sm"
              variant="outline"
              onClick={() => setReloadToken((n) => n + 1)}
            >
              Retry
            </Button>
          </Row>
        </Block>
      )}

      {state.status === "ready" && (
        <ConsentRecord
          consent={state.consent}
          withdrawing={withdrawing}
          onWithdraw={withdraw}
        />
      )}
    </>
  );
}

function ConsentRecord({
  consent,
  withdrawing,
  onWithdraw,
}: {
  consent: ConsentStatus;
  withdrawing: boolean;
  onWithdraw: () => void;
}) {
  // Nothing to take back before anything was given. The 13 accounts that
  // predate the consent columns land here, and offering them a withdraw button
  // would be theatre.
  const hasRecord =
    consent.consent_accepted_at !== null ||
    consent.accepted_terms_version !== null ||
    consent.accepted_privacy_version !== null;

  return (
    <>
      <Block>
        <Row
          title="Status"
          description={
            consent.consent_current
              ? "You have accepted the current versions of both documents."
              : "Your consent is out of date. The assistant stays locked until you accept again."
          }
        >
          <span
            className={cn(
              "inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[11.5px] font-medium",
              consent.consent_current
                ? "bg-brand/10 text-brand"
                : "bg-destructive/10 text-destructive",
            )}
          >
            {consent.consent_current ? (
              <ShieldCheck className="h-3.5 w-3.5" />
            ) : (
              <ShieldAlert className="h-3.5 w-3.5" />
            )}
            {consent.consent_current ? "Current" : "Action needed"}
          </span>
        </Row>

        <Row
          title="Terms of Service"
          description={versionLine(
            consent.accepted_terms_version,
            consent.required_terms_version,
          )}
        >
          <PolicyLink to="/terms" />
        </Row>

        <Row
          title="Privacy Policy"
          description={versionLine(
            consent.accepted_privacy_version,
            consent.required_privacy_version,
          )}
        >
          <PolicyLink to="/privacy" />
        </Row>

        <Row
          title="Recorded"
          description={
            consent.consent_accepted_at
              ? formatTimestamp(consent.consent_accepted_at)
              : "No acceptance on record for this account."
          }
        />

        {hasRecord && (
          <Row
            title="Withdraw consent"
            description="Revokes your agreement without deleting anything."
          >
            <AlertDialog>
              <AlertDialogTrigger asChild>
                {/* The in-flight guard sits here rather than on the action:
                    Radix closes the dialog the moment the action is clicked, so
                    a disabled state on it would never be seen. */}
                <Button size="sm" variant="outline" disabled={withdrawing}>
                  {withdrawing ? (
                    <Loader2 className="mr-1.5 h-3.5 w-3.5 animate-spin" />
                  ) : null}
                  Withdraw
                </Button>
              </AlertDialogTrigger>
              <AlertDialogContent>
                <AlertDialogHeader>
                  <AlertDialogTitle>Withdraw your consent?</AlertDialogTitle>
                  <AlertDialogDescription>
                    Chat, code, images, search and voice will stop working until you
                    accept the policies again — you will be asked on your next request.
                    Your account, chats and files are not deleted. To erase your data,
                    use the delete options instead.
                  </AlertDialogDescription>
                </AlertDialogHeader>
                <AlertDialogFooter>
                  <AlertDialogCancel>Keep consent</AlertDialogCancel>
                  <AlertDialogAction onClick={onWithdraw}>Withdraw</AlertDialogAction>
                </AlertDialogFooter>
              </AlertDialogContent>
            </AlertDialog>
          </Row>
        )}
      </Block>

      <p className="text-muted-foreground/70 mt-2 text-[11.5px] leading-relaxed">
        Withdrawing consent and erasing your data are separate rights. Withdrawal stops
        further processing; deletion removes what is already stored.
      </p>
    </>
  );
}

/** Opens in a new tab on purpose: navigating in place would unmount the
 *  settings dialog, and the user would come back to a closed panel. */
function PolicyLink({ to }: { to: "/terms" | "/privacy" }) {
  return (
    <Link
      to={to}
      target="_blank"
      rel="noopener noreferrer"
      className={cn(consentLinkClass, "inline-flex items-center gap-1 text-[12.5px]")}
    >
      Read
      <ExternalLink className="h-3 w-3" />
    </Link>
  );
}
