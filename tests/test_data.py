import numpy as np
import pandas as pd
import pytest

from src.common import ROOT, config
from src.data_loader import load_raw
from src.preprocessing import clean_transactions, select_products, aggregate_daily, split_dates


def test_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError, match="download_data"):
        load_raw(tmp_path / "absent.xlsx")


def test_missing_schema():
    with pytest.raises(ValueError, match="essential"):
        clean_transactions(pd.DataFrame({"Quantity": [1]}))


def test_cancellations_negative_prices_duplicates_and_missing(transactions):
    extra = transactions.iloc[:6].copy()
    extra["InvoiceNo"] = ["C123456", "123456", "123457", "123458", "123459", "123460"]
    extra["Quantity"] = [10, -2, 3, 4, 5, 6]
    extra.loc[extra.index[2], "UnitPrice"] = 0
    extra.loc[extra.index[3], "StockCode"] = "POST"
    extra.loc[extra.index[4], "InvoiceDate"] = pd.NaT
    extra.loc[extra.index[5], "Description"] = None
    raw = pd.concat([transactions, transactions.iloc[:1], extra], ignore_index=True)
    clean, report = clean_transactions(raw)
    assert len(clean) == 221
    assert report["duplicates_removed"] == 1
    assert report["cancellation_rows_after_dedup"] == 1
    assert report["negative_quantity_rows_after_dedup"] == 1
    assert "CustomerID" not in clean
    assert clean.units.sum() == 446
    assert clean.product_name.dropna().eq("TEST ITEM").all()


def test_nonfinite_and_zero_quantity_removed(transactions):
    transactions["Quantity"] = transactions.Quantity.astype(float)
    transactions.loc[0, "Quantity"] = np.inf
    transactions.loc[1, "Quantity"] = 0
    transactions.loc[2, "UnitPrice"] = np.inf
    clean, _ = clean_transactions(transactions)
    assert len(clean) == 217


def test_selection_ignores_future(transactions):
    clean, _ = clean_transactions(transactions)
    cfg = {"products": 1, "min_active_days": 90, "min_history_days": 180}
    selected = select_products(clean, "2020-07-01", cfg)
    poisoned = clean.copy()
    poisoned.loc[poisoned.date.gt("2020-07-01"), ["product_id", "retail_price", "product_name"]] = ["99999", 999999, "FUTURE"]
    pd.testing.assert_frame_equal(selected, select_products(poisoned, "2020-07-01", cfg))


def test_selection_insufficient_fails(transactions):
    clean, _ = clean_transactions(transactions)
    with pytest.raises(ValueError, match="eligible"):
        select_products(clean, "2020-07-01", {"products": 2, "min_active_days": 90, "min_history_days": 180})


def test_zero_padding_does_not_change_units(transactions):
    clean, _ = clean_transactions(transactions)
    catalog = select_products(clean, "2020-07-01", {"products": 1, "min_active_days": 90, "min_history_days": 180})
    reduced = clean.loc[clean.date.ne("2020-04-01")]
    daily = aggregate_daily(reduced, catalog, "2020-08-07")
    assert daily.loc[daily.date.eq("2020-04-01"), "units"].iloc[0] == 0
    assert daily.units.sum() == reduced.units.sum()
    assert len(daily) == 220


def test_dates_have_three_disjoint_28_day_windows():
    split = split_dates("2011-12-08", config())
    assert split["holdout_start"] == "2011-11-11"
    assert split["selection_cutoff"] == "2011-08-18"
    assert (pd.Timestamp(split["holdout_start"]) - pd.Timestamp(split["selection_cutoff"])).days == 85
