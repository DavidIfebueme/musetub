import asyncio
import base64
import json
import tempfile
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class VideoMetadata:
    duration_seconds: float
    width: int
    height: int
    bitrate: int
    codec: str
    framerate: float
    has_video: bool
    has_audio: bool

    @property
    def resolution(self) -> str:
        if self.height >= 2160:
            return "2160p"
        if self.height >= 1440:
            return "1440p"
        if self.height >= 1080:
            return "1080p"
        if self.height >= 720:
            return "720p"
        if self.height >= 480:
            return "480p"
        if self.height > 0:
            return f"{self.height}p"
        return "unknown"

    @property
    def bitrate_tier(self) -> str:
        if self.bitrate >= 8_000_000:
            return "high"
        if self.bitrate >= 2_500_000:
            return "medium"
        return "low"


async def extract_metadata(file_path: str | Path) -> VideoMetadata:
    proc = await asyncio.create_subprocess_exec(
        "ffprobe", "-v", "quiet", "-print_format", "json",
        "-show_format", "-show_streams", str(file_path),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    if proc.returncode != 0:
        raise RuntimeError(f"ffprobe failed: {stderr.decode()}")

    data = json.loads(stdout.decode())
    video_stream = None
    audio_stream = None
    for stream in data.get("streams", []):
        if stream.get("codec_type") == "video" and video_stream is None:
            video_stream = stream
        if stream.get("codec_type") == "audio" and audio_stream is None:
            audio_stream = stream

    fmt = data.get("format", {})
    duration = float(fmt.get("duration", 0))

    if video_stream:
        width = int(video_stream.get("width", 0))
        height = int(video_stream.get("height", 0))
        stream_bitrate = int(video_stream.get("bit_rate", 0) or 0)
        format_bitrate = int(fmt.get("bit_rate", 0) or 0)
        bitrate = stream_bitrate if stream_bitrate else format_bitrate
        codec = video_stream.get("codec_name", "unknown")
        r_frame_rate = video_stream.get("r_frame_rate", "0/1")
        try:
            num, den = r_frame_rate.split("/")
            framerate = float(num) / float(den) if float(den) else 0.0
        except (ValueError, ZeroDivisionError):
            framerate = 0.0
        if not duration and video_stream.get("duration"):
            duration = float(video_stream["duration"])
    else:
        width = 0
        height = 0
        bitrate = int(fmt.get("bit_rate", 0))
        codec = audio_stream.get("codec_name", "unknown") if audio_stream else "unknown"
        framerate = 0.0
        if audio_stream and not duration and audio_stream.get("duration"):
            duration = float(audio_stream["duration"])

    return VideoMetadata(
        duration_seconds=duration,
        width=width,
        height=height,
        bitrate=bitrate,
        codec=codec,
        framerate=framerate,
        has_video=video_stream is not None,
        has_audio=audio_stream is not None,
    )


async def extract_keyframes(file_path: str | Path, count: int = 4) -> list[bytes]:
    try:
        metadata = await extract_metadata(file_path)
    except Exception:
        return []

    if not metadata.has_video or metadata.duration_seconds <= 0:
        return []

    interval = metadata.duration_seconds / (count + 1)
    timestamps = [interval * (i + 1) for i in range(count)]
    frames: list[bytes] = []

    for ts in timestamps:
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            proc = await asyncio.create_subprocess_exec(
                "ffmpeg", "-y", "-ss", f"{ts:.2f}", "-i", str(file_path),
                "-vframes", "1", "-q:v", "2", "-f", "image2", tmp_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await proc.communicate()
            tmp_file = Path(tmp_path)
            if proc.returncode == 0 and tmp_file.exists():
                frame_data = tmp_file.read_bytes()
                if frame_data:
                    frames.append(frame_data)
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    return frames


def frames_to_base64(frames: list[bytes]) -> list[str]:
    return [base64.b64encode(f).decode("ascii") for f in frames]
