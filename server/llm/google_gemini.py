"""
Google Gemini 2.0 Flash LLM implementation.
Uses function calling for structured action outputs.
"""
import json
import logging
from typing import List, Dict, Any, Optional
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from .base import LLMProvider, Message, LLMResponse, LLMError, LLMTimeoutError, LLMRateLimitError

logger = logging.getLogger(__name__)


class GoogleGemini(LLMProvider):
    """Google Gemini 2.0 Flash LLM provider."""
    
    def __init__(
        self,
        api_key: str,
        model: str = "gemini-2.5-flash",
        temperature: float = 0.7,
        max_tokens: int = 500,
        timeout: float = 10.0,
    ):
        self.api_key = api_key
        self.model_name = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        
        # Configure Gemini
        genai.configure(api_key=api_key)
        
        # Initialize model
        self.model = genai.GenerativeModel(
            model_name=model,
            generation_config={
                "temperature": temperature,
                "max_output_tokens": max_tokens,
            },
            safety_settings={
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            }
        )
        
        # Define function schemas (Gemini format)
        self.tools = [
            {
                "function_declarations": [
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
        Generate response with function calling for structured outputs.
        
        Args:
            messages: Conversation history
            functions: Available functions/tools
            system_prompt: System prompt
            
        Returns:
            LLMResponse with action and args
        """
        try:
            # Build conversation history for Gemini
            # Gemini format: [{"role": "user"/"model", "parts": ["text"]}]
            gemini_messages = []
            
            # Add system instruction if provided
            full_system = system_prompt or "You are a helpful AI receptionist."
            
            # Convert messages to Gemini format
            for msg in messages:
                if msg.role == "user":
                    gemini_messages.append({
                        "role": "user",
                        "parts": [msg.content]
                    })
                elif msg.role == "assistant":
                    gemini_messages.append({
                        "role": "model",
                        "parts": [msg.content]
                    })
                # Skip system messages (handled separately)
            
            # Create chat with tools
            chat = self.model.start_chat(history=gemini_messages[:-1] if len(gemini_messages) > 1 else [])
            
            # Send message with function calling enabled
            response = chat.send_message(
                gemini_messages[-1]["parts"][0] if gemini_messages else "",
                tools=functions,
            )
            
            # Check if function was called
            if response.candidates and len(response.candidates) > 0:
                candidate = response.candidates[0]
                
                # Check for function calls
                if candidate.content.parts:
                    for part in candidate.content.parts:
                        # Check if this part is a function call
                        if hasattr(part, 'function_call') and part.function_call:
                            function_call = part.function_call
                            function_name = function_call.name
                            
                            # Extract arguments
                            function_args = {}
                            for key, value in function_call.args.items():
                                function_args[key] = value
                            
                            # Extract response text
                            response_text = function_args.get("response", "")
                            
                            logger.info(f"Gemini function call: {function_name}")
                            
                            # Create LLM response
                            return LLMResponse(
                                response_text=response_text,
                                action=function_name,
                                action_args=function_args,
                                raw_response=response
                            )
                        
                        # Regular text response
                        elif hasattr(part, 'text'):
                            response_text = part.text
                            return LLMResponse(
                                response_text=response_text,
                                action="answer_faq",
                                action_args={"response": response_text, "category": "general"},
                                raw_response=response
                            )
            
            # Fallback: extract text from response
            response_text = response.text if hasattr(response, 'text') else ""
            return LLMResponse(
                response_text=response_text,
                action="answer_faq",
                action_args={"response": response_text, "category": "general"},
                raw_response=response
            )
        
        except Exception as e:
            error_msg = str(e).lower()
            
            if "timeout" in error_msg or "deadline" in error_msg:
                logger.error(f"Gemini timeout: {e}")
                raise LLMTimeoutError(f"Gemini request timed out: {e}")
            
            elif "quota" in error_msg or "rate" in error_msg:
                logger.error(f"Gemini rate limit: {e}")
                raise LLMRateLimitError(f"Gemini rate limit exceeded: {e}")
            
            else:
                logger.error(f"Gemini error: {e}")
                raise LLMError(f"Gemini request failed: {e}")

