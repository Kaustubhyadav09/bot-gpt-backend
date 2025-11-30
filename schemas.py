# schemas.py
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid


# ============ Conversation Schemas ============

class ConversationCreate(BaseModel):
    user_id: uuid.UUID
    first_message: str = Field(..., min_length=1, max_length=5000)
    mode: str = Field(default="open_chat", pattern="^(open_chat|grounded_rag)$")
    document_ids: Optional[List[uuid.UUID]] = Field(default=[])
    
    @validator('document_ids')
    def validate_document_ids(cls, v, values):
        if values.get('mode') == 'grounded_rag' and not v:
            raise ValueError('document_ids required for grounded_rag mode')
        return v


class MessageDetail(BaseModel):
    id: uuid.UUID
    role: str
    content: str
    tokens: Optional[int]
    created_at: datetime
    metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True


class ConversationResponse(BaseModel):
    conversation_id: uuid.UUID
    message: MessageDetail
    assistant_response: MessageDetail


class ConversationListItem(BaseModel):
    id: uuid.UUID
    title: str
    mode: str
    message_count: int
    created_at: datetime
    updated_at: datetime
    last_message: str


class ConversationListResponse(BaseModel):
    conversations: List[ConversationListItem]
    total: int
    page: int
    limit: int


class DocumentInfo(BaseModel):
    id: uuid.UUID
    filename: str
    created_at: datetime


class ConversationDetailResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    title: str
    mode: str
    created_at: datetime
    updated_at: datetime
    token_count: int
    messages: List[MessageDetail]
    documents: List[DocumentInfo]


# ============ Message Schemas ============

class MessageCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=5000)


class MessageResponse(BaseModel):
    user_message: MessageDetail
    assistant_response: MessageDetail
    conversation_token_count: int


# ============ Document Schemas ============

class DocumentUpload(BaseModel):
    user_id: uuid.UUID


class DocumentResponse(BaseModel):
    document_id: uuid.UUID
    filename: str
    chunks_created: int
    created_at: datetime


class DocumentListItem(BaseModel):
    id: uuid.UUID
    filename: str
    chunk_count: int
    created_at: datetime


# ============ Health Check Schema ============

class HealthResponse(BaseModel):
    status: str
    database: str
    llm_api: str
    timestamp: datetime