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

## HTTP Verbs (methods) + Path = API Endpoint
- GET     = read data
    * /{index}/_doc/{id} → get document by ID
    * /{index}/_search → search/query documents
    * /_cat/indices → list indices (human-readable)
    * /{index}/_mapping → get index schema
    * /_cluster/health → cluster status
- POST    = run action / create
    * /{index}/_doc → create document (auto ID)
    * /{index}/_search → execute search (with body)
    * /_bulk → bulk operations (index/update/delete)
    * /{index}/_update/{id} → partial update
    * /{index}/_delete_by_query → delete matching docs
    * /{index}/_update_by_query → update via query
    * /_reindex → copy data between indices
- PUT     = replace
    * /{index} → create index
    * /{index}/_doc/{id} → create/replace document with ID
    * /{index}/_mapping → update mappings
    * /_snapshot/{repo} → create snapshot repository
- PATCH   = partial update
    * (usually replaced with POST _update)
- DELETE  = remove
    * /{index} → delete index
    * /{index}/_doc/{id} → delete document by ID
    * /{index}/_query → (deprecated, use _delete_by_query)
    * /_snapshot/{repo}/{snapshot} → delete snapshot

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