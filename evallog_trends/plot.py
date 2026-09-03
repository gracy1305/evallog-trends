"""Render a capability-over-time chart from RunRecords.

This is a small, literal prototype of the "METR plot for physical
automation" mentioned in Robocurve's own roadmap: success rate per model,
plotted against time, one line per model, with a shaded confidence band
so the reader can see measurement noise instead of mistaking it for signal.
"""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt

from evallog_trends.aggregate import RunRecord
from evallog_trends.stats import wilson_interval


def plot_capability_over_time(
    records: list[RunRecord],
    task: str,
    out_path: Path,
    confidence: float = 0.95,
) -> None:
    """Plot success rate (with confidence band) per model over time, for one task.

    Runs for the same (model, day) are pooled into a single Wilson interval,
    since real-hardware runs are typically too sparse per day to plot
    individually without the chart becoming unreadable noise.

    Args:
        records: RunRecords to plot (filtered internally to `task`).
        task: the task name to plot; records for other tasks are ignored.
        out_path: where to write the PNG.
        confidence: confidence level for the shaded band, e.g. 0.95.
    """
    task_records = [r for r in records if r.task == task]
    if not task_records:
        raise ValueError(f"No records found for task {task!r}")

    by_model: dict[str, dict[str, list[RunRecord]]] = defaultdict(lambda: defaultdict(list))
    for r in task_records:
        day = r.created.date().isoformat()
        by_model[r.model][day].append(r)

    fig, ax = plt.subplots(figsize=(9, 5))

    for model, by_day in sorted(by_model.items()):
        days = sorted(by_day.keys())
        points, los, his, ns = [], [], [], []
        for day in days:
            day_records = by_day[day]
            successes = sum(r.successes for r in day_records)
            n = sum(r.n for r in day_records)
            sr = wilson_interval(successes, n, confidence=confidence)
            points.append(sr.point)
            los.append(sr.low)
            his.append(sr.high)
            ns.append(n)

        x = list(range(len(days)))
        ax.plot(x, points, marker="o", label=f"{model}  (n={sum(ns)})")
        ax.fill_between(x, los, his, alpha=0.15)
        ax.set_xticks(x)
        ax.set_xticklabels(days, rotation=45, ha="right")

    ax.set_ylim(-0.02, 1.02)
    ax.set_ylabel("Success rate (Wilson %d%% CI)" % int(confidence * 100))
    ax.set_title(f"Capability over time -- {task}")
    ax.legend(loc="best", fontsize=8)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
