/**
 * Chrome around a legal document.
 *
 * Deliberately standalone rather than nested under the `_app` layout: the Terms
 * and Privacy Policy have to be readable while logged out — someone deciding
 * whether to accept them does not have an account yet, and someone blocked by
 * the re-consent gate cannot reach anything behind it. So no sidebar, no auth
 * check, just the document.
 */

import { Link } from "@tanstack/react-router";

import { LegalMarkdown } from "./LegalMarkdown";
import { LEGAL_NAV, type LegalDoc } from "@/content/legal";
import { Logo } from "@/components/brand/Logo";
import { ThemeToggle } from "@/components/shell/ThemeToggle";

/** Render an ISO date as something a reader can parse at a glance. */
function formatDate(iso: string): string {
  if (!iso) return "";
  const parsed = new Date(iso);
  if (Number.isNaN(parsed.getTime())) return iso;
  return parsed.toLocaleDateString("en-GB", {
    day: "numeric",
    month: "long",
    year: "numeric",
  });
}

export function LegalPage({ doc }: { doc: LegalDoc }) {
  const effective = formatDate(doc.effectiveDate);
  const updated = formatDate(doc.lastUpdated);

  return (
    <div className="bg-background text-foreground min-h-screen">
      <header className="border-border/60 bg-background/85 sticky top-0 z-20 border-b backdrop-blur-md">
        <div className="mx-auto flex h-14 max-w-[760px] items-center justify-between px-5 sm:px-8">
          <Link to="/" aria-label="InfiChat home" className="flex items-center">
            <Logo size={20} />
          </Link>
          <ThemeToggle />
        </div>
      </header>

      <main className="mx-auto max-w-[760px] px-5 pt-12 pb-20 sm:px-8">
        <nav aria-label="Legal documents" className="mb-10 flex flex-wrap gap-x-1.5 gap-y-2">
          {LEGAL_NAV.map((item) => {
            const isCurrent = item.slug === doc.slug;
            return (
              <Link
                key={item.slug}
                to="/legal/$slug"
                params={{ slug: item.slug }}
                aria-current={isCurrent ? "page" : undefined}
                className={
                  isCurrent
                    ? "bg-surface-2 text-foreground rounded-full px-3 py-1.5 text-[12.5px] font-medium"
                    : "text-muted-foreground hover:bg-surface-2/60 hover:text-foreground rounded-full px-3 py-1.5 text-[12.5px] transition-colors"
                }
              >
                {item.label}
              </Link>
            );
          })}
        </nav>

        {/* The document's own H1 is stripped from the body by the renderer's
            heading styles, so the version metadata sits directly under it. */}
        <div className="border-border/60 mb-10 border-b pb-8">
          <h1 className="text-foreground text-3xl font-semibold tracking-tight sm:text-4xl">
            {doc.title}
          </h1>
          <dl className="text-muted-foreground mt-4 flex flex-wrap gap-x-6 gap-y-1 text-[12.5px]">
            {doc.version && (
              <div className="flex gap-1.5">
                <dt>Version</dt>
                <dd className="text-foreground/80 font-medium">{doc.version}</dd>
              </div>
            )}
            {effective && (
              <div className="flex gap-1.5">
                <dt>Effective</dt>
                <dd className="text-foreground/80 font-medium">{effective}</dd>
              </div>
            )}
            {updated && updated !== effective && (
              <div className="flex gap-1.5">
                <dt>Last updated</dt>
                <dd className="text-foreground/80 font-medium">{updated}</dd>
              </div>
            )}
          </dl>
        </div>

        <LegalMarkdown body={doc.body} />

        <div className="border-border/60 text-muted-foreground mt-16 border-t pt-8 text-[12.5px]">
          <Link to="/login" className="hover:text-foreground transition-colors">
            Back to sign in
          </Link>
        </div>
      </main>
    </div>
  );
}
