<h1>Udemy: AWS Certified Machine Learning Engineer Associate: Hands On!</h1>   

<details><summary>Section 1: Introduction</summary> 

```
```
</details><br/>

<details><summary>Section 2: Data Ingestion and Storage</summary>   

```   
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
        EBS per Availability Zone (snapshot to migrate)
    EFS
        Network attached Storage
        Attach to multiple EC2 instances
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
        Retain data up to 365 days
        !!! Data cannot be deleted from Kinesis (until it expires)

    Kinesis Data Firehose

    Amazon Managed Service for Apache Flink

    Amazon MSK

```    
</details><br/>

<details><summary>Section 3: Data Transformation, Integrity, and Feature Engineering</summary>

```
```
</details><br/>

<details><summary>Section 4: AWS Managed AI Services</summary>

```
```
</details><br/>

<details><summary>Section 5: Sagemaker Built-In Algorithms</summary>

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
    <li>❗Important</li>
    <li>‼️Really Important</li>
    <li>⚠️ Incomplete</li>
</ul>
