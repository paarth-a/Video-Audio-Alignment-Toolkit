"""Frame extraction utilities."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, List, Sequence, Tuple

import ffmpeg


def get_video_fps(video_path: Path | str) -> float:
    """
    Retrieve the native frames-per-second (FPS) for a given video.

    Parameters
    ----------
    video_path:
        Path to the input video file.

    Returns
    -------
    float
        The nominal FPS reported by ffmpeg.

    Raises
    ------
    FileNotFoundError
        If the input video cannot be found.
    RuntimeError
        If ffmpeg cannot probe the video metadata.
    """
    video_path = Path(video_path)
    if not video_path.exists():
        raise FileNotFoundError(f"Video file does not exist: {video_path}")

    try:
        probe = ffmpeg.probe(str(video_path))
    except ffmpeg.Error as exc:
        raise RuntimeError(f"Unable to probe video metadata for {video_path}") from exc

    video_streams = [
        stream
        for stream in probe.get("streams", [])
        if stream.get("codec_type") == "video"
    ]
    if not video_streams:
        raise RuntimeError(f"No video stream found in {video_path}")

    stream = video_streams[0]
    avg_frame_rate = stream.get("avg_frame_rate")
    if not avg_frame_rate or avg_frame_rate == "0/0":
        return float(stream.get("r_frame_rate", "0/1").split("/")[0])

    num, denom = (int(x) for x in avg_frame_rate.split("/"))
    return num / denom if denom else float(num)


def extract_frames(
    video_path: Path | str,
    output_dir: Path | str,
    *,
    fps: float = 1.0,
) -> Tuple[List[Path], int]:
    """
    Extract frames from ``video_path`` at the specified ``fps``.

    Parameters
    ----------
    video_path:
        Path to the input video file.
    output_dir:
        Target directory for the extracted JPEG frames.
    fps:
        Sampling rate for extraction (frames per second). Defaults to ``1.0``.

    Returns
    -------
    tuple[list[Path], int]
        A tuple containing the ordered list of extracted frame paths and the
        total frame count.

    Raises
    ------
    FileNotFoundError
        If the input video does not exist.
    RuntimeError
        If ffmpeg encounters an error during extraction.
    """
    video_path = Path(video_path)
    if not video_path.exists():
        raise FileNotFoundError(f"Video file does not exist: {video_path}")

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    frame_pattern = output_dir / "frame_%04d.jpg"

    try:
        (
            ffmpeg.input(str(video_path))
            .output(
                str(frame_pattern),
                vf=f"fps={fps}",
                qscale=2,
                start_number=0,
            )
            .overwrite_output()
            .run(quiet=True)
        )
    except ffmpeg.Error as exc:
        raise RuntimeError(f"ffmpeg failed to extract frames from {video_path}") from exc

    frame_paths = sorted(output_dir.glob("frame_*.jpg"))
    return frame_paths, len(frame_paths)


__all__ = ["extract_frames", "get_video_fps"]
