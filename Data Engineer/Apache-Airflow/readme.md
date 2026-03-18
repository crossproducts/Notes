# Apache Airflow

> [!NOTE]   
> **Status**: In Progress
---

## Featrues
- Orchestrate and schedule data workflows
- Coordinating ETL/ELT pipelines, Glue jobs, EMR clusters, and other services 
- Built-in monitoring, retries, and dependency management.

## Core Concepts
- **Workflow / DAG (Directed Acyclic Graph)**: 
    - Sequence of **Tasks**
- **Task**: 
    - Unit of work in a DAG
- **Operator**: 
    - What gets done by a **Task**
    - BashOperator
    - PythinOperator
    - ...
    - Customised Operator
- **Dag Run**: DAG + DATE
- **Task Instance**: Task + DATE
- **Execution Date**: Dag Run + Date

## References
- [Airflow Docker Compose](https://airflow.apache.org/docs/apache-airflow/stable/howto/docker-compose/index.html#fetching-docker-compose-yaml)