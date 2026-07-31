"""Content extraction and search utilities.

Multi-engine approach:
1. DuckDuckGo search (free, no API key)
2. LLM-generated fallback results when search is unavailable
3. Content extraction via trafilatura + BeautifulSoup
4. In-memory cache with TTL to avoid redundant fetches
"""

from app.core.json_utils import extract_json_from_text
import json
import logging
# Silence noisy trafilatura warnings about empty pages
logging.getLogger("trafilatura").setLevel(logging.ERROR)
import time
import re
from urllib.parse import urlparse
from typing import List, Optional, Dict, Any, Callable

logger = logging.getLogger(__name__)

# ── In-memory cache ──────────────────────────────────────
_cache: Dict[str, dict] = {}
_CACHE_TTL = 300  # 5 minutes


def _cache_get(key: str) -> Optional[dict]:
    """Get from cache if not expired."""
    entry = _cache.get(key)
    if entry and time.time() - entry["ts"] < _CACHE_TTL:
        return entry["data"]
    if entry:
        del _cache[key]
    return None


def _cache_set(key: str, data: dict) -> None:
    """Set cache entry."""
    _cache[key] = {"data": data, "ts": time.time()}


def _cache_clear() -> None:
    """Clear all expired cache entries."""
    now = time.time()
    expired = [k for k, v in _cache.items() if now - v["ts"] >= _CACHE_TTL]
    for k in expired:
        del _cache[k]


# ── URL fetching and content extraction ─────────────────

async def fetch_url(url: str, timeout: float = 15.0) -> dict:
    """
    Fetch a URL and extract clean content using a 3-tier fallback:
    1. Trafilatura (best for articles)
    2. BeautifulSoup (fallback for generic HTML)
    3. Raw text (last resort)
    """
    cache_key = f"fetch:{url}"
    cached = _cache_get(cache_key)
    if cached:
        return cached

    result = {"url": url, "title": "", "text": "", "description": "", "success": False}

    try:
        import httpx
        async with httpx.AsyncClient(
            timeout=timeout,
            follow_redirects=True,
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=20),
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                              "AppleWebKit/537.36 (KHTML, like Gecko) "
                              "Chrome/120.0.0.0 Safari/537.36"
            }
        ) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            html = resp.text
            content_type = resp.headers.get("content-type", "")
            
            # Check for JS wall or soft blocks
            if len(html) < 1500 and ("enable javascript" in html.lower() or "cloudflare" in html.lower()):
                raise ValueError("JavaScript wall detected")
                
    except Exception as e:
        logger.debug(f"HTTPx fetch failed or blocked for {url}: {e}. Falling back to Playwright.")
        html, content_type = await _fetch_playwright(url)
        if not html:
            _cache_set(cache_key, result)
            return result

    # PDF detection
    if "application/pdf" in content_type or url.lower().endswith(".pdf"):
        pdf_result = await _extract_pdf(url, timeout)
        _cache_set(cache_key, pdf_result)
        return pdf_result

    # Tier 1: Trafilatura
    try:
        import trafilatura
        extracted = trafilatura.extract(
            html,
            include_comments=False,
            include_tables=True,
            no_fallback=False,
            favor_precision=True,
            output_format="txt",
        )
        if extracted and len(extracted) > 100:
            result["text"] = extracted[:20000]
            result["success"] = True
            # Extract metadata
            meta = extract_metadata(html, url)
            result["title"] = meta.get("title", "")
            result["description"] = meta.get("description", "")
            _cache_set(cache_key, result)
            return result
    except Exception as e:
        logger.debug(f"Trafilatura failed for {url}: {e}")

    # Tier 2: BeautifulSoup
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        # Remove non-content elements
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "iframe", "noscript", "form"]):
            tag.decompose()
        text = soup.get_text(separator="\n", strip=True)
        text = re.sub(r'\n{3,}', '\n\n', text)
        if text and len(text) > 50:
            result["text"] = text[:20000]
            title_tag = soup.title
            result["title"] = title_tag.string.strip() if title_tag and title_tag.string else ""
            result["success"] = True
            _cache_set(cache_key, result)
            return result
    except Exception as e:
        logger.debug(f"BS4 failed for {url}: {e}")

    # Tier 3: Raw text (strip HTML tags)
    if html and len(html) > 50:
        clean = re.sub(r'<[^>]+>', ' ', html)
        clean = re.sub(r'\s+', ' ', clean).strip()
        result["text"] = clean[:10000]
        result["success"] = True

    _cache_set(cache_key, result)
    return result


async def _fetch_playwright(url: str, timeout: float = 20.0):
    """Fallback fetcher using headless Chromium to defeat JS walls and blockers."""
    from app.services.deep_research.scraper.vision_scraper import visual_scrape
    
    text = await visual_scrape(url, timeout=int(timeout*1000))
    if text:
        # We don't have raw HTML, but we have the clean text!
        return f"<html><body>{text}</body></html>", "text/html"
    return None, None


async def _extract_pdf(url: str, timeout: float = 20.0) -> dict:
    """Download and extract text from a PDF URL."""
    result = {"url": url, "title": "", "text": "", "description": "", "success": False}
    try:
        import httpx
        import tempfile
        import os

        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            resp = await client.get(url)
            resp.raise_for_status()

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(resp.content)
            tmp_path = tmp.name

        try:
            import pdfplumber
            with pdfplumber.open(tmp_path) as pdf:
                pages_text = []
                for page in pdf.pages[:30]:
                    text = page.extract_text()
                    if text:
                        pages_text.append(text)
                full_text = "\n\n".join(pages_text)
                result["text"] = full_text[:20000]
                result["title"] = os.path.basename(urlparse(url).path)
                result["success"] = True
        finally:
            os.unlink(tmp_path)
    except ImportError:
        logger.debug("pdfplumber not available, skipping PDF extraction")
    except Exception as e:
        logger.debug(f"PDF extraction failed for {url}: {e}")
    return result


# ── Search ───────────────────────────────────────────────

async def search_searxng(query: str, max_results: int = 10, engines: str = "google,bing,duckduckgo,wikipedia,qwant", time_range: str = "") -> List[dict]:
    """Search SearxNG via REST API for highly advanced multi-engine results."""
    import httpx
    from app.core.config import settings

    searxng_url = (settings.SEARXNG_URL or "http://localhost:8080").rstrip("/")
    url = f"{searxng_url}/search"
    params = {
        "q": query,
        "format": "json",
        "engines": engines,
        "categories": "general,news",
        "language": "en-US",
        "safesearch": "1",
    }
    if time_range:
        params["time_range"] = time_range

    cache_key = f"searxng:{engines}:{time_range}:{query}:{max_results}"
    cached = _cache_get(cache_key)
    if cached:
        return cached["results"]

    results = []
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()

            for r in data.get("results", [])[:max_results]:
                results.append({
                    "title": r.get("title", ""),
                    "url": r.get("url", ""),
                    "snippet": r.get("content", ""),
                    "source_type": "web",
                    "date": r.get("publishedDate"),
                })
        logger.info(f"SearxNG found {len(results)} results for '{query[:60]}'")
    except Exception as e:
        logger.warning(f"SearxNG search failed for '{query[:60]}': {e}")

    _cache_set(cache_key, {"results": results})
    return results

async def search_duckduckgo(query: str, max_results: int = 5) -> List[dict]:
    """Search DuckDuckGo and return structured results.

    Returns a list of dicts with keys: title, url, snippet, date (optional).
    Returns empty list on any failure.
    """
    cache_key = f"ddg:{query}:{max_results}"
    cached = _cache_get(cache_key)
    if cached:
        return cached["results"]

    results = []
    try:
        from duckduckgo_search import DDGS

        def _search_sync():
            """Synchronous DDG search wrapper for thread executor."""
            entries = []
            with DDGS() as ddgs:
                for r in ddgs.text(query, max_results=max_results):
                    entries.append({
                        "title": r.get("title", ""),
                        "url": r.get("href", ""),
                        "snippet": r.get("body", ""),
                    })
            return entries

        import asyncio
        # Add a strict timeout to prevent DDGS from hanging indefinitely
        results = await asyncio.wait_for(
            asyncio.to_thread(_search_sync), 
            timeout=10.0
        )
        logger.info(f"DuckDuckGo found {len(results)} results for '{query[:60]}'")
    except ImportError:
        logger.warning("duckduckgo_search library not installed")
    except asyncio.TimeoutError:
        logger.warning(f"DuckDuckGo search timed out for '{query[:60]}'. Falling back.")
    except Exception as e:
        logger.warning(f"DuckDuckGo search failed for '{query[:60]}': {e}")

    _cache_set(cache_key, {"results": results})
    return results


async def search_wikipedia(query: str, max_results: int = 5) -> List[dict]:
    """Search Wikipedia via the official MediaWiki API. Real results only."""
    import httpx

    cache_key = f"wiki:{query}:{max_results}"
    cached = _cache_get(cache_key)
    if cached:
        return cached["results"]

    results: List[dict] = []
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                "https://en.wikipedia.org/w/api.php",
                params={
                    "action": "query",
                    "list": "search",
                    "srsearch": query,
                    "srlimit": max_results,
                    "format": "json",
                    "srprop": "snippet",
                },
                headers={"User-Agent": "InfiChat-Research/1.0 (self-hosted research assistant)"},
            )
            resp.raise_for_status()
            for item in resp.json().get("query", {}).get("search", []):
                title = item.get("title", "")
                snippet = re.sub(r"<[^>]+>", "", item.get("snippet", ""))
                results.append({
                    "title": title,
                    "url": f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}",
                    "snippet": snippet,
                    "source_type": "wikipedia",
                })
        logger.info(f"Wikipedia found {len(results)} results for '{query[:60]}'")
    except Exception as e:
        logger.warning(f"Wikipedia search failed for '{query[:60]}': {e}")

    _cache_set(cache_key, {"results": results})
    return results


async def search_arxiv(query: str, max_results: int = 5) -> List[dict]:
    """Search arXiv via its official Atom API. Real results only."""
    import httpx
    from xml.etree import ElementTree

    cache_key = f"arxiv:{query}:{max_results}"
    cached = _cache_get(cache_key)
    if cached:
        return cached["results"]

    results: List[dict] = []
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.get(
                "http://export.arxiv.org/api/query",
                params={
                    "search_query": f"all:{query}",
                    "start": 0,
                    "max_results": max_results,
                    "sortBy": "relevance",
                },
            )
            resp.raise_for_status()

        ns = {"atom": "http://www.w3.org/2005/Atom"}
        root = ElementTree.fromstring(resp.text)
        for entry in root.findall("atom:entry", ns):
            title_el = entry.find("atom:title", ns)
            summary_el = entry.find("atom:summary", ns)
            id_el = entry.find("atom:id", ns)
            published_el = entry.find("atom:published", ns)
            if id_el is None:
                continue
            results.append({
                "title": (title_el.text or "").strip() if title_el is not None else "",
                "url": (id_el.text or "").strip(),
                "snippet": (summary_el.text or "").strip()[:500] if summary_el is not None else "",
                "source_type": "academic",
                "date": (published_el.text or "").strip() if published_el is not None else None,
            })
        logger.info(f"arXiv found {len(results)} results for '{query[:60]}'")
    except Exception as e:
        logger.warning(f"arXiv search failed for '{query[:60]}': {e}")

    _cache_set(cache_key, {"results": results})
    return results


async def search_web(
    query: str,
    max_results: int = 10,
    engines: str = "google,bing,duckduckgo,wikipedia,qwant",
    time_range: str = "",
) -> List[dict]:
    """Cascading real-source search.

    Tries providers in order of breadth and stops as soon as one returns
    results: SearxNG -> DuckDuckGo -> Wikipedia -> arXiv.

    IMPORTANT: this function never fabricates results. An empty list means
    nothing was found, and callers must treat it as such. Synthesising
    plausible-looking sources would put invented citations into research
    reports, which is worse than returning nothing.
    """
    providers = (
        ("searxng", lambda: search_searxng(query, max_results, engines, time_range)),
        ("duckduckgo", lambda: search_duckduckgo(query, max_results)),
        ("wikipedia", lambda: search_wikipedia(query, min(max_results, 5))),
        ("arxiv", lambda: search_arxiv(query, min(max_results, 5))),
    )

    for name, provider in providers:
        try:
            results = await provider()
        except Exception as e:
            logger.warning(f"Search provider '{name}' errored for '{query[:60]}': {e}")
            continue
        if results:
            if name != "searxng":
                logger.info(f"Search fell back to '{name}' for '{query[:60]}'")
            return results

    logger.warning(f"No search provider returned results for '{query[:60]}'")
    return []


# ── Metadata extraction ──────────────────────────────────

def extract_metadata(html: str, url: str) -> Dict[str, str]:
    """Extract title, description, and publish date from HTML."""
    meta = {"title": "", "description": "", "published_date": ""}

    try:
        # Try Open Graph and standard meta tags
        import re

        # Title: OG first, then standard
        og_title = re.search(r'<meta\s+property=["\']og:title["\']\s+content=["\']([^"\']+)["\']', html, re.IGNORECASE)
        if og_title:
            meta["title"] = og_title.group(1)

        if not meta["title"]:
            std_title = re.search(r'<meta\s+name=["\']title["\']\s+content=["\']([^"\']+)["\']', html, re.IGNORECASE)
            if std_title:
                meta["title"] = std_title.group(1)

        if not meta["title"]:
            html_title = re.search(r'<title>([^<]+)</title>', html, re.IGNORECASE)
            if html_title:
                meta["title"] = html_title.group(1).strip()

        # Description: OG first, then meta description
        og_desc = re.search(r'<meta\s+property=["\']og:description["\']\s+content=["\']([^"\']+)["\']', html, re.IGNORECASE)
        if og_desc:
            meta["description"] = og_desc.group(1)

        if not meta["description"]:
            meta_desc = re.search(r'<meta\s+name=["\']description["\']\s+content=["\']([^"\']+)["\']', html, re.IGNORECASE)
            if meta_desc:
                meta["description"] = meta_desc.group(1)

        # Published date: article:published_time first
        pub_date = re.search(r'<meta\s+property=["\']article:published_time["\']\s+content=["\']([^"\']+)["\']', html, re.IGNORECASE)
        if pub_date:
            meta["published_date"] = pub_date.group(1)

        if not meta["published_date"]:
            dc_date = re.search(r'<meta\s+name=["\']dc\.date["\']\s+content=["\']([^"\']+)["\']', html, re.IGNORECASE)
            if dc_date:
                meta["published_date"] = dc_date.group(1)

    except Exception as e:
        logger.debug(f"Metadata extraction failed: {e}")

    return meta


# ── Domain utilities ──────────────────────────────────────

def get_domain(url: str) -> str:
    """Extract domain from URL."""
    try:
        return urlparse(url).netloc.replace("www.", "")
    except Exception:
        return ""


def compute_authority_score(url: str) -> float:
    """Score domain authority based on TLD/domain patterns."""
    domain = get_domain(url).lower()

    # Government sources
    if domain.endswith(".gov") or domain.endswith(".gov.uk") or domain.endswith(".mil"):
        return 0.95
    # Educational
    if domain.endswith(".edu") or domain.endswith(".ac.uk") or domain.endswith(".ac.jp"):
        return 0.90
    # Known high-quality domains
    high_authority = [
        "nature.com", "science.org", "thelancet.com", "nejm.org",
        "arxiv.org", "pubmed.ncbi.nlm.nih.gov", "scholar.google.com",
        "who.int", "cdc.gov", "nih.gov", "ieee.org", "acm.org",
        "reuters.com", "apnews.com", "bbc.com", "nytimes.com",
        "wikipedia.org", "britannica.com", "bloomberg.com",
        "wsj.com", "economist.com", "ft.com",
    ]
    for ha in high_authority:
        if ha in domain:
            return 0.85
    # Organizational
    if domain.endswith(".org"):
        return 0.70
    # Established news
    news_domains = ["cnn.com", "theguardian.com", "washingtonpost.com",
                    "forbes.com", "npr.org", "pbs.org", "cspan.org"]
    for nd in news_domains:
        if nd in domain:
            return 0.75
    # Default
    return 0.50


def _cache_clear_all() -> None:
    """Clear entire cache (for testing)."""
    _cache.clear()
