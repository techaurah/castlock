import json
import wave

import timings


def _tiny_wav(path):
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(16000)
        wav.writeframes(b"\x00\x00" * 16000)  # 1 second of silence


def test_estimate_covers_duration_and_is_monotonic():
    words = timings.estimate_timings("one two three four", 4.0)
    assert len(words) == 4
    assert words[0]["start"] == 0.0
    assert words[-1]["end"] == 4.0
    for prev, nxt in zip(words, words[1:]):
        assert nxt["start"] >= prev["start"]
        assert nxt["start"] == prev["end"]


def test_estimate_longer_words_get_more_time():
    words = timings.estimate_timings("a extraordinarily", 3.0)
    short, long_ = words
    assert (long_["end"] - long_["start"]) > (short["end"] - short["start"])


def test_estimate_empty_text():
    assert timings.estimate_timings("", 5.0) == []
    assert timings.estimate_timings("   ", 5.0) == []


def test_main_falls_back_to_estimation_when_whisper_fails(tmp_path, monkeypatch):
    wav = tmp_path / "n.wav"
    _tiny_wav(wav)
    text = tmp_path / "script.txt"
    text.write_text("hello world")
    out = tmp_path / "timings.json"

    def boom(*a, **k):
        raise RuntimeError("model not cached")

    monkeypatch.setattr(timings, "whisper_timings", boom)
    rc = timings.main([str(wav), "--text", str(text), "--out", str(out)])
    assert rc == 0
    payload = json.loads(out.read_text())
    assert payload["estimated"] is True
    assert [w["word"] for w in payload["words"]] == ["hello", "world"]


def test_main_errors_without_text_when_whisper_fails(tmp_path, monkeypatch):
    wav = tmp_path / "n.wav"
    _tiny_wav(wav)

    def boom(*a, **k):
        raise ImportError("no faster_whisper")

    monkeypatch.setattr(timings, "whisper_timings", boom)
    rc = timings.main([str(wav), "--out", str(tmp_path / "t.json")])
    assert rc == 1
