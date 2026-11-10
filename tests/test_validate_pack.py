from pathlib import Path

import validate_pack

ROOT = Path(__file__).resolve().parent.parent


def base_pack(tmp_path, **overrides):
    still = tmp_path / "reference" / "still.png"
    still.parent.mkdir(parents=True, exist_ok=True)
    still.write_bytes(b"png")
    pack = {
        "name": "Test",
        "locked": True,
        "lora": "forbidden",
        "face_generation": "forbidden",
        "reference": {"still": "reference/still.png"},
        "voice": {"id": "am_michael", "speed": 1.0},
        "motion": {
            "source": "image-to-video from reference stills only",
            "clip_seconds": {"min": 2, "max": 5},
        },
    }
    pack.update(overrides)
    return pack


def test_bundled_tara_pack_is_valid():
    pack_dir = ROOT / "characters" / "tara"
    pack = validate_pack.load_pack(pack_dir)
    assert validate_pack.validate_pack(pack, pack_dir) == []


def test_template_yaml_loads():
    pack_dir = ROOT / "characters" / "_template"
    pack = validate_pack.load_pack(pack_dir)
    assert pack["voice"]["id"] == "am_michael"
    assert pack["motion"]["clip_seconds"]["max"] == 5


def test_valid_locked_pack_passes(tmp_path):
    pack = base_pack(tmp_path)
    assert validate_pack.validate_pack(pack, tmp_path) == []


def test_locked_pack_with_lora_allowed_fails(tmp_path):
    pack = base_pack(tmp_path, lora="allowed")
    errors = validate_pack.validate_pack(pack, tmp_path)
    assert any("lora" in e for e in errors)


def test_locked_pack_with_face_generation_allowed_fails(tmp_path):
    pack = base_pack(tmp_path, face_generation="allowed")
    errors = validate_pack.validate_pack(pack, tmp_path)
    assert any("face_generation" in e for e in errors)


def test_locked_pack_with_long_clips_fails(tmp_path):
    pack = base_pack(tmp_path)
    pack["motion"]["clip_seconds"]["max"] = 9
    errors = validate_pack.validate_pack(pack, tmp_path)
    assert any("5 seconds" in e for e in errors)


def test_locked_pack_text_to_video_fails(tmp_path):
    pack = base_pack(tmp_path)
    pack["motion"]["source"] = "text-to-video"
    errors = validate_pack.validate_pack(pack, tmp_path)
    assert any("image-to-video" in e for e in errors)


def test_missing_reference_still_fails(tmp_path):
    pack = base_pack(tmp_path)
    pack["reference"]["still"] = "reference/nope.png"
    errors = validate_pack.validate_pack(pack, tmp_path)
    assert any("not found" in e for e in errors)


def test_unlocked_pack_may_allow_lora(tmp_path):
    pack = base_pack(tmp_path, locked=False, lora="allowed",
                     face_generation="allowed")
    pack["motion"]["clip_seconds"]["max"] = 9
    assert validate_pack.validate_pack(pack, tmp_path) == []


def test_fallback_parser_matches_pack_shape():
    text = (ROOT / "characters" / "tara" / "character.yaml").read_text()
    pack = validate_pack._fallback_yaml(text)
    assert pack["name"] == "Tara"
    assert pack["locked"] is True
    assert pack["lora"] == "forbidden"
    assert pack["motion"]["clip_seconds"]["max"] == 5
    assert "fixed camera" in pack["motion"]["permitted"]
