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
- Optimistic Concurrency 

## HTTP Verbs (methods) + Path = API Endpoint
| Verb   | Path | Definition / Purpose |
|--------|------|---------------------|
| GET | `/{index}/_doc/{id}` | Get document by ID |
|  | `/{index}/_search` | Search/query documents |
|  | `/_cat/indices` | List indices (human-readable) |
|  | `/{index}/_mapping` | Get index schema |
|  | `/_cluster/health` | Cluster status |
| POST | `/{index}/_doc` | Create document (auto ID) |
|  | `/{index}/_search` | Execute search (with body) |
|  | `/_bulk` | Bulk operations (index/update/delete) |
|  | `/{index}/_update/{id}` | Partial update |
|  | `/{index}/_delete_by_query` | Delete matching docs |
|  | `/{index}/_update_by_query` | Update via query |
|  | `/_reindex` | Copy data between indices |
| PUT | `/{index}` | Create index |
|  | `/{index}/_doc/{id}` | Create/replace document with ID |
|  | `/{index}/_mapping` | Update mappings |
|  | `/_snapshot/{repo}` | Create snapshot repository |
| PATCH | `(usually replaced with POST _update)` | Partial update (rare in Elasticsearch) |
| DELETE | `/{index}` | Delete index |
|  | `/{index}/_doc/{id}` | Delete document by ID |
|  | `/{index}/_query` | Deprecated (use `_delete_by_query`) |
|  | `/_snapshot/{repo}/{snapshot}` | Delete snapshot |

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