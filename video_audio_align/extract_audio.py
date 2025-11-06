"""Utilities for extracting audio tracks from video files."""

from __future__ import annotations

from pathlib import Path
from typing import Optional
import warnings

import ffmpeg


def extract_audio(
    video_path: Path | str,
    output_path: Optional[Path | str] = None,
    *,
    sample_rate: int = 16000,
) -> Path:
    """
    Extract the primary audio track from ``video_path`` into a WAV file.

    Parameters
    ----------
    video_path:
        Path to the input video file.
    output_path:
        Path to the desired output WAV file. If omitted, the file is placed next
        to the video with the stem ``<video_name>_audio.wav``.
    sample_rate:
        Target sample rate (Hz) for the output audio. Defaults to 16 kHz for
        Whisper compatibility.

    Returns
    -------
    Path
        The path of the extracted audio file.

    Raises
    ------
    FileNotFoundError
        If ``video_path`` does not exist.
    RuntimeError
        If ffmpeg encounters an error during extraction.
    """
    video_path = Path(video_path)
    if not video_path.exists():
        raise FileNotFoundError(f"Video file does not exist: {video_path}")

    if output_path is None:
        output_path = video_path.with_name(f"{video_path.stem}_audio.wav")
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        probe = ffmpeg.probe(str(video_path))
    except ffmpeg.Error as exc:
        raise RuntimeError(
            f"Unable to probe video metadata for {video_path}"
        ) from exc

    has_audio_stream = any(
        stream.get("codec_type") == "audio" for stream in probe.get("streams", [])
    )
    if not has_audio_stream:
        warnings.warn(
            f"No audio stream detected in {video_path}; skipping extraction.",
            RuntimeWarning,
            stacklevel=2,
        )
        # Create an empty placeholder file to signal the absence of audio.
        output_path.touch()
        return output_path

    try:
        (
            ffmpeg.input(str(video_path))
            .output(
                str(output_path),
                ac=1,
                ar=sample_rate,
                format="wav",
            )
            .overwrite_output()
            .run(quiet=True)
        )
    except ffmpeg.Error as exc:
        raise RuntimeError(f"ffmpeg failed to extract audio from {video_path}") from exc

    return output_path


__all__ = ["extract_audio"]
