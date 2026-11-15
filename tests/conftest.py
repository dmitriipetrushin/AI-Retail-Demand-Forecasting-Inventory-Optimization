import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def transactions():
    dates = pd.date_range("2020-01-01", periods=220)
    return pd.DataFrame({"InvoiceNo": [str(100000 + i) for i in range(220)], "StockCode": "12345A",
                         "Description": " test  ITEM ", "Quantity": 2, "InvoiceDate": dates,
                         "UnitPrice": 2.0, "CustomerID": np.nan, "Country": "United Kingdom"})


@pytest.fixture
def toy_data():
    dates = pd.date_range("2020-01-01", periods=140)
    daily = pd.concat([pd.DataFrame({"product_id": p, "date": dates, "units": 5.0}) for p in ["10001", "10002"]], ignore_index=True)
    catalog = pd.DataFrame({"product_id": ["10001", "10002"], "product_name": ["ONE", "TWO"], "median_retail_price": [2., 3.], "first_sale": [dates[0], dates[0]]})
    scenario = {"lead_days": 2, "review_days": 7, "safety_z": 0., "initial_cover_days": 1,
                "budget_per_review": 100., "purchase_price_fraction": .5, "annual_holding_rate": .25,
                "shortage_cost_multiple": 2., "pack_size": 2, "moq": 4}
    return daily, catalog, scenario
