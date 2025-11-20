"""
OpenAI GPT-4o LLM implementation.
Uses function calling for structured action outputs.
"""
import json
import logging
from typing import List, Dict, Any, Optional
from openai import AsyncOpenAI, APITimeoutError, RateLimitError
from .base import LLMProvider, Message, LLMResponse, LLMError, LLMTimeoutError, LLMRateLimitError

logger = logging.getLogger(__name__)


class OpenAIGPT4o(LLMProvider):
    """OpenAI GPT-4o LLM provider."""
    
    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o",
        temperature: float = 0.7,
        max_tokens: int = 500,
        timeout: float = 10.0,
    ):
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        
        self.client = AsyncOpenAI(api_key=api_key, timeout=timeout)
        
        # Define function schemas for structured outputs
        self.functions = [
            {
                "name": "answer_faq",
                "description": "Answer frequently asked questions about office hours, location, services, etc.",
                "parameters": {
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
                "parameters": {
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
                        },
                        "appointment_type": {
                            "type": "string",
                            "description": "Type of appointment (checkup, consultation, etc.)"
                        }
                    },
                    "required": ["response", "intent"]
                }
            },
            {
                "name": "take_message",
                "description": "Take a message from the caller for callback",
                "parameters": {
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
                            "description": "Urgency level of the message"
                        }
                    },
                    "required": ["response", "message_summary"]
                }
            },
            {
                "name": "route_to_human",
                "description": "Transfer the call to a human agent or take details for callback",
                "parameters": {
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
                            "enum": ["general", "medical", "billing", "scheduling"],
                            "description": "Which department to route to"
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
        """Generate response using function calling."""
        return await self.generate_with_functions(
            messages=messages,
            functions=self.functions,
            system_prompt=system_prompt,
        )
    
    async def generate_with_functions(
        self,
        messages: List[Message],
        functions: List[Dict[str, Any]],
        system_prompt: Optional[str] = None,
    ) -> LLMResponse:
        """
        Generate response with function calling for structured outputs.
        
        Args:
            messages: Conversation history
            functions: Available functions
            system_prompt: System prompt
            
        Returns:
            LLMResponse with action and args
        """
        try:
            # Build messages for OpenAI
            openai_messages = []
            
            # Add system prompt if provided
            if system_prompt:
                openai_messages.append({"role": "system", "content": system_prompt})
            
            # Add conversation messages
            for msg in messages:
                openai_messages.append({"role": msg.role, "content": msg.content})
            
            # Call OpenAI API with function calling
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=openai_messages,
                functions=functions,
                function_call="auto",
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
            
            message = response.choices[0].message
            
            # Check if function was called
            if message.function_call:
                function_name = message.function_call.name
                function_args = json.loads(message.function_call.arguments)
                
                # Extract response text
                response_text = function_args.get("response", "")
                
                # Create LLM response
                return LLMResponse(
                    response_text=response_text,
                    action=function_name,
                    action_args=function_args,
                    raw_response=response
                )
            
            # No function call, return plain response
            response_text = message.content or ""
            return LLMResponse(
                response_text=response_text,
                action="answer_faq",
                action_args={"response": response_text, "category": "general"},
                raw_response=response
            )
        
        except APITimeoutError as e:
            logger.error(f"OpenAI timeout: {e}")
            raise LLMTimeoutError(f"OpenAI request timed out: {e}")
        
        except RateLimitError as e:
            logger.error(f"OpenAI rate limit: {e}")
            raise LLMRateLimitError(f"OpenAI rate limit exceeded: {e}")
        
        except Exception as e:
            logger.error(f"OpenAI error: {e}")
            raise LLMError(f"OpenAI request failed: {e}")







