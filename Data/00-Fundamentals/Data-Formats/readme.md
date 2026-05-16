# Data Formats

> **Status:** 🔴 Pending — skeleton created, content to be filled in.

## Why it matters

File format decides read speed, compression ratio, and how schema changes are handled.

## Formats

| Format | Layout | Best for |
|---|---|---|
| [Parquet](Parquet/) | Columnar | Analytical reads, lakehouse tables |
| [ORC](ORC/) | Columnar | Hive-ecosystem analytics |
| [Avro](Avro/) | Row | Streaming, schema evolution |
| [JSON](JSON/) | Row, text | Interchange, semi-structured data |
