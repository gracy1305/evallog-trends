"""Generate synthetic EvalLog-shaped JSON files so evallog-trends is runnable
without access to real Robocurve run data. NOT real data -- for demo/testing
of the aggregation and plotting logic only.
"""

from __future__ import annotations

import json
import random
from datetime import datetime, timedelta
from pathlib import Path

OUT_DIR = Path("sample_logs")

# A rough, made-up capability curve per model: later models succeed more
# often, with realistic small-N noise. Purely illustrative.
MODELS = {
    "anthropic/claude-fable-5": (0, 0.55),
    "anthropic/claude-opus-5": (10, 0.62),
    "anthropic/claude-sonnet-5": (10, 0.58),
    "anthropic/claude-fable-5-1": (25, 0.71),
}


def make_log(model: str, day_offset: int, p_success: float, n_scenes: int) -> dict:
    created = (datetime(2026, 7, 1) + timedelta(days=day_offset)).isoformat() + "Z"
    samples = []
    for i in range(n_scenes):
        succeeded = random.random() < p_success
        samples.append(
            {
                "scene_id": f"layout-{i}",
                "status": "success" if succeeded else "error",
                "operator_judgement": "pass" if succeeded else "fail",
            }
        )
    return {
        "eval": {"task": "kitchenbench/pour_pasta", "created": created},
        "config": {"policy": model, "embodiment": "yam_arms"},
        "samples": samples,
    }


def main() -> None:
    OUT_DIR.mkdir(exist_ok=True)
    random.seed(7)
    count = 0
    for model, (start_day, p) in MODELS.items():
        for run in range(3):  # a few runs per model, spread over a couple weeks
            day = start_day + run * 5
            n_scenes = random.choice([5, 8, 10])
            log = make_log(model, day, p, n_scenes)
            fname = OUT_DIR / f"{model.replace('/', '_')}_{run}.json"
            fname.write_text(json.dumps(log, indent=2))
            count += 1
    print(f"Wrote {count} sample logs to {OUT_DIR}/")


if __name__ == "__main__":
    main()
