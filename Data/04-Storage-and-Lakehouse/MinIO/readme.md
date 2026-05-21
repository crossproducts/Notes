# Apache Airflow

> [!NOTE]   
> **Status**: In Progress

---

## Notes:
- `mc` = MinIO Client
- Object Storage
- S3-Compatible 
- PBAC (Policy-Based Access Control): AWS IAM-style JSON policies for S3/object-storage access
- Apps can talk to MinIO over HTTP/HTTPS using S3-style APIs
- Browser UI
- Custom expiration of sharable link to file

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

## MinIO CLient Commands

### Essential Client Commands
- `mc alias set`: Configures a new MinIO or S3-compatible server with an alias, URL, and credentials.
- `mc ls`: Lists buckets and objects. Use --recursive (or -r) to see all contents.
- `mc mb`: Creates a new bucket (Make Bucket).
- `mc cp`: Copies objects between sources (local or remote) and targets.
- `mc mv`: Moves objects from one location to another.
- `mc mirror`: Synchronizes (mirrors) a local folder with a remote bucket or vice versa.
- `mc rm`: Removes specific objects.
- `mc rb`: Removes an entire bucket and its contents.
- `mc find`: Searches for objects based on names, sizes, or patterns.
- `mc stat`: Displays detailed metadata for objects and buckets.
- `mc cat`: Displays the content of an object to the standard output.
- `mc share`: Generates temporary URLs for secure object sharing

### Administration Commands (`mc admin`)
- `mc admin info`: Displays overall server status, including disk usage and uptime.
- `mc admin user`: Manages users (add, disable, or list).
- `mc admin policy`: Manages Access Control Policies (IAM).
- `mc admin heal`: Scans and repairs damaged or corrupted data.
- `mc admin update`: Updates all MinIO servers in the deployment to the latest version.
- `mc admin service`: Restarts or stops MinIO server instances

---

## References
- [Youtube | LinuxCloudHacks - MINIO 101](https://www.youtube.com/watch?v=tH8LuZsSdHg)