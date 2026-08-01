/**
 * Public route for every legal document: /legal/terms, /legal/privacy,
 * /legal/acceptable-use, /legal/sub-processors.
 *
 * Public by design — it sits outside the `_app` layout, so it has no auth
 * guard. Someone who has not signed up yet, and someone currently blocked by
 * the re-consent gate, both have to be able to read what they are agreeing to.
 */

import { createFileRoute, notFound } from "@tanstack/react-router";

import { LegalPage } from "@/components/legal/LegalPage";
import { LEGAL_DOCS, isLegalSlug } from "@/content/legal";

export const Route = createFileRoute("/legal/$slug")({
  // Validating in `loader` rather than the component means an unknown slug
  // renders the app's 404 instead of a blank page.
  loader: ({ params }) => {
    if (!isLegalSlug(params.slug)) throw notFound();
    return { slug: params.slug };
  },
  head: ({ params }) => {
    const doc = isLegalSlug(params.slug) ? LEGAL_DOCS[params.slug] : undefined;
    if (!doc) return {};
    const title = `${doc.title} — InfiChat`;
    return {
      meta: [
        { title },
        { name: "description", content: `${doc.title} for InfiChat, version ${doc.version}.` },
        { property: "og:title", content: title },
      ],
    };
  },
  component: LegalDocPage,
});

function LegalDocPage() {
  const { slug } = Route.useLoaderData();
  return <LegalPage doc={LEGAL_DOCS[slug]} />;
}
