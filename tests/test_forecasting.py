import math
import numpy as np
import pandas as pd
import pytest

from src.forecasting import predict, forecast_panel
from src.evaluation import metrics


@pytest.mark.parametrize("model", ["seasonal_naive", "moving_average", "auto_ets", "croston_sba"])
@pytest.mark.parametrize("horizon", [7, 14, 28])
def test_real_forecast_models(model, horizon):
    y = np.tile([2., 4., 3., 5., 6., 1., 0.], 20)
    result = predict(y, horizon, model)
    assert result.effective_model == model
    assert len(result.values) == horizon
    assert np.isfinite(result.values).all()
    assert (result.values >= 0).all()


def test_seasonal_naive_alignment():
    np.testing.assert_equal(predict(np.arange(21), 14).values, np.tile(np.arange(14, 21), 2))


def test_missing_and_short_history():
    assert predict([], 7).effective_model == "zero_fallback"
    assert predict([3.], 7, "auto_ets").fallback_reason
    np.testing.assert_equal(predict([3.], 7, "auto_ets").values, np.full(7, 3.))


def test_invalid_input_and_horizon():
    for y in [[-1, 2], [np.nan, 1], [np.inf]]:
        with pytest.raises(ValueError):
            predict(y)
    with pytest.raises(ValueError):
        predict([1] * 28, 30)


def test_negative_model_output_is_clamped(monkeypatch):
    from statsforecast.models import AutoETS
    monkeypatch.setattr(AutoETS, "forecast", lambda self, y, h: {"mean": np.full(h, -3.)})
    result = predict(np.ones(40), 7, "auto_ets")
    assert result.values.sum() == 0


def test_metric_values_and_undefined_denominators():
    m = metrics([1, 3], [2, 1], 2)
    assert m["mae"] == 1.5
    assert m["rmse"] == pytest.approx(math.sqrt(2.5))
    assert m["wape"] == .75
    assert m["bias"] == -.25
    assert m["mase"] == .75
    zero = metrics([0, 0], [1, 0], 0)
    assert zero["wape"] is None and zero["bias"] is None and zero["mase"] is None
    assert zero["mase_defined_rows"] == 0


def test_future_values_do_not_change_forecasts(toy_data):
    daily, catalog, _ = toy_data
    origin = pd.Timestamp("2020-04-20")
    a = forecast_panel(daily, catalog, origin, ["auto_ets"])
    poison = daily.copy()
    poison.loc[poison.date.gt(origin), "units"] = 99999
    b = forecast_panel(poison, catalog, origin, ["auto_ets"])
    np.testing.assert_array_equal(a.predicted_units.to_numpy(), b.predicted_units.to_numpy())
    assert (a.forecast_date > a.train_end).all()
