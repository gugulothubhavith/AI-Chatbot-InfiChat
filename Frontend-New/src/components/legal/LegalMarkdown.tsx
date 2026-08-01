/**
 * Renderer for the legal documents.
 *
 * Every element is styled explicitly rather than through `@tailwindcss/typography`.
 * That plugin is not installed in this project, so `prose` classes generate
 * nothing — relying on them would silently ship unstyled walls of text.
 *
 * Links are routed through TanStack Router when they are internal, so the
 * cross-references between the four documents navigate client-side instead of
 * triggering full page loads.
 */

import { Link } from "@tanstack/react-router";
import ReactMarkdown, { type Components } from "react-markdown";
import remarkGfm from "remark-gfm";

import { cn } from "@/lib/utils";
import { isLegalSlug, type LegalSlug } from "@/content/legal";

/**
 * Decide how to render an anchor's target.
 *
 * The markdown is authored in-repo, but it is still untrusted input as far as
 * this component is concerned — a `javascript:` or `data:` href reaching the DOM
 * would be an XSS vector, so anything that is not plainly http(s), mailto, or a
 * site-relative path is rendered as inert text.
 */
type LinkKind =
  /** A cross-reference to another legal document — routed client-side. */
  | { kind: "legal"; slug: LegalSlug }
  /** Some other in-app path. Rendered as a plain anchor: the router's `to` is
   *  strictly typed against the generated route tree, so an arbitrary string
   *  from a markdown file cannot be handed to it without lying to the compiler.
   *  A full page load is the honest fallback. */
  | { kind: "path"; href: string }
  | { kind: "fragment"; href: string }
  | { kind: "external"; href: string }
  | { kind: "unsafe" };

function classifyHref(href: string | undefined): LinkKind {
  if (!href) return { kind: "unsafe" };
  const value = href.trim();

  // Site-relative links stay in-app; in-page anchors are left to the browser.
  if (value.startsWith("/") && !value.startsWith("//")) {
    const legalMatch = value.match(/^\/legal\/([^/?#]+)$/);
    if (legalMatch && isLegalSlug(legalMatch[1])) {
      return { kind: "legal", slug: legalMatch[1] };
    }
    return { kind: "path", href: value };
  }
  if (value.startsWith("#")) return { kind: "fragment", href: value };

  // Everything else has to parse as an absolute URL on the allowlist. The URL
  // parser does the scheme normalisation for us — it lowercases the scheme and
  // strips the tabs and newlines browsers ignore — so `JavaScript:` and
  // `java\nscript:` are both caught here, where a prefix check would miss them.
  try {
    const { protocol } = new URL(value);
    if (protocol === "http:" || protocol === "https:" || protocol === "mailto:") {
      return { kind: "external", href: value };
    }
  } catch {
    // Not a parseable absolute URL. Fall through to unsafe rather than guess.
  }

  return { kind: "unsafe" };
}

const linkClass =
  "text-brand underline decoration-brand/40 underline-offset-2 transition-colors hover:decoration-brand";

const components: Components = {
  h1: ({ children }) => (
    <h1 className="text-foreground mt-0 mb-3 text-3xl font-semibold tracking-tight sm:text-4xl">
      {children}
    </h1>
  ),
  h2: ({ children }) => (
    <h2 className="text-foreground border-border/60 mt-12 mb-4 border-t pt-8 text-xl font-semibold tracking-tight first:mt-0 first:border-0 first:pt-0">
      {children}
    </h2>
  ),
  h3: ({ children }) => (
    <h3 className="text-foreground mt-8 mb-3 text-base font-semibold tracking-tight">{children}</h3>
  ),
  h4: ({ children }) => (
    <h4 className="text-foreground mt-6 mb-2 text-sm font-semibold tracking-tight">{children}</h4>
  ),
  p: ({ children }) => (
    <p className="text-muted-foreground mb-4 text-[14.5px] leading-[1.75]">{children}</p>
  ),
  ul: ({ children }) => (
    <ul className="text-muted-foreground marker:text-muted-foreground/50 mb-4 list-disc space-y-1.5 pl-5 text-[14.5px] leading-[1.7]">
      {children}
    </ul>
  ),
  ol: ({ children }) => (
    <ol className="text-muted-foreground marker:text-muted-foreground/50 mb-4 list-decimal space-y-1.5 pl-5 text-[14.5px] leading-[1.7]">
      {children}
    </ol>
  ),
  li: ({ children }) => <li className="pl-1">{children}</li>,
  strong: ({ children }) => <strong className="text-foreground font-semibold">{children}</strong>,
  em: ({ children }) => <em className="italic">{children}</em>,
  hr: () => <hr className="border-border/60 my-10" />,
  blockquote: ({ children }) => (
    <blockquote className="border-brand/40 bg-surface-2/50 text-muted-foreground [&>p:last-child]:mb-0 mb-5 rounded-r-lg border-l-2 px-4 py-3 text-[13.5px] leading-relaxed">
      {children}
    </blockquote>
  ),
  code: ({ children, className }) => {
    // Fenced blocks arrive with a `language-*` class; inline code does not.
    const isBlock = typeof className === "string" && className.includes("language-");
    if (isBlock) {
      return (
        <code className="text-foreground/90 block font-mono text-[12.5px] leading-relaxed">
          {children}
        </code>
      );
    }
    return (
      <code className="bg-surface-2 text-foreground/90 rounded px-[0.35em] py-[0.15em] font-mono text-[0.86em]">
        {children}
      </code>
    );
  },
  pre: ({ children }) => (
    <pre className="border-border/60 bg-surface-2/60 mb-5 overflow-x-auto rounded-xl border p-4">
      {children}
    </pre>
  ),
  // Sub-processors is a table-heavy document, hence remark-gfm plus real
  // table styling with horizontal overflow on narrow viewports.
  table: ({ children }) => (
    <div className="border-border/60 mb-6 overflow-x-auto rounded-xl border">
      <table className="w-full border-collapse text-left text-[13px]">{children}</table>
    </div>
  ),
  thead: ({ children }) => <thead className="bg-surface-2/60">{children}</thead>,
  th: ({ children }) => (
    <th className="text-foreground border-border/60 border-b px-3 py-2.5 font-semibold whitespace-nowrap">
      {children}
    </th>
  ),
  td: ({ children }) => (
    <td className="text-muted-foreground border-border/40 border-b px-3 py-2.5 align-top">
      {children}
    </td>
  ),
  a: ({ href, children }) => {
    const target = classifyHref(href);
    if (target.kind === "legal") {
      return (
        <Link to="/legal/$slug" params={{ slug: target.slug }} className={linkClass}>
          {children}
        </Link>
      );
    }
    if (target.kind === "path" || target.kind === "fragment") {
      return (
        <a href={target.href} className={linkClass}>
          {children}
        </a>
      );
    }
    if (target.kind === "external") {
      // rel="noopener noreferrer" so an opened tab cannot reach window.opener.
      return (
        <a href={target.href} className={linkClass} target="_blank" rel="noopener noreferrer">
          {children}
        </a>
      );
    }
    // Unsafe scheme — keep the label, drop the link.
    return <span className="text-muted-foreground">{children}</span>;
  },
};

export function LegalMarkdown({ body, className }: { body: string; className?: string }) {
  return (
    <div className={cn("max-w-none", className)}>
      <ReactMarkdown remarkPlugins={[remarkGfm]} components={components}>
        {body}
      </ReactMarkdown>
    </div>
  );
}
