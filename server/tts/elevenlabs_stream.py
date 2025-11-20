"""
ElevenLabs streaming TTS implementation.
Uses ElevenLabs Turbo v2.5 for low-latency, natural-sounding speech.
"""
import logging
from typing import AsyncIterator, Optional
from elevenlabs import VoiceSettings
from elevenlabs.client import AsyncElevenLabs
from .base import TTSProvider, TTSError, TTSConnectionError

logger = logging.getLogger(__name__)


class ElevenLabsTTS(TTSProvider):
    """ElevenLabs streaming TTS provider."""
    
    def __init__(
        self,
        api_key: str,
        voice_id: str = "21m00Tcm4TlvDq8ikWAM",  # Rachel
        model: str = "eleven_turbo_v2_5",
        stability: float = 0.5,
        similarity_boost: float = 0.75,
        optimize_streaming_latency: int = 3,  # 0-4, higher = lower latency
    ):
        self.api_key = api_key
        self.voice_id = voice_id
        self.model = model
        self.stability = stability
        self.similarity_boost = similarity_boost
        self.optimize_streaming_latency = optimize_streaming_latency
        
        try:
            self.client = AsyncElevenLabs(api_key=api_key)
        except Exception as e:
            raise TTSConnectionError(f"Failed to initialize ElevenLabs client: {e}")
    
    async def synthesize_streaming(self, text: str) -> AsyncIterator[bytes]:
        """
        Stream TTS audio from ElevenLabs.
        
        Args:
            text: Text to synthesize
            
        Yields:
            Audio chunks as bytes (MP3 format from ElevenLabs)
        """
        if not text or not text.strip():
            logger.warning("Empty text provided to TTS")
            return
        
        try:
            # Configure voice settings
            voice_settings = VoiceSettings(
                stability=self.stability,
                similarity_boost=self.similarity_boost,
            )
            
            # Stream audio from ElevenLabs
            audio_stream = await self.client.text_to_speech.convert_as_stream(
                voice_id=self.voice_id,
                text=text,
                model_id=self.model,
                voice_settings=voice_settings,
                optimize_streaming_latency=self.optimize_streaming_latency,
            )
            
            # Yield audio chunks
            async for chunk in audio_stream:
                if chunk:
                    yield chunk
        
        except Exception as e:
            logger.error(f"ElevenLabs streaming error: {e}")
            raise TTSError(f"TTS streaming failed: {e}")
    
    async def synthesize(self, text: str) -> bytes:
        """
        Synthesize complete audio from ElevenLabs (non-streaming).
        
        Args:
            text: Text to synthesize
            
        Returns:
            Complete audio as bytes (MP3 format)
        """
        if not text or not text.strip():
            logger.warning("Empty text provided to TTS")
            return b""
        
        try:
            voice_settings = VoiceSettings(
                stability=self.stability,
                similarity_boost=self.similarity_boost,
            )
            
            # Generate audio
            audio = await self.client.text_to_speech.convert(
                voice_id=self.voice_id,
                text=text,
                model_id=self.model,
                voice_settings=voice_settings,
            )
            
            # Collect all chunks
            audio_bytes = b""
            async for chunk in audio:
                audio_bytes += chunk
            
            return audio_bytes
        
        except Exception as e:
            logger.error(f"ElevenLabs synthesis error: {e}")
            raise TTSError(f"TTS synthesis failed: {e}")
    
    async def get_available_voices(self) -> list:
        """Get list of available voices from ElevenLabs."""
        try:
            voices = await self.client.voices.get_all()
            return voices.voices
        except Exception as e:
            logger.error(f"Error fetching voices: {e}")
            return []







