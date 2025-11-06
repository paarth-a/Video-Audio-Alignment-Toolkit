# Video Audio Alignment Toolkit

Modular utilities for aligning transcribed speech with extracted video frames. The toolkit produces structured JSON metadata and ready-to-use SRT subtitle files, making it easy to build captioning pipelines, searchable video archives, and multimedia analytics workflows.

## Features

- Audio extraction with ffmpeg and automatic sample-rate normalization for Whisper.
- Frame extraction at configurable sampling rates (default 1 FPS) with sequential naming.
- Whisper-based transcription with segment timestamps.
- JSON alignment output enriched with frame indices and video metadata.
- SRT export helper and a Colab notebook for GPU-friendly execution.

## Repository Layout

```
video_audio_align/
├── align.py              # Orchestrates audio, transcription, frame extraction, and alignment
├── extract_audio.py      # Audio track extraction (16 kHz mono WAV)
├── extract_frames.py     # Frame extraction utilities and video FPS helper
├── example.ipynb         # Google Colab end-to-end demo
├── requirements.txt      # Python dependencies
├── to_srt.py             # JSON → SRT conversion utility
└── README.md             # Usage guide (this file)
```

## Installation

### Local Environment

1. Ensure you have Python 3.9+ and ffmpeg available in your `PATH`.
2. Install dependencies:
   ```bash
   pip install -r video_audio_align/requirements.txt
   ```
3. (Optional) Install GPU acceleration for Whisper by following [PyTorch installation instructions](https://pytorch.org/get-started/locally/).

### Google Colab

Open `video_audio_align/example.ipynb` in Colab. The notebook handles package installation, prompts for a video upload, and runs the full pipeline with GPU acceleration if available.

## Quick Start

```python
from pathlib import Path

from video_audio_align.align import process_video
from video_audio_align.to_srt import alignment_to_srt

video_path = Path("demo.mp4")
output_dir = Path("outputs") / video_path.stem

alignment = process_video(video_path, output_dir, model="small", fps=1.0)
alignment_path = output_dir / "alignment.json"
srt_path = output_dir / "captions.srt"

alignment_to_srt(alignment_path, srt_path)
```

The call returns a list of alignment entries and saves both `alignment.json` and `captions.srt` under `output_dir`.

## Module API Reference

- `extract_audio.extract_audio(video_path, output_path=None, sample_rate=16000)`  
  Extracts the primary audio track into a 16 kHz mono WAV file. Returns the output `Path`. Emits a warning if no audio stream is present.

- `extract_frames.get_video_fps(video_path)`  
  Probes the video to detect its nominal FPS.

- `extract_frames.extract_frames(video_path, output_dir, fps=1.0)`  
  Extracts JPEG frames at the specified sampling rate. Returns a tuple of `(frame_paths, frame_count)`.

- `align.transcribe_audio(audio_path, model='small', language=None)`  
  Runs Whisper transcription with word timestamps, returning cleaned segments.

- `align.align_frames_to_transcript(segments, video_fps, extraction_fps=1.0)`  
  Maps segment timestamps to frame indices and returns enriched alignment entries.

- `align.process_video(video_path, output_dir, model='small', fps=1.0, language=None)`  
  Full pipeline: extract audio, transcribe, extract frames, align, and write `alignment.json` plus `metadata.json`.

- `to_srt.alignment_to_srt(alignment_json_path, output_srt_path)`  
  Converts the JSON alignment to an SRT subtitle file.

## Output Format

`alignment.json` stores a list of objects:

```json
[
  {
    "text": "Hello world",
    "start_time": 0.52,
    "end_time": 2.34,
    "start_frame": 0,
    "end_frame": 2,
    "video_fps": 29.97
  }
]
```

`metadata.json` complements the alignment with the original video path, the extracted audio path, frame directory, frame count, source FPS, and extraction FPS.

## Troubleshooting

- **ffmpeg missing**: Install via Homebrew (`brew install ffmpeg`), apt (`sudo apt-get install ffmpeg`), or download from [ffmpeg.org](https://ffmpeg.org/).
- **Whisper performance**: Swap to `model="tiny"` or `model="base"` for faster CPU runs. Use a GPU-enabled environment for larger models.
- **Memory usage**: Reduce `fps` during frame extraction or process shorter clips.
- **No speech detected**: Check audio levels; silent or music-only tracks produce empty alignments.

## License

MIT License. See `LICENSE` if provided, or feel free to adapt the code with attribution.
