from __future__ import annotations

from datetime import date, timedelta


def daterange(start: date, days: int) -> list[date]:
    return [start + timedelta(days=i) for i in range(days)]


def clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def safe_div(n: float, d: float, default: float = 0.0) -> float:
    return n / d if d else default

