"""
Abstract base class for Speech-to-Text providers.
Enables swapping between Deepgram, Whisper, etc.
"""
from abc import ABC, abstractmethod
from typing import AsyncIterator, Optional
from dataclasses import dataclass


@dataclass
class TranscriptResult:
    """Represents a transcript result from STT."""
    text: str
    is_final: bool
    confidence: Optional[float] = None
    language: Optional[str] = None


class STTProvider(ABC):
    """Abstract base class for STT providers."""
    
    @abstractmethod
    async def connect(self) -> None:
        """Establish connection to STT service (if needed)."""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Close connection to STT service."""
        pass
    
    @abstractmethod
    async def send_audio(self, audio_chunk: bytes) -> None:
        """
        Send audio chunk to STT service for processing.
        
        Args:
            audio_chunk: Raw PCM audio data
        """
        pass
    
    @abstractmethod
    async def receive_transcripts(self) -> AsyncIterator[TranscriptResult]:
        """
        Receive transcript results from STT service.
        
        Yields:
            TranscriptResult objects (partial and final)
        """
        pass
    
    @abstractmethod
    async def close_stream(self) -> None:
        """Signal end of audio stream."""
        pass


class STTError(Exception):
    """Base exception for STT errors."""
    pass


class STTConnectionError(STTError):
    """Raised when STT connection fails."""
    pass


class STTTimeoutError(STTError):
    """Raised when STT operation times out."""
    pass







