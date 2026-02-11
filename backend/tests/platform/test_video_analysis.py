import json
from unittest.mock import AsyncMock, patch

import pytest

from app.platform.services.video_analysis import (
    VideoMetadata,
    extract_metadata,
    extract_keyframes,
    frames_to_base64,
)


def test_resolution_2160p():
    m = VideoMetadata(
        duration_seconds=60.0, width=3840, height=2160,
        bitrate=15_000_000, codec="h264", framerate=30.0,
        has_video=True, has_audio=True,
    )
    assert m.resolution == "2160p"


def test_resolution_1440p():
    m = VideoMetadata(
        duration_seconds=60.0, width=2560, height=1440,
        bitrate=8_000_000, codec="h264", framerate=30.0,
        has_video=True, has_audio=True,
    )
    assert m.resolution == "1440p"


def test_resolution_1080p():
    m = VideoMetadata(
        duration_seconds=60.0, width=1920, height=1080,
        bitrate=5_000_000, codec="h264", framerate=30.0,
        has_video=True, has_audio=True,
    )
    assert m.resolution == "1080p"


def test_resolution_720p():
    m = VideoMetadata(
        duration_seconds=60.0, width=1280, height=720,
        bitrate=2_000_000, codec="h264", framerate=30.0,
        has_video=True, has_audio=True,
    )
    assert m.resolution == "720p"


def test_resolution_480p():
    m = VideoMetadata(
        duration_seconds=60.0, width=854, height=480,
        bitrate=1_000_000, codec="h264", framerate=30.0,
        has_video=True, has_audio=True,
    )
    assert m.resolution == "480p"


def test_resolution_custom():
    m = VideoMetadata(
        duration_seconds=60.0, width=640, height=360,
        bitrate=500_000, codec="h264", framerate=30.0,
        has_video=True, has_audio=True,
    )
    assert m.resolution == "360p"


def test_resolution_unknown_no_video():
    m = VideoMetadata(
        duration_seconds=60.0, width=0, height=0,
        bitrate=128_000, codec="aac", framerate=0.0,
        has_video=False, has_audio=True,
    )
    assert m.resolution == "unknown"


def test_bitrate_tier_high():
    m = VideoMetadata(
        duration_seconds=60.0, width=1920, height=1080,
        bitrate=10_000_000, codec="h264", framerate=30.0,
        has_video=True, has_audio=True,
    )
    assert m.bitrate_tier == "high"


def test_bitrate_tier_medium():
    m = VideoMetadata(
        duration_seconds=60.0, width=1920, height=1080,
        bitrate=4_000_000, codec="h264", framerate=30.0,
        has_video=True, has_audio=True,
    )
    assert m.bitrate_tier == "medium"


def test_bitrate_tier_low():
    m = VideoMetadata(
        duration_seconds=60.0, width=640, height=480,
        bitrate=500_000, codec="h264", framerate=30.0,
        has_video=True, has_audio=True,
    )
    assert m.bitrate_tier == "low"


def test_bitrate_tier_exact_boundary_high():
    m = VideoMetadata(
        duration_seconds=60.0, width=1920, height=1080,
        bitrate=8_000_000, codec="h264", framerate=30.0,
        has_video=True, has_audio=True,
    )
    assert m.bitrate_tier == "high"


def test_bitrate_tier_exact_boundary_medium():
    m = VideoMetadata(
        duration_seconds=60.0, width=1920, height=1080,
        bitrate=2_500_000, codec="h264", framerate=30.0,
        has_video=True, has_audio=True,
    )
    assert m.bitrate_tier == "medium"


def test_frames_to_base64_encodes():
    frames = [b"\xff\xd8\xff\xe0", b"\x89PNG"]
    result = frames_to_base64(frames)
    assert len(result) == 2
    assert all(isinstance(r, str) for r in result)


def test_frames_to_base64_empty():
    assert frames_to_base64([]) == []


def test_frames_to_base64_roundtrip():
    import base64
    original = b"test frame data"
    encoded = frames_to_base64([original])
    decoded = base64.b64decode(encoded[0])
    assert decoded == original


@pytest.mark.asyncio
async def test_extract_metadata_parses_video():
    ffprobe_output = json.dumps({
        "streams": [
            {
                "codec_type": "video",
                "codec_name": "h264",
                "width": 1920,
                "height": 1080,
                "r_frame_rate": "30/1",
                "bit_rate": "5000000",
            },
            {
                "codec_type": "audio",
                "codec_name": "aac",
            },
        ],
        "format": {
            "duration": "120.5",
            "bit_rate": "5500000",
        },
    })

    mock_proc = AsyncMock()
    mock_proc.communicate.return_value = (ffprobe_output.encode(), b"")
    mock_proc.returncode = 0

    with patch("app.platform.services.video_analysis.asyncio.create_subprocess_exec", return_value=mock_proc):
        metadata = await extract_metadata("/tmp/test.mp4")

    assert metadata.duration_seconds == 120.5
    assert metadata.width == 1920
    assert metadata.height == 1080
    assert metadata.bitrate == 5_000_000
    assert metadata.codec == "h264"
    assert metadata.framerate == 30.0
    assert metadata.has_video is True
    assert metadata.has_audio is True
    assert metadata.resolution == "1080p"
    assert metadata.bitrate_tier == "medium"


@pytest.mark.asyncio
async def test_extract_metadata_audio_only():
    ffprobe_output = json.dumps({
        "streams": [
            {
                "codec_type": "audio",
                "codec_name": "mp3",
                "duration": "180.0",
            },
        ],
        "format": {
            "duration": "180.0",
            "bit_rate": "320000",
        },
    })

    mock_proc = AsyncMock()
    mock_proc.communicate.return_value = (ffprobe_output.encode(), b"")
    mock_proc.returncode = 0

    with patch("app.platform.services.video_analysis.asyncio.create_subprocess_exec", return_value=mock_proc):
        metadata = await extract_metadata("/tmp/test.mp3")

    assert metadata.has_video is False
    assert metadata.has_audio is True
    assert metadata.width == 0
    assert metadata.height == 0
    assert metadata.resolution == "unknown"
    assert metadata.duration_seconds == 180.0


@pytest.mark.asyncio
async def test_extract_metadata_failure_raises():
    mock_proc = AsyncMock()
    mock_proc.communicate.return_value = (b"", b"error message")
    mock_proc.returncode = 1

    with patch("app.platform.services.video_analysis.asyncio.create_subprocess_exec", return_value=mock_proc):
        with pytest.raises(RuntimeError, match="ffprobe failed"):
            await extract_metadata("/tmp/bad.mp4")


@pytest.mark.asyncio
async def test_extract_metadata_video_bitrate_fallback_to_format():
    ffprobe_output = json.dumps({
        "streams": [
            {
                "codec_type": "video",
                "codec_name": "hevc",
                "width": 3840,
                "height": 2160,
                "r_frame_rate": "60/1",
                "bit_rate": "0",
            },
        ],
        "format": {
            "duration": "300.0",
            "bit_rate": "20000000",
        },
    })

    mock_proc = AsyncMock()
    mock_proc.communicate.return_value = (ffprobe_output.encode(), b"")
    mock_proc.returncode = 0

    with patch("app.platform.services.video_analysis.asyncio.create_subprocess_exec", return_value=mock_proc):
        metadata = await extract_metadata("/tmp/test.mp4")

    assert metadata.bitrate == 20_000_000
    assert metadata.bitrate_tier == "high"
    assert metadata.resolution == "2160p"
    assert metadata.framerate == 60.0
    assert metadata.codec == "hevc"


@pytest.mark.asyncio
async def test_extract_metadata_malformed_framerate():
    ffprobe_output = json.dumps({
        "streams": [
            {
                "codec_type": "video",
                "codec_name": "h264",
                "width": 1920,
                "height": 1080,
                "r_frame_rate": "invalid",
            },
        ],
        "format": {
            "duration": "60.0",
            "bit_rate": "5000000",
        },
    })

    mock_proc = AsyncMock()
    mock_proc.communicate.return_value = (ffprobe_output.encode(), b"")
    mock_proc.returncode = 0

    with patch("app.platform.services.video_analysis.asyncio.create_subprocess_exec", return_value=mock_proc):
        metadata = await extract_metadata("/tmp/test.mp4")

    assert metadata.framerate == 0.0


@pytest.mark.asyncio
async def test_extract_keyframes_returns_empty_for_audio():
    ffprobe_output = json.dumps({
        "streams": [{"codec_type": "audio", "codec_name": "aac"}],
        "format": {"duration": "120.0", "bit_rate": "128000"},
    })

    mock_proc = AsyncMock()
    mock_proc.communicate.return_value = (ffprobe_output.encode(), b"")
    mock_proc.returncode = 0

    with patch("app.platform.services.video_analysis.asyncio.create_subprocess_exec", return_value=mock_proc):
        frames = await extract_keyframes("/tmp/test.mp3", count=4)

    assert frames == []


@pytest.mark.asyncio
async def test_extract_keyframes_returns_empty_on_failure():
    mock_proc = AsyncMock()
    mock_proc.communicate.return_value = (b"", b"error")
    mock_proc.returncode = 1

    with patch("app.platform.services.video_analysis.asyncio.create_subprocess_exec", return_value=mock_proc):
        frames = await extract_keyframes("/tmp/bad.mp4", count=4)

    assert frames == []
