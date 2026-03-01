from fastapi import APIRouter, Depends, HTTPException
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.code import (
    CodeGenerateRequest, CodeRefactorRequest, CodeExplainRequest,
    CodeTestRequest, CodeResponse
)
from app.services.code_agent import (
    generate_code, refactor_code, explain_code,
    generate_tests
)

router = APIRouter(prefix="/code", tags=["Code Agent"])

@router.post("/generate", response_model=CodeResponse)
async def code_generate(
    payload: CodeGenerateRequest,
    user: User = Depends(get_current_user)
):
    if payload.use_agents:
        from app.services.agent_service import run_orchestration
        # For simplicity, we return the result as a string in CodeResponse
        result = await run_orchestration(payload.prompt)
        return CodeResponse(result=result)
        
    return await generate_code(payload, user)

@router.post("/refactor", response_model=CodeResponse)
async def code_refactor(
    payload: CodeRefactorRequest,
    user: User = Depends(get_current_user)
):
    return await refactor_code(payload, user)

@router.post("/explain", response_model=CodeResponse)
async def code_explain(
    payload: CodeExplainRequest,
    user: User = Depends(get_current_user)
):
    return await explain_code(payload, user)

@router.post("/test", response_model=CodeResponse)
async def code_test(
    payload:  CodeTestRequest,
    user:  User = Depends(get_current_user)
):
    return await generate_tests(payload, user)

