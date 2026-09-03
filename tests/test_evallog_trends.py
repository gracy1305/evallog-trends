"""Tests for evallog_trends.stats and evallog_trends.aggregate."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pytest

from evallog_trends.aggregate import load_run_records
from evallog_trends.stats import wilson_interval


def test_wilson_interval_point_estimate_matches_naive_rate() -> None:
    sr = wilson_interval(successes=8, n=10)
    assert sr.point == pytest.approx(0.8)


def test_wilson_interval_is_wide_at_small_n() -> None:
    """The whole point of this tool: small n means real uncertainty."""
    small = wilson_interval(successes=4, n=5)
    large = wilson_interval(successes=400, n=500)
    assert small.width > large.width


def test_wilson_interval_bounds_are_clamped_to_unit_range() -> None:
    perfect = wilson_interval(successes=5, n=5)
    zero = wilson_interval(successes=0, n=5)
    assert 0.0 <= perfect.low <= perfect.high <= 1.0
    assert 0.0 <= zero.low <= zero.high <= 1.0


def test_wilson_interval_rejects_invalid_input() -> None:
    with pytest.raises(ValueError):
        wilson_interval(successes=0, n=0)
    with pytest.raises(ValueError):
        wilson_interval(successes=6, n=5)


def test_load_run_records_reads_valid_logs_and_skips_junk(tmp_path: Path) -> None:
    good_log = {
        "eval": {"task": "kitchenbench/pour_pasta", "created": "2026-07-01T00:00:00Z"},
        "config": {"policy": "anthropic/claude-opus-5", "embodiment": "yam_arms"},
        "samples": [
            {"scene_id": "a", "status": "success", "operator_judgement": "pass"},
            {"scene_id": "b", "status": "error", "operator_judgement": "fail"},
        ],
    }
    (tmp_path / "good.json").write_text(json.dumps(good_log))
    (tmp_path / "junk.json").write_text("{not valid json")
    (tmp_path / "empty_scenes.json").write_text(
        json.dumps({"eval": {"task": "x", "created": "2026-07-01T00:00:00Z"}, "samples": []})
    )

    records = load_run_records(tmp_path)

    assert len(records) == 1
    record = records[0]
    assert record.model == "anthropic/claude-opus-5"
    assert record.task == "kitchenbench/pour_pasta"
    assert record.successes == 1
    assert record.n == 2
    assert record.created == datetime.fromisoformat("2026-07-01T00:00:00+00:00")
