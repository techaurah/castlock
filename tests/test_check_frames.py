import pytest

import check_frames


def test_frame_timestamps_even_spacing():
    stamps = check_frames.frame_timestamps(30.0, 6)
    assert stamps == [2.5, 7.5, 12.5, 17.5, 22.5, 27.5]


def test_frame_timestamps_single():
    assert check_frames.frame_timestamps(10.0, 1) == [5.0]


def test_frame_timestamps_rejects_bad_inputs():
    with pytest.raises(ValueError):
        check_frames.frame_timestamps(0, 3)
    with pytest.raises(ValueError):
        check_frames.frame_timestamps(10.0, 0)
