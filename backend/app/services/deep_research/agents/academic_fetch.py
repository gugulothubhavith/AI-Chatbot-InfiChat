"""Agent 5: AcademicFetchAgent — Multi-source academic search.

Approach:
1. Try SearxNG first with academic engines (arxiv, scholar, pubmed, wikipedia).
2. If SearxNG returns nothing, fall back to the real arXiv Atom API and the
   Wikipedia MediaWiki API — both return genuine sources.

Sources are NEVER fabricated. If no provider returns anything, the agent adds
nothing rather than inventing plausible-looking citations.
"""

import logging
from typing import List

from app.services.deep_research.models import ResearchState, SourceDocument, SourceType
from app.services.deep_research.utils.scraping import (
    search_searxng,
    search_arxiv,
    search_wikipedia,
    get_domain,
    compute_authority_score,
)

logger = logging.getLogger(__name__)


async def run(state: ResearchState, llm_call=None) -> ResearchState:
    """Fetch academic sources from SearxNG, falling back to arXiv/Wikipedia APIs."""
    topic = state.brief.topic if state.brief else state.query
    key_aspects = state.brief.key_aspects if state.brief else []

    academic_sources: List[SourceDocument] = []
    errors: List[str] = []

    # ── Engine 1: SearxNG (Academic Engines) ──────────────────────────────────
    try:
        searxng_results = await search_searxng(topic, max_results=8, engines="arxiv,scholar,pubmed,wikipedia")
        
        for r in searxng_results:
            url = r.get("url", "")
            if not url or url == "#" or url.startswith("javascript:"):
                continue

            doc = SourceDocument(
                url=url,
                title=r.get("title", ""),
                snippet=r.get("snippet", "")[:500],
                source_type=SourceType.ACADEMIC,
                authority_score=compute_authority_score(url) or 0.85, # Default high authority for academic
                domain=get_domain(url),
                published_date=r.get("date"),
            )
            academic_sources.append(doc)
            
        logger.info(f"SearxNG Academic returned {len(academic_sources)} results for '{topic[:60]}'")
    except Exception as e:
        errors.append(f"SearxNG Academic: {e}")
        logger.warning(f"SearxNG Academic search failed: {e}")

    # Also search key aspects
    if not academic_sources and key_aspects:
        for aspect in key_aspects[:2]:
            try:
                aspect_results = await search_searxng(aspect, max_results=3, engines="arxiv,scholar,pubmed,wikipedia")
                for r in aspect_results:
                    url = r.get("url", "")
                    if not url: continue
                    doc = SourceDocument(
                        url=url,
                        title=r.get("title", ""),
                        snippet=r.get("snippet", "")[:500],
                        source_type=SourceType.ACADEMIC,
                        authority_score=compute_authority_score(url) or 0.85,
                        domain=get_domain(url),
                        published_date=r.get("date"),
                    )
                    academic_sources.append(doc)
            except Exception as e:
                logger.debug(f"SearxNG Academic aspect search failed for '{aspect[:40]}': {e}")


    # ── Engine 2: Real arXiv + Wikipedia APIs (if SearxNG returned nothing) ─
    if not academic_sources:
        logger.info(f"No academic sources from SearxNG, trying arXiv/Wikipedia APIs for '{topic[:60]}'")
        for provider_name, provider in (
            ("arxiv", lambda: search_arxiv(topic, max_results=5)),
            ("wikipedia", lambda: search_wikipedia(topic, max_results=5)),
        ):
            try:
                results = await provider()
            except Exception as e:
                errors.append(f"{provider_name}: {e}")
                logger.warning(f"Academic {provider_name} search failed: {e}")
                continue
            for r in results:
                url = (r.get("url") or "").strip()
                if not url or not url.startswith(("http://", "https://")):
                    continue
                academic_sources.append(SourceDocument(
                    url=url,
                    title=r.get("title", ""),
                    snippet=(r.get("snippet") or "")[:500],
                    source_type=SourceType.ACADEMIC if provider_name == "arxiv" else SourceType.WIKIPEDIA,
                    authority_score=compute_authority_score(url),
                    domain=get_domain(url),
                    published_date=r.get("date"),
                ))
            if academic_sources:
                break

    # ── Merge into state ────────────────────────────────
    for src in academic_sources:
        state.sources.append(src)

    # Deduplicate
    seen = set()
    unique = []
    for src in state.sources:
        if src.url not in seen:
            seen.add(src.url)
            unique.append(src)
    state.sources = unique

    logger.info(
        f"AcademicFetch: added {len(academic_sources)} sources "
        f"(total now {len(state.sources)}). Errors: {len(errors)}"
    )
    return state


# ── LLM Fallback ─────────────────────────────────────────

async def _search_academic_llm(topic: str, llm_call, max_results: int = 5) -> List[SourceDocument]:
    """Generate simulated academic sources via LLM when APIs fail."""
    prompt = f"""You are an academic research source simulator. Generate {max_results} realistic academic/scholarly sources for the topic:

Topic: "{topic}"

For each source, provide:
- title: A realistic academic paper or encyclopedia title
- url: A plausible URL using real domains (arxiv.org, wikipedia.org, nature.com, etc.)
- snippet: A 2-3 sentence abstract or summary
- source_type: one of "academic", "wikipedia"
- published_date: A realistic date (YYYY-MM-DD format)

Return ONLY a JSON array:
[
  {{
    "title": "...",
    "url": "https://...",
    "snippet": "...",
    "source_type": "academic",
    "published_date": "2024-06-15"
  }}
]

Make results specific, factual-sounding, and relevant. Use real-sounding paper titles.
Do NOT include markdown formatting."""

    try:
        response = await llm_call([{"role": "user", "content": prompt}])
        text = response.strip()
        

        data = extract_json_from_text(text)
        if not isinstance(data, list):
            raise ValueError("LLM did not return a list")

        results = []
        for item in data[:max_results]:
            source_type_str = item.get("source_type", "academic")
            try:
                st = SourceType(source_type_str)
            except ValueError:
                st = SourceType.ACADEMIC

            src = SourceDocument(
                url=item.get("url", f"https://arxiv.org/search/?query={topic.replace(' ', '+')}"),
                title=item.get("title", f"Academic paper on {topic}"),
                snippet=item.get("snippet", "")[:500],
                full_text=item.get("snippet", ""),
                source_type=st,
                authority_score=0.85,
                published_date=item.get("published_date"),
                domain="generated",
            )
            results.append(src)

        return results
    except Exception as e:
        logger.error(f"LLM academic generation failed: {e}")
        return []
