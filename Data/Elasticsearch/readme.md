# Elasticsearch

> [!NOTE]   
> **Status**: Pending
---

## Architecture
- **Beats**: Data Collection
- **Redis**, **Kafka** or **RabbitMQ**
- **Logstash**: Data Aggregaton & Processing
- **Elasticsearch**: Indexing & Storage
- **X-Pack**: Additional Features to Elasticsearch
- **Kibana**: Analysis & Visualization

## Features
Full text search   
Vector Database (vector search)   

## Notes
- Sharding: 
    - Index has 1 shard by default 
    - Shards are pieces of an index
    - Split
    - Shrink
    - Cannot change shards, create new index, with new numbe of shards
- Replication:
    - Replicate shards on different nodes 
    - Increase throughput of index
    - Replica Group
- Snapshots
- Node Roles
- Routing

## Elasticsearch → Opensearch
### Migration Scenarios
- If you're on Elasticsearch ≤ 7.10 → migration is easy
- If you're on Elasticsearch ≥ 7.11 → migration is harder
### Migration Methods
- Snapshot & Restore (BEST option)
- Remote Reindex (MOST flexible)
    - OpenSearch pulls data from Elasticsearch
- Dual Write (zero downtime)
    - App writes to **BOTH** clusters

## References
- [Youtube | ByteMonk: Elasticsearch in 10 minutes](https://www.youtube.com/watch?v=6k6-OeWZTYY)
- [Youtube | freeCodeCamp.org : Elasticsearch course for Begnners](https://www.youtube.com/watch?v=a4HBKEda_F8)
    - [Github | ElasticSearch Course / notebooks](https://github.com/ImadSaddik/ElasticSearch_Python_Course/tree/main/notebooks)