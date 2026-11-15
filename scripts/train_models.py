from src.evaluation import develop

if __name__ == "__main__":
    result = develop()
    print({k: result[k] for k in ["selected_model", "development_wape_improvement", "forecast_quality_gate_pass", "frozen_at_utc"]})
