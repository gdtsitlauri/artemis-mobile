from guardian import detect_anomalies, discover_causal_edges, generate_synthetic_telemetry, predict_slo_violation


def test_anomaly_detection():
    telemetry = generate_synthetic_telemetry(60)
    anomalies = detect_anomalies(telemetry)
    assert anomalies
    assert max(anomalies) >= 45


def test_guardian_causal():
    telemetry = generate_synthetic_telemetry(80)
    edges = discover_causal_edges(telemetry)
    assert ("db_latency_ms", "api_latency_ms", 1.0) in edges


def test_prediction():
    telemetry = generate_synthetic_telemetry(80)
    prediction = predict_slo_violation(telemetry)
    assert prediction["predicted_violation"] is True
    assert prediction["lead_time_minutes"] == 5.0
