"""
Anthropic Claude LLM implementation.
Uses tool calling for structured action outputs.
"""
import json
import logging
from typing import List, Dict, Any, Optional
from anthropic import AsyncAnthropic, APITimeoutError, RateLimitError
from .base import LLMProvider, Message, LLMResponse, LLMError, LLMTimeoutError, LLMRateLimitError

logger = logging.getLogger(__name__)


class AnthropicClaude(LLMProvider):
    """Anthropic Claude LLM provider."""
    
    def __init__(
        self,
        api_key: str,
        model: str = "claude-3-5-sonnet-20241022",
        temperature: float = 0.7,
        max_tokens: int = 500,
        timeout: float = 10.0,
    ):
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        
        self.client = AsyncAnthropic(api_key=api_key, timeout=timeout)
        
        # Define tool schemas (Anthropic's tool calling format)
        self.tools = [
            {
                "name": "answer_faq",
                "description": "Answer frequently asked questions about office hours, location, services, etc.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "response": {
                            "type": "string",
                            "description": "The answer to provide to the caller"
                        },
                        "category": {
                            "type": "string",
                            "enum": ["hours", "location", "services", "insurance", "general"],
                            "description": "The category of the FAQ"
                        }
                    },
                    "required": ["response"]
                }
            },
            {
                "name": "schedule_appointment",
                "description": "Schedule, reschedule, or check appointment availability",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "response": {
                            "type": "string",
                            "description": "What to say to the caller"
                        },
                        "intent": {
                            "type": "string",
                            "enum": ["check_availability", "propose_slot", "confirm_booking", "cancel"],
                            "description": "The scheduling intent"
                        },
                        "patient_name": {
                            "type": "string",
                            "description": "Patient's name (if provided)"
                        },
                        "preferred_date": {
                            "type": "string",
                            "description": "Preferred date in YYYY-MM-DD format (if mentioned)"
                        },
                        "preferred_time": {
                            "type": "string",
                            "description": "Preferred time (morning/afternoon/specific time)"
                        }
                    },
                    "required": ["response", "intent"]
                }
            },
            {
                "name": "take_message",
                "description": "Take a message from the caller for callback",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "response": {
                            "type": "string",
                            "description": "What to say to the caller"
                        },
                        "caller_name": {
                            "type": "string",
                            "description": "Caller's name"
                        },
                        "callback_phone": {
                            "type": "string",
                            "description": "Phone number for callback"
                        },
                        "message_summary": {
                            "type": "string",
                            "description": "Brief summary of the message/reason for call"
                        },
                        "urgency": {
                            "type": "string",
                            "enum": ["low", "normal", "high"],
                            "description": "Urgency level"
                        }
                    },
                    "required": ["response", "message_summary"]
                }
            },
            {
                "name": "route_to_human",
                "description": "Transfer the call to a human agent",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "response": {
                            "type": "string",
                            "description": "What to say before transferring"
                        },
                        "reason": {
                            "type": "string",
                            "description": "Reason for human transfer"
                        },
                        "department": {
                            "type": "string",
                            "enum": ["general", "medical", "billing", "scheduling"]
                        }
                    },
                    "required": ["response", "reason"]
                }
            }
        ]
    
    async def generate_response(
        self,
        messages: List[Message],
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """Generate response using tool calling."""
        return await self.generate_with_functions(
            messages=messages,
            functions=self.tools,
            system_prompt=system_prompt,
        )
    
    async def generate_with_functions(
        self,
        messages: List[Message],
        functions: List[Dict[str, Any]],
        system_prompt: Optional[str] = None,
    ) -> LLMResponse:
        """
        Generate response with tool calling.
        
        Args:
            messages: Conversation history
            functions: Available tools
            system_prompt: System prompt
            
        Returns:
            LLMResponse with action and args
        """
        try:
            # Build messages for Claude (exclude system messages)
            claude_messages = []
            for msg in messages:
                if msg.role != "system":
                    claude_messages.append({"role": msg.role, "content": msg.content})
            
            # Call Claude API with tools
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                system=system_prompt or "You are a helpful AI receptionist.",
                messages=claude_messages,
                tools=functions,
            )
            
            # Process response
            response_text = ""
            tool_use = None
            
            for block in response.content:
                if block.type == "text":
                    response_text = block.text
                elif block.type == "tool_use":
                    tool_use = block
            
            # Check if tool was used
            if tool_use:
                tool_name = tool_use.name
                tool_args = tool_use.input
                
                # Extract response text from tool args if present
                if "response" in tool_args:
                    response_text = tool_args["response"]
                
                return LLMResponse(
                    response_text=response_text,
                    action=tool_name,
                    action_args=tool_args,
                    raw_response=response
                )
            
            # No tool use, return plain response
            return LLMResponse(
                response_text=response_text,
                action="answer_faq",
                action_args={"response": response_text, "category": "general"},
                raw_response=response
            )
        
        except APITimeoutError as e:
            logger.error(f"Claude timeout: {e}")
            raise LLMTimeoutError(f"Claude request timed out: {e}")
        
        except RateLimitError as e:
            logger.error(f"Claude rate limit: {e}")
            raise LLMRateLimitError(f"Claude rate limit exceeded: {e}")
        
        except Exception as e:
            logger.error(f"Claude error: {e}")
            raise LLMError(f"Claude request failed: {e}")







