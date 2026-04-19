from slo import Event, compute_error_budget, evaluate_slos


def test_slo_calculation():
    events = [
        Event(timestamp_s=0, latency_ms=100.0, status_code=200),
        Event(timestamp_s=1, latency_ms=120.0, status_code=200),
        Event(timestamp_s=2, latency_ms=450.0, status_code=503),
        Event(timestamp_s=3, latency_ms=130.0, status_code=200),
    ]
    evaluation = evaluate_slos(
        events,
        {"availability_slo": 0.70, "latency_p99_slo_ms": 500.0, "error_rate_slo": 0.30},
    )
    assert round(evaluation.availability, 2) == 0.75
    assert round(evaluation.error_rate, 2) == 0.25
    assert evaluation.slo_met["availability"] is True


def test_error_budget():
    budget = compute_error_budget(0.999, 0.995)
    assert round(budget["budget"], 3) == 0.001
    assert budget["burn_rate"] > 0
