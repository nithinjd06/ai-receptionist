"""
Pydantic schemas for conversation actions and state.
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class ConversationContext(BaseModel):
    """Context for a phone conversation."""
    call_id: int
    call_sid: str
    caller_phone: str
    tenant_id: str = "default"
    turn_number: int = 0
    started_at: datetime = Field(default_factory=datetime.utcnow)
    failed_asr_count: int = 0
    last_action: Optional[str] = None
    conversation_state: Dict[str, Any] = Field(default_factory=dict)
    

class ConversationTurn(BaseModel):
    """Represents a single conversation turn."""
    turn_no: int
    user_text: str
    assistant_text: str
    action: str
    action_args: Dict[str, Any]
    latency_ms: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class FAQAction(BaseModel):
    """FAQ answer action."""
    response: str
    category: str = "general"


class SchedulingAction(BaseModel):
    """Scheduling action."""
    response: str
    intent: str  # check_availability | propose_slot | confirm_booking | cancel
    patient_name: Optional[str] = None
    preferred_date: Optional[str] = None
    preferred_time: Optional[str] = None
    appointment_type: Optional[str] = None
    

class MessageAction(BaseModel):
    """Take message action."""
    response: str
    caller_name: Optional[str] = None
    callback_phone: Optional[str] = None
    message_summary: str
    urgency: str = "normal"


class RouteAction(BaseModel):
    """Route to human action."""
    response: str
    reason: str
    department: str = "general"


class CallSummary(BaseModel):
    """End-of-call summary."""
    call_id: int
    duration_s: float
    turn_count: int
    actions_taken: List[str]
    outcome: str  # completed | transferred | error | hung_up
    appointments_scheduled: int = 0
    messages_taken: int = 0
    errors_encountered: List[str] = Field(default_factory=list)
    summary_text: Optional[str] = None







