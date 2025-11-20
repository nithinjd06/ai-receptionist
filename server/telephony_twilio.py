"""
Twilio Programmable Voice integration with Media Streams.
Handles incoming calls and bidirectional WebSocket audio streaming.
"""
import asyncio
import json
import logging
import base64
from typing import Optional, Dict
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect
from twilio.twiml.voice_response import VoiceResponse, Start, Stream
from twilio.request_validator import RequestValidator
from sqlmodel.ext.asyncio.session import AsyncSession

from .audio_codec import AudioCodec, AudioBuffer
from .stt.base import STTProvider, TranscriptResult
from .tts.base import TTSProvider
from .convo.router import ConversationRouter
from .convo.schema import ConversationContext
from .db.models import Call
from .db.repo import CallRepository, AuditLogRepository
from .config import settings
from .utils import generate_id, sanitize_phone, mask_phone

logger = logging.getLogger(__name__)


class TwilioCallHandler:
    """
    Handles a single Twilio call with bidirectional audio streaming.
    
    Key responsibilities:
    - Manage WebSocket connection with Twilio Media Streams
    - Route audio to STT provider
    - Process transcripts through conversation router
    - Generate TTS responses
    - Send audio back to Twilio
    - Handle barge-in (user interruption)
    """
    
    def __init__(
        self,
        websocket: WebSocket,
        session: AsyncSession,
        stt_provider: STTProvider,
        tts_provider: TTSProvider,
        conversation_router: ConversationRouter,
    ):
        self.ws = websocket
        self.session = session
        self.stt = stt_provider
        self.tts = tts_provider
        self.router = conversation_router
        
        # Call state
        self.call_sid: Optional[str] = None
        self.stream_sid: Optional[str] = None
        self.call_id: Optional[int] = None
        self.context: Optional[ConversationContext] = None
        
        # Audio processing
        self.codec = AudioCodec(sample_rate=8000, channels=1)
        self.audio_buffer = AudioBuffer(target_duration_ms=settings.AUDIO_CHUNK_DURATION_MS)
        
        # State management
        self.is_playing_audio = False
        self.should_stop_playback = False
        self._tasks: list[asyncio.Task] = []
        
        logger.info("TwilioCallHandler initialized")
    
    async def handle_call(self) -> None:
        """
        Main call handling loop.
        Manages WebSocket connection and coordinates audio processing.
        """
        try:
            # Accept WebSocket connection
            await self.ws.accept()
            logger.info("WebSocket connection accepted")
            
            # Start STT connection
            await self.stt.connect()
            
            # Start background tasks
            transcript_task = asyncio.create_task(self._process_transcripts())
            self._tasks.append(transcript_task)
            
            # Main WebSocket message loop
            await self._handle_websocket_messages()
        
        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected for call {self.call_sid}")
        
        except Exception as e:
            logger.error(f"Error handling call: {e}", exc_info=True)
            
            if self.call_id:
                await AuditLogRepository.log_event(
                    self.session,
                    event_type="call_error",
                    event_data={"error": str(e)},
                    call_id=self.call_id,
                    severity="error",
                )
        
        finally:
            await self._cleanup()
    
    async def _handle_websocket_messages(self) -> None:
        """Process incoming WebSocket messages from Twilio."""
        try:
            async for message in self.ws.iter_text():
                data = json.loads(message)
                event_type = data.get("event")
                
                if event_type == "start":
                    await self._handle_start(data)
                
                elif event_type == "media":
                    await self._handle_media(data)
                
                elif event_type == "mark":
                    await self._handle_mark(data)
                
                elif event_type == "stop":
                    await self._handle_stop(data)
                
                else:
                    logger.debug(f"Unhandled event type: {event_type}")
        
        except WebSocketDisconnect:
            logger.info("WebSocket disconnected")
        
        except Exception as e:
            logger.error(f"Error in WebSocket message loop: {e}")
    
    async def _handle_start(self, data: dict) -> None:
        """
        Handle 'start' event from Twilio.
        Initialize call record and conversation context.
        """
        try:
            start_data = data.get("start", {})
            self.stream_sid = data.get("streamSid")
            self.call_sid = start_data.get("callSid")
            
            # Extract caller information
            custom_params = start_data.get("customParameters", {})
            caller_phone = custom_params.get("From", "unknown")
            
            logger.info(f"Call started: {self.call_sid} from {mask_phone(caller_phone)}")
            
            # Create call record in database
            call = Call(
                call_sid=self.call_sid,
                tenant_id="default",
                caller_phone=sanitize_phone(caller_phone),
                started_at=datetime.utcnow(),
            )
            call = await CallRepository.create(self.session, call)
            self.call_id = call.id
            
            # Initialize conversation context
            self.context = ConversationContext(
                call_id=call.id,
                call_sid=self.call_sid,
                caller_phone=caller_phone,
                tenant_id="default",
                turn_number=0,
                started_at=datetime.utcnow(),
            )
            
            # Log start event
            await AuditLogRepository.log_event(
                self.session,
                event_type="call_started",
                event_data={"call_sid": self.call_sid, "stream_sid": self.stream_sid},
                call_id=self.call_id,
                severity="info",
            )
            
            # Send greeting
            await self._speak("Hello! Thank you for calling. How may I help you today?")
        
        except Exception as e:
            logger.error(f"Error handling start event: {e}")
    
    async def _handle_media(self, data: dict) -> None:
        """
        Handle 'media' event from Twilio.
        Process incoming audio and send to STT.
        """
        try:
            media = data.get("media", {})
            payload = media.get("payload")
            
            if not payload:
                return
            
            # Decode μ-law audio to PCM
            pcm_audio = self.codec.decode_mulaw(payload)
            
            # Add to buffer and check if we have a complete chunk
            chunk = self.audio_buffer.add(pcm_audio)
            
            if chunk:
                # Detect if user is speaking (simple voice activity)
                # If we're playing audio and user starts speaking, stop playback (barge-in)
                if self.is_playing_audio and settings.BARGE_IN_ENABLED:
                    await self._handle_barge_in()
                
                # Send audio chunk to STT
                await self.stt.send_audio(chunk)
        
        except Exception as e:
            logger.error(f"Error handling media: {e}")
    
    async def _handle_mark(self, data: dict) -> None:
        """Handle 'mark' event from Twilio (used for audio playback synchronization)."""
        mark_name = data.get("mark", {}).get("name")
        logger.debug(f"Mark received: {mark_name}")
        
        if mark_name == "end_of_speech":
            self.is_playing_audio = False
    
    async def _handle_stop(self, data: dict) -> None:
        """Handle 'stop' event from Twilio (call ended)."""
        logger.info(f"Call stopped: {self.call_sid}")
        
        if self.call_id:
            # Update call record
            await CallRepository.update_end(
                self.session,
                self.call_id,
                outcome="completed",
                summary=None,  # Summary generated separately
            )
            
            # Generate call summary
            if self.context:
                summary = await self.router.generate_call_summary(self.context)
                logger.info(f"Call summary: {summary.summary_text}")
                
                # Update call with summary
                call = await CallRepository.get_by_id(self.session, self.call_id)
                if call:
                    call.summary = summary.summary_text
                    await self.session.commit()
    
    async def _process_transcripts(self) -> None:
        """
        Background task to process STT transcripts.
        Sends final transcripts to conversation router for response generation.
        """
        try:
            async for transcript in self.stt.receive_transcripts():
                if transcript.is_final and transcript.text:
                    logger.info(f"Final transcript: {transcript.text}")
                    
                    # Process through conversation router
                    await self._handle_user_utterance(transcript.text)
                
                else:
                    # Partial transcript (for debugging)
                    logger.debug(f"Partial transcript: {transcript.text}")
        
        except Exception as e:
            logger.error(f"Error processing transcripts: {e}")
    
    async def _handle_user_utterance(self, text: str) -> None:
        """
        Process user utterance through conversation router and generate response.
        
        Args:
            text: User's speech text from STT
        """
        try:
            if not self.context:
                logger.error("No conversation context available")
                return
            
            # Process turn through conversation router
            turn = await self.router.process_turn(self.context, text)
            
            logger.info(
                f"Turn {turn.turn_no}: action={turn.action}, "
                f"latency={turn.latency_ms}ms"
            )
            
            # Speak the assistant's response
            await self._speak(turn.assistant_text)
        
        except Exception as e:
            logger.error(f"Error handling user utterance: {e}")
            await self._speak("I apologize, I didn't catch that. Could you please repeat?")
    
    async def _speak(self, text: str) -> None:
        """
        Convert text to speech and stream to Twilio.
        
        Args:
            text: Text to speak
        """
        try:
            logger.info(f"Speaking: {text}")
            
            self.is_playing_audio = True
            self.should_stop_playback = False
            
            # Stream TTS audio
            async for audio_chunk in self.tts.synthesize_streaming(text):
                if self.should_stop_playback:
                    logger.info("Playback stopped (barge-in)")
                    break
                
                # Note: ElevenLabs returns MP3, but Twilio expects μ-law PCM
                # For production, you'd convert MP3 -> PCM -> μ-law
                # For now, we'll send raw audio (this is simplified)
                
                # Encode audio for Twilio
                try:
                    # Simplified: assume audio_chunk is PCM
                    mulaw_b64 = self.codec.encode_mulaw(audio_chunk)
                    
                    # Send to Twilio via WebSocket
                    message = {
                        "event": "media",
                        "streamSid": self.stream_sid,
                        "media": {
                            "payload": mulaw_b64
                        }
                    }
                    await self.ws.send_json(message)
                
                except Exception as e:
                    logger.error(f"Error sending audio chunk: {e}")
            
            # Send mark to know when audio finishes
            mark_message = {
                "event": "mark",
                "streamSid": self.stream_sid,
                "mark": {
                    "name": "end_of_speech"
                }
            }
            await self.ws.send_json(mark_message)
            
            self.is_playing_audio = False
        
        except Exception as e:
            logger.error(f"Error in speak: {e}")
            self.is_playing_audio = False
    
    async def _handle_barge_in(self) -> None:
        """
        Handle barge-in (user interrupting while assistant is speaking).
        Stops current audio playback.
        """
        logger.info("Barge-in detected, stopping playback")
        self.should_stop_playback = True
        self.is_playing_audio = False
        
        # Send clear message to Twilio to stop audio
        clear_message = {
            "event": "clear",
            "streamSid": self.stream_sid,
        }
        await self.ws.send_json(clear_message)
    
    async def _cleanup(self) -> None:
        """Clean up resources."""
        logger.info("Cleaning up call handler")
        
        # Cancel background tasks
        for task in self._tasks:
            task.cancel()
        
        # Close STT connection
        try:
            await self.stt.disconnect()
        except Exception as e:
            logger.error(f"Error disconnecting STT: {e}")
        
        # Close WebSocket
        try:
            await self.ws.close()
        except Exception:
            pass


def generate_twiml_response(public_url: str, call_sid: str, from_number: str) -> str:
    """
    Generate TwiML response for incoming call.
    
    Args:
        public_url: Public URL for WebSocket connection
        call_sid: Twilio call SID
        from_number: Caller's phone number
        
    Returns:
        TwiML XML string
    """
    response = VoiceResponse()
    
    # Start bidirectional media stream
    start = Start()
    stream = Stream(
        url=f"wss://{public_url}/voice/stream",
        track="both_tracks",  # Bidirectional audio
    )
    
    # Pass call metadata to WebSocket
    stream.parameter(name="CallSid", value=call_sid)
    stream.parameter(name="From", value=from_number)
    
    start.append(stream)
    response.append(start)
    
    # Keep call alive
    response.pause(length=60)
    
    return str(response)


def verify_twilio_signature(
    url: str,
    post_data: dict,
    signature: str,
    auth_token: str,
) -> bool:
    """
    Verify Twilio request signature.
    
    Args:
        url: Full URL of the request
        post_data: POST data dictionary
        signature: X-Twilio-Signature header
        auth_token: Twilio auth token
        
    Returns:
        True if signature is valid
    """
    validator = RequestValidator(auth_token)
    return validator.validate(url, post_data, signature)







