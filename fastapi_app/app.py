"""
dBank Support Copilot - FastAPI RAG System
Always streams responses using OpenAI GPT-4o-mini
"""
import os
import json
import time
from typing import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from models.schemas import AskRequest, HealthCheck
from core.llm_client import get_llm_client
from core.tool_orchestrator import ToolOrchestrator
from core.conversation import get_conversation_manager

load_dotenv()


# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan"""
    print("=" * 60)
    print("🏦 dBank Support Copilot - Starting...")
    print("=" * 60)
    print(f"   Model: OpenAI GPT-4o-mini")
    print(f"   Streaming: Always Enabled")
    print(f"   MCP Server: {os.getenv('MCP_SERVER_URL', 'http://localhost:8000')}")
    
    # Initialize components
    app.state.llm_client = get_llm_client()
    app.state.tool_orchestrator = ToolOrchestrator(
        mcp_server_url=os.getenv("MCP_SERVER_URL", "http://localhost:8000")
    )
    app.state.conversation_manager = get_conversation_manager()
    
    # Health check
    mcp_healthy = await app.state.tool_orchestrator.health_check()
    if not mcp_healthy:
        print("⚠️  Warning: MCP Server not responding")
    else:
        print("✅ MCP Server connected")
    
    print("=" * 60)
    print("✅ dBank Support Copilot Ready!")
    print(f"   API Docs: http://localhost:8001/docs")
    print("=" * 60)
    
    yield
    
    # Shutdown
    print("\n🛑 Shutting down...")
    await app.state.tool_orchestrator.close()
    print("✅ Cleanup complete")


# Create FastAPI app
app = FastAPI(
    title="dBank Support Copilot",
    description="AI-powered support ticket analysis for dBank operations team. Reduces resolution time by 80%.",
    version="1.0.0",
    lifespan=lifespan
)


# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "dBank Support Copilot",
        "version": "1.0.0",
        "model": "OpenAI GPT-4o-mini",
        "streaming": "Always Enabled",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", response_model=HealthCheck)
async def health_check(request: Request):
    """Health check endpoint"""
    
    # Check MCP server
    mcp_healthy = await request.app.state.tool_orchestrator.health_check()
    
    # Check LLM client
    llm_healthy = request.app.state.llm_client is not None
    
    # Check vector store (via MCP)
    vector_healthy = mcp_healthy
    
    status = "healthy" if (mcp_healthy and llm_healthy) else "unhealthy"
    
    return HealthCheck(
        status=status,
        mcp_server=mcp_healthy,
        llm_client=llm_healthy,
        vector_store=vector_healthy
    )


async def process_question_stream(
    request: Request,
    question: str,
    conversation_id: str,
    user_id: str,
    max_tokens: int
) -> AsyncGenerator[str, None]:
    """
    Process support question with streaming response
    
    Yields JSON chunks in Server-Sent Events format
    """
    start_time = time.time()
    
    try:
        # Get components
        llm_client = request.app.state.llm_client
        tool_orchestrator = request.app.state.tool_orchestrator
        conversation_manager = request.app.state.conversation_manager
        
        # Get or create conversation
        conversation = conversation_manager.get_conversation(conversation_id)
        if not conversation:
            conversation_id = conversation_manager.create_conversation(
                user_id=user_id,
                metadata={"source": "dbank_support"}
            )
        
        # Add user message
        conversation_manager.add_message(
            conversation_id=conversation_id,
            role="user",
            content=question
        )
        
        # Get conversation context
        context = conversation_manager.get_context(conversation_id)
        
        # Add current question to context
        messages = context + [{"role": "user", "content": question}]
        
        # Get tool definitions
        tools = tool_orchestrator.get_tool_definitions()
        
        # Initial status
        yield f"data: {json.dumps({'type': 'status', 'content': 'Analyzing your question...'})}\n\n"
        
        # First pass: Get LLM response with potential tool calls
        response = await llm_client.generate(
            messages=messages,
            tools=tools,
            max_tokens=max_tokens,
            temperature=0.3  # Lower temperature for consistent support answers
        )
        
        accumulated_text = ""
        executed_tools = []
        
        # If tool calls requested, execute them
        if response["tool_calls"]:
            tool_count = len(response["tool_calls"])
            yield f"data: {json.dumps({'type': 'status', 'content': f'Executing {tool_count} tool(s)...'})}\n\n"
            
            # Execute tools
            executed_tools = await tool_orchestrator.execute_tools(
                response["tool_calls"]
            )
            
            # Emit tool call events
            for tool_call in executed_tools:
                yield f"data: {json.dumps({'type': 'tool_call', 'data': tool_call.model_dump()})}\n\n"
            
            # Add tool results to context
            for tool_call in executed_tools:
                if not tool_call.error:
                    # Format tool result for context
                    result_summary = json.dumps(tool_call.result, indent=2)[:500]  # Truncate if too long
                    messages.append({
                        "role": "function",
                        "name": tool_call.tool_name,
                        "content": f"Tool '{tool_call.tool_name}' returned:\n{result_summary}"
                    })
            
            # Get final response with tool results
            yield f"data: {json.dumps({'type': 'status', 'content': 'Generating insights...'})}\n\n"
            
            # Stream final response
            async for chunk in llm_client.stream(
                messages=messages,
                tools=None,  # No more tool calls
                max_tokens=max_tokens,
                temperature=0.3
            ):
                if chunk["type"] == "text":
                    accumulated_text += chunk["content"]
                    yield f"data: {json.dumps({'type': 'text', 'content': chunk['content']})}\n\n"
                elif chunk["type"] == "done":
                    break
            
            # Extract citations
            citations = tool_orchestrator.extract_citations(executed_tools)
            
            # Emit citations
            for citation in citations:
                yield f"data: {json.dumps({'type': 'citation', 'data': citation.model_dump()})}\n\n"
            
            # Save assistant message with citations
            conversation_manager.add_message(
                conversation_id=conversation_id,
                role="assistant",
                content=accumulated_text,
                tool_calls=executed_tools,
                citations=citations
            )
            
        else:
            # No tool calls - stream direct response
            async for chunk in llm_client.stream(
                messages=messages,
                tools=None,
                max_tokens=max_tokens,
                temperature=0.3
            ):
                if chunk["type"] == "text":
                    accumulated_text += chunk["content"]
                    yield f"data: {json.dumps({'type': 'text', 'content': chunk['content']})}\n\n"
                elif chunk["type"] == "done":
                    break
            
            # Save assistant message
            conversation_manager.add_message(
                conversation_id=conversation_id,
                role="assistant",
                content=accumulated_text
            )
        
        # Send completion event
        response_time = time.time() - start_time
        yield f"data: {json.dumps({'type': 'done', 'data': {'response_time': response_time, 'conversation_id': conversation_id, 'tool_calls_count': len(executed_tools)}})}\n\n"
        
    except Exception as e:
        error_msg = str(e)
        yield f"data: {json.dumps({'type': 'error', 'content': error_msg})}\n\n"


@app.post("/ask")
async def ask_question(request: Request, ask_request: AskRequest):
    """
    Ask a support question - Main endpoint
    
    Always streams responses for better UX
    """
    
    # Generate conversation ID if not provided
    conversation_id = ask_request.conversation_id
    if not conversation_id:
        conversation_id = request.app.state.conversation_manager.create_conversation(
            user_id=ask_request.user_id,
            metadata={"source": "dbank_support_api"}
        )
    
    # Always stream (ignoring stream parameter)
    return StreamingResponse(
        process_question_stream(
            request=request,
            question=ask_request.question,
            conversation_id=conversation_id,
            user_id=ask_request.user_id or "anonymous",
            max_tokens=ask_request.max_tokens
        ),
        media_type="text/event-stream"
    )


@app.get("/conversations/{conversation_id}")
async def get_conversation(request: Request, conversation_id: str):
    """Get conversation details"""
    
    conversation_manager = request.app.state.conversation_manager
    summary = conversation_manager.get_summary(conversation_id)
    
    if "error" in summary:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return summary


@app.get("/conversations")
async def list_conversations(
    request: Request,
    user_id: str = None,
    limit: int = 50
):
    """List conversations"""
    
    conversation_manager = request.app.state.conversation_manager
    conversations = conversation_manager.list_conversations(
        user_id=user_id,
        limit=limit
    )
    
    return {"conversations": conversations}


@app.delete("/conversations/{conversation_id}")
async def delete_conversation(request: Request, conversation_id: str):
    """Delete a conversation"""
    
    conversation_manager = request.app.state.conversation_manager
    deleted = conversation_manager.delete_conversation(conversation_id)
    
    if not deleted:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return {"message": "Conversation deleted", "conversation_id": conversation_id}


@app.post("/conversations/cleanup")
async def cleanup_conversations(request: Request):
    """Cleanup expired conversations"""
    
    conversation_manager = request.app.state.conversation_manager
    count = conversation_manager.cleanup_expired()
    
    return {"message": f"Cleaned up {count} expired conversations"}


@app.get("/tools")
async def list_tools(request: Request):
    """List available MCP tools"""
    
    tool_orchestrator = request.app.state.tool_orchestrator
    tools = tool_orchestrator.get_tool_definitions()
    
    return {
        "tools": tools,
        "count": len(tools)
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )