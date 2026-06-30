# E-Commerce Data Warehouse

A dimensional data warehouse (star schema) built from raw e-commerce
order data — orders, order items, customers, products — transformed
into clean fact/dimension tables ready for BI and analytics queries.

## Why this exists

Raw transactional order data isn't analytics-ready: it's normalized
across multiple tables, has data quality gaps (missing customer IDs
on guest/failed checkouts), and isn't structured for fast aggregation.
This project applies classic Kimball-style dimensional modeling —
surrogate keys, a conformed date dimension, and a single fact table
at order-line grain — so a BI tool or analyst can run fast, simple
queries instead of complex joins across operational tables.

## Architecture
Raw CSVs (customers, products, orders, order_items)
│
▼  build_dimensional_model.py
Star Schema:
dim_customer  (surrogate key, SCD Type 1)
dim_product   (surrogate key, margin % derived)
dim_date      (conformed date dimension)
fact_order_items  (grain: 1 row per order line item)
│
▼  analytics_report.py
Business KPIs + charts (category revenue, monthly trend, city orders)
In production this is orchestrated by Apache Airflow (DAG definition
pattern shown in `docs/airflow_dag_design.md`) with the dimensional
model loaded into Snowflake or Azure SQL Data Warehouse for BI tools
to query directly.

## Actual run results (reproducible — not illustrative)

Generated from `python src/etl/generate_sample_data.py --orders 50000`
on this exact codebase:
Generated 8000 customers
Generated 1500 products
Generated 50000 orders with line items
[clean] orders: 50000 raw -> 48486 clean, 1514 quarantined (3.0% missing customer_id)
[warehouse] dim_customer: 8000 rows
[warehouse] dim_product:  1500 rows
[warehouse] dim_date:     541 rows
[warehouse] fact_order_items: 145669 rows
[warehouse] total revenue (sanity check): 147,243,806.23


**Top categories by revenue:**

| category | total_revenue |
|---|---|
| Electronics | 26,345,521.82 |
| Apparel | 25,752,670.84 |
| Books | 24,317,497.97 |
| Sports | 24,235,879.29 |
| Toys | 23,753,470.44 |
| Home & Kitchen | 22,838,765.87 |

**Top cities by order count:** Mumbai (8,212), Hyderabad (8,098), Pune (8,066), Bengaluru (8,060), Delhi (8,032), Chennai (8,018)

![Revenue Analytics](docs/reports/revenue_analytics.png)

*(Chart and tables above are generated directly by `src/etl/analytics_report.py` from this synthetic dataset — re-run it yourself to regenerate.)*

## What the cleaning logic does

- Orders missing `customer_id` (~3% of rows, simulating guest/failed checkouts)
  are **quarantined to a separate CSV**, not silently dropped — full audit trail preserved
- Fact table grain is enforced at order-line level so revenue, cost, and profit
  can be sliced by any dimension without re-aggregation errors
- Surrogate keys decouple the warehouse from source system ID changes (standard
  practice — natural keys from source systems shouldn't be primary keys downstream)

## Stack

Python, Pandas (local/dev), designed for Apache Airflow orchestration
and Snowflake/Azure SQL Data Warehouse in production. SQL DDL provided
in `sql/` is standard ANSI SQL, portable to Snowflake/Postgres/Azure SQL
with minor syntax adjustments.

## Running it yourself

```bash
pip install -r requirements.txt
python src/etl/generate_sample_data.py --orders 50000
python src/etl/build_dimensional_model.py
python src/etl/analytics_report.py
pytest tests/
```

## Repo structure

ecommerce-data-warehouse/
├── src/etl/
│   ├── generate_sample_data.py       # synthetic raw data generator
│   ├── build_dimensional_model.py    # star schema builder
│   └── analytics_report.py           # business KPIs + chart generation
├── sql/create_warehouse_schema.sql   # DDL for the star schema
├── docs/reports/                     # generated CSVs + chart (real output)
├── tests/test_warehouse.py
└── data/                             # raw + warehouse output (gitignored)

## Notes

Portfolio/learning project built to practice dimensional modeling
(Kimball star schema), data quality quarantine patterns, and
warehouse-ready analytics. Data is synthetic but the pipeline, tests,
and all numbers/charts above are real, reproducible output from this
exact code — not illustrative placeholders.

