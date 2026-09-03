"""Small-sample-safe success-rate statistics.

Physical-robot evals run at n=5-20 per task (real hardware is expensive),
unlike LLM evals which run at n=1000s. At that sample size, a plain
successes/n point estimate is close to meaningless on its own: an 8/10 run
and a 4/5 run both "look like" 80%, but carry very different uncertainty.

This module supplies the Wilson score interval, which (unlike the naive
normal-approximation interval) stays well-behaved at small n and at success
rates near 0% or 100% -- exactly the regime physical-robot evals live in.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import sqrt

from scipy.stats import norm


@dataclass(frozen=True)
class SuccessRate:
    """A success-rate point estimate with a Wilson score confidence interval.

    Attributes:
        successes: number of successful trials.
        n: total number of trials (n >= successes >= 0).
        confidence: the confidence level used for the interval, e.g. 0.95.
        point: successes / n.
        low: lower bound of the Wilson score interval.
        high: upper bound of the Wilson score interval.
    """

    successes: int
    n: int
    confidence: float
    point: float
    low: float
    high: float

    @property
    def width(self) -> float:
        """Interval width -- a direct, at-a-glance signal of measurement noise."""
        return self.high - self.low


def wilson_interval(successes: int, n: int, confidence: float = 0.95) -> SuccessRate:
    """Compute a Wilson score confidence interval for a binomial success rate.

    Args:
        successes: number of successful trials.
        n: total number of trials. Must be >= 1.
        confidence: confidence level in (0, 1), e.g. 0.95 for a 95% CI.

    Returns:
        A SuccessRate with the point estimate and interval bounds, all
        clamped to [0, 1].

    Raises:
        ValueError: if n < 1 or successes is outside [0, n].
    """
    if n < 1:
        raise ValueError(f"n must be >= 1, got {n}")
    if not (0 <= successes <= n):
        raise ValueError(f"successes ({successes}) must be in [0, {n}]")

    z = norm.ppf(1 - (1 - confidence) / 2)
    p_hat = successes / n
    denom = 1 + z**2 / n
    center = (p_hat + z**2 / (2 * n)) / denom
    half_width = (z * sqrt(p_hat * (1 - p_hat) / n + z**2 / (4 * n**2))) / denom

    low = max(0.0, center - half_width)
    high = min(1.0, center + half_width)
    return SuccessRate(
        successes=successes,
        n=n,
        confidence=confidence,
        point=p_hat,
        low=low,
        high=high,
    )
