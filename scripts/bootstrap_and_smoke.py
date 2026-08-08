#!/usr/bin/env python
"""One-shot: freeze region (offline or API) -> demo cube -> quick baselines + ST."""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(cmd: list[str]):
    print("\n>>>", " ".join(cmd), flush=True)
    subprocess.check_call(cmd, cwd=ROOT)


def pick_python() -> list[str]:
    """Return argv prefix for a Python that imports project deps."""
    candidates = [
        [sys.executable],
        ["py", "-3.12"],
        ["py", "-3.11"],
        ["python"],
    ]
    # dedupe
    seen = set()
    for cmd in candidates:
        key = tuple(cmd)
        if key in seen:
            continue
        seen.add(key)
        if cmd[0] == "py" and shutil.which("py") is None:
            continue
        if cmd[0] != "py" and shutil.which(cmd[0]) is None and not Path(cmd[0]).exists():
            continue
        try:
            subprocess.check_call(
                cmd + ["-c", "import xarray, torch, yaml"],
                cwd=ROOT,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return cmd
        except Exception:
            continue
    return [sys.executable]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--online-survey", action="store_true")
    parser.add_argument("--epochs", type=int, default=8)
    args = parser.parse_args()
    py = pick_python()
    print(f"[smoke] python={' '.join(py)}")
    survey = py + ["scripts/survey_argo_coverage.py", "--freeze"]
    if not args.online_survey:
        survey.append("--offline-demo")
    run(survey)
    run(py + ["scripts/build_demo_cube.py"])
    run(
        py
        + [
            "run_multilead.py",
            "--demo",
            "--quick",
            "--epochs",
            str(args.epochs),
        ]
    )
    run(
        py
        + [
            "run_multilead.py",
            "--demo",
            "--quick",
            "--epochs",
            str(args.epochs),
            "--sparse",
            "station",
            "--stations",
            "8",
        ]
    )
    print("\n[smoke] done. See results/tables/ and results/figures/")


if __name__ == "__main__":
    main()
