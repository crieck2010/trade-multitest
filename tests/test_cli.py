"""End-to-end CLI tests."""

import json
import subprocess
import sys

import pytest

EXAMPLE = "examples/round_example.json"


def _run(*args):
    return subprocess.run(
        [sys.executable, "-m", "trade_multitest.cli", *args],
        capture_output=True, text=True, cwd=".",
    )


def test_cli_text_report():
    proc = _run(EXAMPLE)
    assert proc.returncode == 0, proc.stderr
    out = proc.stdout
    assert "idea-f" in out
    assert "DSR=" in out
    assert "validated" in out or "invalidated" in out
    assert "kill" not in out.lower()


def test_cli_json_report_schema():
    proc = _run(EXAMPLE, "--json")
    assert proc.returncode == 0, proc.stderr
    report = json.loads(proc.stdout)
    assert report["schema"] == "multitest.report.v1"
    assert report["n_trials"] == 6
    assert len(report["per_trial"]) == 6
    for t in report["per_trial"]:
        assert t["dsr"] is None or 0.0 <= t["dsr"] <= 1.0
        assert t["dsr_verdict"] in ("validated", "invalidated", None)


def test_cli_round_with_returns_runs_bootstrap_tests(tmp_path):
    import numpy as np

    rng = np.random.default_rng(99)
    n = 400
    trials = []
    for j, name in enumerate(["a", "b", "c", "d"]):
        r = rng.normal(0.0, 0.01, n)
        if j == 2:
            r += 0.0025
        trials.append({"name": name, "sharpe": 0.5, "returns": r.tolist()})
    path = tmp_path / "round.json"
    path.write_text(json.dumps({"n_boot": 200, "seed": 1, "trials": trials}))
    proc = _run(str(path), "--json")
    assert proc.returncode == 0, proc.stderr
    report = json.loads(proc.stdout)
    rt = report["round_tests"]
    assert rt["reality_check"]["verdict"] == "validated"
    assert rt["spa"]["verdict"] == "validated"
    assert rt["holm"]["n_rejected"] >= 1
    per = {t["name"]: t for t in report["per_trial"]}
    assert per["c"]["holm_verdict"] == "validated"


def test_cli_csv_input(tmp_path):
    path = tmp_path / "round.csv"
    path.write_text(
        "name,sharpe,skew,kurt,n_obs\n"
        "idea-a,1.10,0.1,3.2,1500\nidea-b,-0.40,0.0,3.0,1500\n"
    )
    proc = _run(str(path))
    assert proc.returncode == 0, proc.stderr
    assert "idea-a" in proc.stdout and "DSR=" in proc.stdout


def test_cli_rejects_empty_round(tmp_path):
    path = tmp_path / "empty.json"
    path.write_text(json.dumps({"trials": []}))
    proc = _run(str(path))
    assert proc.returncode == 2
    assert "error" in proc.stderr


def test_no_kill_word_anywhere_in_package():
    import pathlib
    root = pathlib.Path("src/trade_multitest")
    hits = [p for p in root.rglob("*.py") if "kill" in p.read_text().lower()]
    assert not hits, f"'kill' found in: {hits}"
