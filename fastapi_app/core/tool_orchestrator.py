"""
Tool Orchestrator - Manages MCP tool calls for dBank Support Copilot
"""
import httpx
import time
from typing import Dict, Any, List, Optional
from datetime import datetime

from ..models.schemas import ToolCall, Citation

class ToolOrchestrator:
    """Orchestrates calls to MCP server tools for dBank"""
    
    def __init__(self, mcp_server_url: str = "http://localhost:8000"):
        self.mcp_server_url = mcp_server_url.rstrip("/")
        self.client = httpx.AsyncClient(timeout=60.0)  # Longer timeout for complex queries
    
    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """
        Get tool definitions for dBank Support Copilot
        
        Returns tool schemas for OpenAI function calling
        """
        return [
            {
                "name": "sql_query",
                "description": """Execute read-only SQL queries on the dBank analytics warehouse. 
                Use for analyzing tickets, customers, login patterns, and product data. 
                Available tables: dim_customers, dim_products, dim_ticket_categories, dim_root_causes, dim_time, 
                fact_tickets, fact_customer_products, fact_logins.
                All queries are logged and PII is automatically masked.""",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": """SQL query to execute. Must be SELECT only (read-only).
                            Tables available:
                            - dim_customers: customer_id, name, email, segment, region, signup_date
                            - dim_products: product_id, name, category, version
                            - dim_ticket_categories: category_id, name
                            - dim_root_causes: root_cause_id, description
                            - dim_time: date_id, date, year, month, day
                            - fact_tickets: ticket_id, customer_id, product_id, category_id, status, priority, root_cause_id, created_at, resolved_at
                            - fact_customer_products: customer_id, product_id, subscribed_at
                            - fact_logins: access_id, customer_id, login_date, device_type"""
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of rows to return (default: 100, max: 1000)",
                            "default": 100
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "kb_search",
                "description": """Search the dBank knowledge base for product documentation, known issues, 
                policies, release notes, and troubleshooting guides. Use when users ask about 
                'what is', 'how to', 'known issues', or need documentation.""",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query for knowledge base (e.g., 'Digital Lending approval delays', 'app v1.2 known issues')"
                        },
                        "top_k": {
                            "type": "integer",
                            "description": "Number of results to return (default: 5, max: 20)",
                            "default": 5
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                # Use function-name-safe identifier (no dots) for model function calling
                "name": "kpi_top_root_causes",
                "description": """Calculate top root causes of support tickets by category 
                with percentage of open tickets. Use for root cause analysis, pattern identification, 
                and periodic reports (daily, weekly, monthly).""",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "start_date": {
                            "type": "string",
                            "description": "Start date for analysis (YYYY-MM-DD format)",
                            "pattern": "^\\d{4}-\\d{2}-\\d{2}$"
                        },
                        "end_date": {
                            "type": "string",
                            "description": "End date for analysis (YYYY-MM-DD format)",
                            "pattern": "^\\d{4}-\\d{2}-\\d{2}$"
                        },
                        "category": {
                            "type": "string",
                            "description": "Optional: Filter by product category (e.g., 'Digital Saving', 'Digital Lending', 'Payment')"
                        },
                        "top_n": {
                            "type": "integer",
                            "description": "Number of top root causes to return (default: 5)",
                            "default": 5
                        }
                    },
                    "required": ["start_date", "end_date"]
                }
            }
        ]
    
    async def execute_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> ToolCall:
        """
        Execute a single tool call
        
        Args:
            tool_name: Name of the tool (sql.query, kb.search, kpi.top_root_causes)
            arguments: Tool arguments
        
        Returns:
            ToolCall object with results
        """
        start_time = time.time()
        
        tool_call = ToolCall(
            tool_name=tool_name,
            parameters=arguments
        )
        
        try:
            # Map internal function-safe names to MCP tool ids
            mcp_tool_map = {
                "sql_query": "sql.query",
                "kb_search": "kb.search",
                "kpi_top_root_causes": "kpi.top_root_causes",
            }

            if tool_name not in mcp_tool_map:
                raise ValueError(f"Unknown tool: {tool_name}")

            mcp_tool_id = mcp_tool_map[tool_name]
            url = f"{self.mcp_server_url}/tools/call"

            # Special handling for kpi_top_root_causes: convert arguments into KPI aggregate format
            if tool_name == "kpi_top_root_causes":
                # MCP kpi tool expects parameters: year (required), optional month, top_n, category_filter
                # Accept either 'start_date'/'end_date' or direct 'year'/'month' from arguments.
                year = None
                month = None

                # Prefer explicit year/month if provided
                if arguments.get("year"):
                    year = int(arguments.get("year"))
                if arguments.get("month"):
                    month = int(arguments.get("month"))

                # If start_date provided, derive year (and month if start/end in same month)
                if not year and arguments.get("start_date"):
                    try:
                        sd = datetime.strptime(arguments.get("start_date"), "%Y-%m-%d")
                        year = sd.year
                    except Exception:
                        pass

                if arguments.get("start_date") and arguments.get("end_date"):
                    try:
                        sd = datetime.strptime(arguments.get("start_date"), "%Y-%m-%d")
                        ed = datetime.strptime(arguments.get("end_date"), "%Y-%m-%d")
                        # If both dates are within the same month, set month; otherwise leave None
                        if sd.year == ed.year and sd.month == ed.month:
                            month = sd.month
                    except Exception:
                        pass

                # top_n and category mapping
                mcp_params = {}
                if year:
                    mcp_params["year"] = int(year)
                else:
                    raise ValueError("kpi_top_root_causes requires a 'year' or 'start_date' that includes a year")

                if month:
                    mcp_params["month"] = int(month)

                if arguments.get("top_n"):
                    mcp_params["top_n"] = int(arguments.get("top_n"))

                # Map category -> category_filter expected by MCP tool
                if arguments.get("category"):
                    mcp_params["category_filter"] = arguments.get("category")

                mcp_body = {"tool": mcp_tool_id, "parameters": mcp_params}
            else:
                # For other tools, wrap arguments under 'parameters'
                mcp_body = {"tool": mcp_tool_id, "parameters": arguments}

            # Make request to MCP server (ToolCallRequest shape)
            response = await self.client.post(url, json=mcp_body)
            response.raise_for_status()
            
            result = response.json()
            
            # Store result
            tool_call.result = result
            tool_call.execution_time = time.time() - start_time
            
            return tool_call
            
        except Exception as e:
            tool_call.error = str(e)
            tool_call.execution_time = time.time() - start_time
            return tool_call
    
    async def execute_tools(
        self,
        tool_calls: List[Dict[str, Any]]
    ) -> List[ToolCall]:
        """
        Execute multiple tool calls
        
        Args:
            tool_calls: List of tool calls to execute
        
        Returns:
            List of ToolCall results
        """
        results = []
        
        for tool_call in tool_calls:
            result = await self.execute_tool(
                tool_name=tool_call["name"],
                arguments=tool_call["arguments"]
            )
            results.append(result)
        
        return results
    
    def extract_citations(self, tool_calls: List[ToolCall]) -> List[Citation]:
        """
        Extract citations from tool results for dBank
        
        Args:
            tool_calls: List of executed tool calls
        
        Returns:
            List of citations
        """
        citations = []
        
        for tool_call in tool_calls:
            if tool_call.error:
                continue
            
            # Extract citations based on tool type
            if tool_call.tool_name == "kb_search":
                # Knowledge base citations
                if tool_call.result and "results" in tool_call.result:
                    for item in tool_call.result["results"]:
                        source_name = item.get("metadata", {}).get("source", "Knowledge Base")
                        citations.append(Citation(
                            source=f"Product KB - {source_name}",
                            content=item.get("text", "")[:200] + "...",
                            score=item.get("score"),
                            metadata=item.get("metadata")
                        ))
            
            elif tool_call.tool_name == "sql_query":
                # SQL query citations
                if tool_call.result and "rows" in tool_call.result:
                    row_count = len(tool_call.result["rows"])
                    citations.append(Citation(
                        source="Support Database Query",
                        content=f"Based on {row_count} records from support database (PII masked)",
                        metadata={
                            "query_preview": tool_call.parameters.get("query", "")[:100] + "...",
                            "row_count": row_count,
                            "note": "All PII data is automatically masked for security"
                        }
                    ))
            
            elif tool_call.tool_name == "kpi_top_root_causes":
                # KPI root cause citations
                if tool_call.result:
                    citations.append(Citation(
                        source="Root Cause Analysis KPI",
                        content=f"Calculated from tickets between {tool_call.parameters.get('start_date')} and {tool_call.parameters.get('end_date')}",
                        metadata={
                            "date_range": f"{tool_call.parameters.get('start_date')} to {tool_call.parameters.get('end_date')}",
                            "category": tool_call.parameters.get('category', 'All categories'),
                            "top_n": tool_call.parameters.get('top_n', 5)
                        }
                    ))
        
        return citations
    
    async def health_check(self) -> bool:
        """
        Check if MCP server is healthy
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            response = await self.client.get(f"{self.mcp_server_url}/health")
            return response.status_code == 200
        except:
            return False
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()