from fastapi import APIRouter, Depends, HTTPException, Request
from app.core.deps import require_consent
from app.models.user import User
from app.schemas.code import (
    CodeGenerateRequest, CodeRefactorRequest, CodeExplainRequest,
    CodeTestRequest, CodeResponse
)
from app.services.code_agent import (
    generate_code, refactor_code, explain_code,
    generate_tests
)
from app.core.security import limiter
from app.core.concurrency import code_agent_limiter, limit_concurrency

router = APIRouter(prefix="/code", tags=["Code Agent"])

# The rate limit above bounds how many runs a user may *start* per minute; this
# bounds how many may be in flight at once. Both are needed: ten orchestrations
# launched inside one minute stay under 10/minute while holding every key-pool
# lease. Shared across all four routes so the cap is per user, not per route.
_concurrency_cap = Depends(limit_concurrency(code_agent_limiter))


@router.post("/generate", response_model=CodeResponse, dependencies=[_concurrency_cap])
@limiter.limit("10/minute")
async def code_generate(
    request: Request,
    payload: CodeGenerateRequest,
    user: User = Depends(require_consent)
):
    if payload.use_agents:
        from app.services.agent_service import run_orchestration
        # For simplicity, we return the result as a string in CodeResponse
        result = await run_orchestration(payload.prompt)
        return CodeResponse(result=result)
        
    return await generate_code(payload, user)

@router.post("/refactor", response_model=CodeResponse, dependencies=[_concurrency_cap])
@limiter.limit("10/minute")
async def code_refactor(
    request: Request,
    payload: CodeRefactorRequest,
    user: User = Depends(require_consent)
):
    return await refactor_code(payload, user)

@router.post("/explain", response_model=CodeResponse, dependencies=[_concurrency_cap])
@limiter.limit("10/minute")
async def code_explain(
    request: Request,
    payload: CodeExplainRequest,
    user: User = Depends(require_consent)
):
    return await explain_code(payload, user)

@router.post("/test", response_model=CodeResponse, dependencies=[_concurrency_cap])
@limiter.limit("10/minute")
async def code_test(
    request: Request,
    payload:  CodeTestRequest,
    user:  User = Depends(require_consent)
):
    return await generate_tests(payload, user)

