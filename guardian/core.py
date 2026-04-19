from __future__ import annotations

from math import sqrt


def generate_synthetic_telemetry(length: int = 120) -> list[dict[str, float]]:
    samples: list[dict[str, float]] = []
    for minute in range(length):
        db_latency = 25.0 + (minute % 11) * 1.7
        if minute >= length - 20:
            db_latency += (minute - (length - 20)) * 6.0
        api_latency = 80.0 + (db_latency * 1.6)
        mobile_slowdown = 0.15 + (api_latency / 700.0)
        error_rate = 0.01 if minute < length - 15 else 0.04 + (minute - (length - 15)) * 0.006
        samples.append(
            {
                "minute": float(minute),
                "db_latency_ms": db_latency,
                "api_latency_ms": api_latency,
                "mobile_slowdown": mobile_slowdown,
                "error_rate": min(error_rate, 0.25),
                "cpu_pct": 35.0 + (minute % 13) * 2.0,
                "memory_mb": 240.0 + (minute % 9) * 8.0,
            }
        )
    return samples


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _stddev(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    mean = _mean(values)
    variance = sum((value - mean) ** 2 for value in values) / len(values)
    return sqrt(variance)


def detect_anomalies(samples: list[dict[str, float]], field: str = "api_latency_ms") -> list[int]:
    series = [sample[field] for sample in samples]
    mean = _mean(series)
    stddev = _stddev(series)
    if stddev == 0:
        return []
    return [index for index, value in enumerate(series) if (value - mean) / stddev > 1.5]


def discover_causal_edges(samples: list[dict[str, float]]) -> list[tuple[str, str, float]]:
    fields = ["db_latency_ms", "api_latency_ms", "mobile_slowdown", "error_rate"]
    edges: list[tuple[str, str, float]] = []
    for left, right in zip(fields, fields[1:]):
        left_values = [sample[left] for sample in samples]
        right_values = [sample[right] for sample in samples]
        left_mean = _mean(left_values)
        right_mean = _mean(right_values)
        numerator = sum((a - left_mean) * (b - right_mean) for a, b in zip(left_values, right_values))
        left_norm = sqrt(sum((a - left_mean) ** 2 for a in left_values))
        right_norm = sqrt(sum((b - right_mean) ** 2 for b in right_values))
        score = numerator / (left_norm * right_norm) if left_norm and right_norm else 0.0
        edges.append((left, right, round(score, 4)))
    return edges


def predict_slo_violation(samples: list[dict[str, float]], lookback: int = 5) -> dict[str, float | bool]:
    window = samples[-lookback:]
    avg_error = _mean([sample["error_rate"] for sample in window])
    avg_api_latency = _mean([sample["api_latency_ms"] for sample in window])
    slope = window[-1]["api_latency_ms"] - window[0]["api_latency_ms"] if len(window) >= 2 else 0.0
    risk_score = (avg_error * 4.0) + (avg_api_latency / 500.0) + max(slope, 0.0) / 250.0
    return {
        "risk_score": round(risk_score, 4),
        "predicted_violation": risk_score >= 1.0,
        "lead_time_minutes": 5.0 if risk_score >= 1.0 else 0.0,
    }
