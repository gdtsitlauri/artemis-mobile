# ARTEMIS

**Adaptive Reliability and Telemetry Engine for Mobile Intelligent Systems**


ARTEMIS is an open-source research framework that bridges Flutter mobile
engineering, distributed tracing, SLO management, reliability engineering, and
predictive causal ML under one repository.

Its novel **ARTEMIS-GUARDIAN** algorithm detects service degradation **before**
users are affected by combining anomaly detection, causal telemetry analysis, and
short-horizon SLO violation forecasting.


## Project Metadata

| Field | Value |
| --- | --- |
| Author | George David Tsitlauri |
| Affiliation | Dept. of Informatics & Telecommunications, University of Thessaly, Greece |
| Contact | gdtsitlauri@gmail.com |
| Year | 2026 |

## Modules

| Directory | Language | Description |
|-----------|----------|-------------|
| `mobile/` | Dart/Flutter | Task app with built-in observability spans |
| `backend/` | Go | REST API with health, metrics, tracing, telemetry ingestion |
| `slo/` | Python | SLI/SLO evaluation and error-budget burn-rate engine |
| `reliability/` | Python | FMEA, chaos simulation, MTBF/MTTR, post-mortem generator |
| `guardian/` | Python | Synthetic telemetry, Isolation Forest, PC-causal, LSTM prediction |
| `dashboard/` | Python/Streamlit | Live observability dashboard |
| `results/` | — | Baseline experiment artifacts (CSV, JSON, Markdown) |
| `paper/` | LaTeX | IEEE-style research paper draft |

## Quick Start

### Python (SLO · Reliability · GUARDIAN)

```bash
pip install -r requirements.txt
python3 scripts/generate_baselines.py   # regenerate all result artifacts
python3 -m pytest tests/ -v             # 8 tests
streamlit run dashboard/app.py          # dashboard on http://localhost:8501
```

### Go (Backend API)

```bash
cd backend
go test ./...    # 4 tests
go build ./...
./artemis-api    # starts on :8080
```

### Flutter (Mobile App)

```bash
cd mobile
flutter pub get
flutter analyze
flutter test     # 4 tests
```

## Test Results

| Suite | Tests | Status |
|-------|-------|--------|
| Flutter | 4 / 4 | ✅ |
| Go | 4 / 4 | ✅ |
| Python | 8 / 8 | ✅ |

## GUARDIAN — Key Results

| Strategy | False-positive rate | Detection lead time |
|----------|--------------------|--------------------|
| Static thresholds | 0.18 | 0 min |
| Isolation Forest only | 0.11 | 2 min |
| **ARTEMIS-GUARDIAN** | **0.07** | **5 min** |

Additional committed evidence:

- `results/slo/weekly_report.md` records a degraded week with:
  - Availability: `93.33%`
  - Latency p99: `315 ms`
  - Error rate: `6.67%`
  - Error-budget burn: `65.67x`
- `results/reliability/fmea_analysis.csv` identifies the highest-RPN failure
  modes used by the reliability analysis layer.
- `results/guardian/alert_comparison.csv` and
  `results/guardian/prediction_benchmark.csv` support the lead-time and
  false-positive comparisons above.

## Evidence Status

- Mobile, backend, SLO, and reliability modules are implemented and tested.
- The strongest predictive results come from **synthetic telemetry and
  controlled reliability workloads**, not from a long-running production app.
- The repository therefore supports a strong **mobile reliability research**
  narrative, but should not be framed as already externally validated on live
  user traffic at scale.

## Baseline Artifacts

Generated results live in `results/`:

- `results/slo/` — compliance snapshot, burn-rate table, weekly Markdown report
- `results/reliability/` — FMEA ranking (top RPN: SQLite lock contention = 200)
- `results/guardian/` — causal graph JSON, prediction accuracy, alert comparison

Regenerate with:

```bash
python3 scripts/generate_baselines.py
```

## Paper

`paper/artemis_paper.tex` — IEEE Transactions on Software Engineering / ICSE style.  
Sections: Introduction · Mobile Engineering · Backend · SLO/SLI · Reliability · GUARDIAN · Experiments · Conclusion.


