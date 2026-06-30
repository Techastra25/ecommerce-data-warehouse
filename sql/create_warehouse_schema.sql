-- create_warehouse_schema.sql
-- Star schema DDL for the e-commerce data warehouse (Snowflake / Azure SQL / Postgres compatible syntax shown for Postgres)

CREATE SCHEMA IF NOT EXISTS warehouse;

CREATE TABLE IF NOT EXISTS warehouse.dim_customer (
    customer_sk     INT PRIMARY KEY,
    customer_id     VARCHAR(20) UNIQUE NOT NULL,
    signup_date     DATE,
    city            VARCHAR(50),
    state           VARCHAR(50),
    email           VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS warehouse.dim_product (
    product_sk      INT PRIMARY KEY,
    product_id      VARCHAR(20) UNIQUE NOT NULL,
    product_name    VARCHAR(150),
    category        VARCHAR(50),
    list_price      NUMERIC(10,2),
    cost_price      NUMERIC(10,2),
    margin_pct      NUMERIC(5,2)
);

CREATE TABLE IF NOT EXISTS warehouse.dim_date (
    date_key_int    INT PRIMARY KEY,
    date_key        DATE NOT NULL,
    year            INT,
    quarter         INT,
    month           INT,
    month_name      VARCHAR(15),
    day_of_week     VARCHAR(15),
    is_weekend      BOOLEAN
);

CREATE TABLE IF NOT EXISTS warehouse.fact_order_items (
    order_item_id   VARCHAR(20) PRIMARY KEY,
    order_id        VARCHAR(20) NOT NULL,
    order_date_key  INT REFERENCES warehouse.dim_date(date_key_int),
    customer_sk     INT REFERENCES warehouse.dim_customer(customer_sk),
    product_sk      INT REFERENCES warehouse.dim_product(product_sk),
    status          VARCHAR(20),
    shipping_city   VARCHAR(50),
    quantity        INT,
    unit_price      NUMERIC(10,2),
    line_revenue    NUMERIC(12,2),
    line_cost       NUMERIC(12,2),
    line_profit     NUMERIC(12,2)
);

CREATE INDEX IF NOT EXISTS idx_fact_order_date ON warehouse.fact_order_items(order_date_key);
CREATE INDEX IF NOT EXISTS idx_fact_customer ON warehouse.fact_order_items(customer_sk);
CREATE INDEX IF NOT EXISTS idx_fact_product ON warehouse.fact_order_items(product_sk);

-- Example: top 5 categories by revenue (matches src/etl/analytics_report.py logic)
-- SELECT p.category, SUM(f.line_revenue) AS total_revenue
-- FROM warehouse.fact_order_items f
-- JOIN warehouse.dim_product p ON f.product_sk = p.product_sk
-- GROUP BY p.category
-- ORDER BY total_revenue DESC
-- LIMIT 5;
