"""
Whisper batch STT implementation (alternative to Deepgram).
Uses OpenAI Whisper API or local Whisper model.
Note: This is batch-based, so higher latency than streaming Deepgram.
"""
import asyncio
import logging
from typing import AsyncIterator, Optional
import io
from .base import STTProvider, TranscriptResult, STTError

logger = logging.getLogger(__name__)


class WhisperSTT(STTProvider):
    """Whisper batch STT provider."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "whisper-1",
        language: str = "en",
        use_api: bool = True,
    ):
        self.api_key = api_key
        self.model = model
        self.language = language
        self.use_api = use_api
        
        self.audio_buffer = bytearray()
        self.transcript_queue: asyncio.Queue[TranscriptResult] = asyncio.Queue()
        self._processing = False
        
        # Import OpenAI or local Whisper based on configuration
        if use_api:
            try:
                from openai import AsyncOpenAI
                self.client = AsyncOpenAI(api_key=api_key)
            except ImportError:
                raise STTError("OpenAI package not installed. Install with: pip install openai")
        else:
            try:
                import whisper
                self.whisper_model = whisper.load_model(model)
            except ImportError:
                raise STTError("Whisper package not installed. Install with: pip install openai-whisper")
    
    async def connect(self) -> None:
        """No persistent connection needed for batch processing."""
        logger.info("Whisper STT initialized (batch mode)")
    
    async def disconnect(self) -> None:
        """No connection to close for batch processing."""
        self._processing = False
    
    async def send_audio(self, audio_chunk: bytes) -> None:
        """
        Buffer audio chunks. Process in batches when threshold reached.
        
        Args:
            audio_chunk: Raw PCM audio data
        """
        self.audio_buffer.extend(audio_chunk)
        
        # Process every ~2 seconds of audio (16000 samples * 2 bytes at 8kHz)
        threshold = 16000 * 2
        if len(self.audio_buffer) >= threshold and not self._processing:
            # Process buffered audio
            asyncio.create_task(self._process_buffer())
    
    async def receive_transcripts(self) -> AsyncIterator[TranscriptResult]:
        """Receive transcript results."""
        while True:
            try:
                transcript = await asyncio.wait_for(
                    self.transcript_queue.get(),
                    timeout=10.0
                )
                yield transcript
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error receiving transcript: {e}")
                break
    
    async def close_stream(self) -> None:
        """Process any remaining buffered audio."""
        if len(self.audio_buffer) > 0:
            await self._process_buffer()
        self._processing = False
    
    async def _process_buffer(self) -> None:
        """Process buffered audio through Whisper."""
        if self._processing:
            return
        
        self._processing = True
        
        try:
            # Get buffered audio
            audio_data = bytes(self.audio_buffer)
            self.audio_buffer.clear()
            
            # Transcribe
            if self.use_api:
                text = await self._transcribe_api(audio_data)
            else:
                text = await self._transcribe_local(audio_data)
            
            if text:
                # Create transcript result (Whisper only returns final results)
                result = TranscriptResult(
                    text=text.strip(),
                    is_final=True,
                    confidence=1.0,
                    language=self.language
                )
                
                await self.transcript_queue.put(result)
        
        except Exception as e:
            logger.error(f"Error processing Whisper transcription: {e}")
        
        finally:
            self._processing = False
    
    async def _transcribe_api(self, audio_data: bytes) -> str:
        """Transcribe using OpenAI Whisper API."""
        try:
            # Convert PCM to WAV format
            import wave
            wav_buffer = io.BytesIO()
            with wave.open(wav_buffer, 'wb') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(8000)
                wav_file.writeframes(audio_data)
            
            wav_buffer.seek(0)
            wav_buffer.name = "audio.wav"
            
            # Call Whisper API
            response = await self.client.audio.transcriptions.create(
                model=self.model,
                file=wav_buffer,
                language=self.language
            )
            
            return response.text
        
        except Exception as e:
            logger.error(f"Whisper API error: {e}")
            return ""
    
    async def _transcribe_local(self, audio_data: bytes) -> str:
        """Transcribe using local Whisper model."""
        try:
            import numpy as np
            
            # Convert bytes to numpy array
            audio_np = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
            
            # Transcribe (run in thread pool to avoid blocking)
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: self.whisper_model.transcribe(audio_np, language=self.language)
            )
            
            return result.get("text", "")
        
        except Exception as e:
            logger.error(f"Local Whisper error: {e}")
            return ""







