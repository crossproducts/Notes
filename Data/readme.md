# Data Engineering

> Organized as a numbered learning path — from fundamentals up through orchestration,
> streaming, processing, storage, and analytics, ending in end-to-end projects.

## Quick mental model

```
Transactions      → OLTP  → row-based  → RDS / DynamoDB
Analytics         → OLAP  → columnar   → Redshift / Athena
Flexible JSON     → document          → DynamoDB / MongoDB
Relationships     → graph             → Neptune
```

## Path

| # | Category | Covers |
|---|---|---|
| 00 | [Fundamentals](00-Fundamentals/) | Data modeling, SQL, batch vs streaming, ETL vs ELT, file formats |
| 01 | [Orchestration](01-Orchestration/) | Apache Airflow |
| 02 | [Streaming-and-Messaging](02-Streaming-and-Messaging/) | Apache Kafka, Apache NiFi |
| 03 | [Processing-Engines](03-Processing-Engines/) | Apache Spark, Trino |
| 04 | [Storage-and-Lakehouse](04-Storage-and-Lakehouse/) | Data lakehouse, Apache Iceberg, Ceph |
| 05 | [Databases-and-Warehouses](05-Databases-and-Warehouses/) | Amazon Redshift, ClickHouse, MongoDB |
| 06 | [Search-and-Analytics](06-Search-and-Analytics/) | Elasticsearch |
| 99 | [Projects](99-Projects/) | End-to-end batch, streaming, and lakehouse pipelines |
