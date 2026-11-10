from pathlib import Path

import assemble

LOUDNORM_STDERR = """
[Parsed_loudnorm_0 @ 0x55f0] 
{
	"input_i" : "-24.10",
	"input_tp" : "-3.50",
	"input_lra" : "5.20",
	"input_thresh" : "-34.90",
	"output_i" : "-14.05",
	"output_tp" : "-1.00",
	"output_lra" : "4.90",
	"output_thresh" : "-24.80",
	"normalization_type" : "linear",
	"target_offset" : "0.20"
}
"""


def test_mix_command_structure():
    cmd = assemble.build_mix_command(
        [Path("a.mp4"), Path("b.mp4")], Path("narr.wav"), None,
        Path("caps.ass"), Path("tmp.mp4"))
    joined = " ".join(cmd)
    assert "concat=n=2:v=1:a=0" in joined
    assert "scale=1080:1920" in joined
    assert "subtitles=filename='caps.ass'" in joined
    assert "libx264" in joined


def test_mix_command_with_music_ducks():
    cmd = assemble.build_mix_command(
        [Path("a.mp4")], Path("narr.wav"), Path("m.mp3"), None, Path("t.mp4"))
    joined = " ".join(cmd)
    assert "sidechaincompress" in joined
    assert "asplit=2" in joined
    assert "amix=inputs=2" in joined
    assert "-stream_loop" in cmd


def test_mix_command_without_captions_has_no_subtitles():
    cmd = assemble.build_mix_command(
        [Path("a.mp4")], Path("n.wav"), None, None, Path("t.mp4"))
    assert "subtitles" not in " ".join(cmd)


def test_parse_loudnorm_extracts_json():
    measured = assemble.parse_loudnorm(LOUDNORM_STDERR)
    assert measured["input_i"] == "-24.10"
    assert measured["input_tp"] == "-3.50"
    assert measured["target_offset"] == "0.20"


def test_parse_loudnorm_fails_without_json():
    import pytest

    with pytest.raises(ValueError):
        assemble.parse_loudnorm("no measurements here")


def test_apply_command_uses_measured_values():
    measured = assemble.parse_loudnorm(LOUDNORM_STDERR)
    cmd = assemble.build_apply_command(Path("in.mp4"), Path("out.mp4"), measured)
    joined = " ".join(cmd)
    assert "measured_I=-24.10" in joined
    assert "loudnorm=I=-14.0:TP=-1.0" in joined
    assert '"copy"' not in joined and "copy" in cmd


def test_measure_command_targets_house_standard():
    cmd = assemble.build_measure_command(Path("x.mp4"))
    joined = " ".join(cmd)
    assert "loudnorm=I=-14.0:TP=-1.0:LRA=11.0:print_format=json" in joined


def test_sidecar_marks_ai_generated():
    data = assemble.sidecar(Path("out.mp4"), ["12345"], "tara", None)
    assert data["ai_generated"] is True
    assert data["seeds"] == ["12345"]
    names = {m["name"] for m in data["models"]}
    assert names == {"Z-Image Turbo", "Wan 2.2", "Kokoro-82M"}
    assert all(m["license"] == "Apache 2.0" for m in data["models"])
