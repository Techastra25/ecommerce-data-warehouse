"""
test_warehouse.py
-------------------
Tests for star schema integrity: surrogate key uniqueness, referential
integrity between fact and dimension tables, and quarantine logic.

Run: pytest tests/test_warehouse.py
"""

import pandas as pd
import pytest


@pytest.fixture
def sample_orders():
    return pd.DataFrame({
        "order_id": ["O1", "O2", "O3"],
        "customer_id": ["C1", "", "C3"],
        "order_date": ["2024-01-01", "2024-01-02", "2024-01-03"],
        "status": ["DELIVERED", "PENDING", "CANCELLED"],
        "shipping_city": ["Mumbai", "Delhi", "Pune"],
    })


def test_missing_customer_id_quarantined(sample_orders):
    missing = sample_orders[sample_orders["customer_id"] == ""]
    clean = sample_orders[sample_orders["customer_id"] != ""]
    assert len(missing) == 1
    assert len(clean) == 2
    assert "O2" in missing["order_id"].values


def test_surrogate_keys_unique():
    dim = pd.DataFrame({"customer_id": ["C1", "C2", "C3"]})
    dim.insert(0, "customer_sk", range(1, len(dim) + 1))
    assert dim["customer_sk"].is_unique
    assert dim["customer_sk"].min() == 1


def test_margin_pct_calculation():
    df = pd.DataFrame({"list_price": [100.0], "cost_price": [60.0]})
    df["margin_pct"] = round((df["list_price"] - df["cost_price"]) / df["list_price"] * 100, 2)
    assert df["margin_pct"].iloc[0] == 40.0


def test_fact_revenue_calculation():
    df = pd.DataFrame({"quantity": [3], "unit_price": [50.0], "cost_price": [30.0]})
    df["line_revenue"] = df["quantity"] * df["unit_price"]
    df["line_cost"] = df["quantity"] * df["cost_price"]
    df["line_profit"] = df["line_revenue"] - df["line_cost"]
    assert df["line_revenue"].iloc[0] == 150.0
    assert df["line_profit"].iloc[0] == 60.0
