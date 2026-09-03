# evallog-trends

A small, hardware-free prototype: turn a directory of `inspect-robots`
`EvalLog` files into a capability-over-time chart, with confidence
intervals instead of bare point estimates.

## Why

Robocurve's public roadmap talks about "building towards the METR plot for physical automation." This prototype explores one small piece of what that could look like: an *aggregation and statistics* layer that turns individual evaluation runs into a capability-over-time view across models. It is an independent proof of concept built from Robocurve's publicly available `inspect-robots` documentation and synthetic data.

A second, related problem this tool explores is uncertainty at small sample sizes. Real-world robot evaluations can be expensive and time-consuming, so capability estimates may sometimes rely on relatively few runs. At small n, a success-rate point estimate can hide substantial uncertainty: an 8/10 run and a 4/5 run both report 80%, for example, despite different sample sizes. This prototype therefore reports Wilson score intervals alongside success rates, which remain well-behaved at small n and near 0% or 100%.

## What it does

1. `evallog_trends.aggregate.load_run_records` walks a directory of `EvalLog` `*.json` files and reduces each to a `(model, task, embodiment, timestamp, successes, n)` record, skipping unparseable or uninterpretable files rather than crashing.
2. `evallog_trends.stats.wilson_interval` computes a Wilson confidence interval for each `(successes, n)` pair.
3. `evallog_trends.plot.plot_capability_over_time` renders one line per model, success rate against time, with a shaded confidence band.
4. `evallog_trends.cli` ties it together: prints a summary table and writes the chart.

### Example output

![Capability-over-time example](trend.png)

*Example generated from synthetic evaluation data. Shaded regions show 95% Wilson confidence intervals.*

## Try it with synthetic data

```bash
pip install numpy scipy matplotlib pytest
python3 generate_sample_logs.py          # writes sample_logs/*.json (fake data)
python3 -m pytest tests/ -v              # 5/5 passing
python3 -m evallog_trends.cli sample_logs --task kitchenbench/pour_pasta --out trend.png
```

## Using real evaluation data

The current `EvalLog` field mappings are based on `inspect-robots`' public documentation and README. The aggregation and statistics layers are intentionally separated from log parsing, so adapting the prototype to changes in the underlying `EvalLog` schema only requires updating the extraction logic.

Before using this against real evaluation logs, the field mappings should be validated against the current `inspect-robots` schema.

## Possible next steps

- Group by `embodiment` as well as `model`, since sim vs. real-hardware results shouldn't be pooled into one line.
- A `--min-n` flag that greys out or drops points below a trustworthy sample size, instead of just showing a wide band.
- Add support for published evaluation results, so capability trends can be generated from public model-performance history without requiring raw `EvalLog` files.
