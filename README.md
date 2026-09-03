# evallog-trends

A small, hardware-free prototype: turn a directory of `inspect-robots`
`EvalLog` files into a capability-over-time chart, with confidence
intervals instead of bare point estimates.

## Why

Robocurve's own roadmap talks about "building towards the METR plot for
physical automation" -- but that plot isn't just "run more evals," it's an
*aggregation and statistics* layer sitting on top of individual eval runs.
Every `inspect-robots` run already produces a rich, git-revision-stamped
`EvalLog`; nothing currently turns a directory of those logs into a trend
view across models and time.

The second, related problem this tool addresses: physical-robot evals run
at n=5-20 per task, because real hardware is slow and expensive (unlike
LLM evals at n=1000s). At that sample size, a plain success-rate point
estimate is close to meaningless on its own -- an 8/10 run and a 4/5 run
both "look like" 80%, but carry very different uncertainty, and two
models' point estimates can differ by 20 points while being statistically
indistinguishable. The Wilson score interval used here stays well-behaved
at small n and near 0%/100%, which the usual normal-approximation
interval does not.

## What it does

1. `evallog_trends.aggregate.load_run_records` walks a directory of
   `EvalLog` `*.json` files and reduces each to a `(model, task,
   embodiment, timestamp, successes, n)` record, skipping unparseable or
   uninterpretable files rather than crashing.
2. `evallog_trends.stats.wilson_interval` computes a small-sample-safe
   confidence interval for any (successes, n) pair.
3. `evallog_trends.plot.plot_capability_over_time` renders one line per
   model, success rate against time, with a shaded confidence band.
4. `evallog_trends.cli` ties it together: prints a summary table and
   writes the chart.

## Try it (synthetic data, no Robocurve access needed)

```bash
pip install numpy scipy matplotlib pytest
python3 generate_sample_logs.py          # writes sample_logs/*.json (fake data)
python3 -m pytest tests/ -v              # 5/5 passing
python3 -m evallog_trends.cli sample_logs --task kitchenbench/pour_pasta --out trend.png
```

## Point it at real data

`aggregate._extract_record`'s field paths (`eval.task`, `eval.created`,
`config.policy`, `samples[].status`, `samples[].operator_judgement`) are
reconstructed from `inspect-robots`' public docs and README, **not from
reading the actual `EvalLog` dataclass source** -- I don't have a local
clone with real logs to verify against yet. Before this is anything more
than a proof of concept, the field paths need a pass against
`inspect_robots.log.EvalLog` in a real checkout. The aggregation and
statistics logic underneath doesn't depend on getting that exactly right
on the first try -- only `_extract_record` and `_scene_succeeded` would
need to change.

## Possible next steps

- Group by `embodiment` as well as `model`, since sim vs. real-hardware
  results shouldn't be pooled into one line.
- A `--min-n` flag that greys out or drops points below a trustworthy
  sample size, instead of just showing a wide band.
- Feed this from `worldpolicies`' published model cards directly, so the
  chart could run against Robocurve's own public eval-number history
  without needing raw log files at all.
