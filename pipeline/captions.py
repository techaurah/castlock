#!/usr/bin/env python3
"""Build word-by-word ASS captions constrained to the center safe zone.

Input: a timings JSON as written by timings.py, either a list of word
objects or {"words": [...]}. Each word object: {"word", "start", "end"}
in seconds.

The style bakes in the house safe-zone rule for a 1080x1920 frame
(docs/house-rules.md): captions are bottom-center anchored but lifted into
the safe zone, MarginV 470 by default, so the caption band baseline sits
around y 1450, clear of the platform caption block at the frame bottom.
Margins are validated: left at least 140, right at least 200, bottom at
least 360. Values outside the safe zone are an error, not a warning.

Word-by-word means each word gets its own dialogue event spanning the gap
between consecutive word starts, grouped a few words per line so the line
stays readable.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PLAY_RES_X = 1080
PLAY_RES_Y = 1920
MIN_MARGIN_L = 140
MIN_MARGIN_R = 200
MIN_MARGIN_V = 360

HEADER = """[Script Info]
Title: CastLock captions
ScriptType: v4.00+
PlayResX: {resx}
PlayResY: {resy}
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: CastLock,Arial,{fontsize},&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,-1,0,0,0,100,100,0,0,1,3,1,2,{ml},{mr},{mv},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def ass_time(seconds: float) -> str:
    """Format seconds as an ASS timestamp H:MM:SS.cc."""
    if seconds < 0:
        seconds = 0.0
    total_centi = int(round(seconds * 100))
    centi = total_centi % 100
    total_sec = total_centi // 100
    sec = total_sec % 60
    total_min = total_sec // 60
    minute = total_min % 60
    hour = total_min // 60
    return f"{hour}:{minute:02d}:{sec:02d}.{centi:02d}"


def escape_ass(text: str) -> str:
    return text.replace("\\", "").replace("{", "").replace("}", "").strip()


def group_words(words: list[dict], max_words: int = 3, max_pause: float = 0.35) -> list[list[dict]]:
    """Group timed words into caption lines.

    A new line starts when the group reaches max_words, or when the pause
    before the next word exceeds max_pause seconds.
    """
    groups: list[list[dict]] = []
    current: list[dict] = []
    for word in words:
        if current:
            pause = float(word["start"]) - float(current[-1]["end"])
            if len(current) >= max_words or pause > max_pause:
                groups.append(current)
                current = []
        current.append(word)
    if current:
        groups.append(current)
    return groups


def build_ass(words: list[dict], font_size: int = 64, margin_l: int = 170,
              margin_r: int = 230, margin_v: int = 470, max_words: int = 3) -> str:
    """Render the full ASS file text for a word timing list.

    One dialogue event per word (word-by-word highlight timing): each event
    shows its whole line, but starts at its own word's start time, so the
    visible line grows word by word in step with the narration.
    """
    if margin_l < MIN_MARGIN_L or margin_r < MIN_MARGIN_R or margin_v < MIN_MARGIN_V:
        raise ValueError(
            "margins violate the safe zone: need MarginL >= "
            f"{MIN_MARGIN_L}, MarginR >= {MIN_MARGIN_R}, MarginV >= {MIN_MARGIN_V}; "
            f"got L={margin_l} R={margin_r} V={margin_v}"
        )
    text = HEADER.format(resx=PLAY_RES_X, resy=PLAY_RES_Y, fontsize=font_size,
                         ml=margin_l, mr=margin_r, mv=margin_v)
    events: list[str] = []
    flat = [w for w in words if str(w.get("word", "")).strip()]
    for group in group_words(flat, max_words=max_words):
        line = " ".join(escape_ass(str(w["word"])) for w in group)
        for idx, word in enumerate(group):
            start = float(word["start"])
            end = float(group[idx + 1]["start"]) if idx + 1 < len(group) else float(word["end"])
            if end <= start:
                end = start + 0.05
            partial = " ".join(escape_ass(str(w["word"])) for w in group[: idx + 1])
            events.append(
                f"Dialogue: 0,{ass_time(start)},{ass_time(end)},CastLock,,0,0,0,,{partial}"
            )
        _ = line  # full line is the union of the partial events
    return text + "\n".join(events) + ("\n" if events else "")


def load_words(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        words = data.get("words", [])
    else:
        words = data
    if not isinstance(words, list):
        raise ValueError("timings JSON must be a list or an object with a 'words' list")
    return words


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("timings", type=Path, help="timings JSON from timings.py")
    ap.add_argument("--out", type=Path, required=True, help="output .ass path")
    ap.add_argument("--font-size", type=int, default=64)
    ap.add_argument("--margin-l", type=int, default=170)
    ap.add_argument("--margin-r", type=int, default=230)
    ap.add_argument("--margin-v", type=int, default=470)
    ap.add_argument("--max-words", type=int, default=3)
    args = ap.parse_args(argv)

    try:
        words = load_words(args.timings)
        ass = build_ass(words, font_size=args.font_size, margin_l=args.margin_l,
                        margin_r=args.margin_r, margin_v=args.margin_v,
                        max_words=args.max_words)
    except (OSError, ValueError, KeyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    args.out.write_text(ass, encoding="utf-8")
    print(f"wrote {args.out} ({len(words)} words)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
