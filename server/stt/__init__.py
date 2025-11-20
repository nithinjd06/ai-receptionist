"""Speech-to-Text provider implementations."""
from .base import STTProvider, TranscriptResult, STTError, STTConnectionError, STTTimeoutError
from .deepgram_streaming import DeepgramSTT
from .whisper_batch import WhisperSTT

__all__ = [
    'STTProvider',
    'TranscriptResult',
    'STTError',
    'STTConnectionError',
    'STTTimeoutError',
    'DeepgramSTT',
    'WhisperSTT',
]







