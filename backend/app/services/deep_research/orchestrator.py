"""Deep Research Orchestrator — coordinates the multi-agent research pipeline with SSE streaming.

Design notes
------------
* **Per-agent API keys.** Every stage names itself when calling the LLM, so the
  key pool hands each agent its own NVIDIA key. The four agents in the parallel
  analysis stage are pinned to four different keys, which is what makes that
  stage safe to run concurrently without tripping rate limits.

* **Model tiering.** Cheap, structured work (intent, query generation, scoring)
  runs on the fast model. Judgement-heavy work (synthesis, critique, graph
  extraction) runs on the reasoning model with a large completion budget.

* **No fabricated evidence.** Sources come only from real search providers. The
  verification pass drops any claim that cannot be tied back to a retrieved
  source, so citations in the final report always resolve.

* **Event contract.** Status values are always one of `running` / `completed` /
  `error`, and the critic verdict is normalised to `pass` / `fail` for the UI.
  Consumers can rely on these exact strings.
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import AsyncGenerator, Awaitable, Callable, List, Optional

from app.services.deep_research.models import (
    CriticVerdict,
    FactClaim,
    ResearchState,
    SourceDocument,
)
from app.services.deep_research.agents import (
    intent_analysis,
    research_planner,
    adversarial_query,
    parallel_scraper,
    academic_fetch,
    deep_content,
    knowledge_graph,
    temporal_analysis,
    cross_validation,
    critic,
    synthesis,
    knowledge_archiver,
    data_scientist,
    local_retriever,
)
from app.services.llm_router import complete_text
from app.core.config import settings

logger = logging.getLogger(__name__)

TOTAL_STAGES = 12

# Completion budgets per class of work. The router no longer clamps these, so a
# synthesis stage can actually produce a long report.
TOKENS_FAST = 2048
TOKENS_STANDARD = 4096
TOKENS_SYNTHESIS = 16384

# A claim needs at least this confidence to be surfaced as a partial finding.
PARTIAL_FINDING_MIN_CONFIDENCE = 0.7


def _sse_event(event_type: str, data: dict) -> str:
    """Format a Server-Sent Event frame."""
    return f"data: {json.dumps({'type': event_type, **data})}\n\n"


def _make_llm(agent: str, model: str, max_tokens: int = TOKENS_STANDARD,
              temperature: float = 0.4) -> Callable[[list], Awaitable[str]]:
    """Build the `llm_fn(messages) -> str` closure an agent expects.

    Binding the agent name here is what routes the call to that agent's own
    pooled API key.
    """
    async def _call(messages: list) -> str:
        return await complete_text(
            messages,
            agent=agent,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )
    return _call


def _emit_stage(state: ResearchState, stage_name: str, stage_num: int, msg: str) -> str:
    """Record and emit an overall-progress stage change."""
    state.research_stage = stage_name
    state.stage_timestamps[stage_name] = datetime.now(timezone.utc).isoformat()
    return _sse_event("research_stage", {
        "stage": stage_name,
        "stage_number": stage_num,
        "total_stages": TOTAL_STAGES,
        "message": msg,
    })


def _source_payload(src: SourceDocument) -> dict:
    """Shape a source for the UI's source panel."""
    domain = src.domain or ""
    return {
        "id": src.id,
        "title": src.title or domain or src.url,
        "url": src.url,
        "snippet": (src.snippet or src.full_text or "")[:280],
        "domain": domain,
        "favicon": f"https://www.google.com/s2/favicons?domain={domain}&sz=64" if domain else None,
        "authority": round(src.authority_score, 3),
        "source_type": src.source_type.value,
    }


async def run_pipeline(
    query: str,
    model: str = None,
    max_iterations: Optional[int] = None,
) -> AsyncGenerator[str, None]:
    """Execute the full deep research pipeline, yielding SSE events.

    Event types:
        research_stage   — overall stage changed
        agent_status     — an agent started / completed / errored
        plan             — the research plan tree
        source_found     — a new source was retrieved
        partial_finding  — an intermediate verified claim
        quality_gate     — critic results for one iteration
        report           — the final research report
        done             — pipeline finished
        error            — fatal error
    """
    reasoning_model = model or settings.DEEP_RESEARCH_DEFAULT_MODEL
    fast_model = settings.DEEP_RESEARCH_FAST_LOOP_MODEL

    state = ResearchState(query=query)
    if max_iterations is not None:
        state.max_iterations = max(1, min(int(max_iterations), 5))

    # ── Per-agent LLM bindings (each gets its own pooled key) ────────────
    llm_intent = _make_llm("intent", fast_model, TOKENS_FAST, temperature=0.2)
    llm_planner = _make_llm("planner", reasoning_model, TOKENS_STANDARD, temperature=0.3)
    llm_queries = _make_llm("adversarial_query", fast_model, TOKENS_STANDARD, temperature=0.6)
    llm_scraper = _make_llm("scraper", fast_model, TOKENS_FAST, temperature=0.1)
    llm_academic = _make_llm("academic", fast_model, TOKENS_FAST, temperature=0.2)
    llm_content = _make_llm("deep_content", reasoning_model, TOKENS_STANDARD, temperature=0.2)
    llm_graph = _make_llm("knowledge_graph", reasoning_model, TOKENS_STANDARD, temperature=0.2)
    llm_temporal = _make_llm("temporal", fast_model, TOKENS_STANDARD, temperature=0.2)
    llm_crossval = _make_llm("cross_validation", reasoning_model, TOKENS_STANDARD, temperature=0.2)
    llm_datasci = _make_llm("data_scientist", fast_model, TOKENS_STANDARD, temperature=0.2)
    llm_critic = _make_llm("critic", reasoning_model, TOKENS_STANDARD, temperature=0.3)
    llm_synthesis = _make_llm("synthesis", reasoning_model, TOKENS_SYNTHESIS, temperature=0.4)
    llm_archiver = _make_llm("archiver", fast_model, TOKENS_FAST, temperature=0.1)
    llm_local = _make_llm("local_retriever", fast_model, TOKENS_FAST, temperature=0.1)
    llm_verifier = _make_llm("verifier", reasoning_model, TOKENS_STANDARD, temperature=0.0)

    # ── Source streaming ────────────────────────────────────────────────
    # Agents run inside async generators, so they can't yield SSE frames
    # directly. They push onto this queue and the orchestrator drains it.
    source_queue: asyncio.Queue = asyncio.Queue()

    async def on_source(src: SourceDocument) -> None:
        await source_queue.put(src)

    def drain_sources() -> List[str]:
        events = []
        while not source_queue.empty():
            try:
                src = source_queue.get_nowait()
            except asyncio.QueueEmpty:
                break
            events.append(_sse_event("source_found", {"source": _source_payload(src)}))
        return events

    async def run_agent(agent_name: str, agent_num: int, agent_fn, llm_fn,
                        running_msg: str, data_fn=None):
        """Run one agent, yielding running/completed/error events around it.

        Never raises: a failed agent degrades the report rather than killing
        the whole pipeline.
        """
        nonlocal state
        yield _sse_event("agent_status", {
            "agent": agent_name,
            "status": "running",
            "message": running_msg,
            "agent_number": agent_num,
        })
        try:
            result = await agent_fn(state, llm_fn)
            if result is not None:
                state = result
            data = {}
            if data_fn:
                try:
                    data = data_fn(state)
                except Exception as e:
                    logger.debug(f"{agent_name} data_fn failed: {e}")
            yield _sse_event("agent_status", {
                "agent": agent_name,
                "status": "completed",
                "message": f"{agent_name} finished",
                "agent_number": agent_num,
                "data": data,
            })
        except Exception as e:
            logger.error(f"{agent_name} failed: {e}", exc_info=True)
            yield _sse_event("agent_status", {
                "agent": agent_name,
                "status": "error",
                "message": str(e)[:300],
                "agent_number": agent_num,
            })
        for ev in drain_sources():
            yield ev

    try:
        # ═══════════════════════════════════════════════════════════════
        # Stage 1: Intent analysis
        # ═══════════════════════════════════════════════════════════════
        yield _emit_stage(state, "Analyzing Query Intent", 1,
                          "Understanding what you're looking for...")
        async for ev in run_agent(
            "IntentAnalysis", 1, intent_analysis.run, llm_intent,
            "Analyzing your query...",
            lambda s: s.brief.model_dump() if s.brief else {},
        ):
            yield ev

        # ═══════════════════════════════════════════════════════════════
        # Stage 2: Research plan
        # ═══════════════════════════════════════════════════════════════
        yield _emit_stage(state, "Creating Research Plan", 2,
                          "Building a structured research roadmap...")
        async for ev in run_agent(
            "ResearchPlanner", 2, research_planner.run, llm_planner,
            "Creating research plan...",
            lambda s: {"subtopic_count": len(s.plan.subtopics) if s.plan else 0},
        ):
            yield ev
        if state.plan:
            yield _sse_event("plan", {"tree": _plan_tree(state)})

        # ═══════════════════════════════════════════════════════════════
        # Stages 3-10: iterative research loop, gated by the critic
        # ═══════════════════════════════════════════════════════════════
        streamed_findings: set = set()

        while state.iteration < state.max_iterations:
            iteration_label = state.iteration + 1
            critic_feedback = ""
            targeted_queries: List[str] = []
            if state.quality_results:
                last = state.quality_results[-1]
                if last.verdict == CriticVerdict.COMPLETE:
                    break
                critic_feedback = last.feedback
                targeted_queries = last.targeted_queries
            state.critic_feedback = critic_feedback

            # ── Private knowledge base (first iteration only) ──────────
            if state.iteration == 0:
                yield _emit_stage(state, "Retrieving Private Data", 3,
                                  "Searching your local knowledge base...")
                async for ev in run_agent(
                    "LocalRetriever", 3, local_retriever.run, llm_local,
                    "Querying vector database...",
                    lambda s: {"internal_sources": sum(
                        1 for src in s.sources if src.domain == "internal-workspace")},
                ):
                    yield ev

            # ── Query generation ──────────────────────────────────────
            yield _emit_stage(state, "Generating Search Queries", 4,
                              f"Formulating search strategies (iteration {iteration_label})...")
            async for ev in run_agent(
                "AdversarialQuery", 4,
                lambda st, llm: adversarial_query.run(
                    st, llm, critic_feedback=critic_feedback, targeted_queries=targeted_queries),
                llm_queries,
                "Generating search queries...",
                lambda s: {"query_count": len(s.queries)},
            ):
                yield ev

            # ── Web search + extraction (streams source_found) ────────
            yield _emit_stage(state, "Searching the Web", 5,
                              "Scanning sources across the web...")
            sources_before = len(state.sources)
            async for ev in run_agent(
                "ParallelScraper", 5,
                lambda st, llm: parallel_scraper.run(st, llm, on_source=on_source),
                llm_scraper,
                "Executing parallel web searches...",
                lambda s: {"total_sources": len(s.sources),
                           "new_sources": len(s.sources) - sources_before},
            ):
                yield ev

            # ── Academic sources ──────────────────────────────────────
            yield _emit_stage(state, "Fetching Academic Sources", 6,
                              "Searching arXiv, PubMed and reference works...")
            academic_before = len(state.sources)
            async for ev in run_agent(
                "AcademicFetch", 6, academic_fetch.run, llm_academic,
                "Searching academic sources...",
                lambda s: {"total_sources": len(s.sources)},
            ):
                yield ev
            # Academic fetch appends directly, so stream whatever it added.
            for src in state.sources[academic_before:]:
                yield _sse_event("source_found", {"source": _source_payload(src)})

            # Guard: without sources there is nothing to analyse.
            if not state.sources:
                yield _sse_event("agent_status", {
                    "agent": "ParallelScraper", "status": "error", "agent_number": 5,
                    "message": "No sources could be retrieved. Check that SearxNG is reachable "
                               "and the host has outbound internet access.",
                })
                break

            # ── Deep content extraction ───────────────────────────────
            yield _emit_stage(state, "Extracting Content", 7,
                              "Reading and extracting full article contents...")
            async for ev in run_agent(
                "DeepContent", 7, deep_content.run, llm_content,
                "Extracting full article content...",
                lambda s: {"full_text_extracted": sum(
                    1 for src in s.sources if src.full_text and len(src.full_text) > 100)},
            ):
                yield ev

            # ── Parallel analysis ─────────────────────────────────────
            # These four run concurrently on four distinct API keys. Each
            # writes to its own field of `state` (knowledge_graph, temporal,
            # facts, and analytics respectively), so concurrent execution is
            # safe under asyncio's single-threaded scheduling.
            yield _emit_stage(state, "Parallel Analysis", 8,
                              "Running graph, temporal, validation and quantitative analysis...")

            parallel_agents = [
                ("KnowledgeGraph", 8, knowledge_graph.run, llm_graph),
                ("TemporalAnalysis", 9, temporal_analysis.run, llm_temporal),
                ("CrossValidation", 10, cross_validation.run, llm_crossval),
                ("DataScientist", 11, data_scientist.run, llm_datasci),
            ]
            for name, num, _fn, _llm in parallel_agents:
                yield _sse_event("agent_status", {
                    "agent": name, "status": "running",
                    "message": f"{name} analysing...", "agent_number": num,
                })

            async def _run_parallel(name, num, fn, llm):
                try:
                    await fn(state, llm)
                    return _sse_event("agent_status", {
                        "agent": name, "status": "completed",
                        "message": f"{name} finished", "agent_number": num,
                    })
                except Exception as e:
                    logger.error(f"{name} failed: {e}", exc_info=True)
                    return _sse_event("agent_status", {
                        "agent": name, "status": "error",
                        "message": str(e)[:300], "agent_number": num,
                    })

            for ev in await asyncio.gather(
                *(_run_parallel(n, num, fn, llm) for n, num, fn, llm in parallel_agents)
            ):
                yield ev
            for ev in drain_sources():
                yield ev

            # ── Stream newly confirmed findings ───────────────────────
            for fact in state.facts:
                key = (fact.claim or "")[:120]
                if not key or key in streamed_findings:
                    continue
                if fact.confidence < PARTIAL_FINDING_MIN_CONFIDENCE:
                    continue
                streamed_findings.add(key)
                payload = {
                    "claim": fact.claim[:400],
                    "confidence": round(fact.confidence, 3),
                    "source_count": len(fact.supporting_sources) or fact.source_count,
                    "stance": fact.stance.value,
                }
                state.partial_findings.append(payload)
                yield _sse_event("partial_finding", payload)

            # ── Quality gate ──────────────────────────────────────────
            yield _emit_stage(state, "Running Quality Checks", 12,
                              f"Evaluating research quality (iteration {iteration_label})...")
            async for ev in run_agent(
                "Critic", 12, critic.run, llm_critic,
                "Running quality checks...",
                lambda s: {"verdict": s.quality_results[-1].verdict.value
                           if s.quality_results else "unknown"},
            ):
                yield ev

            if state.quality_results:
                last = state.quality_results[-1]
                yield _sse_event("quality_gate", {
                    "iteration": last.iteration or iteration_label,
                    "checks": [c.model_dump() for c in last.checks],
                    # Normalised for the UI; raw_verdict keeps the detail.
                    "verdict": "pass" if last.verdict == CriticVerdict.COMPLETE else "fail",
                    "raw_verdict": last.verdict.value,
                    "confidence": round(last.overall_confidence, 3),
                    "feedback": last.feedback,
                })
                if last.verdict == CriticVerdict.COMPLETE:
                    state.iteration += 1
                    break
            else:
                # Critic produced nothing — don't spin the loop pointlessly.
                logger.warning("Critic returned no verdict; ending research loop")
                state.iteration += 1
                break

            state.iteration += 1

        # ═══════════════════════════════════════════════════════════════
        # Evidence verification — drop unsupported claims before writing
        # ═══════════════════════════════════════════════════════════════
        if state.facts:
            yield _sse_event("agent_status", {
                "agent": "EvidenceVerifier", "status": "running",
                "message": "Verifying every claim against its cited sources...",
                "agent_number": 13,
            })
            try:
                kept, removed = await _verify_evidence(state, llm_verifier)
                yield _sse_event("agent_status", {
                    "agent": "EvidenceVerifier", "status": "completed",
                    "message": f"{kept} claim(s) verified, {removed} unsupported claim(s) dropped",
                    "agent_number": 13,
                    "data": {"verified": kept, "dropped": removed},
                })
            except Exception as e:
                logger.error(f"EvidenceVerifier failed: {e}", exc_info=True)
                yield _sse_event("agent_status", {
                    "agent": "EvidenceVerifier", "status": "error",
                    "message": str(e)[:300], "agent_number": 13,
                })

        # ═══════════════════════════════════════════════════════════════
        # Synthesis
        # ═══════════════════════════════════════════════════════════════
        yield _emit_stage(state, "Writing Final Report", 11,
                          "Synthesizing all findings into a comprehensive report...")
        async for ev in run_agent(
            "Synthesis", 11, synthesis.run, llm_synthesis,
            "Writing final research report...",
            lambda s: {"citations": len(s.report.citations) if s.report else 0},
        ):
            yield ev

        if state.report:
            yield _sse_event("report", {
                "content": state.report.full_markdown,
                "executive_summary": state.report.executive_summary,
                "citations": [c.model_dump() for c in state.report.citations],
                "confidence": round(state.report.confidence_score, 3),
                "source_count": len(state.sources),
                "fact_count": len(state.facts),
                "entity_count": len(state.knowledge_graph.entities) if state.knowledge_graph else 0,
            })
        else:
            yield _sse_event("error", {
                "message": "Synthesis produced no report. See server logs for the failing stage.",
            })

        # ═══════════════════════════════════════════════════════════════
        # Archive to long-term memory
        # ═══════════════════════════════════════════════════════════════
        yield _emit_stage(state, "Archiving Research", 12,
                          "Archiving verified facts to the knowledge base...")
        async for ev in run_agent(
            "KnowledgeArchiver", 12, knowledge_archiver.run, llm_archiver,
            "Archiving research to long-term memory...",
            lambda s: {"archived": sum(1 for f in s.facts if f.stance.value == "confirms")},
        ):
            yield ev

        yield _sse_event("done", {
            "research_id": state.research_id,
            "total_sources": len(state.sources),
            "verified_facts": len(state.facts),
            "iterations": state.iteration,
            "stages_completed": len(state.stage_timestamps),
        })

    except asyncio.CancelledError:
        logger.info(f"Research {state.research_id} cancelled by client")
        raise
    except Exception as e:
        logger.error(f"Research pipeline crashed: {e}", exc_info=True)
        yield _sse_event("error", {"message": f"Research failed: {str(e)[:300]}"})


def _plan_tree(state: ResearchState) -> list:
    """Convert the research plan into the id/title/children tree the UI renders."""
    if not state.plan:
        return []
    tree = []
    for i, sub in enumerate(state.plan.subtopics, start=1):
        tree.append({
            "id": i,
            "title": sub.title,
            "priority": sub.priority,
            "status": sub.status,
            "children": [
                {"id": i * 100 + j, "title": q}
                for j, q in enumerate(sub.queries[:4], start=1)
            ],
        })
    return tree


async def _verify_evidence(state: ResearchState, llm_fn) -> tuple:
    """Drop claims that aren't supported by retrieved source text.

    Two passes:
    1. Structural — a claim must reference at least one source ID that actually
       exists in `state.sources`. This alone removes hallucinated citations.
    2. Semantic — the LLM checks the claim against the cited excerpts and votes
       supported / unsupported. Only confident rejections are removed, so a
       flaky verifier can't silently gut a good report.

    Returns (kept_count, removed_count).
    """
    valid_ids = {src.id for src in state.sources}
    by_id = {src.id: src for src in state.sources}

    structurally_ok: List[FactClaim] = []
    removed = 0
    for fact in state.facts:
        supporting = [sid for sid in fact.supporting_sources if sid in valid_ids]
        if not supporting:
            removed += 1
            logger.debug(f"Dropped claim with no resolvable source: {fact.claim[:80]}")
            continue
        fact.supporting_sources = supporting
        fact.source_count = len(supporting)
        structurally_ok.append(fact)

    if not structurally_ok:
        state.facts = []
        return 0, removed

    # Semantic verification, batched to keep prompts bounded.
    BATCH = 8
    verified: List[FactClaim] = []
    for start in range(0, len(structurally_ok), BATCH):
        batch = structurally_ok[start:start + BATCH]
        blocks = []
        for i, fact in enumerate(batch, start=1):
            excerpts = []
            for sid in fact.supporting_sources[:3]:
                src = by_id.get(sid)
                if not src:
                    continue
                text = (src.full_text or src.snippet or "")[:700]
                excerpts.append(f"  [{sid}] {src.title} ({src.domain}): {text}")
            blocks.append(f"CLAIM {i}: {fact.claim}\nEVIDENCE:\n" + "\n".join(excerpts))

        prompt = (
            "You are a strict fact-checker. For each numbered claim, decide whether the "
            "supplied evidence excerpts actually support it.\n\n"
            + "\n\n".join(blocks)
            + f"\n\nReturn ONLY a JSON array of {len(batch)} objects, in order:\n"
            '[{"claim_number": 1, "supported": true, "confidence": 0.9, "reason": "short"}]\n'
            "Mark supported=false ONLY if the evidence clearly fails to support the claim. "
            "If the evidence is merely thin or partial, mark supported=true with lower confidence."
        )

        try:
            from app.core.json_utils import extract_json_from_text
            raw = await llm_fn([{"role": "user", "content": prompt}])
            verdicts = extract_json_from_text((raw or "").strip())
            if isinstance(verdicts, dict):
                verdicts = next((v for v in verdicts.values() if isinstance(v, list)), [])
            verdict_by_num = {}
            if isinstance(verdicts, list):
                for v in verdicts:
                    if isinstance(v, dict) and "claim_number" in v:
                        try:
                            verdict_by_num[int(v["claim_number"])] = v
                        except (TypeError, ValueError):
                            continue
        except Exception as e:
            logger.warning(f"Evidence verification batch failed, keeping batch as-is: {e}")
            verified.extend(batch)
            continue

        for i, fact in enumerate(batch, start=1):
            verdict = verdict_by_num.get(i)
            if verdict is None:
                # No verdict returned — keep the claim rather than guess.
                verified.append(fact)
                continue
            if verdict.get("supported") is False:
                removed += 1
                logger.debug(
                    f"Dropped unsupported claim: {fact.claim[:80]} "
                    f"({verdict.get('reason', 'no reason given')})"
                )
                continue
            try:
                conf = float(verdict.get("confidence", fact.confidence))
                # Blend the verifier's confidence with the cross-validator's.
                fact.confidence = max(0.0, min(1.0, (fact.confidence + conf) / 2.0))
            except (TypeError, ValueError):
                pass
            verified.append(fact)

    state.facts = verified
    return len(verified), removed
