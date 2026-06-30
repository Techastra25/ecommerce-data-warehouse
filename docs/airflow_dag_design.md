# Airflow DAG Design (Production Orchestration)

In production, this pipeline runs as a daily Airflow DAG rather than
manual script execution. Design:

```python
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

default_args = {
    "owner": "data-eng",
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    "ecommerce_warehouse_daily",
    default_args=default_args,
    schedule_interval="@daily",
    start_date=datetime(2025, 1, 1),
    catchup=False,
) as dag:

    extract = PythonOperator(
        task_id="extract_raw_orders",
        python_callable=extract_from_source_db,
    )

    build_warehouse = PythonOperator(
        task_id="build_dimensional_model",
        python_callable=build_dimensional_model_main,
    )

    run_analytics = PythonOperator(
        task_id="generate_analytics_report",
        python_callable=analytics_report_main,
    )

    data_quality_check = PythonOperator(
        task_id="validate_row_counts",
        python_callable=validate_fact_table_not_empty,
    )

    extract >> build_warehouse >> run_analytics >> data_quality_check
```

Key design decisions:
- **Daily schedule** matches order data's natural arrival cadence
- **Retries with backoff** (2 retries, 5 min delay) handle transient source DB connection issues
- **Data quality gate as the last task** — pipeline isn't considered "done" until row counts are validated, so downstream BI dashboards never silently show stale/empty data
- **Idempotent tasks** — each script overwrites its output tables rather than appending, so re-runs after a failure don't duplicate data
