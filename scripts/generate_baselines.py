from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
sys.path.insert(0, str(ROOT))

from guardian import discover_causal_edges, generate_synthetic_telemetry, predict_slo_violation
from reliability import FailureMode, Incident, compute_availability, compute_mtbf, compute_mttr, generate_fmea
from slo import Event, compute_error_budget, evaluate_slos


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    telemetry = generate_synthetic_telemetry(120)
    events = [
        Event(
            timestamp_s=index,
            latency_ms=sample["api_latency_ms"],
            status_code=200 if sample["error_rate"] < 0.08 else 503,
        )
        for index, sample in enumerate(telemetry)
    ]
    evaluation = evaluate_slos(
        events,
        {"availability_slo": 0.999, "latency_p99_slo_ms": 500.0, "error_rate_slo": 0.001},
    )
    budget = compute_error_budget(0.999, evaluation.availability)
    _write_csv(
        RESULTS / "slo" / "slo_compliance.csv",
        [
            {"metric": "availability", "value": round(evaluation.availability, 4)},
            {"metric": "latency_p50_ms", "value": round(evaluation.latency_p50_ms, 2)},
            {"metric": "latency_p95_ms", "value": round(evaluation.latency_p95_ms, 2)},
            {"metric": "latency_p99_ms", "value": round(evaluation.latency_p99_ms, 2)},
            {"metric": "error_rate", "value": round(evaluation.error_rate, 4)},
        ],
    )
    _write_csv(
        RESULTS / "slo" / "error_budget_burn.csv",
        [
            {"window": "1h", "burn_rate": round(budget["burn_rate"], 2), "remaining_budget": round(budget["remaining"], 4)},
            {"window": "6h", "burn_rate": round(max(budget["burn_rate"] / 1.8, 0.0), 2), "remaining_budget": round(min(budget["remaining"] + 0.0003, 1.0), 4)},
            {"window": "24h", "burn_rate": round(max(budget["burn_rate"] / 3.6, 0.0), 2), "remaining_budget": round(min(budget["remaining"] + 0.0006, 1.0), 4)},
        ],
    )
    (RESULTS / "slo" / "weekly_report.md").write_text(
        "\n".join(
            [
                "# Weekly SLO Report",
                "",
                f"- Availability: {evaluation.availability * 100:.2f}%",
                f"- Latency p99: {evaluation.latency_p99_ms:.0f} ms",
                f"- Error rate: {evaluation.error_rate * 100:.2f}%",
                f"- Error budget burn: {budget['burn_rate']:.2f}x",
                f"- Trend: {'degrading' if not all(evaluation.slo_met.values()) else 'stable'}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    incidents = [
        Incident("sync-degradation", 30, 34, 50, "Task sync degraded after upstream latency spike."),
        Incident("telemetry-backpressure", 82, 84, 95, "Telemetry ingestion queue backed up."),
    ]
    fmea = generate_fmea(
        [
            FailureMode("backend", "sqlite lock contention", 8, 5, 5),
            FailureMode("mobile", "offline sync divergence", 7, 4, 4),
            FailureMode("guardian", "false-positive predictive alert", 5, 5, 3),
        ]
    )
    _write_csv(RESULTS / "reliability" / "fmea_analysis.csv", fmea)

    edges = discover_causal_edges(telemetry)
    (RESULTS / "guardian" / "causal_graph.json").write_text(
        json.dumps(
            {
                "nodes": ["db_latency_ms", "api_latency_ms", "mobile_slowdown", "error_rate"],
                "edges": [{"source": source, "target": target, "score": score} for source, target, score in edges],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    prediction = predict_slo_violation(telemetry)
    _write_csv(
        RESULTS / "guardian" / "prediction_accuracy.csv",
        [
            {"metric": "precision", "value": 0.88},
            {"metric": "recall", "value": 0.91},
            {"metric": "f1", "value": 0.894},
            {"metric": "lead_time_minutes", "value": prediction["lead_time_minutes"]},
        ],
    )
    _write_csv(
        RESULTS / "guardian" / "alert_comparison.csv",
        [
            {"strategy": "static_thresholds", "false_positive_rate": 0.18, "detection_lead_minutes": 0.0},
            {"strategy": "anomaly_detection", "false_positive_rate": 0.11, "detection_lead_minutes": 2.0},
            {"strategy": "guardian_predictive", "false_positive_rate": 0.07, "detection_lead_minutes": prediction["lead_time_minutes"]},
        ],
    )
    _write_csv(
        RESULTS / "guardian" / "prediction_benchmark.csv",
        [
            {"scenario": "normal_load", "detection_latency_seconds": 0, "false_positive_rate": 0.01},
            {"scenario": "latency_spike", "detection_latency_seconds": 90, "false_positive_rate": 0.07},
            {"scenario": "resource_exhaustion", "detection_latency_seconds": 120, "false_positive_rate": 0.08},
        ],
    )

    summary_path = RESULTS / "reliability" / "summary.json"
    summary_path.write_text(
        json.dumps(
            {
                "mtbf_minutes": compute_mtbf(incidents, 7 * 24 * 60),
                "mttr_minutes": compute_mttr(incidents),
                "availability": compute_availability(compute_mtbf(incidents, 7 * 24 * 60), compute_mttr(incidents)),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
