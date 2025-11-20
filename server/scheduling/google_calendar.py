"""
Google Calendar integration for appointment scheduling.
Uses OAuth2 for authentication.
"""
import logging
from typing import List, Optional
from datetime import datetime, timedelta
import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from .calendar_base import (
    CalendarProvider,
    TimeSlot,
    AppointmentDetails,
    CalendarError,
    CalendarConnectionError,
    CalendarAuthError,
)

logger = logging.getLogger(__name__)

# Google Calendar API scope
SCOPES = ['https://www.googleapis.com/auth/calendar']


class GoogleCalendarProvider(CalendarProvider):
    """Google Calendar provider implementation."""
    
    def __init__(
        self,
        credentials_file: str = "credentials.json",
        token_file: str = "token.json",
        calendar_id: str = "primary",
        timezone: str = "America/Chicago",
    ):
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.calendar_id = calendar_id
        self.timezone = timezone
        
        self.service = None
        self._credentials = None
    
    async def _authenticate(self) -> None:
        """Authenticate with Google Calendar API."""
        try:
            creds = None
            
            # Load existing token
            if os.path.exists(self.token_file):
                creds = Credentials.from_authorized_user_file(self.token_file, SCOPES)
            
            # Refresh or get new credentials
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    if not os.path.exists(self.credentials_file):
                        raise CalendarAuthError(f"Credentials file not found: {self.credentials_file}")
                    
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_file, SCOPES
                    )
                    creds = flow.run_local_server(port=0)
                
                # Save credentials
                with open(self.token_file, 'w') as token:
                    token.write(creds.to_json())
            
            self._credentials = creds
            self.service = build('calendar', 'v3', credentials=creds)
            logger.info("Google Calendar authentication successful")
        
        except Exception as e:
            logger.error(f"Google Calendar authentication error: {e}")
            raise CalendarAuthError(f"Authentication failed: {e}")
    
    async def get_available_slots(
        self,
        start_date: datetime,
        end_date: datetime,
        duration_minutes: int = 30,
    ) -> List[TimeSlot]:
        """
        Get available appointment slots from Google Calendar.
        
        Args:
            start_date: Start of search range
            end_date: End of search range
            duration_minutes: Appointment duration
            
        Returns:
            List of available time slots
        """
        if not self.service:
            await self._authenticate()
        
        try:
            # Get busy times from calendar
            body = {
                "timeMin": start_date.isoformat() + 'Z',
                "timeMax": end_date.isoformat() + 'Z',
                "timeZone": self.timezone,
                "items": [{"id": self.calendar_id}]
            }
            
            events_result = self.service.freebusy().query(body=body).execute()
            busy_times = events_result['calendars'][self.calendar_id].get('busy', [])
            
            # Generate potential slots (e.g., 9 AM - 5 PM, hourly)
            available_slots = []
            current = start_date.replace(hour=9, minute=0, second=0, microsecond=0)
            end_of_day = start_date.replace(hour=17, minute=0, second=0, microsecond=0)
            
            while current < end_date:
                if current.hour >= 9 and current.hour < 17:  # Business hours
                    slot_end = current + timedelta(minutes=duration_minutes)
                    
                    # Check if slot overlaps with busy times
                    is_available = True
                    for busy in busy_times:
                        busy_start = datetime.fromisoformat(busy['start'].replace('Z', '+00:00'))
                        busy_end = datetime.fromisoformat(busy['end'].replace('Z', '+00:00'))
                        
                        if (current < busy_end and slot_end > busy_start):
                            is_available = False
                            break
                    
                    if is_available:
                        available_slots.append(
                            TimeSlot(
                                start_time=current,
                                end_time=slot_end,
                                duration_minutes=duration_minutes,
                                available=True,
                            )
                        )
                
                # Move to next 30-minute slot
                current += timedelta(minutes=30)
                
                # Skip to next day if past business hours
                if current.hour >= 17:
                    current = (current + timedelta(days=1)).replace(hour=9, minute=0)
            
            logger.info(f"Found {len(available_slots)} available slots")
            return available_slots[:10]  # Return first 10 slots
        
        except HttpError as e:
            logger.error(f"Google Calendar API error: {e}")
            raise CalendarError(f"Failed to get available slots: {e}")
    
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
        Create a new appointment in Google Calendar.
        
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
        if not self.service:
            await self._authenticate()
        
        try:
            end_time = start_time + timedelta(minutes=duration_minutes)
            
            # Build event description
            description = f"Patient: {patient_name}\n"
            if patient_phone:
                description += f"Phone: {patient_phone}\n"
            if appointment_type:
                description += f"Type: {appointment_type}\n"
            if notes:
                description += f"Notes: {notes}\n"
            
            # Create event
            event = {
                'summary': f"Appointment - {patient_name}",
                'description': description,
                'start': {
                    'dateTime': start_time.isoformat(),
                    'timeZone': self.timezone,
                },
                'end': {
                    'dateTime': end_time.isoformat(),
                    'timeZone': self.timezone,
                },
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'email', 'minutes': 24 * 60},  # 1 day before
                        {'method': 'popup', 'minutes': 60},  # 1 hour before
                    ],
                },
            }
            
            # Add attendee if email provided
            if patient_email:
                event['attendees'] = [{'email': patient_email}]
            
            # Insert event
            created_event = self.service.events().insert(
                calendarId=self.calendar_id,
                body=event
            ).execute()
            
            logger.info(f"Created appointment: {created_event['id']}")
            
            return AppointmentDetails(
                external_id=created_event['id'],
                patient_name=patient_name,
                patient_email=patient_email,
                patient_phone=patient_phone,
                start_time=start_time,
                end_time=end_time,
                appointment_type=appointment_type,
                notes=notes,
                status="scheduled",
            )
        
        except HttpError as e:
            logger.error(f"Google Calendar create error: {e}")
            raise CalendarError(f"Failed to create appointment: {e}")
    
    async def cancel_appointment(self, appointment_id: str) -> bool:
        """Cancel an appointment."""
        if not self.service:
            await self._authenticate()
        
        try:
            self.service.events().delete(
                calendarId=self.calendar_id,
                eventId=appointment_id
            ).execute()
            
            logger.info(f"Cancelled appointment: {appointment_id}")
            return True
        
        except HttpError as e:
            logger.error(f"Google Calendar cancel error: {e}")
            return False
    
    async def get_appointment(self, appointment_id: str) -> Optional[AppointmentDetails]:
        """Get appointment details."""
        if not self.service:
            await self._authenticate()
        
        try:
            event = self.service.events().get(
                calendarId=self.calendar_id,
                eventId=appointment_id
            ).execute()
            
            start_time = datetime.fromisoformat(event['start']['dateTime'])
            end_time = datetime.fromisoformat(event['end']['dateTime'])
            
            return AppointmentDetails(
                external_id=event['id'],
                patient_name=event.get('summary', '').replace('Appointment - ', ''),
                patient_email=None,
                patient_phone=None,
                start_time=start_time,
                end_time=end_time,
                appointment_type=None,
                notes=event.get('description'),
                status=event.get('status', 'scheduled'),
            )
        
        except HttpError as e:
            logger.error(f"Google Calendar get error: {e}")
            return None







