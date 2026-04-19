from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

from guardian import discover_causal_edges, generate_synthetic_telemetry, predict_slo_violation
from reliability import FailureMode, Incident, compute_availability, compute_mtbf, compute_mttr, generate_fmea
from slo import Event, compute_error_budget, evaluate_slos


def load_baseline():
    telemetry = generate_synthetic_telemetry()
    events = [
        Event(timestamp_s=index, latency_ms=sample["api_latency_ms"], status_code=200 if sample["error_rate"] < 0.08 else 503)
        for index, sample in enumerate(telemetry)
    ]
    evaluation = evaluate_slos(
        events,
        {
            "availability_slo": 0.999,
            "latency_p99_slo_ms": 500.0,
            "error_rate_slo": 0.001,
        },
    )
    budget = compute_error_budget(0.999, evaluation.availability)
    incidents = [
        Incident("sync-degradation", 30, 34, 50, "Task sync degraded after upstream latency spike."),
        Incident("telemetry-backpressure", 82, 84, 95, "Telemetry ingestion queue backed up."),
    ]
    reliability = {
        "mtbf": compute_mtbf(incidents, 7 * 24 * 60),
        "mttr": compute_mttr(incidents),
    }
    reliability["availability"] = compute_availability(reliability["mtbf"], reliability["mttr"])
    fmea = generate_fmea(
        [
            FailureMode("backend", "sqlite lock contention", 8, 5, 5),
            FailureMode("mobile", "offline sync divergence", 7, 4, 4),
            FailureMode("guardian", "false-positive predictive alert", 5, 5, 3),
        ]
    )
    return telemetry, evaluation, budget, reliability, fmea


st.set_page_config(page_title="ARTEMIS Dashboard", layout="wide")
st.title("ARTEMIS Observability Dashboard")

telemetry, evaluation, budget, reliability, fmea = load_baseline()
prediction = predict_slo_violation(telemetry)
causal_edges = discover_causal_edges(telemetry)

col1, col2, col3 = st.columns(3)
col1.metric("Availability", f"{evaluation.availability * 100:.2f}%")
col2.metric("Error Budget Burn", f"{budget['burn_rate']:.2f}x")
col3.metric("Predictive Alert", "Active" if prediction["predicted_violation"] else "Normal")

st.subheader("SLO Overview")
st.json(
    {
        "latency_p99_ms": evaluation.latency_p99_ms,
        "throughput_rps": round(evaluation.throughput_rps, 2),
        "error_rate": round(evaluation.error_rate, 4),
        "slo_met": evaluation.slo_met,
    }
)

st.subheader("GUARDIAN Causal Graph")
st.table([{"source": left, "target": right, "score": score} for left, right, score in causal_edges])

st.subheader("Reliability Snapshot")
st.table(fmea)

results_dir = Path(__file__).resolve().parents[1] / "results" / "guardian"
graph_path = results_dir / "causal_graph.json"
if graph_path.exists():
    st.subheader("Saved Graph Artifact")
    st.code(json.dumps(json.loads(graph_path.read_text(encoding="utf-8")), indent=2), language="json")
