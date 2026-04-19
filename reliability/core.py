from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FailureMode:
    component: str
    mode: str
    severity: int
    probability: int
    detectability: int

    @property
    def risk_priority_number(self) -> int:
        return self.severity * self.probability * self.detectability


@dataclass(frozen=True)
class Incident:
    name: str
    start_minute: int
    detected_minute: int
    recovered_minute: int
    summary: str


def inject_faults(samples: list[dict[str, float]]) -> list[dict[str, float]]:
    mutated: list[dict[str, float]] = []
    for index, sample in enumerate(samples):
        current = dict(sample)
        if index % 5 == 0:
            current["latency_ms"] += 180.0
        if index % 7 == 0:
            current["error_rate"] = min(1.0, current.get("error_rate", 0.0) + 0.15)
        if index % 9 == 0:
            current["cpu_pct"] += 25.0
        mutated.append(current)
    return mutated


def generate_fmea(modes: list[FailureMode]) -> list[dict[str, int | str]]:
    ranked = sorted(modes, key=lambda item: item.risk_priority_number, reverse=True)
    return [
        {
            "component": mode.component,
            "failure_mode": mode.mode,
            "severity": mode.severity,
            "probability": mode.probability,
            "detectability": mode.detectability,
            "rpn": mode.risk_priority_number,
        }
        for mode in ranked
    ]


def compute_mtbf(incidents: list[Incident], observation_window_minutes: int) -> float:
    if not incidents:
        return float(observation_window_minutes)
    return observation_window_minutes / max(len(incidents), 1)


def compute_mttr(incidents: list[Incident]) -> float:
    if not incidents:
        return 0.0
    durations = [incident.recovered_minute - incident.start_minute for incident in incidents]
    return sum(durations) / len(durations)


def compute_mttd(incidents: list[Incident]) -> float:
    if not incidents:
        return 0.0
    durations = [incident.detected_minute - incident.start_minute for incident in incidents]
    return sum(durations) / len(durations)


def compute_availability(mtbf: float, mttr: float) -> float:
    denominator = mtbf + mttr
    if denominator <= 0:
        return 1.0
    return mtbf / denominator


def generate_postmortem(incident: Incident, trace_summary: str, root_cause: str) -> str:
    return f"""# Post-mortem: {incident.name}

## Summary
{incident.summary}

## Timeline
- Start: minute {incident.start_minute}
- Detected: minute {incident.detected_minute}
- Recovered: minute {incident.recovered_minute}
- Trace summary: {trace_summary}

## Root Cause
{root_cause}

## Five Whys
1. Why did users feel pain? Elevated latency and failed task sync requests.
2. Why did latency rise? A dependent component saturated available resources.
3. Why was saturation not absorbed? Protective backpressure was insufficient.
4. Why was detection delayed? Alert routing lagged leading indicators.
5. Why did that matter? Recovery started after error budget burn accelerated.

## Action Items
- Add predictive alert coverage for rising latency and CPU.
- Tune resource thresholds and load-shedding policy.
- Rehearse the incident in chaos simulations.
"""
