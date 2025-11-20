"""
Deepgram streaming STT implementation.
Uses Deepgram Nova 2 for low-latency, high-accuracy transcription.
"""
import asyncio
import json
import logging
from typing import AsyncIterator, Optional
from deepgram import (
    DeepgramClient,
    DeepgramClientOptions,
    LiveTranscriptionEvents,
    LiveOptions,
)
from .base import STTProvider, TranscriptResult, STTConnectionError, STTTimeoutError

logger = logging.getLogger(__name__)


class DeepgramSTT(STTProvider):
    """Deepgram streaming STT provider."""
    
    def __init__(
        self,
        api_key: str,
        model: str = "nova-2",
        language: str = "en-US",
        sample_rate: int = 8000,
        channels: int = 1,
        encoding: str = "linear16",
        interim_results: bool = True,
    ):
        self.api_key = api_key
        self.model = model
        self.language = language
        self.sample_rate = sample_rate
        self.channels = channels
        self.encoding = encoding
        self.interim_results = interim_results
        
        self.client: Optional[DeepgramClient] = None
        self.connection = None
        self.transcript_queue: asyncio.Queue[TranscriptResult] = asyncio.Queue()
        self._connected = False
    
    async def connect(self) -> None:
        """Establish WebSocket connection to Deepgram."""
        try:
            # Initialize Deepgram client
            config = DeepgramClientOptions(
                options={"keepalive": "true"}
            )
            self.client = DeepgramClient(self.api_key, config)
            
            # Create live transcription connection
            self.connection = self.client.listen.asyncwebsocket.v("1")
            
            # Register event handlers
            self.connection.on(LiveTranscriptionEvents.Transcript, self._on_transcript)
            self.connection.on(LiveTranscriptionEvents.Error, self._on_error)
            
            # Configure live options
            options = LiveOptions(
                model=self.model,
                language=self.language,
                sample_rate=self.sample_rate,
                channels=self.channels,
                encoding=self.encoding,
                interim_results=self.interim_results,
                punctuate=True,
                smart_format=True,
                utterance_end_ms="1000",  # 1 second silence detection
                vad_events=True,
            )
            
            # Start connection
            if await self.connection.start(options):
                self._connected = True
                logger.info("Deepgram connection established")
            else:
                raise STTConnectionError("Failed to start Deepgram connection")
                
        except Exception as e:
            logger.error(f"Failed to connect to Deepgram: {e}")
            raise STTConnectionError(f"Deepgram connection failed: {e}")
    
    async def disconnect(self) -> None:
        """Close Deepgram connection."""
        if self.connection and self._connected:
            try:
                await self.connection.finish()
                self._connected = False
                logger.info("Deepgram connection closed")
            except Exception as e:
                logger.error(f"Error closing Deepgram connection: {e}")
    
    async def send_audio(self, audio_chunk: bytes) -> None:
        """Send audio chunk to Deepgram."""
        if not self._connected or not self.connection:
            raise STTConnectionError("Not connected to Deepgram")
        
        try:
            await self.connection.send(audio_chunk)
        except Exception as e:
            logger.error(f"Error sending audio to Deepgram: {e}")
            raise
    
    async def receive_transcripts(self) -> AsyncIterator[TranscriptResult]:
        """Receive transcripts from Deepgram."""
        while True:
            try:
                # Wait for transcript with timeout
                transcript = await asyncio.wait_for(
                    self.transcript_queue.get(),
                    timeout=10.0
                )
                yield transcript
            except asyncio.TimeoutError:
                # No transcript received, continue waiting
                continue
            except Exception as e:
                logger.error(f"Error receiving transcript: {e}")
                break
    
    async def close_stream(self) -> None:
        """Signal end of audio stream to Deepgram."""
        await self.disconnect()
    
    def _on_transcript(self, *args, **kwargs) -> None:
        """Handle transcript event from Deepgram."""
        try:
            # Extract result from args
            result = kwargs.get("result") or (args[1] if len(args) > 1 else args[0])
            
            # Parse transcript
            if hasattr(result, 'channel'):
                channel = result.channel
                alternatives = channel.alternatives
                
                if alternatives and len(alternatives) > 0:
                    alternative = alternatives[0]
                    text = alternative.transcript.strip()
                    
                    if text:  # Only process non-empty transcripts
                        is_final = result.is_final if hasattr(result, 'is_final') else False
                        confidence = alternative.confidence if hasattr(alternative, 'confidence') else None
                        
                        transcript_result = TranscriptResult(
                            text=text,
                            is_final=is_final,
                            confidence=confidence,
                            language=self.language
                        )
                        
                        # Add to queue (non-blocking)
                        try:
                            self.transcript_queue.put_nowait(transcript_result)
                        except asyncio.QueueFull:
                            logger.warning("Transcript queue full, dropping result")
        
        except Exception as e:
            logger.error(f"Error processing transcript: {e}")
    
    def _on_error(self, *args, **kwargs) -> None:
        """Handle error event from Deepgram."""
        error = kwargs.get("error") or (args[1] if len(args) > 1 else args[0])
        logger.error(f"Deepgram error: {error}")







