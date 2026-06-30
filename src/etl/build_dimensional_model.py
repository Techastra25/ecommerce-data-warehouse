"""
build_dimensional_model.py
----------------------------
Transforms raw e-commerce extracts into a proper star schema:
  - dim_customer, dim_product, dim_date (dimension tables)
  - fact_order_items (grain: one row per order line item)

Implements standard dimensional modeling patterns: surrogate keys,
SCD Type 1 for dimensions, and a conformed date dimension.

Run:
    python src/etl/build_dimensional_model.py
"""

import os
import pandas as pd

RAW_DIR = "data/raw"
WAREHOUSE_DIR = "data/warehouse"


def load_raw():
    customers = pd.read_csv(f"{RAW_DIR}/customers/customers.csv")
    products = pd.read_csv(f"{RAW_DIR}/products/products.csv")
    orders = pd.read_csv(f"{RAW_DIR}/orders/orders.csv")
    order_items = pd.read_csv(f"{RAW_DIR}/order_items/order_items.csv")
    return customers, products, orders, order_items


def clean_orders(orders: pd.DataFrame) -> pd.DataFrame:
    before = len(orders)
    # Quarantine orders with missing customer_id instead of silently dropping
    missing_customer = orders[orders["customer_id"].isna() | (orders["customer_id"] == "")]
    os.makedirs(f"{WAREHOUSE_DIR}/_quarantine", exist_ok=True)
    missing_customer.to_csv(f"{WAREHOUSE_DIR}/_quarantine/orders_missing_customer.csv", index=False)

    clean = orders.dropna(subset=["customer_id"])
    clean = clean[clean["customer_id"] != ""]
    clean["order_date"] = pd.to_datetime(clean["order_date"])
    print(f"[clean] orders: {before} raw -> {len(clean)} clean, {len(missing_customer)} quarantined")
    return clean


def build_dim_customer(customers: pd.DataFrame) -> pd.DataFrame:
    dim = customers.copy().reset_index(drop=True)
    dim.insert(0, "customer_sk", range(1, len(dim) + 1))
    dim["signup_date"] = pd.to_datetime(dim["signup_date"])
    return dim


def build_dim_product(products: pd.DataFrame) -> pd.DataFrame:
    dim = products.copy().reset_index(drop=True)
    dim.insert(0, "product_sk", range(1, len(dim) + 1))
    dim["margin_pct"] = round((dim["list_price"] - dim["cost_price"]) / dim["list_price"] * 100, 2)
    return dim


def build_dim_date(orders: pd.DataFrame) -> pd.DataFrame:
    min_date = orders["order_date"].min().normalize()
    max_date = orders["order_date"].max().normalize()
    dates = pd.date_range(min_date, max_date, freq="D")
    dim = pd.DataFrame({"date_key": dates})
    dim["date_key_int"] = dim["date_key"].dt.strftime("%Y%m%d").astype(int)
    dim["year"] = dim["date_key"].dt.year
    dim["quarter"] = dim["date_key"].dt.quarter
    dim["month"] = dim["date_key"].dt.month
    dim["month_name"] = dim["date_key"].dt.month_name()
    dim["day_of_week"] = dim["date_key"].dt.day_name()
    dim["is_weekend"] = dim["date_key"].dt.dayofweek >= 5
    return dim


def build_fact_order_items(order_items, orders_clean, dim_customer, dim_product, dim_date):
    fact = order_items.merge(orders_clean, on="order_id", how="inner")  # drops items for quarantined orders
    fact = fact.merge(
        dim_customer[["customer_id", "customer_sk"]], on="customer_id", how="left"
    )
    fact = fact.merge(
        dim_product[["product_id", "product_sk", "cost_price"]], on="product_id", how="left"
    )
    fact["order_date_key"] = fact["order_date"].dt.strftime("%Y%m%d").astype(int)

    fact["line_revenue"] = fact["quantity"] * fact["unit_price"]
    fact["line_cost"] = fact["quantity"] * fact["cost_price"]
    fact["line_profit"] = fact["line_revenue"] - fact["line_cost"]

    cols = [
        "order_item_id", "order_id", "order_date_key", "customer_sk", "product_sk",
        "status", "shipping_city", "quantity", "unit_price",
        "line_revenue", "line_cost", "line_profit",
    ]
    return fact[cols]


def main():
    os.makedirs(WAREHOUSE_DIR, exist_ok=True)
    customers, products, orders, order_items = load_raw()
    orders_clean = clean_orders(orders)

    dim_customer = build_dim_customer(customers)
    dim_product = build_dim_product(products)
    dim_date = build_dim_date(orders_clean)
    fact = build_fact_order_items(order_items, orders_clean, dim_customer, dim_product, dim_date)

    dim_customer.to_csv(f"{WAREHOUSE_DIR}/dim_customer.csv", index=False)
    dim_product.to_csv(f"{WAREHOUSE_DIR}/dim_product.csv", index=False)
    dim_date.to_csv(f"{WAREHOUSE_DIR}/dim_date.csv", index=False)
    fact.to_csv(f"{WAREHOUSE_DIR}/fact_order_items.csv", index=False)

    print(f"[warehouse] dim_customer: {len(dim_customer)} rows")
    print(f"[warehouse] dim_product:  {len(dim_product)} rows")
    print(f"[warehouse] dim_date:     {len(dim_date)} rows")
    print(f"[warehouse] fact_order_items: {len(fact)} rows")
    print(f"[warehouse] total revenue (sanity check): {fact['line_revenue'].sum():,.2f}")


if __name__ == "__main__":
    main()
