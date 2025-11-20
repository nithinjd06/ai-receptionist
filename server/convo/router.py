"""
Conversation router that manages conversation flow, context, and action routing.
"""
import logging
from typing import Optional, List
from datetime import datetime
from sqlmodel.ext.asyncio.session import AsyncSession

from .schema import ConversationContext, ConversationTurn, CallSummary
from .prompts import get_system_prompt, get_off_hours_addendum
from .faq_loader import get_faq_enhanced_prompt
from ..llm.base import LLMProvider, Message, LLMResponse
from ..db.repo import TurnRepository, CallRepository, AuditLogRepository
from ..config import settings

logger = logging.getLogger(__name__)


class ConversationRouter:
    """
    Manages conversation flow, context, and routes actions to appropriate handlers.
    """
    
    def __init__(
        self,
        llm_provider: LLMProvider,
        session: AsyncSession,
        business_name: str = "Our Office",
        business_hours: str = "8 AM to 5 PM, Monday-Friday",
    ):
        self.llm = llm_provider
        self.session = session
        self.business_name = business_name
        self.business_hours = business_hours
        
        # System prompt
        self.system_prompt = get_system_prompt(business_name, business_hours)
    
    async def process_turn(
        self,
        context: ConversationContext,
        user_utterance: str,
    ) -> ConversationTurn:
        """
        Process a single conversation turn.
        
        Args:
            context: Current conversation context
            user_utterance: User's speech input
            
        Returns:
            ConversationTurn with response and action
        """
        start_time = datetime.utcnow()
        
        try:
            # Build conversation history
            messages = await self._build_message_history(context)
            
            # Add current user message
            messages.append(Message(role="user", content=user_utterance))
            
            # Check if off-hours
            system_prompt = self.system_prompt
            if self._is_off_hours():
                system_prompt += get_off_hours_addendum()
            
            # Enhance with FAQ knowledge base
            system_prompt = get_faq_enhanced_prompt(system_prompt)
            
            # Get LLM response with action
            llm_response = await self.llm.generate_response(
                messages=messages,
                system_prompt=system_prompt,
            )
            
            # Calculate latency
            latency_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            # Update context
            context.turn_number += 1
            context.last_action = llm_response.action
            
            # Save turn to database
            await self._save_turn(
                context=context,
                user_text=user_utterance,
                assistant_text=llm_response.response_text,
                action=llm_response.action,
                action_args=llm_response.action_args,
                latency_ms=latency_ms,
            )
            
            # Create turn object
            turn = ConversationTurn(
                turn_no=context.turn_number,
                user_text=user_utterance,
                assistant_text=llm_response.response_text,
                action=llm_response.action,
                action_args=llm_response.action_args,
                latency_ms=latency_ms,
            )
            
            # Log action
            await AuditLogRepository.log_event(
                self.session,
                event_type=f"action_{llm_response.action}",
                event_data={
                    "turn": context.turn_number,
                    "action": llm_response.action,
                    "args": llm_response.action_args,
                },
                call_id=context.call_id,
                severity="info",
            )
            
            return turn
        
        except Exception as e:
            logger.error(f"Error processing turn: {e}")
            
            # Log error
            await AuditLogRepository.log_event(
                self.session,
                event_type="error_processing_turn",
                event_data={"error": str(e), "user_utterance": user_utterance},
                call_id=context.call_id,
                severity="error",
            )
            
            # Return fallback response
            context.turn_number += 1
            return ConversationTurn(
                turn_no=context.turn_number,
                user_text=user_utterance,
                assistant_text="I apologize, I'm having trouble processing that. Could you please repeat?",
                action="take_message",
                action_args={"response": "I apologize for the difficulty. Let me take your information for a callback."},
                latency_ms=0,
            )
    
    async def _build_message_history(self, context: ConversationContext) -> List[Message]:
        """Build message history from database."""
        turns = await TurnRepository.get_conversation_history(
            self.session,
            context.call_id,
            limit=10,  # Keep last 10 turns for context
        )
        
        messages = []
        for turn in turns:
            messages.append(Message(role="user", content=turn.text))
            # Get next turn (assistant response)
        
        return messages
    
    async def _save_turn(
        self,
        context: ConversationContext,
        user_text: str,
        assistant_text: str,
        action: str,
        action_args: dict,
        latency_ms: int,
    ) -> None:
        """Save conversation turn to database."""
        from ..db.models import Turn
        
        # Save user turn
        user_turn = Turn(
            call_id=context.call_id,
            turn_no=context.turn_number * 2 - 1,  # Odd numbers for user
            role="user",
            text=user_text,
            latency_ms=0,
        )
        await TurnRepository.create(self.session, user_turn)
        
        # Save assistant turn
        assistant_turn = Turn(
            call_id=context.call_id,
            turn_no=context.turn_number * 2,  # Even numbers for assistant
            role="assistant",
            text=assistant_text,
            action=action,
            action_args=action_args,
            latency_ms=latency_ms,
        )
        await TurnRepository.create(self.session, assistant_turn)
    
    def _is_off_hours(self) -> bool:
        """Check if current time is outside business hours."""
        try:
            now = datetime.now()
            
            # Parse business days
            business_days = [int(d) for d in settings.BUSINESS_DAYS.split(",")]
            # Monday = 1, Sunday = 7 (ISO format)
            weekday = now.isoweekday()
            
            if weekday not in business_days:
                return True
            
            # Parse business hours
            start_hour, start_min = map(int, settings.BUSINESS_HOURS_START.split(":"))
            end_hour, end_min = map(int, settings.BUSINESS_HOURS_END.split(":"))
            
            current_time = now.hour * 60 + now.minute
            start_time = start_hour * 60 + start_min
            end_time = end_hour * 60 + end_min
            
            return current_time < start_time or current_time >= end_time
        
        except Exception as e:
            logger.error(f"Error checking business hours: {e}")
            return False
    
    async def generate_call_summary(self, context: ConversationContext) -> CallSummary:
        """Generate end-of-call summary."""
        # Get all turns
        turns = await TurnRepository.get_by_call(self.session, context.call_id)
        
        # Get call record
        call = await CallRepository.get_by_id(self.session, context.call_id)
        
        # Analyze actions taken
        actions_taken = []
        appointments_scheduled = 0
        messages_taken = 0
        
        for turn in turns:
            if turn.action:
                actions_taken.append(turn.action)
                if turn.action == "schedule_appointment":
                    appointments_scheduled += 1
                elif turn.action == "take_message":
                    messages_taken += 1
        
        # Calculate duration
        duration_s = 0.0
        if call and call.duration_s:
            duration_s = call.duration_s
        
        # Get audit log errors
        from ..db.repo import AuditLogRepository
        audit_logs = await AuditLogRepository.get_by_call(self.session, context.call_id)
        errors = [log.event_type for log in audit_logs if log.severity == "error"]
        
        # Generate summary text
        summary_text = f"Call completed with {len(turns)} turns. "
        if appointments_scheduled > 0:
            summary_text += f"Scheduled {appointments_scheduled} appointment(s). "
        if messages_taken > 0:
            summary_text += f"Took {messages_taken} message(s). "
        
        summary = CallSummary(
            call_id=context.call_id,
            duration_s=duration_s,
            turn_count=len(turns),
            actions_taken=list(set(actions_taken)),
            outcome="completed",
            appointments_scheduled=appointments_scheduled,
            messages_taken=messages_taken,
            errors_encountered=errors,
            summary_text=summary_text,
        )
        
        return summary

