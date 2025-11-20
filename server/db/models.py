"""
SQLModel database models for calls, turns, appointments, messages, and audit logs.
"""
from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field, Column, JSON
from sqlalchemy import Index


class Call(SQLModel, table=True):
    """Represents a phone call session."""
    __tablename__ = "calls"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    call_sid: str = Field(index=True, unique=True)  # Twilio Call SID
    tenant_id: str = Field(default="default", index=True)
    caller_phone: str
    started_at: datetime = Field(default_factory=datetime.utcnow)
    ended_at: Optional[datetime] = None
    duration_s: Optional[float] = None
    outcome: Optional[str] = None  # completed, transferred, error, hung_up
    summary: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Turn(SQLModel, table=True):
    """Represents a single conversation turn (user utterance + assistant response)."""
    __tablename__ = "turns"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    call_id: int = Field(foreign_key="calls.id", index=True)
    turn_no: int  # Sequential turn number within the call
    role: str  # user | assistant
    text: str
    action: Optional[str] = None  # answer_faq, schedule_appointment, take_message, route_to_human
    action_args: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    latency_ms: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_call_turn', 'call_id', 'turn_no'),
    )


class Appointment(SQLModel, table=True):
    """Represents a scheduled appointment."""
    __tablename__ = "appointments"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    call_id: Optional[int] = Field(default=None, foreign_key="calls.id", index=True)
    external_id: str = Field(index=True)  # Google Calendar event ID or Calendly ID
    provider: str  # google | calendly | athena
    patient_name: Optional[str] = None
    patient_phone: Optional[str] = None
    patient_email: Optional[str] = None
    appointment_type: Optional[str] = None
    start_time: datetime
    end_time: datetime
    status: str = "scheduled"  # scheduled | confirmed | cancelled | completed
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Message(SQLModel, table=True):
    """Represents a message taken during a call."""
    __tablename__ = "messages"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    call_id: int = Field(foreign_key="calls.id", index=True)
    caller_name: Optional[str] = None
    caller_phone: str
    callback_phone: Optional[str] = None
    summary: str
    urgency: str = "normal"  # low | normal | high
    status: str = "new"  # new | acknowledged | completed
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class AuditLog(SQLModel, table=True):
    """Audit trail for critical events and actions."""
    __tablename__ = "audit_logs"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    call_id: Optional[int] = Field(default=None, foreign_key="calls.id", index=True)
    event_type: str = Field(index=True)  # call_started, action_taken, error, etc.
    event_data: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    severity: str = "info"  # debug | info | warning | error | critical
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)







