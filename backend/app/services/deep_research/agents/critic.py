"""Agent 10: CriticAgent — 6-check quality gate with loop-back capability."""

from app.core.json_utils import extract_json_from_text
import json
import logging
from app.services.deep_research.models import (
    ResearchState, QualityGateResult, QualityCheck, CriticVerdict,
)

logger = logging.getLogger(__name__)

QUALITY_CHECKS = [
    "coverage",       # Are all subtopics covered?
    "source_diversity", # Multiple source types?
    "fact_validation",  # Are claims cross-validated?
    "balance",         # Both supporting and contradicting views?
    "recency",         # Are sources recent enough?
    "depth",           # Sufficient detail for the depth level?
]

CRITIC_PROMPT = """You are a research quality critic. Evaluate this research data and determine if it's ready for final synthesis.

Topic: "{topic}"
Required Depth: {depth}

Research Statistics:
- Total sources found: {source_count}
- Sources with full text: {full_text_count}
- Academic sources: {academic_count}
- News sources: {news_count}
- Fact claims validated: {fact_count}
- Knowledge graph entities: {entity_count}
- Timeline events: {event_count}

Key Aspects to Cover: {aspects}

Fact Claims Found:
{fact_summary}

Evaluate these 6 quality checks and return JSON:
{{
  "checks": [
    {{"name": "coverage", "passed": true/false, "detail": "explanation"}},
    {{"name": "source_diversity", "passed": true/false, "detail": "explanation"}},
    {{"name": "fact_validation", "passed": true/false, "detail": "explanation"}},
    {{"name": "balance", "passed": true/false, "detail": "explanation"}},
    {{"name": "recency", "passed": true/false, "detail": "explanation"}},
    {{"name": "depth", "passed": true/false, "detail": "explanation"}}
  ],
  "branch_evaluations": [
    {{
      "title": "exact title of hypothesis/subtopic",
      "status": "active" or "pruned" or "completed",
      "score": 0.0-1.0
    }}
  ],
  "verdict": "COMPLETE" or "NEEDS_MORE",
  "feedback": "what additional research is needed if NEEDS_MORE",
  "overall_confidence": 0.0-1.0,
  "targeted_queries": ["if NEEDS_MORE, provide 3-5 specific search queries to resolve contradictions or missing info"]
}}

Be strict but fair. If a hypothesis branch (subtopic) yields bad data or is entirely refuted, mark its status as "pruned".
If 4+ checks pass AND there are no major unresolved contradictions, verdict should be COMPLETE.
Return ONLY valid JSON."""


async def run(state: ResearchState, llm_call) -> ResearchState:
    """Run 6-check quality gate. Returns verdict: COMPLETE or NEEDS_MORE."""
    # NOTE: iteration is incremented by the orchestrator, not here

    # Compute statistics
    sources = state.sources
    full_text_sources = [s for s in sources if s.full_text and len(s.full_text) > 100]
    academic_sources = [s for s in sources if s.source_type.value == "academic"]
    news_sources = [s for s in sources if s.source_type.value == "news"]
    entities = state.knowledge_graph.entities if state.knowledge_graph else []
    events = state.temporal.events if state.temporal else []
    facts = state.facts

    # Build fact summary
    fact_summary = ""
    for f in facts[:15]:
        fact_summary += f"- [{f.stance.value}] {f.claim} (confidence: {f.confidence})\n"

    # Build active branches summary
    branches_summary = ""
    if state.plan:
        for st in state.plan.subtopics:
            branches_summary += f"- [Status: {st.status}] {st.title} (Priority: {st.priority})\n"

    prompt = CRITIC_PROMPT.format(
        topic=state.brief.topic if state.brief else state.query,
        depth=state.brief.depth_level if state.brief else "standard",
        source_count=len(sources),
        full_text_count=len(full_text_sources),
        academic_count=len(academic_sources),
        news_count=len(news_sources),
        fact_count=len(facts),
        entity_count=len(entities),
        event_count=len(events),
        aspects=", ".join(state.brief.key_aspects) if state.brief else state.query,
        fact_summary=fact_summary or "No facts extracted yet.",
    )
    # Inject branches if present
    if branches_summary:
        prompt += f"\nActive Research Branches (Hypotheses):\n{branches_summary}"

    try:
        response = await llm_call([{"role": "user", "content": prompt}])
        text = response.strip()
        
        data = extract_json_from_text(text)

        checks = []
        for check_data in data.get("checks", []):
            checks.append(QualityCheck(
                name=check_data.get("name", ""),
                passed=check_data.get("passed", False),
                detail=check_data.get("detail", ""),
            ))

        # Parse Tree-of-Thought branch evaluations
        branch_evals = data.get("branch_evaluations", [])
        if state.plan and branch_evals:
            for eval_data in branch_evals:
                t = eval_data.get("title", "")
                st = eval_data.get("status", "active")
                sc = eval_data.get("score", 0.0)
                for subtopic in state.plan.subtopics:
                    if subtopic.title == t:
                        subtopic.status = st
                        subtopic.score = sc

        verdict_str = data.get("verdict", "NEEDS_MORE")
        try:
            verdict = CriticVerdict(verdict_str)
        except ValueError:
            verdict = CriticVerdict.NEEDS_MORE

        result = QualityGateResult(
            iteration=state.iteration,
            checks=checks,
            verdict=verdict,
            feedback=data.get("feedback", ""),
            overall_confidence=data.get("overall_confidence", 0.5),
            targeted_queries=data.get("targeted_queries", []),
        )

    except Exception as e:
        logger.warning(f"Critic LLM failed: {e}. Using heuristic evaluation.")
        # Heuristic fallback
        checks = []
        checks.append(QualityCheck(name="coverage", passed=len(sources) >= 10, detail=f"{len(sources)} sources"))
        checks.append(QualityCheck(name="source_diversity", passed=len(academic_sources) >= 2 and len(news_sources) >= 1, detail="type mix"))
        checks.append(QualityCheck(name="fact_validation", passed=len(facts) >= 3, detail=f"{len(facts)} facts"))
        checks.append(QualityCheck(name="balance", passed=any(f.stance.value == "contradicts" for f in facts), detail="stance check"))
        checks.append(QualityCheck(name="recency", passed=len(events) >= 3, detail=f"{len(events)} events"))
        checks.append(QualityCheck(name="depth", passed=len(full_text_sources) >= 5, detail=f"{len(full_text_sources)} full texts"))

        passed_count = sum(1 for c in checks if c.passed)
        verdict = CriticVerdict.COMPLETE if passed_count >= 4 else CriticVerdict.NEEDS_MORE

        result = QualityGateResult(
            iteration=state.iteration,
            checks=checks,
            verdict=verdict,
            feedback="Need more diverse sources" if verdict == CriticVerdict.NEEDS_MORE else "",
            overall_confidence=passed_count / 6,
        )

    state.quality_results.append(result)

    # Force COMPLETE if max iterations reached
    if state.iteration >= state.max_iterations:
        result.verdict = CriticVerdict.COMPLETE
        result.feedback = "Max iterations reached. Proceeding with available data."
        logger.info("Critic: max iterations reached, forcing COMPLETE")

    logger.info(f"Critic iteration {state.iteration}: {result.verdict.value} (confidence: {result.overall_confidence})")
    return state
