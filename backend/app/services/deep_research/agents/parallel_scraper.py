"""Agent 4: ParallelScraperAgent — Multi-engine web search with dynamic routing and recursive traversal.

Approach:
1. Search real providers via a cascading fallback (SearxNG -> DuckDuckGo -> Wikipedia -> arXiv).
   Sources are never fabricated: if nothing is found, nothing is added.
2. Skip URLs already collected in earlier iterations before spending a fetch on them.
3. Extract content from each new URL using Trafilatura/BS4/Playwright.
4. Recursive traversal: follow outbound links from the strongest sources for a 2nd hop.
5. Score sources by relevance to the research question using the LLM.
"""

from app.core.json_utils import extract_json_from_text
import asyncio
import logging
import re
from typing import Awaitable, Callable, List, Optional, Set

from app.services.deep_research.models import ResearchState, SourceDocument, SourceType
from app.services.deep_research.utils.scraping import (
    search_web,
    fetch_url,
    get_domain,
    compute_authority_score,
)

logger = logging.getLogger(__name__)

MAX_CONCURRENT = 8
MAX_SOURCES_PER_QUERY = 6
MAX_TOTAL_SOURCES = 30
MAX_2ND_HOP_SOURCES = 10
MAX_QUERIES_PER_ITERATION = 12
MIN_USABLE_TEXT = 200

# Link targets that are never worth a second hop.
_HOP2_SKIP_PATTERNS = re.compile(
    r"(?:facebook|twitter|x)\.com|linkedin\.com|instagram\.com|youtube\.com|"
    r"t\.co/|doubleclick|googletagmanager|google-analytics|/cdn-cgi/|"
    r"\.(?:png|jpe?g|gif|svg|webp|ico|css|js|woff2?|zip|mp4|mp3)(?:\?|$)",
    re.IGNORECASE,
)

SourceCallback = Optional[Callable[[SourceDocument], Awaitable[None]]]


async def run(state: ResearchState, llm_call=None, on_source: SourceCallback = None) -> ResearchState:
    """Run parallel web searches across all queries using dynamic engine routing.

    Args:
        state: pipeline state; `state.sources` is extended in place.
        llm_call: async callable for relevance scoring. Optional.
        on_source: async callback invoked once per newly accepted source, so the
            orchestrator can stream `source_found` events to the UI.
    """
    if not state.queries:
        logger.warning("ParallelScraper: no queries to search")
        return state

    # URLs already collected in previous iterations — never re-fetch these.
    known_urls: Set[str] = {src.url for src in state.sources if src.url}

    sorted_queries = sorted(state.queries, key=lambda q: q.priority, reverse=True)
    queries_to_search = sorted_queries[:MAX_QUERIES_PER_ITERATION]

    semaphore = asyncio.Semaphore(MAX_CONCURRENT)

    async def _search_single_query(query_obj) -> List[SourceDocument]:
        query = query_obj.query
        engines = getattr(query_obj, "target_engines", "google,bing,duckduckgo")
        time_range = getattr(query_obj, "time_range", "")

        results = await search_web(
            query,
            max_results=MAX_SOURCES_PER_QUERY * 2,
            engines=engines,
            time_range=time_range,
        )

        docs: List[SourceDocument] = []
        for r in results:
            url = (r.get("url") or "").strip()
            if not url or url == "#" or not url.startswith(("http://", "https://")):
                continue
            docs.append(
                SourceDocument(
                    url=url,
                    title=r.get("title", ""),
                    snippet=(r.get("snippet") or "")[:500],
                    source_type=_classify_source_type(r.get("source_type"), url),
                    authority_score=compute_authority_score(url),
                    domain=get_domain(url),
                    published_date=r.get("date"),
                )
            )
        return docs

    # ── 1. Launch all searches concurrently ────────────────────────────
    all_results = await asyncio.gather(
        *(_search_single_query(q) for q in queries_to_search),
        return_exceptions=True,
    )

    candidates: List[SourceDocument] = []
    for result in all_results:
        if isinstance(result, list):
            candidates.extend(result)
        elif isinstance(result, Exception):
            logger.warning(f"ParallelScraper: a query failed: {result}")

    # ── 2. Deduplicate against known + within this batch, BEFORE fetching ──
    fresh: List[SourceDocument] = []
    batch_urls: Set[str] = set()
    for doc in candidates:
        if doc.url in known_urls or doc.url in batch_urls:
            continue
        batch_urls.add(doc.url)
        fresh.append(doc)

    if not fresh:
        logger.info("ParallelScraper: no new sources this iteration")
        return state

    fresh.sort(key=lambda s: s.authority_score, reverse=True)
    sources_to_extract = fresh[:MAX_TOTAL_SOURCES]

    # ── 3. Content extraction in parallel ──────────────────────────────
    logger.info(f"ParallelScraper: fetching content from {len(sources_to_extract)} new sources")
    content_results = await asyncio.gather(
        *(_fetch_source_content(src, semaphore) for src in sources_to_extract),
        return_exceptions=True,
    )
    updated_sources = [r for r in content_results if isinstance(r, SourceDocument)]

    # ── 4. Recursive 2nd hop from the strongest sources ────────────────
    hop2_candidates: List[str] = []
    seen_hop2: Set[str] = set()
    for src in updated_sources[:5]:
        if not src.full_text:
            continue
        for link in re.findall(r"https?://[^\s\)\]\"'<>]+", src.full_text):
            link = link.rstrip(".,;:)")
            if (
                link in seen_hop2
                or link in known_urls
                or link in batch_urls
                or get_domain(link) == src.domain
                or _HOP2_SKIP_PATTERNS.search(link)
            ):
                continue
            seen_hop2.add(link)
            hop2_candidates.append(link)

    if hop2_candidates:
        top_hop2 = hop2_candidates[:MAX_2ND_HOP_SOURCES]
        logger.info(f"ParallelScraper: fetching {len(top_hop2)} secondary sources (2nd hop)")
        hop2_docs = [
            SourceDocument(
                url=u,
                domain=get_domain(u),
                title="",
                authority_score=compute_authority_score(u) * 0.9,  # 2nd-hop penalty
            )
            for u in top_hop2
        ]
        hop2_results = await asyncio.gather(
            *(_fetch_source_content(src, semaphore) for src in hop2_docs),
            return_exceptions=True,
        )
        for result in hop2_results:
            if isinstance(result, SourceDocument) and result.full_text:
                updated_sources.append(result)

    # ── 5. Drop sources with no usable content ─────────────────────────
    usable = [
        s for s in updated_sources
        if (s.full_text and len(s.full_text) >= MIN_USABLE_TEXT) or (s.snippet and len(s.snippet) > 80)
    ]
    dropped = len(updated_sources) - len(usable)
    if dropped:
        logger.info(f"ParallelScraper: dropped {dropped} source(s) with no extractable content")

    # ── 6. LLM relevance scoring ───────────────────────────────────────
    if llm_call and usable:
        try:
            usable = await _score_sources_relevance(usable, state.query, llm_call)
        except Exception as e:
            logger.warning(f"Relevance scoring failed: {e}")

    # ── 7. Commit and stream ───────────────────────────────────────────
    for src in usable:
        state.sources.append(src)
        if on_source:
            try:
                await on_source(src)
            except Exception as e:
                logger.debug(f"source_found callback failed: {e}")

    logger.info(
        f"ParallelScraper complete: +{len(usable)} new, {len(state.sources)} total unique sources"
    )
    return state


def _classify_source_type(raw: Optional[str], url: str) -> SourceType:
    """Map a provider's source_type hint onto the SourceType enum."""
    domain = get_domain(url).lower()
    if url.lower().endswith(".pdf"):
        return SourceType.PDF
    if "wikipedia.org" in domain:
        return SourceType.WIKIPEDIA
    if "arxiv.org" in domain or "pubmed" in domain or "doi.org" in domain:
        return SourceType.ACADEMIC
    if domain.endswith(".gov") or domain.endswith(".mil"):
        return SourceType.GOVERNMENT
    mapping = {
        "academic": SourceType.ACADEMIC,
        "news": SourceType.NEWS,
        "wikipedia": SourceType.WIKIPEDIA,
        "forum": SourceType.FORUM,
        "pdf": SourceType.PDF,
    }
    return mapping.get((raw or "").lower(), SourceType.WEB)


async def _fetch_source_content(source: SourceDocument, semaphore: asyncio.Semaphore) -> SourceDocument:
    async with semaphore:
        if source.full_text and len(source.full_text) > MIN_USABLE_TEXT:
            return source
        if not source.url:
            return source

        try:
            result = await fetch_url(source.url, timeout=15.0)
            if result["success"]:
                source.full_text = result["text"]
                if result.get("title") and not source.title:
                    source.title = result["title"]
                if result.get("published_date") and not source.published_date:
                    source.published_date = result["published_date"]
        except Exception as e:
            logger.debug(f"Content fetch failed for {source.url}: {e}")

        if not source.title:
            source.title = source.domain or source.url[:80]
        return source


async def _score_sources_relevance(sources: List[SourceDocument], query: str, llm_call) -> List[SourceDocument]:
    """Blend domain authority with LLM-judged topical relevance."""
    if not sources:
        return sources

    # Score in batches so a long list doesn't blow the context window.
    BATCH = 20
    for start in range(0, len(sources), BATCH):
        batch = sources[start:start + BATCH]
        source_list = ""
        for i, src in enumerate(batch):
            snippet = (src.snippet or src.full_text or "")[:200]
            source_list += f"{i+1}. {src.title} ({src.domain})\n   {snippet}\n\n"

        prompt = f"""You are a research relevance scorer. Rate each source on how directly it helps answer the research question.

Research question: "{query}"

Sources:
{source_list}

Score each source from 0.0 (irrelevant) to 1.0 (directly answers the question).
Return ONLY a JSON array of {len(batch)} numbers in the same order, e.g. [0.95, 0.3, 0.8]"""

        try:
            response = await llm_call([{"role": "user", "content": prompt}])
            scores = extract_json_from_text((response or "").strip())
            if isinstance(scores, list) and len(scores) == len(batch):
                for src, score in zip(batch, scores):
                    if isinstance(score, (int, float)):
                        relevance = max(0.0, min(1.0, float(score)))
                        # Weight relevance above raw domain authority: a highly
                        # authoritative but off-topic page is not useful here.
                        src.authority_score = 0.4 * src.authority_score + 0.6 * relevance
        except Exception as e:
            logger.debug(f"Relevance scoring batch failed: {e}")

    sources.sort(key=lambda s: s.authority_score, reverse=True)
    return sources
