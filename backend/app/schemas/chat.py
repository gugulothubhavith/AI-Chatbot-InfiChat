from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime
from uuid import UUID

class Message(BaseModel):
    role: str
    content: str
    image: Optional[str] = None
    file_name: Optional[str] = None
    file_type: Optional[str] = None

class ChatRequest(BaseModel):
    messages: List[Message]
    conversation_id: Optional[UUID] = None
    web_search: bool = False
    # When True (default), a plain chat turn may transparently escalate to a
    # grounded web search based on the prompt's intent. This is unmetered and
    # abuse-capped server-side. Users can turn it off in settings, which sends
    # False here. The manual `web_search` toggle above is a separate, metered path.
    auto_web_search: bool = True
    use_rag: bool = False
    system_prompt: Optional[str] = None
    model: Optional[str] = None
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 2048
    top_p: Optional[float] = 1.0
    frequency_penalty: Optional[float] = 0.0
    presence_penalty: Optional[float] = 0.0
    history_limit: Optional[int] = None
    workspace: Optional[str] = "personal"

class ChatResponse(BaseModel):
    role: str
    content: str

class ChatSessionSchema(BaseModel):
    id: UUID
    title: str
    is_pinned: bool
    is_archived: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ChatSessionCreate(BaseModel):
    title: Optional[str] = None
    workspace: Optional[str] = "personal"

class ChatSessionUpdate(BaseModel):
    title: Optional[str] = None
    is_pinned: Optional[bool] = None
    is_archived: Optional[bool] = None

class SharedChatSnapshot(BaseModel):
    id: UUID
    session_id: UUID
    share_token: str
    snapshot_json: dict
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ChatExport(BaseModel):
    sessions: List[dict]
    generated_at: datetime
