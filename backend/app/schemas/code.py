from pydantic import BaseModel
from typing import Optional

class CodeGenerateRequest(BaseModel):
    prompt: str
    use_agents: Optional[bool] = False

class CodeRefactorRequest(BaseModel):
    goal: str
    code: str

class CodeExplainRequest(BaseModel):
    code: str

class CodeTestRequest(BaseModel):
    code: str

class CodeResponse(BaseModel):
    result: str