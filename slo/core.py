from __future__ import annotations

from dataclasses import dataclass
from math import ceil
from typing import Iterable


@dataclass(frozen=True)
class Event:
    timestamp_s: int
    latency_ms: float
    status_code: int


@dataclass(frozen=True)
class SLOEvaluation:
    availability: float
    error_rate: float
    throughput_rps: float
    latency_p50_ms: float
    latency_p95_ms: float
    latency_p99_ms: float
    slo_met: dict[str, bool]


def _percentile(values: list[float], percentile: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    index = ceil((percentile / 100.0) * len(ordered)) - 1
    index = min(max(index, 0), len(ordered) - 1)
    return float(ordered[index])


def compute_availability(events: Iterable[Event]) -> float:
    series = list(events)
    if not series:
        return 1.0
    successes = sum(1 for event in series if event.status_code < 500)
    return successes / len(series)


def compute_error_rate(events: Iterable[Event]) -> float:
    series = list(events)
    if not series:
        return 0.0
    failures = sum(1 for event in series if event.status_code >= 500)
    return failures / len(series)


def compute_latency_percentiles(events: Iterable[Event]) -> dict[str, float]:
    latencies = [event.latency_ms for event in events]
    return {
        "p50": _percentile(latencies, 50),
        "p95": _percentile(latencies, 95),
        "p99": _percentile(latencies, 99),
    }


def compute_throughput(events: Iterable[Event]) -> float:
    series = list(events)
    if not series:
        return 0.0
    start = min(event.timestamp_s for event in series)
    end = max(event.timestamp_s for event in series)
    duration = max(end - start + 1, 1)
    return len(series) / duration


def compute_error_budget(target: float, observed_availability: float) -> dict[str, float]:
    budget = max(0.0, 1.0 - target)
    consumed = max(0.0, target - observed_availability)
    burn_rate = consumed / budget if budget > 0 else 0.0
    remaining = max(0.0, budget - consumed)
    return {
        "budget": budget,
        "consumed": consumed,
        "remaining": remaining,
        "burn_rate": burn_rate,
    }


def evaluate_slos(events: Iterable[Event], slo_config: dict[str, float]) -> SLOEvaluation:
    series = list(events)
    availability = compute_availability(series)
    error_rate = compute_error_rate(series)
    throughput = compute_throughput(series)
    latency = compute_latency_percentiles(series)
    return SLOEvaluation(
        availability=availability,
        error_rate=error_rate,
        throughput_rps=throughput,
        latency_p50_ms=latency["p50"],
        latency_p95_ms=latency["p95"],
        latency_p99_ms=latency["p99"],
        slo_met={
            "availability": availability >= slo_config.get("availability_slo", 0.0),
            "latency_p99": latency["p99"] <= slo_config.get("latency_p99_slo_ms", float("inf")),
            "error_rate": error_rate <= slo_config.get("error_rate_slo", 1.0),
        },
    )
