"""Multi-Agent Coding Orchestrator — coordinates the 7-agent coding pipeline with SSE streaming.

Design notes
------------
* **Per-agent API keys.** Every agent stage names itself when calling the LLM
  via `complete_text(agent=...)`. The key pool hands each coding agent its own
  NVIDIA key, so concurrent coder swarm tasks don't share a quota.

* **Test → Debug loop.** After the tester runs, we check its output for
  failures. If any are found, the debugger is called to fix the code, and we
  re-run the tester (up to MAX_DEBUG_ITERATIONS times).

* **No destructive truncation.** The optimizer sees file content but never
  replaces the full original with a shortened LLM response unless it covers
  the whole file.

* **Event contract.** Status values are always one of `running` / `completed`
  / `error`. Consumers can rely on these exact strings.
"""

import json
import asyncio
import logging
from typing import AsyncGenerator, List

from app.services.code_orchestrator.models import (
    OrchestrationState, AgentType, CodingTask,
)
from app.services.code_orchestrator.agents import (
    run_architect,
    run_spec_writer,
    run_task_decomposer,
    run_coder,
    run_tester,
    run_debugger,
    run_optimizer,
)
from app.services.llm_router import complete_text
from app.core.config import settings

logger = logging.getLogger(__name__)

MAX_DEBUG_ITERATIONS = 2


# ── Helpers ───────────────────────────────────────────────────────────────

def _sse_event(event_type: str, data: dict) -> str:
    """Format a Server-Sent Event."""
    return f"data: {json.dumps({'type': event_type, **data})}\n\n"


async def _code_llm(messages: list, agent: str = "coder", stream: bool = False):
    """LLM call for code pipeline agents — always key-pooled.

    In non-streaming mode, returns the text content string.
    In streaming mode, returns an async generator of content-delta strings.
    """
    from app.services.llm_router import call_llm

    model = settings.CODER_MODEL
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.2,
        "max_tokens": 16384,
    }
    if stream:
        return await call_llm("code_generate", payload, agent=agent, stream=True)
    result = await call_llm("code_generate", payload, agent=agent, stream=False)
    try:
        return result["choices"][0]["message"]["content"] or ""
    except (KeyError, IndexError, TypeError):
        return ""


# ── Pipeline ──────────────────────────────────────────────────────────────

async def run_coding_pipeline(prompt: str) -> AsyncGenerator[str, None]:
    """Execute the 7-agent multi-agent coding pipeline.

    Yields SSE events for each stage of progress.

    Event types:
        - agent_status: Agent started/completed/errored
        - plan: Task plan tree
        - code_generated: Individual file output
        - code_chunk: Streaming code chunk
        - code_progress: Per-task progress
        - test_results: Test output
        - report: Final report with all files
        - done: Pipeline complete
        - error: Fatal error
    """
    state = OrchestrationState(prompt=prompt)

    # Build per-agent LLM closures — each routes to its own pooled key.
    async def llm_architect(messages: list, stream: bool = False):
        return await _code_llm(messages, agent="code_architect", stream=stream)

    async def llm_spec(messages: list, stream: bool = False):
        return await _code_llm(messages, agent="code_spec", stream=stream)

    async def llm_decomposer(messages: list, stream: bool = False):
        return await _code_llm(messages, agent="code_decomposer", stream=stream)

    async def llm_coder(messages: list, stream: bool = False):
        return await _code_llm(messages, agent="coder", stream=stream)

    async def llm_tester(messages: list, stream: bool = False):
        return await _code_llm(messages, agent="code_tester", stream=stream)

    async def llm_debugger(messages: list, stream: bool = False):
        return await _code_llm(messages, agent="code_debugger", stream=stream)

    async def llm_optimizer(messages: list, stream: bool = False):
        return await _code_llm(messages, agent="code_optimizer", stream=stream)

    try:
        # ── Agent 1: Architect ──────────────────────────────
        state.current_agent = AgentType.ARCHITECT
        yield _sse_event("agent_status", {
            "agent": "Architect", "status": "running",
            "message": "Designing system architecture...",
            "agent_number": 1,
        })
        try:
            state = await run_architect(state, llm_architect)
            yield _sse_event("agent_status", {
                "agent": "Architect", "status": "completed",
                "agent_number": 1,
                "data": {
                    "components": len(state.architecture.components) if state.architecture else 0,
                    "tech_stack": state.architecture.tech_stack if state.architecture else [],
                },
            })
        except Exception as e:
            logger.error(f"Architect failed: {e}", exc_info=True)
            yield _sse_event("agent_status", {
                "agent": "Architect", "status": "error",
                "agent_number": 1, "message": str(e)[:300],
            })

        # ── Agent 2: Spec Writer ────────────────────────────
        state.current_agent = AgentType.SPEC_WRITER
        yield _sse_event("agent_status", {
            "agent": "SpecWriter", "status": "running",
            "message": "Creating detailed specifications...",
            "agent_number": 2,
        })
        try:
            state = await run_spec_writer(state, llm_spec)
            yield _sse_event("agent_status", {
                "agent": "SpecWriter", "status": "completed",
                "agent_number": 2,
                "data": {
                    "requirements": len(state.specification.functional_requirements) if state.specification else 0,
                    "endpoints": len(state.specification.api_endpoints) if state.specification else 0,
                },
            })
        except Exception as e:
            logger.error(f"SpecWriter failed: {e}", exc_info=True)
            yield _sse_event("agent_status", {
                "agent": "SpecWriter", "status": "error",
                "agent_number": 2, "message": str(e)[:300],
            })

        # ── Agent 3: Task Decomposer ────────────────────────
        state.current_agent = AgentType.TASK_DECOMPOSER
        yield _sse_event("agent_status", {
            "agent": "TaskDecomposer", "status": "running",
            "message": "Breaking down into parallel coding tasks...",
            "agent_number": 3,
        })
        try:
            state = await run_task_decomposer(state, llm_decomposer)
            tasks_data = [
                {"id": t.id, "title": t.title, "dependencies": t.dependencies, "status": t.status}
                for t in state.tasks
            ]
            yield _sse_event("plan", {"tree": tasks_data})
            yield _sse_event("agent_status", {
                "agent": "TaskDecomposer", "status": "completed",
                "agent_number": 3,
                "data": {"task_count": len(state.tasks)},
            })
        except Exception as e:
            logger.error(f"TaskDecomposer failed: {e}", exc_info=True)
            yield _sse_event("agent_status", {
                "agent": "TaskDecomposer", "status": "error",
                "agent_number": 3, "message": str(e)[:300],
            })

        # ── Agent 4: Coder Swarm ────────────────────────────
        state.current_agent = AgentType.CODER
        yield _sse_event("agent_status", {
            "agent": "CoderSwarm", "status": "running",
            "message": f"Running {len(state.tasks)} parallel coding agents...",
            "agent_number": 4,
        })

        # Process tasks respecting dependency order
        completed_tasks: set = set()
        remaining_tasks = list(state.tasks)

        while remaining_tasks:
            ready = [t for t in remaining_tasks if all(dep in completed_tasks for dep in t.dependencies)]
            if not ready:
                logger.warning("Circular dependency detected; running all remaining tasks")
                ready = remaining_tasks[:]

            event_queue: asyncio.Queue = asyncio.Queue()

            async def _coder_wrapper(task: CodingTask):
                await event_queue.put(_sse_event("code_progress", {
                    "task_id": task.id, "title": task.title,
                    "status": "running", "message": f"Coding {task.title}...",
                }))
                try:
                    result = await run_coder(state, task, llm_coder)
                    for f in result.output_files:
                        await event_queue.put(_sse_event("code_generated", {
                            "file": {"path": f.path, "content": f.content, "language": f.language},
                        }))
                    await event_queue.put(_sse_event("code_progress", {
                        "task_id": task.id, "title": task.title,
                        "status": "completed" if result.status == "completed" else "failed",
                        "files": [{"path": f.path, "language": f.language} for f in result.output_files],
                        "error": result.error,
                    }))
                    # Update the task in state (safe: each wrapper touches its own task)
                    task.status = result.status
                    task.output_files = result.output_files
                    task.error = result.error
                except Exception as e:
                    logger.error(f"Coder failed for '{task.title[:50]}': {e}", exc_info=True)
                    await event_queue.put(_sse_event("code_progress", {
                        "task_id": task.id, "title": task.title,
                        "status": "error", "error": str(e)[:300],
                    }))
                    task.status = "failed"
                    task.error = str(e)

            active_count = len(ready)
            sentinel = object()

            async def _launch_all():
                await asyncio.gather(*(_coder_wrapper(t) for t in ready))
                await event_queue.put(sentinel)

            gather_task = asyncio.create_task(_launch_all())

            while True:
                item = await event_queue.get()
                if item is sentinel:
                    break
                yield item

            for t in ready:
                remaining_tasks.remove(t)
                completed_tasks.add(t.id)

        # Collect all generated files from tasks into state.output_files
        state.output_files = []
        for task in state.tasks:
            for f in task.output_files:
                if f.content:
                    state.output_files.append(f)

        yield _sse_event("agent_status", {
            "agent": "CoderSwarm", "status": "completed",
            "agent_number": 4,
            "data": {"files_generated": len(state.output_files)},
        })

        # ── Agent 5: Tester + Agent 6: Debugger loop ───────
        for debug_iter in range(MAX_DEBUG_ITERATIONS + 1):
            state.current_agent = AgentType.TESTER
            yield _sse_event("agent_status", {
                "agent": "Tester", "status": "running",
                "message": f"Generating and verifying tests (pass {debug_iter + 1})...",
                "agent_number": 5,
            })
            try:
                state = await run_tester(state, llm_tester)
                test_failures = _extract_test_failures(state)
                yield _sse_event("agent_status", {
                    "agent": "Tester", "status": "completed",
                    "agent_number": 5,
                    "data": {
                        "test_files": len([f for f in state.output_files if "test" in f.path.lower()]),
                        "failures_found": len(test_failures),
                    },
                })
            except Exception as e:
                logger.error(f"Tester failed: {e}", exc_info=True)
                yield _sse_event("agent_status", {
                    "agent": "Tester", "status": "error",
                    "agent_number": 5, "message": str(e)[:300],
                })
                break

            if not test_failures or debug_iter >= MAX_DEBUG_ITERATIONS:
                break

            # Debugger pass
            state.current_agent = AgentType.DEBUGGER
            yield _sse_event("agent_status", {
                "agent": "Debugger", "status": "running",
                "message": f"Fixing {len(test_failures)} issue(s) found by tester...",
                "agent_number": 6,
            })
            try:
                error_summary = "\n".join(test_failures[:5])
                state = await run_debugger(state, error_summary, llm_debugger)
                yield _sse_event("agent_status", {
                    "agent": "Debugger", "status": "completed",
                    "agent_number": 6,
                    "data": {"issues_addressed": len(test_failures)},
                })
            except Exception as e:
                logger.error(f"Debugger failed: {e}", exc_info=True)
                yield _sse_event("agent_status", {
                    "agent": "Debugger", "status": "error",
                    "agent_number": 6, "message": str(e)[:300],
                })
                break

        # ── Agent 7: Optimizer ──────────────────────────────
        state.current_agent = AgentType.OPTIMIZER
        yield _sse_event("agent_status", {
            "agent": "Optimizer", "status": "running",
            "message": "Reviewing and optimizing code...",
            "agent_number": 7,
        })
        try:
            state = await run_optimizer(state, llm_optimizer)
            yield _sse_event("agent_status", {
                "agent": "Optimizer", "status": "completed",
                "agent_number": 7,
                "data": {"files_optimized": len(state.output_files)},
            })
        except Exception as e:
            logger.error(f"Optimizer failed: {e}", exc_info=True)
            yield _sse_event("agent_status", {
                "agent": "Optimizer", "status": "error",
                "agent_number": 7, "message": str(e)[:300],
            })

        state.status = "completed"

        # ── Final Report ────────────────────────────────────
        yield _sse_event("report", {
            "content": _build_report(state),
            "files": [
                {
                    "path": f.path,
                    "content": f.content,
                    "language": f.language,
                    "description": f.description,
                }
                for f in state.output_files
            ],
            "architecture": state.architecture.model_dump() if state.architecture else {},
            "tasks": [{"id": t.id, "title": t.title, "status": t.status} for t in state.tasks],
        })

        yield _sse_event("done", {
            "session_id": state.session_id,
            "total_files": len(state.output_files),
            "total_tasks": len(state.tasks),
        })

    except asyncio.CancelledError:
        logger.info(f"Coding pipeline {state.session_id} cancelled by client")
        raise
    except Exception as e:
        logger.error(f"Coding pipeline crashed: {e}", exc_info=True)
        yield _sse_event("error", {"message": f"Coding pipeline failed: {str(e)[:300]}"})


# ── Utilities ─────────────────────────────────────────────────────────────

def _extract_test_failures(state: OrchestrationState) -> List[str]:
    """Look at test files for failure markers.

    This is heuristic: test files written by the tester LLM aren't executed
    (there's no sandbox). Instead the tester is prompted to produce assertions
    and note expected failures. We scan the test output for keywords the tester
    may have added.
    """
    failures: List[str] = []
    for f in state.output_files:
        if "test" not in f.path.lower():
            continue
        content = f.content.lower()
        for marker in ("fail", "error", "bug", "broken", "fixme", "issue"):
            if f"# {marker}" in content or f"# known {marker}" in content:
                failures.append(f"{f.path}: contains '{marker}' annotation")
                break
    return failures


def _build_report(state: OrchestrationState) -> str:
    """Build a human-readable report of the coding pipeline results."""
    lines = []
    lines.append("# Code Generation Report")
    lines.append("")
    lines.append("## Architecture Overview")
    lines.append(f"{state.architecture.overview if state.architecture else 'N/A'}")
    lines.append("")
    if state.architecture:
        lines.append("### Components")
        for c in state.architecture.components:
            lines.append(f"- **{c.get('name')}**: {c.get('responsibility')}")
    lines.append("")
    lines.append("## Generated Files")
    for f in state.output_files:
        lines.append(f"- `{f.path}` ({f.language})")
    lines.append("")
    lines.append("## Tasks Completed")
    for t in state.tasks:
        icon = "✅" if t.status == "completed" else "❌"
        lines.append(f"- {icon} {t.title} ({t.status})")
    lines.append("")
    lines.append(f"**Total files generated: {len(state.output_files)}**")
    return "\n".join(lines)
