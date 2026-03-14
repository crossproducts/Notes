L1 regularization adds a penalty proportional to the absolute value of weights.
If a feature is not important, the weight becomes 0, effectively removing it.

L2 adds a penalty based on the square of weights.

During training, random neurons are temporarily turned off.

Early stopping Training stops when validation performance stops improving.

Canary deployment: releases the new version to a small percentage of users first.

Linear Deployment: Traffic shifts gradually and evenly over time.

Blue-Green: Two identical evironments 

Rolling Deployment: Servers update one group at a time.

A/B Testing: Two versions run simultaneously to test performance

Accuracy: Classes balanced

F1: dataset is imbalanced
pdate
AUC: evaluating model ranking ability / compare models

MAE (Mean Absolute Error): show interpretable errors

Precision: false positives are costly

Recall: False negatives are costly

## Decision tree 
```
Is the problem regression?
      ↓
Yes → MAE or RMSE

No → classification
      ↓
Dataset balanced?
      ↓
Yes → Accuracy

No → F1

Need model ranking?
      ↓
Use ROC-AUC
```

## Instance types
Compute: C
GPU: G, P
Inferentia
Tranium
...

## 
S3 Event Notification: Trigger Lambda, SNS, SQS 
EventBridge: Trigger way more, Sagemaker pipeline

## high-throughput, low-latency access to hundreds of terabytes of video data across multiple SageMaker instances
Amazon FSx for Lustre
Amazon EFS throughput modes

