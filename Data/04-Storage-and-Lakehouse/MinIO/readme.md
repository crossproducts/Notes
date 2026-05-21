# MinIO

> [!NOTE]   
> **Status**: Done

---

## Notes:
- `mc` = MinIO Client
- S3-compatible object storage; self-hosted (on-prem, K8s, edge)
- Apps talk to MinIO over HTTP/HTTPS using S3 APIs — drop-in for `boto3`, `aws-sdk`, etc.
- PBAC (Policy-Based Access Control): AWS IAM-style JSON policies
- Erasure coding spreads object shards across drives/nodes for redundancy without RAID
- Distributed mode: 4+ nodes pooled into a single namespace
- Versioning + object locking (WORM) for compliance / ransomware recovery
- Server-side encryption (SSE-S3, SSE-KMS, SSE-C)
- Built-in browser console at `:9001`
- Pre-signed URLs with custom expiration for temporary sharing
- Bucket notifications → Kafka, webhooks, NATS, etc.

<div style="text-align: center;">

```
AWS ECS / EKS / EC2 App
↓
HTTPS connection
↓
Public DNS / VPN / Private tunnel
↓
MinIO outside AWS
↓
Encrypted local disk / on-prem storage
```
</div>

--- 

## MinIO Client Commands

### Essential Client Commands
- `mc alias set` — register a server (alias, URL, credentials)
- `mc ls` — list buckets/objects (`-r` for recursive)
- `mc mb` — make bucket
- `mc cp` — copy objects (local ↔ remote)
- `mc mv` — move objects
- `mc mirror` — sync folder ↔ bucket
- `mc rm` — remove objects
- `mc rb` — remove bucket (and contents)
- `mc find` — search by name, size, or pattern
- `mc stat` — show object/bucket metadata
- `mc cat` — stream object to stdout
- `mc share` — generate pre-signed URL

### Administration Commands (`mc admin`)
- `mc admin info` — server status, disk usage, uptime
- `mc admin user` — add / disable / list users
- `mc admin policy` — manage IAM policies
- `mc admin heal` — scan and repair corrupted data
- `mc admin update` — update servers in the deployment
- `mc admin service` — restart or stop server instances

---

## References
- [Youtube | LinuxCloudHacks - MINIO 101](https://www.youtube.com/watch?v=tH8LuZsSdHg)