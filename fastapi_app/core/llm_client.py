"""
LLM Client - OpenAI GPT-4o-mini for dBank Support Copilot
"""
import os
import json
from typing import List, Dict, Any, Optional, AsyncGenerator

import openai
from openai import AsyncOpenAI
from dotenv import load_dotenv

from prompts.system_prompts import DBANK_SYSTEM_PROMPT

load_dotenv()


class OpenAIClient:
    """OpenAI client for dBank support copilot"""
    
    def __init__(
        self, 
        api_key: Optional[str] = None, 
        model: str = "gpt-4o-mini"
    ):
        """
        Initialize OpenAI client
        
        Args:
            api_key: OpenAI API key (defaults to env var)
            model: Model to use (default: gpt-4o-mini)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is required")
        
        self.model = model
        self.client = AsyncOpenAI(api_key=self.api_key)
    
    def _convert_tools(self, tools: Optional[List[Dict]]) -> Optional[List[Dict]]:
        """Convert tool definitions to OpenAI format"""
        if not tools:
            return None
        
        openai_tools = []
        for tool in tools:
            openai_tools.append({
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": tool["parameters"]
                }
            })
        return openai_tools
    
    async def generate(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict]] = None,
        max_tokens: int = 2000,
        temperature: float = 0.3  # Lower for more consistent support answers
    ) -> Dict[str, Any]:
        """
        Generate a response using OpenAI
        
        Args:
            messages: Conversation messages
            tools: Available tools
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature (0.3 for support use case)
        
        Returns:
            Response with content and tool calls
        """
        
        # Prepare messages with system prompt
        formatted_messages = [{"role": "system", "content": DBANK_SYSTEM_PROMPT}]
        formatted_messages.extend(messages)
        
        # Prepare request
        request_params = {
            "model": self.model,
            "messages": formatted_messages,
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        # Add tools if provided
        if tools:
            request_params["tools"] = self._convert_tools(tools)
            request_params["tool_choice"] = "auto"
        
        # Make request
        response = await self.client.chat.completions.create(**request_params)
        
        # Parse response
        message = response.choices[0].message
        
        result = {
            "content": message.content or "",
            "tool_calls": [],
            "finish_reason": response.choices[0].finish_reason,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
        }
        
        # Extract tool calls
        if message.tool_calls:
            for tool_call in message.tool_calls:
                result["tool_calls"].append({
                    "id": tool_call.id,
                    "name": tool_call.function.name,
                    "arguments": json.loads(tool_call.function.arguments)
                })
        
        return result
    
    async def stream(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict]] = None,
        max_tokens: int = 2000,
        temperature: float = 0.3
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream a response using OpenAI
        
        Args:
            messages: Conversation messages
            tools: Available tools
            max_tokens: Maximum tokens
            temperature: Sampling temperature
        
        Yields:
            Response chunks
        """
        
        # Prepare messages with system prompt
        formatted_messages = [{"role": "system", "content": DBANK_SYSTEM_PROMPT}]
        formatted_messages.extend(messages)
        
        # Prepare request
        request_params = {
            "model": self.model,
            "messages": formatted_messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": True
        }
        
        # Add tools if provided
        if tools:
            request_params["tools"] = self._convert_tools(tools)
            request_params["tool_choice"] = "auto"
        
        # Stream response
        stream = await self.client.chat.completions.create(**request_params)
        
        tool_calls_buffer = {}  # Buffer for tool calls
        
        async for chunk in stream:
            if not chunk.choices:
                continue
                
            delta = chunk.choices[0].delta
            
            # Text content
            if delta.content:
                yield {
                    "type": "text",
                    "content": delta.content
                }
            
            # Tool calls
            if delta.tool_calls:
                for tool_call in delta.tool_calls:
                    idx = tool_call.index
                    
                    if idx not in tool_calls_buffer:
                        tool_calls_buffer[idx] = {
                            "id": "",
                            "name": "",
                            "arguments": ""
                        }
                    
                    if tool_call.id:
                        tool_calls_buffer[idx]["id"] = tool_call.id
                    
                    if tool_call.function:
                        if tool_call.function.name:
                            tool_calls_buffer[idx]["name"] = tool_call.function.name
                        if tool_call.function.arguments:
                            tool_calls_buffer[idx]["arguments"] += tool_call.function.arguments
            
            # End of stream
            if chunk.choices[0].finish_reason:
                # Emit completed tool calls
                for tool_call in tool_calls_buffer.values():
                    if tool_call["name"]:
                        yield {
                            "type": "tool_call",
                            "id": tool_call["id"],
                            "name": tool_call["name"],
                            "arguments": json.loads(tool_call["arguments"]) if tool_call["arguments"] else {}
                        }
                
                yield {
                    "type": "done",
                    "finish_reason": chunk.choices[0].finish_reason
                }


def get_llm_client() -> OpenAIClient:
    """
    Get OpenAI client for dBank
    
    Returns:
        OpenAI client instance
    """
    return OpenAIClient(model="gpt-4o-mini")