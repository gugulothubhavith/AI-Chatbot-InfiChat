"""Agent 3: AdversarialQueryAgent — Generates multi-angle search queries with intelligent engine routing."""

import json
import logging
from typing import List, Dict, Any
from app.core.json_utils import extract_json_from_text
from app.services.deep_research.models import ResearchState, SearchQuery
from app.services.deep_research.utils.nlp import extract_keywords

logger = logging.getLogger(__name__)

PROMPT_TEMPLATE = """You are an elite research query generator. Given the topic and research plan, generate exactly 15 highly optimized search queries.

Topic: "{topic}"
Key Aspects: {key_aspects}

For each query, you must choose:
1. The exact query string.
2. The category (supporting, debunking, academic, news, data, temporal, regional).
3. The target_engines. Choose a comma-separated list of the best engines for this specific query. Options include:
   - "google,bing,duckduckgo,qwant" (General Web)
   - "google news,bing news" (News)
   - "scholar,arxiv,pubmed" (Academic)
   - "github,stackoverflow" (IT/Code)
   - "reddit,hackernews" (Forums/Discussions)
4. The time_range. If the query requires recent info, specify "month", "week", or "day". If historical/general, use "year" or "".

Return ONLY a JSON array in this exact format:
[
  {{
    "query": "exact search string",
    "category": "news",
    "priority": 8,
    "target_engines": "google news,bing news",
    "time_range": "month"
  }},
  ...
]
"""

async def run(state: ResearchState, llm_call, critic_feedback: str = "", targeted_queries: List[str] = None) -> ResearchState:
    """Generate intelligent queries using LLM."""
    if targeted_queries is None:
        targeted_queries = []
    topic = state.brief.topic if state.brief else state.query
    key_aspects = state.brief.key_aspects if state.brief else []

    # Filter active branches (ToT Pruning)
    active_branches = []
    if state.plan:
        active_branches = [st.title for st in state.plan.subtopics if st.status == "active"]
    
    if active_branches:
        key_aspects.extend([f"FOCUS ON ACTIVE BRANCH: {b}" for b in active_branches])

    if critic_feedback:
        topic += f" (Focus on feedback: {critic_feedback})"

    prompt = PROMPT_TEMPLATE.format(topic=topic, key_aspects=key_aspects)

    try:
        response = await llm_call([{"role": "user", "content": prompt}])
        text = response.strip()
        data = extract_json_from_text(text)
        
        if not isinstance(data, list):
            raise ValueError("LLM did not return a list")

        unique = []
        seen = set()
        
        # Prepend targeted surgical queries from the critic
        for tq in targeted_queries:
            q_str = tq.strip()
            if q_str and q_str.lower() not in seen:
                seen.add(q_str.lower())
                unique.append(SearchQuery(
                    query=q_str, category="targeted_surgical", priority=10, target_engines="google,bing"
                ))

        for item in data[:20]:
            q_str = item.get("query", "").strip()
            if not q_str or q_str.lower() in seen:
                continue
            seen.add(q_str.lower())
            
            priority_val = item.get("priority", 5)
            try:
                priority_int = int(priority_val) if str(priority_val).strip() != "" else 5
            except ValueError:
                priority_int = 5
                
            unique.append(SearchQuery(
                query=q_str,
                category=item.get("category", "general"),
                priority=priority_int,
                target_engines=item.get("target_engines", "google,bing,duckduckgo"),
                time_range=item.get("time_range", "")
            ))
            
        state.queries = unique
        logger.info(f"AdversarialQuery generated {len(unique)} dynamic queries (including {len(targeted_queries)} targeted)")
        
    except Exception as e:
        logger.error(f"AdversarialQuery LLM failed: {e}. Falling back to default.")
        state.queries = [
            SearchQuery(query=topic, priority=10, target_engines="google,bing", time_range=""),
            SearchQuery(query=f"{topic} latest news", priority=8, target_engines="google news,bing news", time_range="month"),
            SearchQuery(query=f"{topic} research paper", priority=8, target_engines="scholar,arxiv", time_range="year"),
            SearchQuery(query=f"{topic} discussion", priority=7, target_engines="reddit,hackernews", time_range="year"),
        ]

    return state
