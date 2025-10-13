"""
Conversation Manager - Handles conversation context and history
"""
import uuid
from typing import Dict, List, Optional
from datetime import datetime, timedelta

from models.schemas import Conversation, Message, ToolCall, Citation


class ConversationManager:
    """Manages conversation history and context"""
    
    def __init__(self, max_history: int = 10, ttl_hours: int = 24):
        """
        Initialize conversation manager
        
        Args:
            max_history: Maximum messages to keep in context
            ttl_hours: Hours before conversation expires
        """
        self.conversations: Dict[str, Conversation] = {}
        self.max_history = max_history
        self.ttl_hours = ttl_hours
    
    def create_conversation(
        self,
        user_id: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Create a new conversation
        
        Args:
            user_id: Optional user ID
            metadata: Optional metadata
        
        Returns:
            Conversation ID
        """
        conversation_id = f"conv_{uuid.uuid4().hex[:12]}"
        
        self.conversations[conversation_id] = Conversation(
            conversation_id=conversation_id,
            user_id=user_id,
            metadata=metadata or {}
        )
        
        return conversation_id
    
    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """
        Get conversation by ID
        
        Args:
            conversation_id: Conversation ID
        
        Returns:
            Conversation or None if not found/expired
        """
        if conversation_id not in self.conversations:
            return None
        
        conversation = self.conversations[conversation_id]
        
        # Check if expired
        if self._is_expired(conversation):
            del self.conversations[conversation_id]
            return None
        
        return conversation
    
    def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        tool_calls: Optional[List[ToolCall]] = None,
        citations: Optional[List[Citation]] = None
    ) -> Message:
        """
        Add a message to conversation
        
        Args:
            conversation_id: Conversation ID
            role: Message role (user/assistant/system)
            content: Message content
            tool_calls: Optional tool calls
            citations: Optional citations
        
        Returns:
            Created message
        """
        conversation = self.get_conversation(conversation_id)
        
        if not conversation:
            # Create new conversation if doesn't exist
            self.create_conversation()
            conversation = self.conversations[conversation_id]
        
        message = Message(
            role=role,
            content=content,
            tool_calls=tool_calls,
            citations=citations
        )
        
        conversation.messages.append(message)
        conversation.updated_at = datetime.utcnow()
        
        # Trim history if too long
        if len(conversation.messages) > self.max_history:
            # Keep system messages + recent messages
            system_messages = [m for m in conversation.messages if m.role == "system"]
            recent_messages = [m for m in conversation.messages if m.role != "system"][-self.max_history:]
            conversation.messages = system_messages + recent_messages
        
        return message
    
    def get_context(
        self,
        conversation_id: str,
        include_system: bool = True
    ) -> List[Dict[str, str]]:
        """
        Get conversation context for LLM
        
        Args:
            conversation_id: Conversation ID
            include_system: Include system messages
        
        Returns:
            List of messages in LLM format
        """
        conversation = self.get_conversation(conversation_id)
        
        if not conversation:
            return []
        
        messages = []
        
        for msg in conversation.messages:
            if not include_system and msg.role == "system":
                continue
            
            messages.append({
                "role": msg.role,
                "content": msg.content
            })
        
        return messages
    
    def get_summary(self, conversation_id: str) -> Dict:
        """
        Get conversation summary
        
        Args:
            conversation_id: Conversation ID
        
        Returns:
            Summary with stats
        """
        conversation = self.get_conversation(conversation_id)
        
        if not conversation:
            return {"error": "Conversation not found"}
        
        user_messages = [m for m in conversation.messages if m.role == "user"]
        assistant_messages = [m for m in conversation.messages if m.role == "assistant"]
        
        total_tool_calls = sum(
            len(m.tool_calls or []) 
            for m in conversation.messages
        )
        
        total_citations = sum(
            len(m.citations or [])
            for m in conversation.messages
        )
        
        return {
            "conversation_id": conversation_id,
            "user_id": conversation.user_id,
            "created_at": conversation.created_at,
            "updated_at": conversation.updated_at,
            "message_count": len(conversation.messages),
            "user_messages": len(user_messages),
            "assistant_messages": len(assistant_messages),
            "tool_calls": total_tool_calls,
            "citations": total_citations,
            "metadata": conversation.metadata
        }
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """
        Delete a conversation
        
        Args:
            conversation_id: Conversation ID
        
        Returns:
            True if deleted, False if not found
        """
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]
            return True
        return False
    
    def cleanup_expired(self) -> int:
        """
        Remove expired conversations
        
        Returns:
            Number of conversations removed
        """
        expired = [
            conv_id
            for conv_id, conv in self.conversations.items()
            if self._is_expired(conv)
        ]
        
        for conv_id in expired:
            del self.conversations[conv_id]
        
        return len(expired)
    
    def _is_expired(self, conversation: Conversation) -> bool:
        """Check if conversation is expired"""
        expiry_time = conversation.updated_at + timedelta(hours=self.ttl_hours)
        return datetime.utcnow() > expiry_time
    
    def list_conversations(
        self,
        user_id: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict]:
        """
        List conversations
        
        Args:
            user_id: Filter by user ID
            limit: Maximum conversations to return
        
        Returns:
            List of conversation summaries
        """
        conversations = []
        
        for conv in self.conversations.values():
            if user_id and conv.user_id != user_id:
                continue
            
            conversations.append(self.get_summary(conv.conversation_id))
        
        # Sort by updated_at desc
        conversations.sort(key=lambda x: x["updated_at"], reverse=True)
        
        return conversations[:limit]


# Global conversation manager instance
conversation_manager = ConversationManager()


def get_conversation_manager() -> ConversationManager:
    """Get the global conversation manager instance"""
    return conversation_manager