"""
Tests for conversation router and intent classification.
"""
import pytest
from datetime import datetime
from sqlmodel import create_engine, SQLModel, Session
from sqlmodel.pool import StaticPool

from server.convo.router import ConversationRouter
from server.convo.schema import ConversationContext
from server.llm.base import LLMProvider, Message, LLMResponse
from server.db.models import Call


class MockLLMProvider(LLMProvider):
    """Mock LLM provider for testing."""
    
    def __init__(self):
        self.responses = []
        self.call_count = 0
    
    def add_response(self, action: str, response_text: str, args: dict):
        """Add a mock response."""
        self.responses.append(
            LLMResponse(
                response_text=response_text,
                action=action,
                action_args=args,
            )
        )
    
    async def generate_response(self, messages, system_prompt=None, temperature=None, max_tokens=None):
        """Return next mock response."""
        if self.call_count < len(self.responses):
            response = self.responses[self.call_count]
            self.call_count += 1
            return response
        
        # Default response
        return LLMResponse(
            response_text="I understand.",
            action="answer_faq",
            action_args={"response": "I understand.", "category": "general"},
        )
    
    async def generate_with_functions(self, messages, functions, system_prompt=None):
        """Return next mock response."""
        return await self.generate_response(messages, system_prompt)


@pytest.fixture
def db_session():
    """Create in-memory database session for testing."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    
    with Session(engine) as session:
        yield session


@pytest.fixture
def mock_llm():
    """Create mock LLM provider."""
    return MockLLMProvider()


@pytest.fixture
def conversation_router(db_session, mock_llm):
    """Create conversation router with mocks."""
    return ConversationRouter(
        llm_provider=mock_llm,
        session=db_session,
        business_name="Test Clinic",
        business_hours="9 AM to 5 PM",
    )


@pytest.fixture
def conversation_context(db_session):
    """Create test conversation context."""
    call = Call(
        call_sid="test_call_sid",
        tenant_id="test",
        caller_phone="+15551234567",
    )
    db_session.add(call)
    db_session.commit()
    db_session.refresh(call)
    
    return ConversationContext(
        call_id=call.id,
        call_sid="test_call_sid",
        caller_phone="+15551234567",
        tenant_id="test",
    )


@pytest.mark.asyncio
async def test_faq_action(conversation_router, conversation_context, mock_llm):
    """Test FAQ action handling."""
    mock_llm.add_response(
        action="answer_faq",
        response_text="We're open Monday through Friday, 9 AM to 5 PM.",
        args={"response": "We're open Monday through Friday, 9 AM to 5 PM.", "category": "hours"},
    )
    
    turn = await conversation_router.process_turn(
        context=conversation_context,
        user_utterance="What are your hours?",
    )
    
    assert turn.action == "answer_faq"
    assert "9 AM to 5 PM" in turn.assistant_text
    assert turn.latency_ms > 0


@pytest.mark.asyncio
async def test_scheduling_action(conversation_router, conversation_context, mock_llm):
    """Test scheduling action handling."""
    mock_llm.add_response(
        action="schedule_appointment",
        response_text="I can help you schedule an appointment. What day works best for you?",
        args={
            "response": "I can help you schedule an appointment. What day works best for you?",
            "intent": "check_availability",
        },
    )
    
    turn = await conversation_router.process_turn(
        context=conversation_context,
        user_utterance="I'd like to schedule an appointment",
    )
    
    assert turn.action == "schedule_appointment"
    assert "schedule" in turn.assistant_text.lower()


@pytest.mark.asyncio
async def test_take_message_action(conversation_router, conversation_context, mock_llm):
    """Test take message action."""
    mock_llm.add_response(
        action="take_message",
        response_text="I'll take your information for a callback.",
        args={
            "response": "I'll take your information for a callback.",
            "caller_name": "John Doe",
            "callback_phone": "+15551234567",
            "message_summary": "General inquiry",
            "urgency": "normal",
        },
    )
    
    turn = await conversation_router.process_turn(
        context=conversation_context,
        user_utterance="Can someone call me back?",
    )
    
    assert turn.action == "take_message"
    assert "callback" in turn.assistant_text.lower()


@pytest.mark.asyncio
async def test_route_to_human_action(conversation_router, conversation_context, mock_llm):
    """Test route to human action."""
    mock_llm.add_response(
        action="route_to_human",
        response_text="Let me transfer you to a staff member.",
        args={
            "response": "Let me transfer you to a staff member.",
            "reason": "Complex medical question",
            "department": "medical",
        },
    )
    
    turn = await conversation_router.process_turn(
        context=conversation_context,
        user_utterance="I need to speak with a doctor",
    )
    
    assert turn.action == "route_to_human"
    assert "transfer" in turn.assistant_text.lower() or "staff" in turn.assistant_text.lower()


@pytest.mark.asyncio
async def test_conversation_history(conversation_router, conversation_context, mock_llm):
    """Test conversation history tracking."""
    # First turn
    mock_llm.add_response(
        action="answer_faq",
        response_text="We're open 9 AM to 5 PM.",
        args={"response": "We're open 9 AM to 5 PM.", "category": "hours"},
    )
    
    turn1 = await conversation_router.process_turn(
        context=conversation_context,
        user_utterance="What are your hours?",
    )
    
    # Second turn
    mock_llm.add_response(
        action="schedule_appointment",
        response_text="I can help with that.",
        args={"response": "I can help with that.", "intent": "check_availability"},
    )
    
    turn2 = await conversation_router.process_turn(
        context=conversation_context,
        user_utterance="I'd like to make an appointment",
    )
    
    assert turn1.turn_no == 1
    assert turn2.turn_no == 2
    assert conversation_context.turn_number == 2


@pytest.mark.asyncio
async def test_call_summary_generation(conversation_router, conversation_context, mock_llm, db_session):
    """Test call summary generation."""
    # Have a conversation
    mock_llm.add_response(
        action="schedule_appointment",
        response_text="Appointment scheduled.",
        args={"response": "Appointment scheduled.", "intent": "confirm_booking"},
    )
    
    await conversation_router.process_turn(
        context=conversation_context,
        user_utterance="Schedule appointment for Monday",
    )
    
    # Generate summary
    summary = await conversation_router.generate_call_summary(conversation_context)
    
    assert summary.call_id == conversation_context.call_id
    assert summary.turn_count > 0
    assert "schedule_appointment" in summary.actions_taken







