"""Refit in an isolated temporary study and compare with preserved main evidence."""
from pathlib import Path
import os
import shutil
import subprocess
import sys
import tempfile
import time

import numpy as np
import pandas as pd

from src.common import ROOT, sha256, utc_now, write_json


def main():
    started = time.monotonic()
    with tempfile.TemporaryDirectory(prefix="retail-reproduction-") as directory:
        scratch = Path(directory)
        for name in ["src", "scripts", "config"]:
            shutil.copytree(ROOT / name, scratch / name, ignore=shutil.ignore_patterns("__pycache__"))
        (scratch / "data/raw").mkdir(parents=True)
        (scratch / "reports/figures").mkdir(parents=True)
        shutil.copy2(ROOT / "data/source-manifest.json", scratch / "data/source-manifest.json")
        for name in ["Online Retail.xlsx", "online-retail.zip"]:
            # Read-only acquisition inputs; commands never modify existing source bytes.
            try:
                os.link(ROOT / "data/raw" / name, scratch / "data/raw" / name)
            except OSError:
                shutil.copy2(ROOT / "data/raw" / name, scratch / "data/raw" / name)
        commands = []
        for script in ["download_data", "prepare_data", "train_models", "run_evaluation", "run_simulation", "generate_reports"]:
            before = time.monotonic()
            proc = subprocess.run([sys.executable, "-m", f"scripts.{script}"], cwd=scratch, capture_output=True, text=True, timeout=300,
                                  env={**os.environ, "OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1"})
            if proc.returncode:
                raise RuntimeError(f"{script}: {proc.stdout}\n{proc.stderr}")
            commands.append({"command": f"python -m scripts.{script}", "passed": True, "seconds": round(time.monotonic() - before, 3)})
        exact_paths = ["data/processed/daily_sales.csv", "data/processed/products.csv"]
        exact = {name: sha256(ROOT / name) == sha256(scratch / name) for name in exact_paths}
        if not all(exact.values()):
            raise AssertionError("Prepared data differed in the clean reproduction")
        comparisons = {}
        for name in ["development-comparison.csv", "holdout-comparison.csv", "simulation-summary.csv"]:
            a, b = pd.read_csv(ROOT / "reports" / name), pd.read_csv(scratch / "reports" / name)
            numeric = a.select_dtypes(include="number").columns
            np.testing.assert_allclose(a[numeric].to_numpy(), b[numeric].to_numpy(), rtol=1e-8, atol=1e-8, equal_nan=True)
            nonnumeric = [c for c in a if c not in numeric]
            pd.testing.assert_frame_equal(a[nonnumeric], b[nonnumeric])
            comparisons[name] = {"passed": True, "max_numeric_difference": float(np.nanmax(np.abs(a[numeric].to_numpy() - b[numeric].to_numpy())))}
        report = {"passed": True, "verified_at_utc": utc_now(), "elapsed_seconds": round(time.monotonic() - started, 3),
                  "method": "Isolated temporary source/config copy; fresh preparation, all model fitting and final holdout; same downloaded official source bytes. Main artifacts were never overwritten.",
                  "commands": commands, "prepared_checksums_equal": exact, "comparisons": comparisons,
                  "scope": "Local reproduction in the same tested Python environment; not independent multi-platform or GitHub CI validation"}
        write_json(ROOT / "reports/reproduction-verification.json", report)
        print(report)


if __name__ == "__main__":
    main()
