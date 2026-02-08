<h1>AWS Security Specialty</h1>

<details><summary>Section 1: Important Course Infromation</summary> 

```
```
</details><br/>

<details><summary>Section 2: Code and Slides Download</summary> 

```
```
</details><br/>

<details><summary>Section 3: Domain 1: Detection</summary> 

```
GuardDuty
Threat detection service that continuously analyzes AWS data sources for malicious activity
Protect against CryptoCurrency, Crypto-mining Attacks
GuardDuty detects threats but never blocks them
Data Sources
CloudTrail Event Logs
VPC Flow Logs
DNS Logs
Optional Features: EKS Audit Logs, RDS & Aurora, EBS, Lambda, S3 Data Events
EventBridge Rules
Detective
Identify root causes of security issues or suspicious activities 
(using ML or graphs)
Security Hub
Central security posture management service.
Aggregates and prioritizes security findings across AWS services.
Security Hub + Integrated Service
Integrated Services
GuardDuty
Inspector
Macie
IAM Access Analyzer
Firewall Manager
Third-party tools
Config
Firewall Manager
GuardDuty
Health

Penetration Testing on AWS
Test without prior approval
EC2
RDS
CloudFront
Aurora
API Gateway
Lambda and Lambda Edge Functions
LightSail
Elastic Beanstalk
Prohibited Activities
DNS zone walking via Amazon Route53 Hosted Zones
Denial of service (DoS)
Distributed Denial of Service (DDoS)
Simulated DoS
Simulated DDoS
Else
Contact aws-security-simualted-event@amazon.com
https://aws.amazon.com/security/penatration-testing/ 
DDoS Simulation Testing on AWS
Must be AWS DDoS Test Partner
Controlled DDoS attack
Protected Resources or Edge-Optimized API Gateway that is subscribed to Shield Advanced
Attacks must NOT be originated from AWS resources
Attacks must NOT exceed 20 GB/second
Attacks must NOT exceed 5 million packets/second for CloudFront
Attacks must NOT exceed 50,000 packets/second for any other service

Compromised AWS Resources
Compromise EC2
Steps to address  compromised instances
Capture Instance metadata
Enable Termination Protection
Isolate Instance (replace instances SG - no outbound traffic authorized)
Detach Instance from ASG (suspend processes)
Deregister the instance from any ELB 
Snapshot the EBS volumes (deep analysis)
Tag the EC2 Instance (i.e investigation ticket)
Offline Investigation
Shutdown instance
Online Investigation
Snapshot memory or capture network traffic
Automate the isolation process
Lambda
Automate memory capture
SSM Run Command
Compromised S3 Bucket
GuardDuty: Identify compromised S3 bucket
CloudTrail or Amazon Detective: Identify the source of the malicious activity and the api calls
Compromised ECS Cluster
GuardDuty: Identify affected ECS Cluster
CloudTrail or Amazon Detective: Identify the source of the malicious activity and the api calls
Isolate the impacted tasks (deny all ingress/egress traffic to the task using security groups)
Evaluate the presence of malicious activity
Compromised AWS Credentials

EC2 Instance Connect
Acceptable Use Policy’
Abuse Report
IAM Access Analyzer
Multiple Accounts - Security Hub Designated Administrator per sub account
```
</details><br/>

<details><summary>Section 4: Domain 2: Incident Response</summary> 

```
Inspector
Inspect for vulnerabilities (CVE’s)
EC2
ECS container images
Lambda
System Manager (SSM)
Tags & Resource Groups
specify which resources SSM should work on
Documents & Run Commands
JSON or Yaml
Define parameters and actions
Define what SSM should do 
```
</details><br/>

<details><summary>Section 5: Domain 3: Infrastructure Security</summary> 

```
```
</details><br/>

<details><summary>Section 6: Domain 4: Identity and Access Management</summary> 

```
IAM Policies
Identity Based Policies
Users
Groups
Roles (Federated Access or AWS Services - S3, EC2, DynamoDB)
Resource Based Policies
AWS Resources - Byproducts from  AWS Services (S3 Buckets, the storage or compute)
IAM Policy Structure
"Version" - Always includes "2012-10-17"
"Id" - Policy Identifier (optional)
"Statement" - One or more statements
"Sid" - Statement Identifier
"Effect" - Allow or Deny
"Principal" - Account / User / Role to which this policy applies to (WHO is allowed or denied)
Principal is required ONLY in resource-based policies.
Principal is NOT allowed in identity-based policies.
"Action" - List of actions this policy allows or denies (according to the "Efffect")
"NotAction" - <"Effect": Allow / Deny> anything NOT in the <"NotAction"> 
"Resource" - List of resources to which the action applied to (WHAT is allowed or denied)

"Condition" - Conditions for when this policy is in effect
String Operator:
"StringEquals" - Exact match
"StringNotEquals" - Not equal
"StringLike" - Wildcard
"aws:PrincipalArn" - restricts WHO among already-matched "Principal" 
"StringNotLike" - Negated wildcard
Numeric Operator:
NumericEquals
NumericLessThan
NumericGreaterThan
NumericBetween
Data Operator
DateEquals
DateLessThan
DateGreaterThan
Boolean Operator
"Bool"
IP Address Operator
"IpAddress"
"NotIpAddress"
ARN Operator
"ArnEquals"
"ArnLike"
Global Condition Keys
aws:SourceIp - Client IP
aws:RequestedRegion - Region restriction
aws:CurrentTime - Time-based access
aws:MultiFactorAuthPresent - MFA required
aws:PrincipalArn - Who is calling
aws:PrincipalAccount - Account ID
aws:PrincipalTag
aws:UserAgent - SDK / CLI
aws:ViaAWSService - Service-to-service calls
aws:SecureTransport - HTTPS required
Condition Modifiers
EXAMPLE: StringEqualsIfExists
"...IfExists" - Only evaluate if key exists
"...ForAllValues" - All must match
"...ForAnyValue" - Any may match
IAM MFA - Multi Factor Authentication

STS
STS - Security Token Service
Toke valid for up to 1 hour
AssumeRole - 
AssumeRoleWithSAML - 
AssumeRoleWithWebIdentity - 
GetSessionToken - 



SCP
SCP - Security Control Policy
S3

⚠️ Cognito ⚠️
⚠️ Federated Identity ⚠️
⚠️ Directory Service ⚠️
AD - Microsoft Active Directory


Objects are organized in Trees
A group of Trees is a Forest
ADFS - Microsoft Active Directory Federation Services
AWS Directory Service - AWS Managed Microsoft Active Directory
AD Connector - 
Simple AD - 
```
</details><br/>

<details><summary>Section 7: Domain 5: Data Protection</summary> 

```
Client Side Encryption
Server Side Encryption (at rest)
```
</details><br/>

<details><summary>Section 8: Domain 6: Security Foundations and Governance</summary> 

```
Organizations
Control Tower
IAM Policy & Tag Policy
Config
Config - Account Compliance
All AWS services or specific AWS services
Config - Aggregator: Collect Config Compliance from other AWS accounts
Config -> EventBridge -> Lambda (invoke action)
Config -> EventBridge -> SNS (trigger notification)
Config -> SSM Automation -> (Ex. Rotate Access Keys)
Trusted Advisor
Recommendations on Account Categories
Cost Optimization
Performance
Security
Fault Tolerance
Service Limits
Operational Excellence
Business & Enterprise Support Plan 
Full Set of Checks
Programmatic Access using AWS Support API
Cost Explorer
Cost Dashboard and Reports
Cost Anomaly Detection
Audit Manager
Automates evidence collection for audit readiness (SOC 2, ISO 27001, PCI DSS, CIS, HIPAA).
Continuously maps AWS resource configurations and activities to control frameworks.

Cloud Formation
Cloud Formation - Service Role
Allows CloudFormation to assume an IAM role when creating/updating/deleting resources.
Cloud Formation - Stack Policy
Protects specific resources in a stack from being updated or deleted.
Cloud Formation - Dynamic References
Securely reference secrets at runtime without storing them in templates.
AWS Secrets Manager
SSM Parameter Store
Cloud Formation - Termination Protection
Prevents accidental deletion of a stack
Cloud Formation - Drift Detection
Detects when stack resources no longer match the template
Cloud Formation - Guard
Defines policy-as-code rules for CloudFormation templates
Enforce
Encryption at rest
No public S3 buckets
Mandatory tags
Restricted IAM policies
Service Catalog
Provides approved, governed infrastructure products to end users
Resource Access Manager (AWS RAM)
```
</details><br/>

<details><summary>Section 9: Other Services</summary> 

```
```
</details><br/>

<details><summary>Section 10: Exam Preparation</summary> 

```
```
</details><br/>

<details><summary>Section 11: Congraulations - AWS Certified Security Specialty</summary> 

```
```
</details><br/>