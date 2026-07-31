"""Multi-agent coding agents — each handles one phase of the coding pipeline.

All agent functions accept ``(state, llm_call)`` where ``llm_call`` is an
``async (messages, stream=False)`` closure already bound to a pooled API key.
"""

import json
import logging
import re
from typing import Callable, Dict, List

from app.services.code_orchestrator.models import (
    OrchestrationState, ArchitecturePlan, Specification,
    CodingTask, CodeFile, AgentMessage, AgentType,
)

logger = logging.getLogger(__name__)

# ── System Prompts ────────────────────────────────────────────

ARCHITECT_PROMPT = """You are a senior software architect. Design a complete system architecture for the following request.

Request: "{prompt}"

Provide your architecture plan in this JSON format:
{{
  "overview": "High-level architecture description",
  "components": [
    {{"name": "ComponentName", "responsibility": "What this component does", "technologies": ["tech1", "tech2"]}}
  ],
  "data_flow": [
    {{"from": "ComponentA", "to": "ComponentB", "description": "What flows between them"}}
  ],
  "tech_stack": ["technology1", "technology2"],
  "directory_structure": ["src/component1/", "src/component2/"]
}}

Be specific, thorough, and production-oriented. Consider error handling, scalability, and security.
Return ONLY valid JSON, no markdown."""

SPEC_WRITER_PROMPT = """You are a technical specification writer. Based on the architecture plan, create a detailed specification.

Architecture Overview: {overview}
Components: {components}
Tech Stack: {tech_stack}

Provide a specification in this JSON format:
{{
  "functional_requirements": ["req1", "req2"],
  "api_endpoints": [
    {{"method": "GET/POST/PUT/DELETE", "path": "/api/endpoint", "description": "What it does", "request_body": "schema", "response": "schema"}}
  ],
  "data_models": [
    {{"name": "ModelName", "fields": [{{"name": "field1", "type": "string", "description": "description"}}]}}
  ],
  "error_handling": ["strategy1", "strategy2"]
}}

Be specific and production-ready. Return ONLY valid JSON, no markdown."""

TASK_DECOMPOSER_PROMPT = """You are a task decomposition expert. Break the specification into independent coding tasks that can be worked on in parallel.

Requirements: {requirements}
API Endpoints: {endpoints}
Data Models: {models}

Return a JSON object:
{{
  "tasks": [
    {{
      "id": "task-1", "title": "Implement X", "description": "Detailed implementation instructions including file paths and key logic",
      "dependencies": [], "output_files": ["path/to/file.py", "path/to/file.ts"]
    }},
    {{
      "id": "task-2", "title": "Implement Y", "description": "Detailed implementation instructions",
      "dependencies": ["task-1"], "output_files": ["path/to/other.py"]
    }}
  ]
}}

Tasks without dependencies can run in parallel. Tasks with dependencies must wait.
Return ONLY valid JSON, no markdown."""

CODER_SYSTEM_PROMPT = """You are CODE_AGENT — an elite production-grade programmer.

Rules:
- Output ONLY complete, executable code.
- NO placeholders, NO pseudocode.
- Use best practices: error handling, input validation, logging, type hints.
- Every function must have a docstring.
- Handle edge cases explicitly.
- Output full file contents including imports.
- Format: each file in a code block with the filename as the language tag.

Example output format:

```python:src/main.py
import os
import logging

logger = logging.getLogger(__name__)

def main():
    \"\"\"Application entry point.\"\"\"
    logger.info("Starting application")
    return 0

if __name__ == "__main__":
    main()
```

```javascript:src/app.js
const express = require('express');
const app = express();

function start(port) {
    app.listen(port, () => {
        console.log(`Server running on port ${port}`);
    });
}

module.exports = { start };
```
"""

TESTER_PROMPT = """You are a test generation expert. Create comprehensive unit tests for the following code.

Code files:
{files}

Generate test files that:
1. Test all major functions and edge cases
2. Use the appropriate testing framework (pytest for Python, jest for JS/TS, etc.)
3. Include setup/teardown where needed
4. Cover error cases and edge cases
5. Mock external dependencies
6. Mark any test you are unsure will pass with a comment "# may-fail: <reason>"

Output format: each test file in a code block with the filename as the language tag.
Example: ```python:test_main.py```"""

DEBUGGER_PROMPT = """You are a code debugger. The following code has issues that need fixing.

Code:
{code}

Test Output / Error:
{error}

Fix ALL bugs and issues. Output the COMPLETE corrected file content.
Maintain the same code style and conventions.
Output each file in a code block with the filename as the language tag, e.g. ```python:src/main.py```"""

OPTIMIZER_PROMPT = """You are a code optimization and security expert. Review the following code and suggest improvements.

Files:
{files}

Review for:
1. Performance improvements
2. Security vulnerabilities
3. Code quality and best practices
4. Error handling completeness
5. Memory/CPU efficiency

CRITICAL RULE: You MUST output the COMPLETE file content for each file you improve.
Do NOT truncate or abbreviate any file. If a file is already good, output it unchanged.

Output each file in a code block with the filename as the language tag."""


# ── Agent Functions ───────────────────────────────────────────

async def run_architect(state: OrchestrationState, llm_call: Callable) -> OrchestrationState:
    """Design system architecture from prompt."""
    prompt = ARCHITECT_PROMPT.format(prompt=state.prompt)
    try:
        response = await llm_call([
            {"role": "system", "content": "You are a senior software architect."},
            {"role": "user", "content": prompt},
        ])
        text = _strip_fences(response)
        data = json.loads(text)
        state.architecture = ArchitecturePlan(
            overview=data.get("overview", ""),
            components=data.get("components", []),
            data_flow=data.get("data_flow", []),
            tech_stack=data.get("tech_stack", []),
            directory_structure=data.get("directory_structure", []),
        )
        logger.info(f"Architect: designed {len(state.architecture.components)} components")
    except Exception as e:
        logger.warning(f"Architect LLM failed: {e}. Using fallback architecture.")
        state.architecture = ArchitecturePlan(
            overview=f"Architecture for: {state.prompt[:100]}",
            components=[{"name": "MainApp", "responsibility": state.prompt[:200], "technologies": ["python"]}],
            tech_stack=["python"],
            directory_structure=["src/"],
        )
    return state


async def run_spec_writer(state: OrchestrationState, llm_call: Callable) -> OrchestrationState:
    """Create detailed specifications from architecture."""
    if not state.architecture:
        logger.warning("No architecture found, skipping spec writer")
        state.specification = Specification(
            functional_requirements=[state.prompt[:200]],
        )
        return state

    prompt = SPEC_WRITER_PROMPT.format(
        overview=state.architecture.overview,
        components=json.dumps(state.architecture.components, indent=2),
        tech_stack=", ".join(state.architecture.tech_stack),
    )
    try:
        response = await llm_call([
            {"role": "system", "content": "You are a technical specification writer."},
            {"role": "user", "content": prompt},
        ])
        text = _strip_fences(response)
        data = json.loads(text)
        state.specification = Specification(
            functional_requirements=data.get("functional_requirements", []),
            api_endpoints=data.get("api_endpoints", []),
            data_models=data.get("data_models", []),
            error_handling=data.get("error_handling", []),
        )
        logger.info(f"SpecWriter: created {len(state.specification.functional_requirements)} requirements")
    except Exception as e:
        logger.warning(f"SpecWriter LLM failed: {e}. Using fallback spec.")
        state.specification = Specification(
            functional_requirements=[f"Implement: {state.prompt[:200]}"],
        )
    return state


async def run_task_decomposer(state: OrchestrationState, llm_call: Callable) -> OrchestrationState:
    """Break specification into independent coding tasks."""
    spec = state.specification
    if not spec:
        state.tasks = [CodingTask(
            id="task-1", title="Implement main code",
            description=state.prompt[:500],
            dependencies=[],
        )]
        return state

    prompt = TASK_DECOMPOSER_PROMPT.format(
        requirements="\n".join(spec.functional_requirements),
        endpoints=json.dumps(spec.api_endpoints, indent=2),
        models=json.dumps(spec.data_models, indent=2),
    )
    try:
        response = await llm_call([
            {"role": "system", "content": "You are a task decomposition expert."},
            {"role": "user", "content": prompt},
        ])
        text = _strip_fences(response)
        data = json.loads(text)
        tasks_data = data.get("tasks", [])
        state.tasks = [
            CodingTask(
                id=t.get("id", f"task-{i+1}"),
                title=t.get("title", f"Task {i+1}"),
                description=t.get("description", ""),
                dependencies=t.get("dependencies", []),
                output_files=[CodeFile(path=p, content="") for p in t.get("output_files", [])],
            )
            for i, t in enumerate(tasks_data)
        ]
        logger.info(f"TaskDecomposer: created {len(state.tasks)} tasks")
    except Exception as e:
        logger.warning(f"TaskDecomposer LLM failed: {e}. Creating single task.")
        state.tasks = [CodingTask(
            id="task-1", title=f"Implement {state.prompt[:60]}",
            description=state.prompt[:500],
            dependencies=[],
        )]
    return state


async def run_coder(state: OrchestrationState, task: CodingTask,
                    llm_call: Callable, chunk_callback: Callable = None) -> CodingTask:
    """Generate code for a single task."""
    prompt = f"""Task: {task.title}

Description: {task.description}

Expected output files: {[f.path for f in task.output_files]}

Architecture context: {state.architecture.overview[:500] if state.architecture else ""}

Generate COMPLETE, production-ready code for each file. Include imports, error handling, logging, and type hints.
Output each file in a code block with the filename as a markdown language tag."""
    try:
        if chunk_callback:
            response_gen = await llm_call([
                {"role": "system", "content": CODER_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ], stream=True)
            text = ""
            async for chunk in response_gen:
                text += chunk
                await chunk_callback(chunk)
        else:
            response = await llm_call([
                {"role": "system", "content": CODER_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ])
            text = response.strip()

        files = _parse_code_blocks(text)
        if files:
            task.output_files = [
                CodeFile(path=p, content=c, language=_detect_language(p))
                for p, c in files.items()
            ]
            task.status = "completed"
            logger.info(f"Coder: generated {len(files)} files for '{task.title[:50]}'")
        else:
            # Fallback: use entire response as a single file
            fallback_path = task.output_files[0].path if task.output_files else "src/main.py"
            task.output_files = [CodeFile(
                path=fallback_path,
                content=text,
                language=_detect_language(fallback_path),
            )]
            task.status = "completed"
    except Exception as e:
        logger.error(f"Coder failed for '{task.title[:50]}': {e}")
        task.status = "failed"
        task.error = str(e)
    return task


async def run_tester(state: OrchestrationState, llm_call: Callable) -> OrchestrationState:
    """Generate tests for all output files."""
    if not state.output_files:
        logger.warning("No output files to test")
        return state

    # Send full file contents — the tester needs to see the complete code
    files_text = "\n\n".join([
        f"--- {f.path} ---\n{f.content}"
        for f in state.output_files
        if "test" not in f.path.lower()  # don't test the tests
    ])

    prompt = TESTER_PROMPT.format(files=files_text)
    try:
        response = await llm_call([
            {"role": "system", "content": CODER_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ])
        text = response.strip()
        test_files = _parse_code_blocks(text)
        for path, content in test_files.items():
            # Don't duplicate if the test file already exists from a prior pass
            existing = [f for f in state.output_files if f.path == path]
            if existing:
                existing[0].content = content
            else:
                state.output_files.append(CodeFile(
                    path=path,
                    content=content,
                    language=_detect_language(path),
                    description="Test file",
                ))
        logger.info(f"Tester: generated {len(test_files)} test files")
    except Exception as e:
        logger.warning(f"Tester LLM failed: {e}")
    return state


async def run_debugger(state: OrchestrationState, error_info: str, llm_call: Callable) -> OrchestrationState:
    """Fix bugs in generated code based on error feedback."""
    if not state.output_files:
        return state

    # Collect non-test files to fix
    code_files = [f for f in state.output_files if "test" not in f.path.lower()]
    if not code_files:
        return state

    # Send all code files in one prompt for context-aware fixing
    code_text = "\n\n".join([
        f"--- {f.path} ---\n{f.content}" for f in code_files
    ])

    prompt = DEBUGGER_PROMPT.format(code=code_text, error=error_info[:2000])
    try:
        response = await llm_call([
            {"role": "system", "content": CODER_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ])
        text = response.strip()
        fixed_files = _parse_code_blocks(text)
        fixed_count = 0
        for path, content in fixed_files.items():
            for f in state.output_files:
                if f.path == path:
                    f.content = content
                    fixed_count += 1
                    break
        logger.info(f"Debugger: fixed {fixed_count} file(s)")
    except Exception as e:
        logger.warning(f"Debugger failed: {e}")

    return state


async def run_optimizer(state: OrchestrationState, llm_call: Callable) -> OrchestrationState:
    """Review and optimize all output files.

    IMPORTANT: Unlike the old version, we send complete file contents and only
    replace a file if the LLM returns a version that is at least 80% the
    length of the original. This prevents the optimizer from accidentally
    truncating files it could only partially see.
    """
    if not state.output_files:
        return state

    # Send full file contents (not truncated)
    files_text = "\n\n".join([
        f"--- {f.path} ---\n{f.content}"
        for f in state.output_files
    ])

    prompt = OPTIMIZER_PROMPT.format(files=files_text)
    try:
        response = await llm_call([
            {"role": "system", "content": CODER_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ])
        text = response.strip()
        optimized_files = _parse_code_blocks(text)
        replaced = 0
        for path, content in optimized_files.items():
            for f in state.output_files:
                if f.path == path:
                    original_len = len(f.content)
                    new_len = len(content)
                    # Safety check: don't replace if the optimized version is
                    # suspiciously shorter (the LLM may have truncated it).
                    if original_len > 0 and new_len < original_len * 0.8:
                        logger.warning(
                            f"Optimizer returned truncated content for {path} "
                            f"({new_len} vs {original_len} chars); keeping original"
                        )
                        continue
                    f.content = content
                    replaced += 1
                    break
        logger.info(f"Optimizer: reviewed {len(optimized_files)} files, replaced {replaced}")
    except Exception as e:
        logger.warning(f"Optimizer LLM failed: {e}")
    return state


# ── Utility Functions ─────────────────────────────────────────

def _strip_fences(text: str) -> str:
    """Strip markdown code fences from a JSON response."""
    text = (text or "").strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
    return text


def _parse_code_blocks(text: str) -> Dict[str, str]:
    """Parse code blocks from LLM response into {filename: content} dict."""
    files: Dict[str, str] = {}
    # Match ```[language][separator][filename]\n[content]```
    pattern = re.compile(r"```[ \t]*([a-zA-Z0-9_+\-]+)?[ \t]*:?[ \t]*([^\n]+)?\n(.*?)\n```", re.DOTALL)
    for match in pattern.finditer(text):
        lang = (match.group(1) or "").strip()
        filename = (match.group(2) or "").strip()
        content = match.group(3).strip()

        # Sometimes LLMs put the filename on the first line as a comment
        if not filename and content:
            first_line = content.split('\n')[0].strip()
            if first_line.startswith('// filepath:') or first_line.startswith('# filepath:'):
                filename = first_line.split(':', 1)[1].strip()

        if filename:
            files[filename] = content
        elif lang:
            files[f"main.{lang}"] = content

    # If no code blocks found, try fallback regex
    if not files:
        pattern_fallback = re.compile(r"```[^\n]*\n(.*?)```", re.DOTALL)
        match = pattern_fallback.search(text)
        if match:
            files["main.txt"] = match.group(1).strip()

    return files


def _detect_language(filename: str) -> str:
    """Detect programming language from filename."""
    ext = filename.split(".")[-1].lower() if "." in filename else ""
    lang_map = {
        "py": "python", "js": "javascript", "ts": "typescript",
        "tsx": "typescriptreact", "jsx": "javascriptreact",
        "html": "html", "css": "css", "json": "json",
        "yaml": "yaml", "yml": "yaml", "md": "markdown",
        "sql": "sql", "sh": "bash", "bat": "batch",
        "go": "go", "rs": "rust", "java": "java",
        "cpp": "cpp", "c": "c", "h": "c",
        "rb": "ruby", "php": "php", "swift": "swift",
        "kt": "kotlin", "scala": "scala", "r": "r",
    }
    return lang_map.get(ext, ext)
