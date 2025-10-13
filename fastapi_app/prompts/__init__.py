# fastapi_app/prompts/__init__.py
"""
System prompts for LLM
"""
from .system_prompts import (
    DBANK_SYSTEM_PROMPT,
    TOOL_SELECTION_EXAMPLES,
    CITATION_FORMAT,
    ERROR_HANDLING_PROMPT,
)

__all__ = [
    "DBANK_SYSTEM_PROMPT",
    "TOOL_SELECTION_EXAMPLES",
    "CITATION_FORMAT",
    "ERROR_HANDLING_PROMPT",
]