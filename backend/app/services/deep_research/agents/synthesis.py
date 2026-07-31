"""Agent 11: SynthesisAgent — Final structured report with citations."""

import json
import logging
from app.services.deep_research.models import (
    ResearchState, ResearchReport, Citation,
)

logger = logging.getLogger(__name__)

# Bounds on what gets packed into the synthesis prompt. Without these, an
# exhaustive run overflows the context window and the model silently truncates
# mid-report.
MAX_FACTS = 40
MAX_SOURCES = 30
SOURCE_EXCERPT_CHARS = 1200
MAX_TIMELINE_EVENTS = 30
MAX_ENTITIES = 40
MAX_CONTRADICTIONS = 15

SYNTHESIS_PROMPT = """You are a senior research analyst writing the definitive report on a question. Your work will be read by decision-makers who will act on it.

Research question: "{topic}"
Domain: {domain}
Audience: {audience}

## Source Material

### Cross-validated facts
{facts_text}

### Sources (cite these by number)
{sources_text}

### Timeline
{timeline_text}

### Key entities
{entities_text}

### Contradictions and disputes
{contradictions_text}

## Grounding rules (these override any instinct to sound authoritative)

1. Every substantive claim MUST carry an inline citation to a numbered source above, e.g. [3] or [1][4].
2. Cite ONLY source numbers that appear in the "Sources" list. Never invent a number, a title, or a URL.
3. If the sources do not settle a question, say so explicitly and explain what evidence is missing. A precise "the evidence is inconclusive because X" is more valuable than false confidence.
4. Where sources disagree, present both positions with their citations and assess which is better supported and why.
5. Do not introduce facts from your own background knowledge unless you flag them clearly as unsourced context.

## Report structure (Markdown)

1. **Executive Summary** — 2-3 paragraphs that answer the question directly, up front.
2. **Key Findings** — bullets, each with citations and a confidence signal.
3. **Detailed Analysis** — organised by theme, not by source. Synthesise across sources; do not summarise them one at a time.
4. **Evidence For** — the strongest support, with citations.
5. **Evidence Against / Counterpoints** — the strongest opposing evidence, with citations.
6. **Timeline of Key Events** — only if the timeline data is relevant.
7. **Visualisation** — at least one Mermaid chart (`graph LR`, `pie`, or `gantt`) in a ```mermaid block, visualising the entity graph, the timeline, or key quantities.
8. **Confidence Assessment** — what you are confident about, what is uncertain, and what further research would resolve.
9. **Conclusion** — the bottom line.
10. **Sources** — numbered list matching the citations used.

Citation format: standard square brackets only, e.g. [1], [2]. NEVER use the 【1†L1-L3】 format.

Write the complete report. Be specific and quantitative wherever the sources permit. Do not abbreviate, and never emit placeholder text."""


async def run(state: ResearchState, llm_call) -> ResearchState:
    """Synthesize all research data into a final structured report.

    Inputs are bounded so the prompt stays inside the context window even after
    an exhaustive multi-iteration run, and citations are emitted ONLY for the
    sources actually shown to the model — so every [n] in the report resolves.
    """
    topic = state.brief.topic if state.brief else state.query

    # Highest-confidence facts first, capped.
    ranked_facts = sorted(state.facts, key=lambda f: f.confidence, reverse=True)[:MAX_FACTS]
    facts_text = "".join(
        f"- [{f.stance.value.upper()}] {f.claim} "
        f"(confidence: {f.confidence:.0%}, {len(f.supporting_sources) or f.source_count} source(s))\n"
        for f in ranked_facts
    ) or "No cross-validated facts available.\n"

    # Only the strongest sources are cited, and only these get citation entries.
    top_sources = sorted(state.sources, key=lambda s: s.authority_score, reverse=True)[:MAX_SOURCES]
    sources_text = ""
    citations = []
    for i, src in enumerate(top_sources):
        idx = i + 1
        content = (src.full_text or src.snippet or "")[:SOURCE_EXCERPT_CHARS]
        sources_text += (
            f"\n[{idx}] {src.title} ({src.domain}, authority: {src.authority_score:.2f})\n{content}\n"
        )
        citations.append(Citation(
            index=idx,
            title=src.title or src.domain,
            url=src.url,
            authority=src.authority_score,
        ))

    # Build timeline text
    timeline_text = ""
    if state.temporal and state.temporal.events:
        for event in state.temporal.events[:MAX_TIMELINE_EVENTS]:
            timeline_text += f"- {event.date}: {event.description}\n"
    else:
        timeline_text = "No timeline data available.\n"

    # Build entities text — most-mentioned first.
    entities_text = ""
    if state.knowledge_graph and state.knowledge_graph.entities:
        top_entities = sorted(
            state.knowledge_graph.entities, key=lambda e: e.mentions, reverse=True
        )[:MAX_ENTITIES]
        for ent in top_entities:
            entities_text += f"- {ent.name} ({ent.entity_type}, {ent.mentions} mentions)\n"
    else:
        entities_text = "No entities extracted.\n"

    # Surface contradictions explicitly so the report can discuss controversy.
    contradictions_text = ""
    if state.knowledge_graph and state.knowledge_graph.contradictions:
        for c in state.knowledge_graph.contradictions[:MAX_CONTRADICTIONS]:
            contradictions_text += f"- {c}\n"
    contra_facts = [f for f in state.facts if f.stance.value == "contradicts"][:MAX_CONTRADICTIONS]
    for f in contra_facts:
        contradictions_text += f"- Disputed: {f.claim}\n"
    if not contradictions_text:
        contradictions_text = "No direct contradictions detected between sources.\n"

    prompt = SYNTHESIS_PROMPT.format(
        topic=topic,
        domain=state.brief.domain if state.brief else "general",
        audience=state.brief.audience if state.brief else "general",
        facts_text=facts_text,
        sources_text=sources_text,
        timeline_text=timeline_text,
        entities_text=entities_text,
        contradictions_text=contradictions_text,
    )

    try:
        response = await llm_call([{"role": "user", "content": prompt}])
        
        import re
        full_markdown = response.strip()
        # Clean up stray RAG citations (e.g. 【3†L1-L3】 -> [3])
        full_markdown = re.sub(r'【(\d+)(?:†[^】]+)?】', r'[\1]', full_markdown)

        # Drop citations pointing past the end of the source list. A dangling
        # [47] when only 30 sources exist is a hallucinated reference, and
        # leaving it in makes the whole report untrustworthy.
        max_index = len(citations)
        dangling = {
            int(m) for m in re.findall(r'\[(\d{1,3})\]', full_markdown)
            if int(m) > max_index or int(m) == 0
        }
        if dangling:
            logger.warning(
                f"Synthesis emitted {len(dangling)} out-of-range citation(s) "
                f"{sorted(dangling)} against {max_index} sources — removing them"
            )
            for bad in dangling:
                full_markdown = full_markdown.replace(f"[{bad}]", "")

        # Keep only the citations actually referenced in the prose.
        used_indices = {
            int(m) for m in re.findall(r'\[(\d{1,3})\]', full_markdown)
            if 0 < int(m) <= max_index
        }
        if used_indices:
            citations = [c for c in citations if c.index in used_indices]

        # Extract structured sections (best effort)
        key_findings = []
        evidence_for = []
        evidence_against = []

        # Parse sections from the markdown
        sections = full_markdown.split("\n## ")
        for section in sections:
            lower = section.lower()
            if "key finding" in lower:
                lines = [l.strip("- •").strip() for l in section.split("\n") if l.strip().startswith(("-", "•", "*"))]
                key_findings = [{"finding": l} for l in lines]
            elif "evidence for" in lower or "supporting" in lower:
                lines = [l.strip("- •").strip() for l in section.split("\n") if l.strip().startswith(("-", "•", "*"))]
                evidence_for = lines
            elif "evidence against" in lower or "contradicting" in lower:
                lines = [l.strip("- •").strip() for l in section.split("\n") if l.strip().startswith(("-", "•", "*"))]
                evidence_against = lines

        # Build timeline data
        timeline_data = []
        if state.temporal and state.temporal.events:
            timeline_data = [
                {"date": e.date, "event": e.description}
                for e in state.temporal.events
            ]

        # Knowledge graph JSON
        kg_json = {}
        if state.knowledge_graph:
            kg_json = {
                "entities": [{"name": e.name, "type": e.entity_type, "mentions": e.mentions}
                             for e in state.knowledge_graph.entities],
                "relationships": [{"from": r.source_entity, "to": r.target_entity, "type": r.relation_type}
                                  for r in state.knowledge_graph.relationships],
            }

        # Compute overall confidence
        confidence = 0.5
        if state.quality_results:
            last_qr = state.quality_results[-1]
            confidence = last_qr.overall_confidence

        state.report = ResearchReport(
            executive_summary=_extract_section(full_markdown, "executive summary"),
            key_findings=key_findings,
            evidence_for=evidence_for,
            evidence_against=evidence_against,
            timeline=timeline_data,
            knowledge_graph_json=kg_json,
            citations=citations,
            full_markdown=full_markdown,
            confidence_score=confidence,
        )

    except Exception as e:
        logger.error(f"Synthesis failed: {e}")
        # Fallback: create a basic report from available data
        fallback_md = f"# Research Report: {topic}\n\n"
        fallback_md += "## Sources Found\n\n"
        for i, src in enumerate(top_sources):
            fallback_md += f"{i+1}. [{src.title}]({src.url}) — {src.snippet[:200]}\n\n"

        state.report = ResearchReport(
            executive_summary=f"Research on '{topic}' found {len(state.sources)} sources.",
            citations=citations,
            full_markdown=fallback_md,
            confidence_score=0.3,
        )

    logger.info(f"Synthesis complete: {len(citations)} citations, confidence: {state.report.confidence_score}")
    return state


def _extract_section(markdown: str, section_name: str) -> str:
    """Extract a section from markdown by heading name."""
    import re
    pattern = rf'##?\s*{re.escape(section_name)}.*?\n(.*?)(?=\n##|\Z)'
    match = re.search(pattern, markdown, re.IGNORECASE | re.DOTALL)
    return match.group(1).strip() if match else ""
