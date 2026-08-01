/**
 * Short path for the Privacy Policy. See `terms.tsx` for why both `/privacy`
 * and the canonical `/legal/privacy` exist.
 */

import { createFileRoute } from "@tanstack/react-router";

import { LegalPage } from "@/components/legal/LegalPage";
import { LEGAL_DOCS } from "@/content/legal";

const doc = LEGAL_DOCS.privacy;

export const Route = createFileRoute("/privacy")({
  head: () => ({
    meta: [
      { title: `${doc.title} — InfiChat` },
      { name: "description", content: `${doc.title} for InfiChat, version ${doc.version}.` },
      { property: "og:title", content: `${doc.title} — InfiChat` },
    ],
    links: [{ rel: "canonical", href: "/legal/privacy" }],
  }),
  component: () => <LegalPage doc={doc} />,
});
