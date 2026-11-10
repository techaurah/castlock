#!/usr/bin/env python3
"""Word timings for captions, from a narration WAV.

Primary route: faster-whisper (small model) transcribes the finished
narration and returns word-level timestamps. Output is then marked
"estimated": false.

Fallback route: if the faster-whisper route is unavailable (not installed,
model not cached, or no network to fetch it), timings are estimated from
the narration text and the audio duration, allocating each word a share of
the duration proportional to its character length. The output is then
marked "estimated": true, loudly, in the JSON and on the console.
Estimated timings are a drafting aid, not a delivery standard
(docs/stack.md).
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def audio_duration(path: Path) -> float:
    """Duration in seconds.

    Prefers ffprobe. When ffprobe is not installed (minimal CI runners,
    small containers), WAV files are measured with the stdlib wave module
    instead, so the estimation fallback never hard-depends on ffprobe for
    the pipeline's own narration format.
    """
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "json", str(path)],
            capture_output=True, text=True,
        )
        if out.returncode == 0:
            return float(json.loads(out.stdout)["format"]["duration"])
        ffprobe_error = out.stderr.strip()
    except FileNotFoundError:
        ffprobe_error = "ffprobe not installed"
    if path.suffix.lower() == ".wav":
        import wave

        with wave.open(str(path), "rb") as wav:
            return wav.getnframes() / float(wav.getframerate())
    raise RuntimeError(f"ffprobe failed on {path}: {ffprobe_error}")


def estimate_timings(text: str, duration: float) -> list[dict]:
    """Character-count based word timing estimation.

    Each token gets a time share proportional to len(token) + 1 (the +1
    stands in for the following space or pause). Shares are laid out back
    to back across the whole duration. Monotonic by construction.
    """
    tokens = [t for t in text.split() if t]
    if not tokens:
        return []
    weights = [len(t) + 1 for t in tokens]
    total = sum(weights)
    words: list[dict] = []
    cursor = 0.0
    for token, weight in zip(tokens, weights):
        span = duration * weight / total
        words.append({"word": token, "start": round(cursor, 3),
                      "end": round(cursor + span, 3)})
        cursor += span
    if words:
        words[-1]["end"] = round(duration, 3)
    return words


def whisper_timings(path: Path, model_size: str = "small") -> list[dict]:
    """Word timings from faster-whisper. Raises ImportError if unavailable."""
    from faster_whisper import WhisperModel  # type: ignore

    model = WhisperModel(model_size, device="cpu", compute_type="int8")
    segments, _info = model.transcribe(str(path), word_timestamps=True)
    words: list[dict] = []
    for segment in segments:
        for w in segment.words or []:
            words.append({"word": w.word.strip(), "start": round(w.start, 3),
                          "end": round(w.end, 3)})
    return [w for w in words if w["word"]]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("wav", type=Path, help="narration WAV")
    ap.add_argument("--out", type=Path, required=True, help="output timings JSON")
    ap.add_argument("--text", type=Path,
                    help="narration text (required for the estimation fallback)")
    ap.add_argument("--model", default="small", help="faster-whisper model size")
    args = ap.parse_args(argv)

    if not args.wav.is_file():
        print(f"ERROR: no such file: {args.wav}", file=sys.stderr)
        return 1

    words: list[dict]
    estimated = False
    method = "faster-whisper"
    whisper_error: Exception | None = None
    try:
        words = whisper_timings(args.wav, args.model)
        if not words:
            raise RuntimeError("faster-whisper returned no words")
    except Exception as exc:  # ImportError, model download or runtime failure
        whisper_error = exc
        words = []
    if whisper_error is not None:
        if args.text is None:
            print(f"ERROR: faster-whisper route failed ({whisper_error}) and "
                  "no --text was given for the estimation fallback",
                  file=sys.stderr)
            return 1
        print(f"note: faster-whisper route failed ({type(whisper_error).__name__}); "
              "using the estimation fallback", file=sys.stderr)
        duration = audio_duration(args.wav)
        text = args.text.read_text(encoding="utf-8")
        words = estimate_timings(text, duration)
        estimated = True
        method = "character-count estimation (faster-whisper unavailable)"

    payload = {"estimated": estimated, "method": method,
               "source": str(args.wav), "words": words}
    args.out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    flag = "ESTIMATED timings" if estimated else "timings"
    print(f"wrote {args.out}: {len(words)} words, {flag} via {method}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
