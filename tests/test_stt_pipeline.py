"""
Tests for STT pipeline and audio processing.
"""
import pytest
import asyncio
from server.audio_codec import AudioCodec, AudioBuffer
from server.stt.base import TranscriptResult


def test_audio_codec_mulaw_decode():
    """Test μ-law audio decoding."""
    codec = AudioCodec(sample_rate=8000, channels=1)
    
    # Create test μ-law audio (base64 encoded)
    import base64
    test_mulaw = base64.b64encode(b'\x00' * 160).decode('utf-8')
    
    # Decode
    pcm = codec.decode_mulaw(test_mulaw)
    
    assert isinstance(pcm, bytes)
    assert len(pcm) > 0


def test_audio_codec_mulaw_encode():
    """Test μ-law audio encoding."""
    codec = AudioCodec(sample_rate=8000, channels=1)
    
    # Create test PCM audio
    test_pcm = b'\x00\x00' * 160
    
    # Encode
    mulaw_b64 = codec.encode_mulaw(test_pcm)
    
    assert isinstance(mulaw_b64, str)
    assert len(mulaw_b64) > 0


def test_audio_buffer_accumulation():
    """Test audio buffer accumulation."""
    buffer = AudioBuffer(target_duration_ms=300)
    
    # Add chunks
    chunk1 = b'\x00\x00' * 800  # 800 samples
    result1 = buffer.add(chunk1)
    
    # Should not return chunk yet (need more data)
    assert result1 is None
    
    # Add more data
    chunk2 = b'\x00\x00' * 800
    result2 = buffer.add(chunk2)
    
    # Should return a complete chunk
    assert result2 is not None
    assert isinstance(result2, bytes)


def test_audio_buffer_flush():
    """Test audio buffer flushing."""
    buffer = AudioBuffer(target_duration_ms=300)
    
    # Add incomplete chunk
    chunk = b'\x00\x00' * 100
    buffer.add(chunk)
    
    # Flush
    flushed = buffer.flush()
    
    assert flushed is not None
    assert len(flushed) == len(chunk)


def test_audio_chunk_duration_calculation():
    """Test audio duration calculation."""
    codec = AudioCodec(sample_rate=8000, channels=1)
    
    # 8000 samples per second, 2 bytes per sample
    # 1 second = 16000 bytes
    one_second_pcm = b'\x00\x00' * 8000
    
    duration = codec.calculate_duration_ms(one_second_pcm)
    
    assert 950 < duration < 1050  # Allow some margin


def test_audio_resampling():
    """Test audio resampling."""
    codec = AudioCodec(sample_rate=8000, channels=1)
    
    # Create test audio
    test_pcm = b'\x00\x00' * 8000  # 1 second at 8kHz
    
    # Resample to 16kHz
    resampled = codec.resample(test_pcm, from_rate=8000, to_rate=16000)
    
    assert isinstance(resampled, bytes)
    # Should be approximately double the length
    assert len(resampled) > len(test_pcm) * 1.5


def test_pcm_to_wav_conversion():
    """Test PCM to WAV conversion."""
    codec = AudioCodec(sample_rate=8000, channels=1)
    
    # Create test PCM
    test_pcm = b'\x00\x00' * 1600  # 0.2 seconds
    
    # Convert to WAV
    wav_data = codec.pcm_to_wav(test_pcm)
    
    assert isinstance(wav_data, bytes)
    assert len(wav_data) > len(test_pcm)  # WAV has header
    
    # Check WAV header (RIFF)
    assert wav_data[:4] == b'RIFF'
    assert wav_data[8:12] == b'WAVE'


class MockSTTProvider:
    """Mock STT provider for testing."""
    
    def __init__(self):
        self.audio_chunks = []
        self.transcripts = [
            TranscriptResult(text="hello", is_final=False, confidence=0.8),
            TranscriptResult(text="hello world", is_final=True, confidence=0.95),
        ]
        self.transcript_index = 0
    
    async def connect(self):
        pass
    
    async def disconnect(self):
        pass
    
    async def send_audio(self, audio_chunk: bytes):
        self.audio_chunks.append(audio_chunk)
    
    async def receive_transcripts(self):
        for transcript in self.transcripts:
            yield transcript
            await asyncio.sleep(0.1)
    
    async def close_stream(self):
        pass


@pytest.mark.asyncio
async def test_stt_streaming_pipeline():
    """Test STT streaming pipeline."""
    provider = MockSTTProvider()
    
    await provider.connect()
    
    # Send audio chunks
    await provider.send_audio(b'\x00\x00' * 1600)
    await provider.send_audio(b'\x00\x00' * 1600)
    
    # Receive transcripts
    transcripts = []
    async for transcript in provider.receive_transcripts():
        transcripts.append(transcript)
    
    await provider.disconnect()
    
    assert len(transcripts) == 2
    assert transcripts[0].is_final == False
    assert transcripts[1].is_final == True
    assert transcripts[1].text == "hello world"







