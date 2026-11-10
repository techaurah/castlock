import pytest

import captions


def words(*specs):
    return [{"word": w, "start": s, "end": e} for w, s, e in specs]


def test_ass_time_formats():
    assert captions.ass_time(0) == "0:00:00.00"
    assert captions.ass_time(1.5) == "0:00:01.50"
    assert captions.ass_time(65.25) == "0:01:05.25"
    assert captions.ass_time(3661.07) == "1:01:01.07"
    assert captions.ass_time(-2) == "0:00:00.00"


def test_group_words_respects_max_words():
    ws = words(("a", 0.0, 0.2), ("b", 0.2, 0.4), ("c", 0.4, 0.6), ("d", 0.6, 0.8))
    groups = captions.group_words(ws, max_words=3)
    assert [len(g) for g in groups] == [3, 1]


def test_group_words_splits_on_pause():
    ws = words(("a", 0.0, 0.2), ("b", 1.0, 1.2))
    groups = captions.group_words(ws, max_words=3, max_pause=0.35)
    assert [len(g) for g in groups] == [1, 1]


def test_build_ass_safe_zone_style_and_events():
    ws = words(("Hello", 0.0, 0.4), ("world", 0.4, 0.9), ("again", 0.9, 1.4))
    ass = captions.build_ass(ws)
    assert "PlayResX: 1080" in ass and "PlayResY: 1920" in ass
    assert ",170,230,470,1" in ass  # MarginL, MarginR, MarginV inside the safe zone
    dialogue = [l for l in ass.splitlines() if l.startswith("Dialogue:")]
    assert len(dialogue) == 3  # one event per word
    assert dialogue[0].endswith(",Hello")
    assert dialogue[1].endswith(",Hello world")
    assert dialogue[2].endswith(",Hello world again")
    assert "0:00:00.00,0:00:00.40" in dialogue[0]


def test_build_ass_rejects_unsafe_margins():
    ws = words(("Hi", 0.0, 0.3))
    with pytest.raises(ValueError):
        captions.build_ass(ws, margin_v=100)
    with pytest.raises(ValueError):
        captions.build_ass(ws, margin_r=120)
    with pytest.raises(ValueError):
        captions.build_ass(ws, margin_l=50)


def test_escape_ass_strips_braces():
    assert captions.escape_ass("a{b}c\\d") == "abcd"
