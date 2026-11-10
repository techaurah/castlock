#!/usr/bin/env python3
"""Extract a contact sheet from a rendered video for drift review.

    python3 check_frames.py final.mp4 characters/tara/reference/still.png --out sheet.jpg

Frames are sampled evenly across the video and tiled into one sheet, with
the locked reference still placed alongside at the same height. A review
checklist (sheet .md sibling) states what the reviewer must compare. The
visual verdict stays with the human or agent reviewer: this script gathers
the evidence, it does not pass or fail a face.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

CHECKLIST = """# Frame review checklist

Video: {video}
Reference: {reference}

Compare every sampled frame against the reference still:

- [ ] Same person: eyes, eyebrows, nose, lips and jaw match the reference
- [ ] Hair: colour, length and style unchanged
- [ ] Signature details present and unchanged (for Tara: hoop earrings, dark clover pendant)
- [ ] No morphing artefacts around the face in any frame
- [ ] Framing respects the safe zone (nothing important in the edges)
- [ ] Captions legible, spelled correctly, inside the safe zone
- [ ] On-screen text spelled correctly

Verdict (fill in): PASS / REJECT, with the frame number for any failure.
"""


def frame_timestamps(duration: float, count: int) -> list[float]:
    """Evenly spaced sample points, one per segment of the video."""
    if count < 1:
        raise ValueError("count must be at least 1")
    if duration <= 0:
        raise ValueError("duration must be positive")
    return [round((i + 0.5) * duration / count, 3) for i in range(count)]


def probe_duration(path: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "json", str(path)],
        capture_output=True, text=True)
    if out.returncode != 0:
        raise RuntimeError(f"ffprobe failed on {path}: {out.stderr.strip()}")
    return float(json.loads(out.stdout)["format"]["duration"])


def probe_height(path: Path) -> int:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=height", "-of", "json", str(path)],
        capture_output=True, text=True)
    if out.returncode != 0:
        raise RuntimeError(f"ffprobe failed on {path}: {out.stderr.strip()}")
    return int(json.loads(out.stdout)["streams"][0]["height"])


def run(cmd: list[str]) -> None:
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        print(proc.stderr[-2000:], file=sys.stderr)
        raise RuntimeError(f"command failed: {' '.join(cmd[:3])} ...")


def build_sheet(video: Path, reference: Path, out: Path, count: int) -> None:
    duration = probe_duration(video)
    stamps = frame_timestamps(duration, count)
    cols = 3
    rows = (count + cols - 1) // cols
    with tempfile.TemporaryDirectory() as tmp:
        tmpdir = Path(tmp)
        for i, ts in enumerate(stamps):
            # format=yuvj420p: modern ffmpeg mjpeg encoding rejects
            # limited-range YUV without the conversion.
            run(["ffmpeg", "-y", "-ss", str(ts), "-i", str(video),
                 "-frames:v", "1", "-vf", "format=yuvj420p", "-q:v", "3",
                 str(tmpdir / f"frame_{i:02d}.jpg")])
        tiled = tmpdir / "tiled.jpg"
        run(["ffmpeg", "-y", "-i", str(tmpdir / "frame_%02d.jpg"),
             "-vf", f"scale=360:-1,format=yuvj420p,tile={cols}x{rows}",
             "-frames:v", "1", str(tiled)])
        height = probe_height(tiled)
        run(["ffmpeg", "-y", "-i", str(tiled), "-i", str(reference),
             "-filter_complex",
             f"[1:v]scale=-1:{height}[ref];[0:v][ref]hstack=inputs=2,"
             "format=yuvj420p[out]",
             "-map", "[out]", "-frames:v", "1", str(out)])


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("video", type=Path)
    ap.add_argument("reference", type=Path, help="the locked reference still")
    ap.add_argument("--out", type=Path, required=True, help="contact sheet image")
    ap.add_argument("--frames", type=int, default=6)
    args = ap.parse_args(argv)

    for path in (args.video, args.reference):
        if not path.is_file():
            print(f"ERROR: no such file: {path}", file=sys.stderr)
            return 1
    try:
        build_sheet(args.video, args.reference, args.out, args.frames)
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    checklist = args.out.with_suffix(".md")
    checklist.write_text(CHECKLIST.format(video=args.video, reference=args.reference),
                         encoding="utf-8")
    print(f"wrote {args.out} and {checklist}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
