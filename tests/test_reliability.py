from reliability import FailureMode, Incident, compute_mttd, compute_mtbf, compute_mttr, generate_fmea, generate_postmortem


def test_fmea_analysis():
    fmea = generate_fmea(
        [
            FailureMode("backend", "db lock", 9, 5, 4),
            FailureMode("mobile", "frame jank", 6, 3, 3),
        ]
    )
    assert fmea[0]["component"] == "backend"
    assert fmea[0]["rpn"] == 180


def test_reliability_metrics_and_postmortem():
    incidents = [
        Incident("sync", 10, 12, 20, "Sync degraded."),
        Incident("telemetry", 60, 63, 69, "Queue backed up."),
    ]
    assert compute_mtbf(incidents, 120) == 60
    assert compute_mttr(incidents) == 9.5
    assert compute_mttd(incidents) == 2.5
    report = generate_postmortem(incidents[0], "trace reconstructed", "database saturation")
    assert "database saturation" in report
