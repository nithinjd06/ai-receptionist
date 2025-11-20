"""
Abstract base class for LLM providers.
Enables swapping between OpenAI, Anthropic, etc.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class Message:
    """Represents a conversation message."""
    role: str  # system | user | assistant
    content: str


@dataclass
class LLMResponse:
    """Represents an LLM response with action."""
    response_text: str
    action: str  # answer_faq | schedule_appointment | take_message | route_to_human
    action_args: Dict[str, Any]
    raw_response: Optional[Any] = None


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    async def generate_response(
        self,
        messages: List[Message],
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Generate a response from the LLM.
        
        Args:
            messages: Conversation history
            system_prompt: System prompt (optional, provider-specific default used if None)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            LLMResponse with text, action, and args
        """
        pass
    
    @abstractmethod
    async def generate_with_functions(
        self,
        messages: List[Message],
        functions: List[Dict[str, Any]],
        system_prompt: Optional[str] = None,
    ) -> LLMResponse:
        """
        Generate a response using function calling.
        
        Args:
            messages: Conversation history
            functions: Available functions/tools
            system_prompt: System prompt
            
        Returns:
            LLMResponse with function call details
        """
        pass


class LLMError(Exception):
    """Base exception for LLM errors."""
    pass


class LLMTimeoutError(LLMError):
    """Raised when LLM operation times out."""
    pass


class LLMRateLimitError(LLMError):
    """Raised when rate limit is exceeded."""
    pass







