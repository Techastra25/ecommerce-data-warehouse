"""
analytics_report.py
---------------------
Runs business-analytics queries against the star schema and saves both
a results CSV and a chart — used to validate the warehouse is actually
query-ready, and to generate real (not fabricated) visuals for the README.

Run:
    python src/etl/analytics_report.py
"""

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

WAREHOUSE_DIR = "data/warehouse"
REPORTS_DIR = "docs/reports"


def top_categories_by_revenue(fact, dim_product):
    merged = fact.merge(dim_product[["product_sk", "category"]], on="product_sk", how="left")
    result = (
        merged.groupby("category")["line_revenue"]
        .sum()
        .sort_values(ascending=False)
        .reset_index()
        .rename(columns={"line_revenue": "total_revenue"})
    )
    return result


def monthly_revenue_trend(fact, dim_date):
    merged = fact.merge(
        dim_date[["date_key_int", "year", "month_name", "month"]],
        left_on="order_date_key", right_on="date_key_int", how="left",
    )
    result = (
        merged.groupby(["year", "month", "month_name"])["line_revenue"]
        .sum()
        .reset_index()
        .sort_values(["year", "month"])
        .rename(columns={"line_revenue": "monthly_revenue"})
    )
    return result


def top_cities_by_orders(fact):
    return (
        fact.groupby("shipping_city")["order_id"]
        .nunique()
        .sort_values(ascending=False)
        .reset_index()
        .rename(columns={"order_id": "order_count"})
    )


def customer_value_distribution(fact, dim_customer):
    spend = fact.groupby("customer_sk")["line_revenue"].sum().reset_index()
    merged = spend.merge(dim_customer[["customer_sk", "city"]], on="customer_sk", how="left")
    return merged


def main():
    import os
    os.makedirs(REPORTS_DIR, exist_ok=True)

    fact = pd.read_csv(f"{WAREHOUSE_DIR}/fact_order_items.csv")
    dim_product = pd.read_csv(f"{WAREHOUSE_DIR}/dim_product.csv")
    dim_date = pd.read_csv(f"{WAREHOUSE_DIR}/dim_date.csv")
    dim_customer = pd.read_csv(f"{WAREHOUSE_DIR}/dim_customer.csv")

    cat_rev = top_categories_by_revenue(fact, dim_product)
    cat_rev.to_csv(f"{REPORTS_DIR}/top_categories_by_revenue.csv", index=False)
    print("\nTop categories by revenue:")
    print(cat_rev.to_string(index=False))

    monthly = monthly_revenue_trend(fact, dim_date)
    monthly.to_csv(f"{REPORTS_DIR}/monthly_revenue_trend.csv", index=False)

    cities = top_cities_by_orders(fact)
    cities.to_csv(f"{REPORTS_DIR}/top_cities_by_orders.csv", index=False)
    print("\nTop cities by order count:")
    print(cities.to_string(index=False))

    # --- Real chart, generated from real data ---
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))

    axes[0].barh(cat_rev["category"], cat_rev["total_revenue"], color="#2563eb")
    axes[0].set_title("Total Revenue by Category")
    axes[0].set_xlabel("Revenue (₹)")
    axes[0].invert_yaxis()

    monthly_sorted = monthly.reset_index(drop=True)
    axes[1].plot(range(len(monthly_sorted)), monthly_sorted["monthly_revenue"], marker="o", color="#16a34a")
    axes[1].set_title("Monthly Revenue Trend")
    axes[1].set_xlabel("Month index")
    axes[1].set_ylabel("Revenue (₹)")

    plt.tight_layout()
    plt.savefig(f"{REPORTS_DIR}/revenue_analytics.png", dpi=120)
    print(f"\nChart saved -> {REPORTS_DIR}/revenue_analytics.png")


if __name__ == "__main__":
    main()
