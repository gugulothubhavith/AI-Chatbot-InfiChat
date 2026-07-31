"""Agent 9: CrossValidationAgent — 3-source triangulation and stance detection."""

from app.core.json_utils import extract_json_from_text
import logging
from app.services.deep_research.models import ResearchState, FactClaim, Stance
from app.services.deep_research.utils.scoring import (
    semantic_similarity_texts, compute_weighted_score,
)

logger = logging.getLogger(__name__)


async def run(state: ResearchState, llm_call) -> ResearchState:
    """Cross-validate facts across sources using TF-IDF similarity and LLM stance detection."""
    sources_with_content = [
        s for s in state.sources
        if (s.full_text and len(s.full_text) > 50) or (s.snippet and len(s.snippet) > 30)
    ]

    if len(sources_with_content) < 2:
        logger.warning("CrossValidation: not enough sources with content")
        return state

    # 1. Map Phase: Chunk sources into batches of 5
    topic = state.brief.topic if state.brief else state.query
    
    # We use all sources with content now, not just the top 10!
    import asyncio
    
    # Sort by authority but use up to 30
    all_sources = sorted(sources_with_content, key=lambda s: s.authority_score, reverse=True)[:30]
    
    batch_size = 5
    batches = [all_sources[i:i + batch_size] for i in range(0, len(all_sources), batch_size)]
    
    async def extract_claims_from_batch(batch):
        source_summaries = ""
        for i, src in enumerate(batch):
            text = (src.full_text or src.snippet)[:600]
            source_summaries += f"\n[Source {src.id}: {src.title}]\n{text}\n"

        claim_prompt = f"""Analyze these sources about "{topic}" and extract 2-4 key factual claims. Ensure extraction is highly concise.

{source_summaries}

For each claim, note which source IDs support or contradict it.
Return JSON array:
[
  {{
    "claim": "factual statement",
    "supporting_sources": ["id1", "id2"],
    "contradicting_sources": [],
    "confidence": 0.85
  }}
]

Return ONLY valid JSON array."""
        
        try:
            response = await llm_call([{"role": "user", "content": claim_prompt}])
            return extract_json_from_text(response.strip())
        except Exception as e:
            logger.warning(f"CrossValidation Map LLM failed: {e}")
            return []

    # Run map phase concurrently
    logger.info(f"CrossValidation: Running {len(batches)} concurrent Map-Reduce tasks")
    map_results = await asyncio.gather(*(extract_claims_from_batch(b) for b in batches))
    
    facts = []
    
    # Reduce Phase: Merge and determine stance
    # In a fully strict map-reduce, we would run another LLM call to deduplicate these facts.
    # For now, we flatten and calculate stance manually to save time.
    for claims_data in map_results:
        if not claims_data or not isinstance(claims_data, list):
            continue
            
        for claim_data in claims_data:
            supporting = claim_data.get("supporting_sources", [])
            contradicting = claim_data.get("contradicting_sources", [])

            # Map source IDs back to actual source objects for domain checks
            sup_sources = [s for s in all_sources if s.id in supporting]
            con_sources = [s for s in all_sources if s.id in contradicting]
            
            sup_ids = [s.id for s in sup_sources]
            con_ids = [s.id for s in con_sources]
            
            sup_domains = set([s.domain for s in sup_sources])

            # Determine stance with strict corroboration (Requires >= 2 distinct domains)
            if len(contradicting) > 0 and len(sup_domains) > len(contradicting):
                stance = Stance.PARTIAL
            elif len(contradicting) >= len(sup_domains) and len(contradicting) > 0:
                stance = Stance.CONTRADICTS
            elif len(sup_domains) >= 2:
                stance = Stance.CONFIRMS
            else:
                stance = Stance.NOISE

            facts.append(FactClaim(
                claim=claim_data.get("claim", ""),
                supporting_sources=sup_ids,
                contradicting_sources=con_ids,
                stance=stance,
                confidence=claim_data.get("confidence", 0.5),
                source_count=len(sup_ids) + len(con_ids),
            ))

    if not facts:
        logger.warning(f"CrossValidation LLM extracted 0 facts. Using TF-IDF fallback.")
        top_sources = all_sources[:10]
        # Fallback: compute pairwise similarity between sources
        for i, src_a in enumerate(top_sources[:5]):
            text_a = (src_a.full_text or src_a.snippet)[:500]
            similar_sources = []
            for j, src_b in enumerate(top_sources):
                if i == j:
                    continue
                text_b = (src_b.full_text or src_b.snippet)[:500]
                sim = semantic_similarity_texts(text_a, text_b)
                if sim > 0.3:
                    similar_sources.append(src_b.id)

            if similar_sources:
                facts.append(FactClaim(
                    claim=src_a.title or src_a.snippet[:100],
                    supporting_sources=similar_sources[:3],
                    stance=Stance.CONFIRMS if len(similar_sources) >= 2 else Stance.PARTIAL,
                    confidence=min(len(similar_sources) / 3, 1.0),
                    source_count=len(similar_sources) + 1,
                ))

    state.facts = facts
    logger.info(f"CrossValidation: {len(facts)} fact claims validated")
    return state
