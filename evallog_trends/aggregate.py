"""Turn a directory of inspect-robots EvalLog files into a tidy trend table.

ASSUMPTIONS TO VERIFY: this module's field lookups are reconstructed from
inspect-robots' public docs and README (EvalLog.samples, SceneResult.status,
git-revision-stamped config, eval.task / eval.created), not from reading the
actual EvalLog dataclass source. Before relying on this for a real PR or
proposal, diff `_extract_record`'s field paths against
`inspect_robots.log.EvalLog` in a local clone and adjust as needed -- the
aggregation and statistics logic underneath does not depend on getting the
field paths exactly right on the first try.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True)
class RunRecord:
    """One EvalLog file, reduced to what the trend view needs.

    Attributes:
        model: the policy identity, e.g. "anthropic/claude-opus-5".
        task: the task/benchmark name, e.g. "kitchenbench/pour_pasta".
        embodiment: the embodiment name, e.g. "yam_arms".
        created: when the run was created (used as the x-axis).
        successes: count of scenes judged successful.
        n: total scenes attempted.
    """

    model: str
    task: str
    embodiment: str
    created: datetime
    successes: int
    n: int


def _scene_succeeded(scene: dict) -> bool | None:
    """Judge one scene's outcome, preferring an explicit operator verdict.

    Returns True/False if a verdict exists, or None if the scene has no
    interpretable outcome yet (e.g. cancelled with no operator judgement).
    """
    verdict = scene.get("operator_judgement")
    if verdict in ("pass", "success", True):
        return True
    if verdict in ("fail", "failure", False):
        return False

    status = scene.get("status")
    if status == "success":
        return True
    if status in ("error", "cancelled"):
        return False

    reduced = scene.get("reduced") or {}
    if "success_at_end" in reduced:
        return bool(reduced["success_at_end"] >= 0.5)

    return None


def _extract_record(log: dict, source: Path) -> RunRecord | None:
    """Reduce one parsed EvalLog dict to a RunRecord, or None if unusable."""
    eval_meta = log.get("eval", {})
    config = log.get("config") or log.get("plan") or {}

    task = eval_meta.get("task") or "unknown-task"
    model = config.get("policy") or config.get("model") or "unknown-model"
    embodiment = config.get("embodiment") or "unknown-embodiment"

    created_raw = eval_meta.get("created") or log.get("created")
    if not created_raw:
        return None
    try:
        created = datetime.fromisoformat(str(created_raw).replace("Z", "+00:00"))
    except ValueError:
        return None

    scenes = log.get("samples") or []
    outcomes = [o for o in (_scene_succeeded(s) for s in scenes) if o is not None]
    if not outcomes:
        return None

    return RunRecord(
        model=str(model),
        task=str(task),
        embodiment=str(embodiment),
        created=created,
        successes=sum(outcomes),
        n=len(outcomes),
    )


def load_run_records(log_dir: Path) -> list[RunRecord]:
    """Load every parseable EvalLog *.json file under log_dir into RunRecords.

    Files that don't parse as JSON, or that don't contain interpretable
    scene outcomes, are skipped rather than raising -- a trend tool should
    degrade gracefully on a directory of heterogeneous, partially-broken
    real-world logs.

    Args:
        log_dir: directory containing EvalLog *.json files (searched
            recursively).

    Returns:
        A list of RunRecord, one per usable log file, unsorted.
    """
    records: list[RunRecord] = []
    for path in sorted(log_dir.rglob("*.json")):
        try:
            log = json.loads(path.read_text())
        except (json.JSONDecodeError, OSError):
            continue
        record = _extract_record(log, path)
        if record is not None:
            records.append(record)
    return records
