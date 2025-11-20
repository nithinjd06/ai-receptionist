"""
Repository layer for database CRUD operations.
All operations are async-first for FastAPI compatibility.
"""
from typing import List, Optional
from datetime import datetime
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from .models import Call, Turn, Appointment, Message, AuditLog


class CallRepository:
    """Repository for Call operations."""
    
    @staticmethod
    async def create(session: AsyncSession, call: Call) -> Call:
        """Create a new call record."""
        session.add(call)
        await session.commit()
        await session.refresh(call)
        return call
    
    @staticmethod
    async def get_by_id(session: AsyncSession, call_id: int) -> Optional[Call]:
        """Get a call by ID."""
        return await session.get(Call, call_id)
    
    @staticmethod
    async def get_by_call_sid(session: AsyncSession, call_sid: str) -> Optional[Call]:
        """Get a call by Twilio Call SID."""
        stmt = select(Call).where(Call.call_sid == call_sid)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()
    
    @staticmethod
    async def update_end(session: AsyncSession, call_id: int, outcome: str, summary: Optional[str] = None) -> None:
        """Update call end time and outcome."""
        call = await session.get(Call, call_id)
        if call:
            call.ended_at = datetime.utcnow()
            if call.started_at:
                call.duration_s = (call.ended_at - call.started_at).total_seconds()
            call.outcome = outcome
            call.summary = summary
            await session.commit()
    
    @staticmethod
    async def get_recent(session: AsyncSession, tenant_id: str = "default", limit: int = 50) -> List[Call]:
        """Get recent calls for a tenant."""
        stmt = select(Call).where(Call.tenant_id == tenant_id).order_by(Call.started_at.desc()).limit(limit)
        result = await session.execute(stmt)
        return list(result.scalars().all())


class TurnRepository:
    """Repository for Turn operations."""
    
    @staticmethod
    async def create(session: AsyncSession, turn: Turn) -> Turn:
        """Create a new turn record."""
        session.add(turn)
        await session.commit()
        await session.refresh(turn)
        return turn
    
    @staticmethod
    async def get_by_call(session: AsyncSession, call_id: int) -> List[Turn]:
        """Get all turns for a call, ordered by turn number."""
        stmt = select(Turn).where(Turn.call_id == call_id).order_by(Turn.turn_no)
        result = await session.execute(stmt)
        return list(result.scalars().all())
    
    @staticmethod
    async def get_conversation_history(session: AsyncSession, call_id: int, limit: int = 10) -> List[Turn]:
        """Get recent conversation history for context."""
        stmt = (
            select(Turn)
            .where(Turn.call_id == call_id)
            .order_by(Turn.turn_no.desc())
            .limit(limit)
        )
        result = await session.execute(stmt)
        turns = list(result.scalars().all())
        return list(reversed(turns))  # Return in chronological order


class AppointmentRepository:
    """Repository for Appointment operations."""
    
    @staticmethod
    async def create(session: AsyncSession, appointment: Appointment) -> Appointment:
        """Create a new appointment record."""
        session.add(appointment)
        await session.commit()
        await session.refresh(appointment)
        return appointment
    
    @staticmethod
    async def get_by_external_id(session: AsyncSession, external_id: str, provider: str) -> Optional[Appointment]:
        """Get an appointment by external ID and provider."""
        stmt = select(Appointment).where(
            Appointment.external_id == external_id,
            Appointment.provider == provider
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()
    
    @staticmethod
    async def update_status(session: AsyncSession, appointment_id: int, status: str) -> None:
        """Update appointment status."""
        appt = await session.get(Appointment, appointment_id)
        if appt:
            appt.status = status
            appt.updated_at = datetime.utcnow()
            await session.commit()
    
    @staticmethod
    async def get_by_call(session: AsyncSession, call_id: int) -> List[Appointment]:
        """Get all appointments for a call."""
        stmt = select(Appointment).where(Appointment.call_id == call_id)
        result = await session.execute(stmt)
        return list(result.scalars().all())


class MessageRepository:
    """Repository for Message operations."""
    
    @staticmethod
    async def create(session: AsyncSession, message: Message) -> Message:
        """Create a new message record."""
        session.add(message)
        await session.commit()
        await session.refresh(message)
        return message
    
    @staticmethod
    async def get_unread(session: AsyncSession, limit: int = 100) -> List[Message]:
        """Get unread messages."""
        stmt = (
            select(Message)
            .where(Message.status == "new")
            .order_by(Message.created_at.desc())
            .limit(limit)
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())
    
    @staticmethod
    async def update_status(session: AsyncSession, message_id: int, status: str) -> None:
        """Update message status."""
        msg = await session.get(Message, message_id)
        if msg:
            msg.status = status
            msg.updated_at = datetime.utcnow()
            await session.commit()


class AuditLogRepository:
    """Repository for AuditLog operations."""
    
    @staticmethod
    async def create(session: AsyncSession, log: AuditLog) -> AuditLog:
        """Create a new audit log entry."""
        session.add(log)
        await session.commit()
        await session.refresh(log)
        return log
    
    @staticmethod
    async def log_event(
        session: AsyncSession,
        event_type: str,
        event_data: Optional[dict] = None,
        call_id: Optional[int] = None,
        severity: str = "info"
    ) -> AuditLog:
        """Convenience method to create an audit log."""
        log = AuditLog(
            call_id=call_id,
            event_type=event_type,
            event_data=event_data,
            severity=severity
        )
        return await AuditLogRepository.create(session, log)
    
    @staticmethod
    async def get_by_call(session: AsyncSession, call_id: int) -> List[AuditLog]:
        """Get all audit logs for a call."""
        stmt = select(AuditLog).where(AuditLog.call_id == call_id).order_by(AuditLog.created_at)
        result = await session.execute(stmt)
        return list(result.scalars().all())







