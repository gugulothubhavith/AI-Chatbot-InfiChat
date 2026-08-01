/**
 * Short path for the Terms of Service.
 *
 * `/legal/terms` is the canonical URL — that is what the cross-links inside the
 * documents point to — but `/terms` is the shape people type, and the one the
 * sign-in and registration screens link to. It renders the same document rather
 * than redirecting: a redirect would flash an intermediate page for someone in
 * the middle of deciding whether to accept. `rel="canonical"` keeps search
 * engines from treating the two paths as duplicate content.
 */

import { createFileRoute } from "@tanstack/react-router";

import { LegalPage } from "@/components/legal/LegalPage";
import { LEGAL_DOCS } from "@/content/legal";

const doc = LEGAL_DOCS.terms;

export const Route = createFileRoute("/terms")({
  head: () => ({
    meta: [
      { title: `${doc.title} — InfiChat` },
      { name: "description", content: `${doc.title} for InfiChat, version ${doc.version}.` },
      { property: "og:title", content: `${doc.title} — InfiChat` },
    ],
    links: [{ rel: "canonical", href: "/legal/terms" }],
  }),
  component: () => <LegalPage doc={doc} />,
});
