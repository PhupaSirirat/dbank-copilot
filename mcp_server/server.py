"""
MCP Server for dBank Deep Insights Copilot
Implements Model Context Protocol with 3 tools
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
import os
from dotenv import load_dotenv
from datetime import datetime

# Import tools
from tools.sql_query import execute_sql_query
from tools.kb_search import search_knowledge_base_tool
from tools.kpi_tools import get_top_root_causes
from utils.logger import log_tool_call, get_recent_logs

load_dotenv()

# Initialize FastAPI
app = FastAPI(
    title="dBank MCP Server",
    description="Model Context Protocol server for Deep Insights Copilot",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =====================================================
# MCP Protocol Models
# =====================================================

class ToolParameter(BaseModel):
    type: str
    description: str
    enum: Optional[List[str]] = None
    default: Optional[Any] = None

class Tool(BaseModel):
    name: str
    description: str
    parameters: Dict[str, ToolParameter]
    required: List[str] = []

class ToolCallRequest(BaseModel):
    tool: str
    parameters: Dict[str, Any]
    user_id: Optional[str] = "anonymous"
    session_id: Optional[str] = None

class ToolCallResponse(BaseModel):
    success: bool
    result: Any
    execution_time_ms: int
    tool_call_id: str
    metadata: Dict[str, Any] = {}

# =====================================================
# Tool Registry
# =====================================================

TOOLS_REGISTRY = {
    "sql.query": {
        "name": "sql.query",
        "description": "Execute read-only SQL queries against the dBank database. Automatically masks PII. Only SELECT queries allowed.",
        "parameters": {
            "query": {
                "type": "string",
                "description": "SQL SELECT query to execute. Must be read-only. Parameters should use {{param_name}} syntax."
            },
            "parameters": {
                "type": "object",
                "description": "Parameters to substitute in the query (for SQL injection protection)",
                "default": {}
            },
            "mask_pii": {
                "type": "boolean",
                "description": "Whether to mask PII fields (email, phone, IDs). Default: true",
                "default": True
            }
        },
        "required": ["query"]
    },
    
    "kb.search": {
        "name": "kb.search",
        "description": "Semantic search over the knowledge base (products, policies, troubleshooting, FAQs). Returns relevant document chunks.",
        "parameters": {
            "query": {
                "type": "string",
                "description": "Search query in natural language"
            },
            "top_k": {
                "type": "integer",
                "description": "Number of results to return (1-20)",
                "default": 5
            },
            "category": {
                "type": "string",
                "description": "Optional category filter",
                "enum": ["product_guide", "support_doc", "reference_doc"],
                "default": None
            },
            "min_similarity": {
                "type": "number",
                "description": "Minimum similarity score (0.0-1.0)",
                "default": 0.7
            }
        },
        "required": ["query"]
    },
    
    "kpi.top_root_causes": {
        "name": "kpi.top_root_causes",
        "description": "Get top root causes of tickets by time period. Pre-aggregated KPI data with percentages and metrics.",
        "parameters": {
            "year": {
                "type": "integer",
                "description": "Year (e.g., 2025)"
            },
            "month": {
                "type": "integer",
                "description": "Month (1-12). Optional - if not provided, returns all months.",
                "default": None
            },
            "top_n": {
                "type": "integer",
                "description": "Number of top root causes to return (1-50)",
                "default": 10
            },
            "category_filter": {
                "type": "string",
                "description": "Optional ticket category filter",
                "default": None
            }
        },
        "required": ["year"]
    }
}

# =====================================================
# MCP Endpoints
# =====================================================

@app.get("/")
async def root():
    """Health check"""
    return {
        "service": "dBank MCP Server",
        "status": "operational",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/tools/list")
async def list_tools():
    """MCP: List available tools"""
    return {
        "tools": [
            {
                "name": tool_id,
                **tool_def
            }
            for tool_id, tool_def in TOOLS_REGISTRY.items()
        ]
    }

@app.post("/tools/call")
async def call_tool(request: ToolCallRequest) -> ToolCallResponse:
    """MCP: Call a tool"""
    start_time = datetime.now()
    tool_call_id = f"{request.tool}_{start_time.strftime('%Y%m%d_%H%M%S_%f')}"
    
    try:
        # Validate tool exists
        if request.tool not in TOOLS_REGISTRY:
            raise HTTPException(
                status_code=400,
                detail=f"Tool '{request.tool}' not found. Available tools: {list(TOOLS_REGISTRY.keys())}"
            )
        
        # Route to appropriate tool
        if request.tool == "sql.query":
            result = execute_sql_query(
                query=request.parameters.get("query"),
                parameters=request.parameters.get("parameters", {}),
                mask_pii=request.parameters.get("mask_pii", True)
            )
        
        elif request.tool == "kb.search":
            result = search_knowledge_base_tool(
                query=request.parameters.get("query"),
                top_k=request.parameters.get("top_k", 5),
                category=request.parameters.get("category"),
                min_similarity=request.parameters.get("min_similarity", 0.7)
            )
        
        elif request.tool == "kpi.top_root_causes":
            result = get_top_root_causes(
                year=request.parameters.get("year"),
                month=request.parameters.get("month"),
                top_n=request.parameters.get("top_n", 10),
                category_filter=request.parameters.get("category_filter")
            )
        
        else:
            raise HTTPException(status_code=501, detail="Tool not implemented")
        
        # Calculate execution time
        execution_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
        
        # Log the tool call
        log_tool_call(
            tool_name=request.tool,
            parameters=request.parameters,
            user_id=request.user_id,
            session_id=request.session_id,
            execution_time_ms=execution_time_ms,
            status="success",
            result_summary=f"Returned {len(result) if isinstance(result, list) else 1} results"
        )
        
        return ToolCallResponse(
            success=True,
            result=result,
            execution_time_ms=execution_time_ms,
            tool_call_id=tool_call_id,
            metadata={
                "tool": request.tool,
                "timestamp": datetime.now().isoformat()
            }
        )
    
    except Exception as e:
        execution_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
        
        # Log the error
        log_tool_call(
            tool_name=request.tool,
            parameters=request.parameters,
            user_id=request.user_id,
            session_id=request.session_id,
            execution_time_ms=execution_time_ms,
            status="error",
            error_message=str(e)
        )
        
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/logs/recent")
async def recent_logs(limit: int = 50):
    """Get recent tool call logs"""
    try:
        logs = get_recent_logs(limit=limit)
        return {"logs": logs, "count": len(logs)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "tools_count": len(TOOLS_REGISTRY),
        "database": "connected"
    }

# =====================================================
# Run Server
# =====================================================

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("MCP_SERVER_PORT", 8000))
    
    print("=" * 60)
    print("🚀 Starting dBank MCP Server")
    print("=" * 60)
    print(f"\n📍 Server: http://localhost:{port}")
    print(f"📚 Docs: http://localhost:{port}/docs")
    print(f"🔧 Tools: {len(TOOLS_REGISTRY)}")
    print("\nAvailable Tools:")
    for tool_name in TOOLS_REGISTRY.keys():
        print(f"  - {tool_name}")
    print("\n" + "=" * 60)
    
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )