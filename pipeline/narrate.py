#!/usr/bin/env python3
"""Narrate a text file with Kokoro ONNX, on CPU.

    python3 narrate.py script.md --voice am_michael --out narration.wav

The Kokoro v1.0 model files (kokoro-v1.0.onnx and voices-v1.0.bin) are
located in this order: --model/--voices flags, the CASTLOCK_KOKORO_MODEL
and CASTLOCK_KOKORO_VOICES environment variables, ~/workspace/tools/kokoro/,
./models/, ~/.local/share/castlock/. Run this script with a Python that has
kokoro-onnx installed (for example the kokoro-venv interpreter); if it is
missing, the error says so instead of failing obscurely.

--dry-run prints the resolved configuration as JSON and exits without
loading the model.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

DEFAULT_VOICE = "am_michael"
MODEL_NAME = "kokoro-v1.0.onnx"
VOICES_NAME = "voices-v1.0.bin"


def extract_text(path: Path) -> str:
    """Plain narration text from a .md or .txt script.

    Markdown heading lines and horizontal rules are dropped; the rest is
    joined into flowing paragraphs.
    """
    lines: list[str] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line.startswith("#"):
            continue
        if line in ("---", "***", "___"):
            continue
        lines.append(line)
    return " ".join(l for l in lines if l).strip()


def find_model_file(filename: str, flag_value: str | None, env_key: str) -> Path | None:
    candidates: list[Path] = []
    if flag_value:
        candidates.append(Path(flag_value))
    env_value = os.environ.get(env_key)
    if env_value:
        candidates.append(Path(env_value))
    candidates += [
        Path.home() / "workspace" / "tools" / "kokoro" / filename,
        Path("models") / filename,
        Path.home() / ".local" / "share" / "castlock" / filename,
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None


def resolve_config(args: argparse.Namespace) -> dict:
    model = find_model_file(MODEL_NAME, args.model, "CASTLOCK_KOKORO_MODEL")
    voices = find_model_file(VOICES_NAME, args.voices, "CASTLOCK_KOKORO_VOICES")
    return {
        "input": str(args.input),
        "out": str(args.out) if args.out else None,
        "voice": args.voice,
        "speed": args.speed,
        "model": str(model) if model else None,
        "voices": str(voices) if voices else None,
    }


def render(config: dict, text: str) -> Path:
    try:
        from kokoro_onnx import Kokoro  # type: ignore
    except ImportError:
        raise RuntimeError(
            "kokoro-onnx is not installed in this Python. Run narrate.py with "
            "the interpreter that has it (for example ~/workspace/tools/"
            "kokoro-venv/bin/python), or pip install kokoro-onnx soundfile."
        )
    if not config["model"] or not config["voices"]:
        raise RuntimeError(
            f"could not find {MODEL_NAME} / {VOICES_NAME}; pass --model and "
            "--voices or set CASTLOCK_KOKORO_MODEL and CASTLOCK_KOKORO_VOICES"
        )
    kokoro = Kokoro(config["model"], config["voices"])
    samples, sample_rate = kokoro.create(
        text, voice=config["voice"], speed=config["speed"], lang="en-us"
    )
    out = Path(config["out"])
    try:
        import soundfile as sf  # type: ignore

        sf.write(str(out), samples, sample_rate)
    except ImportError:
        import wave

        import numpy as np  # kokoro-onnx depends on numpy

        pcm = (np.clip(samples, -1.0, 1.0) * 32767).astype("<i2")
        with wave.open(str(out), "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(sample_rate)
            wav.writeframes(pcm.tobytes())
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("input", type=Path, help="narration script (.md or .txt)")
    ap.add_argument("--out", type=Path, default=Path("narration.wav"))
    ap.add_argument("--voice", default=DEFAULT_VOICE,
                    help=f"Kokoro voice id (default {DEFAULT_VOICE}; af_heart is the other house candidate)")
    ap.add_argument("--speed", type=float, default=1.0)
    ap.add_argument("--model", help="path to kokoro-v1.0.onnx")
    ap.add_argument("--voices", help="path to voices-v1.0.bin")
    ap.add_argument("--dry-run", action="store_true",
                    help="print the resolved configuration and exit")
    args = ap.parse_args(argv)

    if not args.input.is_file():
        print(f"ERROR: no such file: {args.input}", file=sys.stderr)
        return 1
    config = resolve_config(args)
    if args.dry_run:
        print(json.dumps(config, indent=2))
        return 0
    text = extract_text(args.input)
    if not text:
        print("ERROR: no narration text after cleanup", file=sys.stderr)
        return 1
    try:
        out = render(config, text)
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"wrote {out} (voice {config['voice']}, {len(text)} characters)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
