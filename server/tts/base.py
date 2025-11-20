"""
Abstract base class for Text-to-Speech providers.
Enables swapping between ElevenLabs, Azure, etc.
"""
from abc import ABC, abstractmethod
from typing import AsyncIterator


class TTSProvider(ABC):
    """Abstract base class for TTS providers."""
    
    @abstractmethod
    async def synthesize_streaming(self, text: str) -> AsyncIterator[bytes]:
        """
        Synthesize text to speech with streaming output.
        
        Args:
            text: Text to synthesize
            
        Yields:
            Audio chunks as bytes (PCM format)
        """
        pass
    
    @abstractmethod
    async def synthesize(self, text: str) -> bytes:
        """
        Synthesize text to speech (full audio at once).
        
        Args:
            text: Text to synthesize
            
        Returns:
            Complete audio as bytes (PCM format)
        """
        pass


class TTSError(Exception):
    """Base exception for TTS errors."""
    pass


class TTSConnectionError(TTSError):
    """Raised when TTS connection fails."""
    pass


class TTSTimeoutError(TTSError):
    """Raised when TTS operation times out."""
    pass







