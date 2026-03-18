# Apache Airflow

> [!NOTE]   
> **Status**: In Progress

---

## What is Airflow?

A platform to **programmatically author, schedule, and monitor** data workflows as code (Python).

**Use cases:** ETL/ELT pipelines · Glue jobs · EMR clusters · ML pipeline orchestration

---

## Core Concepts

| Term | Definition |
| --- | --- |
| **DAG** (Directed Acyclic Graph) | A workflow — a collection of Tasks with defined dependencies |
| **Task** | A single unit of work inside a DAG |
| **Operator** | Defines *what* a Task does |
| **DAG Run** | A DAG instance triggered at a specific date |
| **Task Instance** | A Task within a specific DAG Run |
| **Execution Date** | The logical date of a DAG Run (not necessarily wall-clock time) |

---

## Operators

| Operator | Purpose |
| --- | --- |
| `BashOperator` | Execute a bash command |
| `PythonOperator` | Call a Python function |
| `BranchPythonOperator` | Conditional branching in a DAG |
| `EmptyOperator` | No-op, useful for grouping |
| Custom Operator | Extend `BaseOperator` for reusable logic |

---

## Scheduling

| Schedule | Meaning |
| --- | --- |
| `@once` | Run once |
| `@daily` | Every day at midnight |
| `@hourly` | Every hour |
| `0 6 * * *` | Cron — every day at 6 AM |
| `None` | Manual trigger only |

> `catchup=False` — prevents backfilling missed runs on first deploy.

---

## Task States

| State | Description |
| --- | --- |
| `scheduled` | Ready to run, waiting for a worker |
| `queued` | Picked up by the executor |
| `running` | Currently executing |
| `success` | Completed successfully |
| `failed` | Errored — retries if configured |
| `up_for_retry` | Waiting before the next retry attempt |
| `skipped` | Skipped via branching logic |
| `upstream_failed` | A dependency task failed |

---

## Local Setup (Docker Compose)

<details>
<summary>Show local setup steps</summary>

```bash
# 1. Fetch official docker-compose
curl -LfO 'https://airflow.apache.org/docs/apache-airflow/stable/docker-compose.yaml'

# 2. Create required directories
mkdir -p ./dags ./logs ./plugins

# 3. Set Airflow UID
echo -e "AIRFLOW_UID=$(id -u)" > .env

# 4. Init the database
docker compose up airflow-init

# 5. Start all services
docker compose up -d
```

**UI:** http://localhost:8080 · Default creds: `airflow / airflow`
</details>

---

## DAG Anatomy

<details>
<summary>Show example DAG</summary>

```python
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from datetime import datetime

with DAG(
    dag_id="my_dag",
        start_date=datetime(2024, 1, 1),
            schedule="@daily",
                catchup=False,
                ) as dag:

                    task_a = PythonOperator(task_id="task_a", python_callable=my_fn)
                        task_b = BashOperator(task_id="task_b", bash_command="echo done")

                            task_a >> task_b  # task_a runs first
```

</details>

---

## References

- [Official Docs](https://airflow.apache.org/docs/)
- [Docker Compose Setup](https://airflow.apache.org/docs/apache-airflow/stable/howto/docker-compose/index.html#fetching-docker-compose-yaml)
- [Airflow Best Practices](https://airflow.apache.org/docs/apache-airflow/stable/best-practices.html)