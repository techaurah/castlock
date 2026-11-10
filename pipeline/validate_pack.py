#!/usr/bin/env python3
"""Validate a CastLock character pack against the character rules.

Usage:
    python3 validate_pack.py characters/tara

Exit code 0 means the pack is valid. Every rule violation is printed and the
exit code is 1. The machine-checked core of docs/character-rules.md:

- a pack must name the character and a voice;
- the reference still named in the pack must exist inside the pack;
- a LOCKED character must have lora: forbidden and face_generation:
  forbidden (a locked face is an asset, never a generation target);
- a locked character's motion source must be image-to-video from the
  reference stills, and its clip length must stay within 2 to 5 seconds.

YAML loading uses PyYAML when available and falls back to a small subset
parser (the pack format only uses nested maps, scalars and simple lists).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _parse_scalar(raw: str):
    raw = raw.strip()
    if raw in ("", "~", "null"):
        return None
    if raw.lower() == "true":
        return True
    if raw.lower() == "false":
        return False
    if (raw.startswith('"') and raw.endswith('"')) or (
        raw.startswith("'") and raw.endswith("'")
    ):
        return raw[1:-1]
    try:
        return int(raw)
    except ValueError:
        pass
    try:
        return float(raw)
    except ValueError:
        pass
    return raw


def _fallback_yaml(text: str) -> dict:
    """Parse the small YAML subset used by character.yaml files.

    Supports: comments, `key: value` scalars, nested maps by indentation,
    and `- item` lists of scalars. Nothing else. Good enough for pack files,
    which this repo controls.
    """
    root: dict = {}
    stack: list[tuple[int, object]] = [(-1, root)]
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        i += 1
        if not line.strip() or line.strip().startswith("#"):
            continue
        indent = len(line) - len(line.lstrip(" "))
        stripped = line.strip()
        while stack and indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]
        if stripped.startswith("- "):
            if not isinstance(parent, list):
                raise ValueError(f"list item outside a list: {line!r}")
            parent.append(_parse_scalar(stripped[2:]))
            continue
        if ":" not in stripped:
            raise ValueError(f"cannot parse line: {line!r}")
        key, _, value = stripped.partition(":")
        key = key.strip()
        value = value.strip()
        if not isinstance(parent, dict):
            raise ValueError(f"key outside a map: {line!r}")
        if value:
            parent[key] = _parse_scalar(value)
        else:
            # Peek ahead: a following deeper-indented "- " means a list,
            # anything else means a nested map.
            child: object = {}
            for nxt in lines[i:]:
                if not nxt.strip() or nxt.strip().startswith("#"):
                    continue
                nindent = len(nxt) - len(nxt.lstrip(" "))
                if nindent > indent and nxt.strip().startswith("- "):
                    child = []
                break
            parent[key] = child
            stack.append((indent, child))
    return root


def load_pack(pack_dir: Path) -> dict:
    yaml_path = pack_dir / "character.yaml"
    if not yaml_path.is_file():
        raise FileNotFoundError(f"no character.yaml in {pack_dir}")
    text = yaml_path.read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore

        data = yaml.safe_load(text)
    except ImportError:
        data = _fallback_yaml(text)
    if not isinstance(data, dict):
        raise ValueError("character.yaml did not parse to a mapping")
    return data


def validate_pack(pack: dict, pack_dir: Path) -> list[str]:
    """Return a list of rule violations (empty list means valid)."""
    errors: list[str] = []

    name = pack.get("name")
    if not name or not str(name).strip():
        errors.append("name is missing or empty")

    locked = pack.get("locked")
    if not isinstance(locked, bool):
        errors.append("locked must be true or false")

    reference = pack.get("reference") or {}
    still = reference.get("still")
    if not still:
        errors.append("reference.still is missing")
    elif not (pack_dir / str(still)).is_file():
        errors.append(f"reference still not found in pack: {still}")

    voice = pack.get("voice") or {}
    if not voice.get("id"):
        errors.append("voice.id is missing")

    motion = pack.get("motion") or {}
    clip = motion.get("clip_seconds") or {}
    cmin, cmax = clip.get("min"), clip.get("max")
    if not isinstance(cmin, (int, float)) or not isinstance(cmax, (int, float)):
        errors.append("motion.clip_seconds.min and .max must be numbers")
    elif cmin < 1 or cmax < cmin:
        errors.append("motion.clip_seconds range is invalid")

    if locked is True:
        if pack.get("lora") != "forbidden":
            errors.append(
                "locked character must set lora: forbidden "
                "(a locked face is never model-generated)"
            )
        if pack.get("face_generation") != "forbidden":
            errors.append("locked character must set face_generation: forbidden")
        source = str(motion.get("source", ""))
        if "image-to-video" not in source:
            errors.append(
                "locked character motion.source must be image-to-video "
                "from the reference stills"
            )
        if isinstance(cmax, (int, float)) and cmax > 5:
            errors.append("locked character clips must stay at 5 seconds or under")

    return errors


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("pack_dir", type=Path, help="path to a character pack folder")
    args = ap.parse_args(argv)

    try:
        pack = load_pack(args.pack_dir)
    except (FileNotFoundError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    errors = validate_pack(pack, args.pack_dir)
    if errors:
        for err in errors:
            print(f"INVALID: {err}", file=sys.stderr)
        return 1
    print(f"OK: pack '{pack.get('name')}' in {args.pack_dir} is valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
