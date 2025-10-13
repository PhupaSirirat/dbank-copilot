"""
Pydantic models for FastAPI RAG System
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime


# Request Models
class AskRequest(BaseModel):
    """Request model for /ask endpoint"""
    question: str = Field(..., min_length=1, max_length=2000, description="User's question")
    conversation_id: Optional[str] = Field(None, description="Conversation ID for context")
    user_id: Optional[str] = Field(None, description="User ID for audit")
    stream: bool = Field(True, description="Enable streaming responses")
    max_tokens: int = Field(2000, ge=100, le=4000, description="Max response tokens")
    
    class Config:
        json_schema_extra = {
            "example": {
                "question": "What were the top 3 products by revenue in Q4 2024?",
                "conversation_id": "conv_123",
                "user_id": "user_456",
                "stream": True
            }
        }


# Response Models
class Citation(BaseModel):
    """Citation from knowledge base or data source"""
    source: str = Field(..., description="Source name (file, table, etc)")
    content: str = Field(..., description="Relevant excerpt")
    score: Optional[float] = Field(None, description="Relevance score")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class ToolCall(BaseModel):
    """Tool execution record"""
    tool_name: str
    parameters: Dict[str, Any]
    result: Optional[Any] = None
    execution_time: Optional[float] = None
    error: Optional[str] = None


class AskResponse(BaseModel):
    """Response model for /ask endpoint"""
    answer: str = Field(..., description="AI-generated answer")
    conversation_id: str = Field(..., description="Conversation ID")
    citations: List[Citation] = Field(default_factory=list, description="Sources used")
    tool_calls: List[ToolCall] = Field(default_factory=list, description="Tools executed")
    tokens_used: Optional[int] = Field(None, description="Total tokens used")
    response_time: float = Field(..., description="Total response time in seconds")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class StreamChunk(BaseModel):
    """Streaming response chunk"""
    type: Literal["text", "citation", "tool_call", "done", "error"]
    content: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


# Conversation Models
class Message(BaseModel):
    """Single message in conversation"""
    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    tool_calls: Optional[List[ToolCall]] = None
    citations: Optional[List[Citation]] = None


class Conversation(BaseModel):
    """Conversation history"""
    conversation_id: str
    user_id: Optional[str] = None
    messages: List[Message] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


# Health Check Models
class HealthCheck(BaseModel):
    """Health check response"""
    status: Literal["healthy", "unhealthy"]
    mcp_server: bool
    llm_client: bool
    vector_store: bool
    timestamp: datetime = Field(default_factory=datetime.utcnow)