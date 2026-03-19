# Lakehouse

> [!NOTE]   
> **Status**: Done
---

## Lakehouse Architecture
| | Query Engine |  | Data Catalog |  | Open Table Formats |  | Data Lake |
| :--: | :--: | -- | :--: | -- | :--: | -- | :--: |
| Purpose: | Query Data | | Table definitions <br> Schema tracking <br> Permissions (RBAC) <br> Data discovery | | ACID transactions on data lakes <br> Time travel <br> Schema evolution <br> Upserts / deletes  | | Cheap Object Storage |
| Tools: | Apache Spark <br> ClickHouse <br> Trino | → | AWS Glue <br> UnityCatalog | → | Apache Iceberg <br> Delta Lake <br> Hudi | → | S3 |

---

- Challenges Solved:
  - Scheme Evolution
  - Data Integrity
  - Query Performance
  - Data Discovery
  - Access Control

--- 

- Medallion Pattern
    - Gold → Silver → Bronze

---

## References
- [Youtube: Clickhouse - Data lakehouses (in under 3 minutes)](https://www.youtube.com/watch?v=mueG6z1mo8Y)
- [Medium - Data Engineering System Design: Clickstream Data Into a Modern Lakehouse](https://medium.com/@s.sarathvarma/data-engineering-system-design-clickstream-pipeline-into-a-modern-lakehouse-b977696030f7)