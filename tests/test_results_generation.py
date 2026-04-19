from pathlib import Path
import subprocess
import sys


def test_generate_baselines_script():
    root = Path(__file__).resolve().parents[1]
    subprocess.run([sys.executable, "scripts/generate_baselines.py"], cwd=root, check=True)
    assert (root / "results" / "guardian" / "causal_graph.json").exists()
    assert (root / "results" / "reliability" / "summary.json").exists()
