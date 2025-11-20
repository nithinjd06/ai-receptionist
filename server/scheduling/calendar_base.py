"""
Abstract base class for calendar/scheduling providers.
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime
from dataclasses import dataclass


@dataclass
class TimeSlot:
    """Represents an available time slot."""
    start_time: datetime
    end_time: datetime
    duration_minutes: int
    available: bool = True
    

@dataclass
class AppointmentDetails:
    """Represents appointment details."""
    external_id: str
    patient_name: str
    patient_email: Optional[str]
    patient_phone: Optional[str]
    start_time: datetime
    end_time: datetime
    appointment_type: Optional[str]
    notes: Optional[str]
    status: str  # scheduled | confirmed | cancelled


class CalendarProvider(ABC):
    """Abstract base class for calendar providers."""
    
    @abstractmethod
    async def get_available_slots(
        self,
        start_date: datetime,
        end_date: datetime,
        duration_minutes: int = 30,
    ) -> List[TimeSlot]:
        """
        Get available appointment slots.
        
        Args:
            start_date: Start of search range
            end_date: End of search range
            duration_minutes: Appointment duration
            
        Returns:
            List of available time slots
        """
        pass
    
    @abstractmethod
    async def create_appointment(
        self,
        patient_name: str,
        start_time: datetime,
        duration_minutes: int,
        patient_email: Optional[str] = None,
        patient_phone: Optional[str] = None,
        appointment_type: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> AppointmentDetails:
        """
        Create a new appointment.
        
        Args:
            patient_name: Patient's name
            start_time: Appointment start time
            duration_minutes: Duration in minutes
            patient_email: Patient's email
            patient_phone: Patient's phone
            appointment_type: Type of appointment
            notes: Additional notes
            
        Returns:
            Created appointment details
        """
        pass
    
    @abstractmethod
    async def cancel_appointment(self, appointment_id: str) -> bool:
        """
        Cancel an appointment.
        
        Args:
            appointment_id: External appointment ID
            
        Returns:
            True if successful
        """
        pass
    
    @abstractmethod
    async def get_appointment(self, appointment_id: str) -> Optional[AppointmentDetails]:
        """
        Get appointment details.
        
        Args:
            appointment_id: External appointment ID
            
        Returns:
            Appointment details or None
        """
        pass


class CalendarError(Exception):
    """Base exception for calendar errors."""
    pass


class CalendarConnectionError(CalendarError):
    """Raised when calendar connection fails."""
    pass


class CalendarAuthError(CalendarError):
    """Raised when calendar authentication fails."""
    pass







