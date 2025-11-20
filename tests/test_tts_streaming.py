"""
Tests for TTS streaming.
"""
import pytest
from server.tts.base import TTSProvider


class MockTTSProvider(TTSProvider):
    """Mock TTS provider for testing."""
    
    async def synthesize_streaming(self, text: str):
        """Yield fake audio chunks."""
        # Simulate streaming by yielding chunks
        chunk_size = 1024
        total_chunks = 5
        
        for i in range(total_chunks):
            yield b'\x00' * chunk_size
    
    async def synthesize(self, text: str) -> bytes:
        """Return complete audio."""
        return b'\x00' * 5120


@pytest.mark.asyncio
async def test_tts_streaming():
    """Test TTS streaming output."""
    provider = MockTTSProvider()
    
    chunks = []
    async for chunk in provider.synthesize_streaming("Hello, world!"):
        chunks.append(chunk)
    
    assert len(chunks) == 5
    assert all(len(chunk) == 1024 for chunk in chunks)


@pytest.mark.asyncio
async def test_tts_full_synthesis():
    """Test full TTS synthesis."""
    provider = MockTTSProvider()
    
    audio = await provider.synthesize("Hello, world!")
    
    assert isinstance(audio, bytes)
    assert len(audio) == 5120


@pytest.mark.asyncio
async def test_tts_empty_text():
    """Test TTS with empty text."""
    provider = MockTTSProvider()
    
    chunks = []
    async for chunk in provider.synthesize_streaming(""):
        chunks.append(chunk)
    
    # Should still produce chunks (mock behavior)
    assert len(chunks) > 0


@pytest.mark.asyncio
async def test_tts_chunk_timing():
    """Test TTS chunk timing for smooth playback."""
    import time
    
    provider = MockTTSProvider()
    
    start_time = time.time()
    chunk_times = []
    
    async for chunk in provider.synthesize_streaming("Test message"):
        chunk_times.append(time.time() - start_time)
    
    # Chunks should arrive quickly (streaming)
    # All chunks within 1 second for mock
    assert chunk_times[-1] < 1.0







