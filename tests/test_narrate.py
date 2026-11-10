import argparse
from pathlib import Path

import narrate


def make_args(tmp_path, **kw):
    base = {"input": tmp_path / "script.md", "out": tmp_path / "n.wav",
            "voice": "am_michael", "speed": 1.0, "model": None, "voices": None,
            "dry_run": True}
    base.update(kw)
    return argparse.Namespace(**base)


def test_extract_text_drops_headings_and_rules(tmp_path):
    script = tmp_path / "s.md"
    script.write_text("# Title\n\nFirst line.\n\n---\n\nSecond line.\n")
    assert narrate.extract_text(script) == "First line. Second line."


def test_dry_run_defaults_to_am_michael(tmp_path):
    config = narrate.resolve_config(make_args(tmp_path))
    assert config["voice"] == "am_michael"
    assert config["speed"] == 1.0


def test_dry_run_voice_flag_af_heart(tmp_path):
    config = narrate.resolve_config(make_args(tmp_path, voice="af_heart"))
    assert config["voice"] == "af_heart"


def test_main_dry_run_exit_zero(tmp_path, capsys):
    script = tmp_path / "s.md"
    script.write_text("Hello world.\n")
    rc = narrate.main([str(script), "--out", str(tmp_path / "n.wav"), "--dry-run"])
    assert rc == 0
    assert '"voice": "am_michael"' in capsys.readouterr().out


def test_main_missing_input_errors(tmp_path):
    rc = narrate.main([str(tmp_path / "nope.md"), "--dry-run"])
    assert rc == 1
