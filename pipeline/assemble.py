#!/usr/bin/env python3
"""Assemble a CastLock video: shots + narration + optional music, loud.

Steps:
1. Mix: concat the shots (each scaled and cropped to the 1080x1920
   master), burn in captions if given, lay the narration over the music
   with sidechain ducking if music is given.
2. Measure: ffmpeg loudnorm analysis pass on the mix.
3. Apply: second loudnorm pass with the measured values, targeting about
   -14 LUFS integrated and true peak at or below -1 dBFS (the house
   standard, docs/house-rules.md).
4. Verify: measure the final file and print its integrated loudness and
   true peak. A video whose loudness was not measured is not finished.

A sidecar JSON lands next to the output with the model list, licences,
seeds and ai_generated: true, ready for the platform AI label step.

--dry-run prints every command and the sidecar without running anything.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

TARGET_I = -14.0
TARGET_TP = -1.0
TARGET_LRA = 11.0
WIDTH, HEIGHT = 1080, 1920

MODELS = [
    {"name": "Z-Image Turbo", "role": "stills", "license": "Apache 2.0"},
    {"name": "Wan 2.2", "role": "image-to-video", "license": "Apache 2.0"},
    {"name": "Kokoro-82M", "role": "narration", "license": "Apache 2.0"},
]


def escape_filter_path(path: Path) -> str:
    """Escape a path for use inside an ffmpeg filter argument."""
    text = str(path).replace("\\", "/")
    return text.replace(":", "\\:").replace("'", "\\'")


def build_mix_command(shots: list[Path], narration: Path, music: Path | None,
                      captions: Path | None, tmp_out: Path) -> list[str]:
    cmd: list[str] = ["ffmpeg", "-y"]
    for shot in shots:
        cmd += ["-i", str(shot)]
    cmd += ["-i", str(narration)]
    narration_idx = len(shots)
    music_idx = None
    if music:
        cmd += ["-stream_loop", "-1", "-i", str(music)]
        music_idx = narration_idx + 1

    filters: list[str] = []
    for i in range(len(shots)):
        filters.append(
            f"[{i}:v]scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=increase,"
            f"crop={WIDTH}:{HEIGHT},fps=30,setsar=1[v{i}]"
        )
    concat_inputs = "".join(f"[v{i}]" for i in range(len(shots)))
    filters.append(f"{concat_inputs}concat=n={len(shots)}:v=1:a=0[vcat]")
    if captions:
        filters.append(f"[vcat]subtitles=filename='{escape_filter_path(captions)}'[v]")
    else:
        filters.append("[vcat]null[v]")
    if music_idx is None:
        filters.append(f"[{narration_idx}:a]aresample=48000[aout]")
    else:
        # The voice feeds both the compressor sidechain and the final mix,
        # so it is split in two first.
        filters.append(f"[{music_idx}:a]aresample=48000,volume=0.12[music]")
        filters.append(
            f"[{narration_idx}:a]aresample=48000,asplit=2[voice_sc][voice_mix]"
        )
        filters.append(
            "[music][voice_sc]sidechaincompress=threshold=0.02:ratio=8:"
            "attack=50:release=300[ducked]"
        )
        filters.append("[voice_mix][ducked]amix=inputs=2:duration=first:normalize=0[aout]")

    cmd += ["-filter_complex", ";".join(filters),
            "-map", "[v]", "-map", "[aout]",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
            "-c:a", "aac", "-b:a", "192k", str(tmp_out)]
    return cmd


def build_measure_command(path: Path) -> list[str]:
    return ["ffmpeg", "-i", str(path), "-vn",
            "-af", f"loudnorm=I={TARGET_I}:TP={TARGET_TP}:LRA={TARGET_LRA}:print_format=json",
            "-f", "null", "-"]


def parse_loudnorm(stderr_text: str) -> dict:
    """Pull the loudnorm JSON block out of ffmpeg's stderr."""
    match = None
    for match in re.finditer(r"\{[^{}]*\"input_i\"[^{}]*\}", stderr_text, re.DOTALL):
        pass
    if match is None:
        raise ValueError("no loudnorm JSON found in ffmpeg output")
    return json.loads(match.group(0))


def build_apply_command(src: Path, dst: Path, measured: dict) -> list[str]:
    filt = (
        f"loudnorm=I={TARGET_I}:TP={TARGET_TP}:LRA={TARGET_LRA}"
        f":measured_I={measured['input_i']}:measured_TP={measured['input_tp']}"
        f":measured_LRA={measured['input_lra']}:measured_thresh={measured['input_thresh']}"
        f":offset={measured['target_offset']}:linear=true"
    )
    return ["ffmpeg", "-y", "-i", str(src), "-map", "0:v", "-map", "0:a",
            "-c:v", "copy", "-af", filt, "-c:a", "aac", "-b:a", "192k",
            "-ar", "48000", str(dst)]


def run(cmd: list[str]) -> subprocess.CompletedProcess:
    print("+", " ".join(cmd[:2]), "...", str(cmd[-1]))
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        print(proc.stderr[-3000:], file=sys.stderr)
        raise RuntimeError(f"command failed: {cmd[0]}")
    return proc


def sidecar(out: Path, seeds: list[str], character: str | None,
            loudness: dict | None) -> dict:
    return {
        "file": str(out),
        "ai_generated": True,
        "character": character,
        "models": MODELS,
        "seeds": seeds,
        "loudness": loudness,
        "master": {"width": WIDTH, "height": HEIGHT},
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("shots", nargs="+", type=Path, help="shot videos, in order")
    ap.add_argument("--narration", type=Path, required=True)
    ap.add_argument("--music", type=Path, help="optional background music (ducked under the voice)")
    ap.add_argument("--captions", type=Path, help="optional .ass captions to burn in")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--seed", action="append", default=[],
                    help="seed used for a shot, recorded in the sidecar (repeatable)")
    ap.add_argument("--character", help="character pack name, recorded in the sidecar")
    ap.add_argument("--dry-run", action="store_true",
                    help="print the commands and sidecar without running anything")
    args = ap.parse_args(argv)

    tmp_out = args.out.with_suffix(".mixed.mp4")
    mix_cmd = build_mix_command(args.shots, args.narration, args.music,
                                args.captions, tmp_out)
    measure_cmd = build_measure_command(tmp_out)
    placeholder_measured = {"input_i": "<measured>", "input_tp": "<measured>",
                            "input_lra": "<measured>", "input_thresh": "<measured>",
                            "target_offset": "<measured>"}

    if args.dry_run:
        print("MIX:     ", " ".join(mix_cmd))
        print("MEASURE: ", " ".join(measure_cmd))
        print("APPLY:   ", " ".join(build_apply_command(tmp_out, args.out, placeholder_measured)))
        print("SIDECAR: ", json.dumps(sidecar(args.out, args.seed, args.character, None), indent=2))
        return 0

    for path in [*args.shots, args.narration]:
        if not path.is_file():
            print(f"ERROR: no such file: {path}", file=sys.stderr)
            return 1

    try:
        run(mix_cmd)
        measured = parse_loudnorm(run(measure_cmd).stderr)
        run(build_apply_command(tmp_out, args.out, measured))
        final = parse_loudnorm(run(build_measure_command(args.out)).stderr)
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    loudness = {"integrated_lufs": float(final["input_i"]),
                "true_peak_dbfs": float(final["input_tp"]),
                "target_integrated_lufs": TARGET_I, "target_true_peak_dbfs": TARGET_TP}
    print(f"LOUDNESS: integrated {loudness['integrated_lufs']:.2f} LUFS, "
          f"true peak {loudness['true_peak_dbfs']:.2f} dBFS "
          f"(target about {TARGET_I} LUFS, peak at or below {TARGET_TP} dBFS)")
    sidecar_path = args.out.with_suffix(".json")
    sidecar_path.write_text(
        json.dumps(sidecar(args.out, args.seed, args.character, loudness), indent=2),
        encoding="utf-8")
    print(f"wrote {args.out} and {sidecar_path}")
    tmp_out.unlink(missing_ok=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
