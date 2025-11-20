"""
Audio codec utilities for handling Twilio Media Streams.
Twilio sends audio as base64-encoded μ-law (G.711) at 8kHz mono.
"""
import base64
import audioop
import io
import wave
from typing import Optional


class AudioCodec:
    """Handle audio encoding/decoding for Twilio Media Streams."""
    
    def __init__(self, sample_rate: int = 8000, channels: int = 1):
        self.sample_rate = sample_rate
        self.channels = channels
        self.frame_size = 160  # 20ms at 8kHz
    
    def decode_mulaw(self, base64_audio: str) -> bytes:
        """
        Decode base64 μ-law audio to linear PCM.
        
        Args:
            base64_audio: Base64-encoded μ-law audio from Twilio
            
        Returns:
            Linear PCM audio as bytes (16-bit signed)
        """
        try:
            mulaw_data = base64.b64decode(base64_audio)
            # Convert μ-law to linear PCM (16-bit)
            pcm_data = audioop.ulaw2lin(mulaw_data, 2)  # 2 = 16-bit samples
            return pcm_data
        except Exception as e:
            raise ValueError(f"Failed to decode μ-law audio: {e}")
    
    def encode_mulaw(self, pcm_data: bytes) -> str:
        """
        Encode linear PCM to base64 μ-law for Twilio.
        
        Args:
            pcm_data: Linear PCM audio (16-bit signed)
            
        Returns:
            Base64-encoded μ-law audio string
        """
        try:
            # Convert linear PCM to μ-law
            mulaw_data = audioop.lin2ulaw(pcm_data, 2)  # 2 = 16-bit samples
            # Encode to base64
            return base64.b64encode(mulaw_data).decode('utf-8')
        except Exception as e:
            raise ValueError(f"Failed to encode μ-law audio: {e}")
    
    def pcm_to_wav(self, pcm_data: bytes, sample_rate: Optional[int] = None) -> bytes:
        """
        Convert raw PCM to WAV format for STT services.
        
        Args:
            pcm_data: Raw PCM audio data
            sample_rate: Sample rate (defaults to self.sample_rate)
            
        Returns:
            WAV file as bytes
        """
        if sample_rate is None:
            sample_rate = self.sample_rate
        
        buffer = io.BytesIO()
        with wave.open(buffer, 'wb') as wav_file:
            wav_file.setnchannels(self.channels)
            wav_file.setsampwidth(2)  # 16-bit = 2 bytes
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(pcm_data)
        
        return buffer.getvalue()
    
    def resample(self, pcm_data: bytes, from_rate: int, to_rate: int) -> bytes:
        """
        Resample PCM audio from one rate to another.
        
        Args:
            pcm_data: Raw PCM audio data
            from_rate: Source sample rate
            to_rate: Target sample rate
            
        Returns:
            Resampled PCM data
        """
        if from_rate == to_rate:
            return pcm_data
        
        try:
            # audioop.ratecv: (fragment, width, nchannels, inrate, outrate, state)
            resampled, _ = audioop.ratecv(pcm_data, 2, self.channels, from_rate, to_rate, None)
            return resampled
        except Exception as e:
            raise ValueError(f"Failed to resample audio: {e}")
    
    def chunk_audio(self, audio_data: bytes, chunk_duration_ms: int) -> list[bytes]:
        """
        Split audio into fixed-duration chunks.
        
        Args:
            audio_data: Raw PCM audio data
            chunk_duration_ms: Chunk duration in milliseconds
            
        Returns:
            List of audio chunks
        """
        # Calculate chunk size in bytes
        # bytes_per_sample = 2 (16-bit)
        # samples_per_ms = sample_rate / 1000
        bytes_per_ms = (self.sample_rate // 1000) * 2 * self.channels
        chunk_size = bytes_per_ms * chunk_duration_ms
        
        chunks = []
        for i in range(0, len(audio_data), chunk_size):
            chunk = audio_data[i:i + chunk_size]
            if len(chunk) == chunk_size:  # Only include full chunks
                chunks.append(chunk)
        
        return chunks
    
    def calculate_duration_ms(self, pcm_data: bytes) -> float:
        """
        Calculate the duration of PCM audio in milliseconds.
        
        Args:
            pcm_data: Raw PCM audio data
            
        Returns:
            Duration in milliseconds
        """
        num_samples = len(pcm_data) // (2 * self.channels)  # 2 bytes per sample
        duration_s = num_samples / self.sample_rate
        return duration_s * 1000


class AudioBuffer:
    """Circular buffer for collecting audio chunks before processing."""
    
    def __init__(self, target_duration_ms: int = 300):
        self.target_duration_ms = target_duration_ms
        self.buffer = bytearray()
        self.sample_rate = 8000
        self.bytes_per_ms = (self.sample_rate // 1000) * 2  # 16-bit mono
        self.target_bytes = self.bytes_per_ms * target_duration_ms
    
    def add(self, audio_chunk: bytes) -> Optional[bytes]:
        """
        Add audio chunk to buffer. Returns complete chunk when ready.
        
        Args:
            audio_chunk: PCM audio chunk to add
            
        Returns:
            Complete audio chunk if buffer is full, None otherwise
        """
        self.buffer.extend(audio_chunk)
        
        if len(self.buffer) >= self.target_bytes:
            # Extract a complete chunk
            chunk = bytes(self.buffer[:self.target_bytes])
            # Keep remainder in buffer
            self.buffer = self.buffer[self.target_bytes:]
            return chunk
        
        return None
    
    def flush(self) -> Optional[bytes]:
        """
        Flush remaining buffer contents.
        
        Returns:
            Remaining audio data, or None if empty
        """
        if len(self.buffer) > 0:
            chunk = bytes(self.buffer)
            self.buffer.clear()
            return chunk
        return None
    
    def clear(self):
        """Clear the buffer."""
        self.buffer.clear()







