"""
Tests for calendar integration.
"""
import pytest
from datetime import datetime, timedelta
from server.scheduling.calendar_base import TimeSlot, AppointmentDetails, CalendarProvider


class MockCalendarProvider(CalendarProvider):
    """Mock calendar provider for testing."""
    
    def __init__(self):
        self.appointments = {}
        self.next_id = 1
    
    async def get_available_slots(self, start_date, end_date, duration_minutes=30):
        """Return mock available slots."""
        slots = []
        current = start_date.replace(hour=9, minute=0, second=0, microsecond=0)
        
        for i in range(10):
            slots.append(
                TimeSlot(
                    start_time=current,
                    end_time=current + timedelta(minutes=duration_minutes),
                    duration_minutes=duration_minutes,
                    available=True,
                )
            )
            current += timedelta(hours=1)
        
        return slots
    
    async def create_appointment(
        self, patient_name, start_time, duration_minutes,
        patient_email=None, patient_phone=None, appointment_type=None, notes=None
    ):
        """Create mock appointment."""
        appointment_id = f"appt_{self.next_id}"
        self.next_id += 1
        
        appointment = AppointmentDetails(
            external_id=appointment_id,
            patient_name=patient_name,
            patient_email=patient_email,
            patient_phone=patient_phone,
            start_time=start_time,
            end_time=start_time + timedelta(minutes=duration_minutes),
            appointment_type=appointment_type,
            notes=notes,
            status="scheduled",
        )
        
        self.appointments[appointment_id] = appointment
        return appointment
    
    async def cancel_appointment(self, appointment_id):
        """Cancel mock appointment."""
        if appointment_id in self.appointments:
            self.appointments[appointment_id].status = "cancelled"
            return True
        return False
    
    async def get_appointment(self, appointment_id):
        """Get mock appointment."""
        return self.appointments.get(appointment_id)


@pytest.mark.asyncio
async def test_get_available_slots():
    """Test getting available appointment slots."""
    provider = MockCalendarProvider()
    
    start = datetime.now()
    end = start + timedelta(days=7)
    
    slots = await provider.get_available_slots(start, end, duration_minutes=30)
    
    assert len(slots) > 0
    assert all(slot.available for slot in slots)
    assert all(slot.duration_minutes == 30 for slot in slots)


@pytest.mark.asyncio
async def test_create_appointment():
    """Test creating an appointment."""
    provider = MockCalendarProvider()
    
    start_time = datetime.now() + timedelta(days=1, hours=10)
    
    appointment = await provider.create_appointment(
        patient_name="John Doe",
        start_time=start_time,
        duration_minutes=30,
        patient_phone="+15551234567",
        appointment_type="Consultation",
    )
    
    assert appointment.external_id.startswith("appt_")
    assert appointment.patient_name == "John Doe"
    assert appointment.status == "scheduled"
    assert appointment.start_time == start_time


@pytest.mark.asyncio
async def test_cancel_appointment():
    """Test cancelling an appointment."""
    provider = MockCalendarProvider()
    
    # Create appointment
    start_time = datetime.now() + timedelta(days=1)
    appointment = await provider.create_appointment(
        patient_name="Jane Smith",
        start_time=start_time,
        duration_minutes=30,
    )
    
    # Cancel it
    success = await provider.cancel_appointment(appointment.external_id)
    
    assert success == True
    
    # Verify cancelled
    cancelled_appt = await provider.get_appointment(appointment.external_id)
    assert cancelled_appt.status == "cancelled"


@pytest.mark.asyncio
async def test_get_appointment():
    """Test retrieving an appointment."""
    provider = MockCalendarProvider()
    
    # Create appointment
    start_time = datetime.now() + timedelta(days=2)
    created = await provider.create_appointment(
        patient_name="Bob Johnson",
        start_time=start_time,
        duration_minutes=60,
    )
    
    # Retrieve it
    retrieved = await provider.get_appointment(created.external_id)
    
    assert retrieved is not None
    assert retrieved.external_id == created.external_id
    assert retrieved.patient_name == "Bob Johnson"


@pytest.mark.asyncio
async def test_appointment_slot_duration():
    """Test appointment slot durations."""
    provider = MockCalendarProvider()
    
    start = datetime.now()
    end = start + timedelta(days=1)
    
    # Test different durations
    slots_30 = await provider.get_available_slots(start, end, duration_minutes=30)
    slots_60 = await provider.get_available_slots(start, end, duration_minutes=60)
    
    assert all(slot.duration_minutes == 30 for slot in slots_30)
    assert all(slot.duration_minutes == 60 for slot in slots_60)







