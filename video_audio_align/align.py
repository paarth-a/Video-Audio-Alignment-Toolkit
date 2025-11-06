"""Main orchestration logic for aligning speech segments with extracted frames."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Sequence
import warnings

import whisper

try:  # pragma: no cover - import guard for both script and package usage
    from .extract_audio import extract_audio  # type: ignore[attr-defined]
    from .extract_frames import extract_frames, get_video_fps  # type: ignore[attr-defined]
except ImportError:  # pragma: no cover
    from extract_audio import extract_audio
    from extract_frames import extract_frames, get_video_fps


Segment = Dict[str, float | str]
AlignmentEntry = Dict[str, float | int | str]


def transcribe_audio(
    audio_path: Path | str,
    *,
    model: str = "small",
    language: str | None = None,
) -> List[Segment]:
    """
    Transcribe the audio file and return structured segment information.

    Parameters
    ----------
    audio_path:
        Path to the WAV audio to transcribe.
    model:
        Whisper model size to load.
    language:
        Optional ISO language code hint for Whisper.

    Returns
    -------
    list[dict]
        Each segment contains ``text``, ``start_time``, and ``end_time`` keys.
    """
    audio_path = Path(audio_path)
    if not audio_path.exists():
        raise FileNotFoundError(f"Audio file does not exist: {audio_path}")

    if audio_path.stat().st_size == 0:
        warnings.warn(
            f"Audio file {audio_path} is empty; no transcription generated.",
            RuntimeWarning,
            stacklevel=2,
        )
        return []

    asr_model = whisper.load_model(model)
    result = asr_model.transcribe(
        str(audio_path),
        word_timestamps=True,
        verbose=False,
        language=language,
    )

    segments: List[Segment] = []
    for segment in result.get("segments", []):
        text = segment.get("text", "").strip()
        if not text:
            continue

        segments.append(
            {
                "text": text,
                "start_time": float(segment.get("start", 0.0)),
                "end_time": float(segment.get("end", 0.0)),
            }
        )

    return segments


def align_frames_to_transcript(
    segments: Sequence[Segment],
    *,
    video_fps: float,
    extraction_fps: float = 1.0,
) -> List[AlignmentEntry]:
    """
    Align transcription segments with frame indices based on timestamps.

    Parameters
    ----------
    segments:
        Iterable of transcription segments produced by :func:`transcribe_audio`.
    video_fps:
        Nominal FPS of the original video. Included for reference in alignment.
    extraction_fps:
        FPS used when extracting frames. Defaults to ``1.0``.

    Returns
    -------
    list[dict]
        Each entry contains ``text``, ``start_time``, ``end_time``,
        ``start_frame``, and ``end_frame``.
    """
    aligned: List[AlignmentEntry] = []

    for segment in segments:
        start_time = float(segment["start_time"])
        end_time = float(segment["end_time"])
        start_frame = max(0, int(start_time * extraction_fps))
        end_frame = max(start_frame, int(end_time * extraction_fps))

        aligned.append(
            {
                "text": segment["text"],
                "start_time": start_time,
                "end_time": end_time,
                "start_frame": start_frame,
                "end_frame": end_frame,
                "video_fps": video_fps,
            }
        )

    return aligned


def process_video(
    video_path: Path | str,
    output_dir: Path | str,
    *,
    model: str = "small",
    fps: float = 1.0,
    language: str | None = None,
) -> List[AlignmentEntry]:
    """
    Execute the full alignment pipeline for a given video.

    The resulting alignment metadata is saved to ``alignment.json`` within
    ``output_dir`` and returned to the caller.
    """
    video_path = Path(video_path)
    if not video_path.exists():
        raise FileNotFoundError(f"Video file does not exist: {video_path}")

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    audio_path = output_dir / "audio.wav"
    extracted_audio = extract_audio(video_path, audio_path)
    if extracted_audio.stat().st_size == 0:
        warnings.warn(
            f"No audio content found in {video_path}; alignment will be empty.",
            RuntimeWarning,
            stacklevel=2,
        )
        segments: List[Segment] = []
    else:
        segments = transcribe_audio(extracted_audio, model=model, language=language)

    # Even if the audio is empty, we still extract frames for completeness.
    frame_dir = output_dir / "frames"
    _frame_paths, frame_count = extract_frames(video_path, frame_dir, fps=fps)
    video_fps = get_video_fps(video_path)

    if not segments:
        alignment: List[AlignmentEntry] = []
    else:
        alignment = align_frames_to_transcript(
            segments,
            video_fps=video_fps,
            extraction_fps=fps,
        )

    alignment_path = output_dir / "alignment.json"
    with alignment_path.open("w", encoding="utf-8") as fp:
        json.dump(alignment, fp, indent=2)

    metadata_path = output_dir / "metadata.json"
    metadata = {
        "video_path": str(video_path),
        "audio_path": str(extracted_audio),
        "frame_dir": str(frame_dir),
        "frame_count": frame_count,
        "video_fps": video_fps,
        "extraction_fps": fps,
    }
    with metadata_path.open("w", encoding="utf-8") as fp:
        json.dump(metadata, fp, indent=2)

    return alignment


__all__ = ["transcribe_audio", "align_frames_to_transcript", "process_video"]
