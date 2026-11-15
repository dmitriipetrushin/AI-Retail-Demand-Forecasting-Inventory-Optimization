#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python -m scripts.download_data
python -m scripts.prepare_data
python -m scripts.train_models
python -m scripts.run_evaluation
python -m scripts.run_simulation
python -m scripts.generate_reports
python -m pytest --junitxml=reports/test-results.xml
python -m scripts.generate_reports
python -m scripts.write_portfolio
