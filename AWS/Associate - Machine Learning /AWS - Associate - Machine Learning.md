# Udemy: AWS Certified Machine Learning Engineer Associate: Hands On!

<details><summary>Section 1: Introduction</summary> 

```
```
</details><br/>

<details><summary>Section 2: Data Ingestion and Storage</summary>   

```   
    Data Warehouse  - Structured Data
        RDS
        Aurora
        Redshift
        DynamoDB
    Data Lake       - Unstructured Data
        S3
        EFS
        FSx
        Glacier
        Backup
    Data Lakehouse  - Semi-Structured Data
        S3
    File Storage - EFS
    Block Storage - EBS
    Object Storage - S3
    AuthN vs AuthZ - Authentication (who) vs Authorization (what they can do)
    S3: 
        S3 Storage Classes
            Standard
            Standard-Infrequent Access
            One Zone-Inferquent Access
            Glacier Instant Retrieval
            Glacier Flexible Retrieval
            Glacier Deep Archive
            Intelligent Tiering
        S3 Lifecycle Rules
            Automate move data to different storage class
        S3 Event Notifications
            S3 → SNS or SQS or Lambda or EventBridge
            May require Policy
        S3 Encryption (At Rest)
            SSE-S3: Server Side Encryption
            SSE-KMS: Server Side Encryption w/ KMS
            SSE-C: Server Side Encryption w/ Customer Provided Keys
            Client Side Encryption
            DSSE-KMS: Dual Server Side Encryption w/ KMS
        S3 Encryption (In Transit)
            SSL/TLS
            Use HTTPS, recommended
            HTTPS is mandatory for SSE-C
            IAM force Encryption In Transit {…“aws:SecureTransport”:”false”...}
            IAM force Encryption At Rest
        S3 Access Points
            Each AP has its own DNS Name
            VPC Origin - instance access not over internet uses VPC Endpoint
        S3 Object Lambda
            Change the S3 object before its retrieved by the caller application
            EX. Redacting information
    EBS
        Attach usb stick
        Can be left unattached
        1 instance to many ebs volumes (may be possoble many instances to 1 or more ebs volume)
        EBS isolated to 1 Availability Zone (snapshot to migrate)
    EFS
        Network attached Storage
        Attach to multiple EC2 instances
        Multiple AZ
        3x cost EBS Volume
        only compatible with linux based AMI (not windows)
        Lifecycle Policy
        EFS Storage Class:
            Standard: Frequently Accessed
            Infrequent Access: cost to retrieve, lower price to store
            Archive: rarely accessed data, 50% cheaper
    FSx
        For 3rd party file Systems:
            FSx for Luster (Linux Cluster)
            FSx for Windows File Server
            FSx for NetApp ONTAP
            FSx for OpenZFS
    Kinesis Data Streams
        Collect and store streaming data in real time
        Replay Capability
        Retain data up to 365 days
        ❗ Data cannot be deleted from Kinesis (until it expires)
        Data up to 1MB
        Data order gauranteed for data with the same "Partial ID"
        At Rest KMS Encryption
        In Flight KMS Encryption
        Kinesis Producer Library (KPL) to write an optimized producer application
        Kinesis Client Library (KCL) to write an optimized consumer application
        Capacity Modes
            Provisioned Mode
            On-Demand Mode
    Amazon Data Firehose (Kinesis Data Firehose)
        Load streaming data into S3 / Redshift / OpenSearch / 3rd Party / custom HTTP
        Fully Managed Sevice
        ❗Near Real Time
        Supports: CSV, JSON, Parquet, Avro, Raw Text, Binary Data
        Converion To: Parquet / ORC, compressions with gzip / snappy
        Custom Conversion using Lambda
    Amazon Managed Service for Apache Flink
        Serverless
        Common Use Cases:
            Streming ETL
            Coninous metric generation
            Responsive Analytics
        Flink Source:
            Amazon Kinesis Data Streams
            Amazon Managed Streaming for Apache Kafka
        Flink Sinks:
            S3
            Amazon Kinesis Data Streams
            Amazon Kinesis Data Firehose
    Amazon Managed Service for Kafka (MSK)
        Kafka is alternative to Kinesis
            Can send larger messages than Kinesis (10MB) 
            More Configurable
        MSK fully managed service 
        Producers --> MSK --> Consumers
        Producers:
            Kinesis
            IOT
            RDS
        Consumers:
            EMR
            S3
            SageMaker
            Kinesis
            RDS
        MSK Security
            Encryption
                Optional in-flight TLS between brokers
                Optional in-flight TLS between brokers and clients
                At rest for EBS volumes using KMS
            Network Security
                Authorize specific Security Groups for Apache Kafka clients
            Authentication & Authorization
                Define who can read and write to which topics
                Mutual TLS (AuthN) + Kafka ACLs (AuthZ)
                SASL/SCRAM (AuthN) + Kafka ACLs (AuthZ)
                IAM Access Control (AuthN + AuthZ)
            MSK Connect

```    
</details><br/>

<details><summary>Section 3: Data Transformation, Integrity, and Feature Engineering</summary>

```
    AWS EMR (Elastic Map Reduce)
    SageMaker   
        SageMaker AI 
        SageMaker Ground Truth
            Humans Label large datasets
        Amazon Mechanical Turk
        SageMaker Data Wrangler
        SageMaker Model Monitor
        SageMaker Clarify
            Detect Bias
        SageMaker Feature Store
        SageMaker Canvas
        SageMaker Neo
            deploy models on "Edge devices"
    AWS Glue
        AWS Glue
            Schedule and manage ETL Jobs
        AWS Glue Studio
            Full ETL pipeline creation and orchestration
        AWS Glue Data Quality
        AWS Glue DataBrew
            UI, Pre-processing large data sets, Output S3
            Over 250 ready-made transformations
            Purpose: Data cleaning & preparation, exploratory transformation
            Skewed Data, use Median replacement for missing data
            SMOTE (Synthetic Minority Over-sampling Technique) - generate synthetic data without simply duplicating existing data
    Amazon Athena
        Interactive Query service for S3
        Serverless
        CSV, TSV, JSON (human readable)
        ORC, Parquet (columnar, splittable)
        Avro (splittable)
        Snappy, Zlib, LZO, Gzip (compression)
        S3 --> Glue --> Amazon Athena --> Amazon Quicksight
        Athena Workgroups - (IAM) limit access / usage / encryption / cost
        Save Money / Better Performance: 
            ORC or Parquet
            Use partitions
            small number of large files > than large number of small files
        ACID Transaction
            Concurrent users safe
            No need to lock and unlock file
```
</details><br/>

<details><summary>Section 4: AWS Managed AI Services</summary>

```
```
</details><br/>

<details><summary>Section 5: SageMaker Built-In Algorithms</summary>

```
```
</details><br/>

<details><summary>Section 6: Model Training, Tuning, and Evaluation</summary>

```
```
</details><br/>

<details><summary>Section 7: Generative AI Model Fundamentals</summary>

```
```
</details><br/>

<details><summary>Section 8: Building Generative AI Applications with Bedrock</summary>

```
```
</details><br/>

<details><summary>Section 9: Machine Learning Operations (MLOps) with AWS</summary>

```
```
</details><br/>

<details><summary>Section 10: Security, Identity and Compliance</summary>

```
```
</details><br/>

<details><summary>Section 11: Management and Governance</summary>

```
```
</details><br/>

<details><summary>Section 12: Machine Learning Best Practices</summary>

```
```
</details><br/>

<details><summary>Section 13: Practice Test</summary>

```
```
</details><br/>

<details><summary>Section 14: Wrapping Up</summary>

```
```
</details><br/>

<hr/>

<h3>Key</h3>
<ul>
    <li>❗ : Important</li>
    <li>‼️ : Really Important</li>
    <li>⚠️ : Incomplete</li>
</ul>



AWS Batch