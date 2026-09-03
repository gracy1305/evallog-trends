"""Command-line entry point: evallog-trends <log_dir> --task <task> --out <png>."""

from __future__ import annotations

import argparse
from pathlib import Path

from evallog_trends.aggregate import load_run_records
from evallog_trends.plot import plot_capability_over_time
from evallog_trends.stats import wilson_interval


def main() -> None:
    """Parse args, load logs, print a summary table, and write a trend chart."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log_dir", type=Path, help="directory of EvalLog *.json files")
    parser.add_argument("--task", required=True, help="task name to summarize/plot")
    parser.add_argument("--out", type=Path, default=Path("trend.png"), help="output PNG path")
    parser.add_argument("--confidence", type=float, default=0.95)
    args = parser.parse_args()

    records = load_run_records(args.log_dir)
    task_records = [r for r in records if r.task == args.task]
    if not task_records:
        raise SystemExit(f"No usable records for task {args.task!r} in {args.log_dir}")

    by_model: dict[str, list[int]] = {}
    for r in task_records:
        by_model.setdefault(r.model, [0, 0])
        by_model[r.model][0] += r.successes
        by_model[r.model][1] += r.n

    print(f"{'model':<32} {'n':>5}   success rate ({int(args.confidence * 100)}% CI)")
    for model, (successes, n) in sorted(by_model.items()):
        sr = wilson_interval(successes, n, confidence=args.confidence)
        print(f"{model:<32} {n:>5}   {sr.point:5.1%}  [{sr.low:5.1%}, {sr.high:5.1%}]")

    plot_capability_over_time(records, args.task, args.out, confidence=args.confidence)
    print(f"\nWrote {args.out}")


if __name__ == "__main__":
    main()
