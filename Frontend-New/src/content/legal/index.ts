/**
 * Registry of the legal documents served by the app.
 *
 * The markdown lives beside this file and is pulled in with Vite's `?raw`
 * suffix, so the documents ship as part of the bundle rather than being fetched
 * at runtime. That matters for compliance: the Terms and Privacy Policy must be
 * reachable while logged out, on a cold cache, and even if the API is down —
 * a network fetch could fail exactly when a user is trying to read what they
 * are being asked to agree to.
 *
 * Each document carries YAML frontmatter that is metadata for us, not content
 * for the reader, so it is stripped before rendering.
 */

import acceptableUseRaw from "./acceptable-use.md?raw";
import privacyRaw from "./privacy.md?raw";
import subProcessorsRaw from "./sub-processors.md?raw";
import termsRaw from "./terms.md?raw";

/** The four documents, addressed by their URL slug. */
export type LegalSlug = "terms" | "privacy" | "acceptable-use" | "sub-processors";

export type LegalDoc = {
  slug: LegalSlug;
  /** Human title, taken from frontmatter. */
  title: string;
  /** Document version — compared against the backend's required version. */
  version: string;
  effectiveDate: string;
  lastUpdated: string;
  /** Markdown body with the frontmatter block removed. */
  body: string;
};

// Matches a leading `---` ... `---` block. Deliberately anchored to the start
// of the string: a `---` horizontal rule further down the document must not be
// mistaken for a frontmatter fence.
const FRONTMATTER = /^---\r?\n([\s\S]*?)\r?\n---\r?\n?/;

/** Unwrap `"quoted"` / `'quoted'` frontmatter values. */
function unquote(value: string): string {
  const trimmed = value.trim();
  const isQuoted =
    trimmed.length >= 2 &&
    ((trimmed.startsWith('"') && trimmed.endsWith('"')) ||
      (trimmed.startsWith("'") && trimmed.endsWith("'")));
  return isQuoted ? trimmed.slice(1, -1) : trimmed;
}

/**
 * Split a document into its frontmatter fields and its body.
 *
 * This is a deliberately minimal parser rather than a YAML dependency: the
 * frontmatter here is four flat `key: value` pairs, and pulling in a parser to
 * read them would be more moving parts for no benefit. Nested YAML is not
 * supported and is not used.
 */
function parse(raw: string): { fields: Record<string, string>; body: string } {
  const match = raw.match(FRONTMATTER);
  if (!match) return { fields: {}, body: raw.trim() };

  const fields: Record<string, string> = {};
  for (const line of match[1].split(/\r?\n/)) {
    const separator = line.indexOf(":");
    if (separator === -1) continue;
    const key = line.slice(0, separator).trim();
    if (key) fields[key] = unquote(line.slice(separator + 1));
  }

  return { fields, body: raw.slice(match[0].length).trim() };
}

/**
 * Drop the document's own title and version line from the top of the body.
 *
 * Every document opens with `# Title` followed by `**Version x.y.z** — Effective
 * ...`. Both are metadata we already hold in structured form from the
 * frontmatter, and the page renders them as a proper header, so leaving them in
 * the body would print each one twice.
 */
function stripRedundantHeader(body: string): string {
  let rest = body.replace(/^#\s+[^\n]*\r?\n+/, "");
  rest = rest.replace(/^\*\*Version[^\n]*\r?\n+/, "");
  return rest;
}

function toDoc(slug: LegalSlug, raw: string, fallbackTitle: string): LegalDoc {
  const { fields, body } = parse(raw);
  return {
    slug,
    title: fields.title || fallbackTitle,
    version: fields.version || "",
    effectiveDate: fields.effective_date || "",
    lastUpdated: fields.last_updated || "",
    body: stripRedundantHeader(body),
  };
}

export const LEGAL_DOCS: Record<LegalSlug, LegalDoc> = {
  terms: toDoc("terms", termsRaw, "Terms of Service"),
  privacy: toDoc("privacy", privacyRaw, "Privacy Policy"),
  "acceptable-use": toDoc("acceptable-use", acceptableUseRaw, "Acceptable Use Policy"),
  "sub-processors": toDoc("sub-processors", subProcessorsRaw, "Sub-processors"),
};

/**
 * Nav order for the footer/header links. Terms and Privacy come first because
 * they are the two documents consent is recorded against.
 */
export const LEGAL_NAV: ReadonlyArray<{ slug: LegalSlug; label: string }> = [
  { slug: "terms", label: "Terms" },
  { slug: "privacy", label: "Privacy" },
  { slug: "acceptable-use", label: "Acceptable Use" },
  { slug: "sub-processors", label: "Sub-processors" },
];

export function isLegalSlug(value: string): value is LegalSlug {
  return Object.prototype.hasOwnProperty.call(LEGAL_DOCS, value);
}

/** Canonical in-app path for a document. The markdown cross-links use these. */
export function legalPath(slug: LegalSlug): string {
  return `/legal/${slug}`;
}
