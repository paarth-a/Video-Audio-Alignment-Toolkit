"""Convert alignment JSON files into SRT subtitle format."""

from __future__ import annotations

import json
from pathlib import Path
from typing import List


def _format_timestamp(seconds: float) -> str:
    """
    Convert a float timestamp in seconds to SRT ``HH:MM:SS,mmm`` format.
    """
    millis = int(round(seconds * 1000))
    hours, remainder = divmod(millis, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    secs, millis = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def alignment_to_srt(
    alignment_json_path: Path | str,
    output_srt_path: Path | str,
) -> Path:
    """
    Convert a JSON alignment file produced by ``process_video`` into SRT format.

    Parameters
    ----------
    alignment_json_path:
        Path to the JSON alignment file (list of segments).
    output_srt_path:
        Destination for the generated ``.srt`` file.

    Returns
    -------
    Path
        Path to the created SRT file.
    """
    alignment_json_path = Path(alignment_json_path)
    if not alignment_json_path.exists():
        raise FileNotFoundError(f"Alignment file not found: {alignment_json_path}")

    with alignment_json_path.open("r", encoding="utf-8") as fp:
        alignment = json.load(fp)

    output_srt_path = Path(output_srt_path)
    output_srt_path.parent.mkdir(parents=True, exist_ok=True)

    lines: List[str] = []
    for idx, segment in enumerate(alignment, start=1):
        start_time = _format_timestamp(float(segment["start_time"]))
        end_time = _format_timestamp(float(segment["end_time"]))
        text = str(segment["text"]).strip() or "[inaudible]"

        lines.extend([str(idx), f"{start_time} --> {end_time}", text, ""])

    output_srt_path.write_text("\n".join(lines), encoding="utf-8")
    return output_srt_path


__all__ = ["alignment_to_srt"]
