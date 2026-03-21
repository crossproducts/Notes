# The Ultimate AWS Certified Machine Learning Engineer — Associate MLA-C01 cheatsheet: Tools, Techniques, and Key Concepts

By Rafa Xu

[Medium Article](https://medium.com/@rafa.xu.au/the-ultimate-aws-certified-machine-learning-engineer-associate-mla-c01-cheatsheet-tools-e9ad9065f108)

---

## 1. The Amazon SageMaker Ecosystem

### 1.1 SageMaker Studio

Amazon SageMaker Studio: An integrated development environment (IDE) for machine learning, providing a single, web-based interface to perform data preprocessing, model training, and deployment.

### 1.2 SageMaker Domain & User Profile

SageMaker Domain: A domain captures user settings, configurations, and security policies for Studio usage across your organization.

SageMaker User Profile: Represents an individual user within a SageMaker Domain, storing preferences like kernels and compute settings.

### 1.3 SageMaker Pipelines

Amazon SageMaker Pipelines: A fully managed workflow service for building, automating, and managing ML pipelines — handling tasks like data loading, model training, and deployment in a CI/CD-like fashion.

### 1.4 SageMaker Autopilot

SageMaker Autopilot: Automatically explores multiple ML algorithms, tuning parameters to create high-quality models. Provides generated notebooks for transparency and reproducibility.

### 1.5 SageMaker Model Registry & Model Group

Model Registry: A central repository to track and catalog trained models, maintaining version control, approvals, and deployment history.

Model Group: A logical container grouping together different versions of the same model, facilitating model versioning and promotion to production.

### 1.6 SageMaker ML Lineage Tracking

ML Lineage: Tracks the origin of datasets, transformations, and training runs that lead to model creation, helping with reproducibility and audit trails.

### 1.7 SageMaker Managed Spot Training

Managed Spot Training: Leverages unused EC2 capacity at a lower cost. Automatically retries interrupted jobs to reduce overall training costs while handling large datasets.

### 1.8 SageMaker Distributed Data Parallel (SMDDP)

SMDDP Library: A distributed training library enabling data parallelism across multiple instances, thus reducing training time for large models or datasets.

### 1.9 SageMaker Experiments

Experiments: A feature that lets you organize, track, compare, and evaluate machine learning experiments (training jobs) at scale within SageMaker.

### 1.10 SageMaker Debugger

Debugger: Monitors model training in real time, capturing metrics (e.g., gradients, weights) and providing alerts or rules to detect anomalies like vanishing gradients.

### 1.11 SageMaker Endpoint Production Variants

Production Variants: Enables deploying multiple variants of a model to a single SageMaker endpoint, facilitating A/B testing and canary releases for model updates.

### 1.12 SageMaker Shadow Testing

Shadow Testing: Allows you to send a copy of real-time inference traffic to a 'shadow' endpoint, helping validate new model versions without affecting production outcomes.

### 1.13 SageMaker Inference Recommender

Inference Recommender: Helps you choose the optimal instance type and configuration for model inference, automating load testing and performance analysis.

### 1.14 SageMaker Canvas

Canvas: A no-code/low-code interface for business analysts to build ML models via a visual interface, without requiring extensive coding knowledge.

### 1.15 SageMaker Script Mode & Pre-built Containers

Script Mode: Lets you bring your own training script while benefiting from SageMaker's high-performance and distributed training environment.

Pre-built Containers: Managed Docker containers with preinstalled frameworks (e.g., TensorFlow, PyTorch, MXNet) for quick training and deployment.

---

## 2. Data Preparation & Feature Engineering

### 2.1 Amazon SageMaker Data Wrangler

Data Wrangler: A tool within SageMaker Studio for data preparation. You can import datasets, clean and transform data, and automate feature engineering flows.

### 2.2 AWS Glue & Glue DataBrew

AWS Glue: A fully managed ETL service to prepare, transform, and load data for analytics.

Glue DataBrew: A visual data preparation tool for cleaning and normalizing data with an interactive interface.

### 2.5 Feature Engineering Techniques

Feature Group: In SageMaker Feature Store, a logical grouping of data that includes feature definitions and related metadata.

One-Hot Encoding: Transforms categorical variables into a series of binary (0/1) features.

Feature Splitting: Breaks down composite features (e.g., text fields) into multiple meaningful features (e.g., parsing or tokenizing).

Logarithmic Transformation: Applies log(x) to reduce skewness and stabilize variance.

Standardized Distribution: Scales features to have zero mean and unit variance.

Padding: Common in NLP or image tasks to make all input data consistent in size.

### 2.6 Data Wrangler Image Transformations

Enhance Image Contrast: Adjusts image brightness and contrast for better visibility or model performance.

Corrupt Image Transform: Purposefully degrades image quality to augment data and improve model robustness.

Resize Image Transform: Uniformly changes the resolution of images while preserving aspect ratios.

---

## 3. Training & Tuning

### 3.1 Hyperparameter Tuning

Hyperband: An optimization algorithm that dynamically allocates resources to promising hyperparameter configurations.

Grid Search: Exhaustively tests all combinations of hyperparameters within specified ranges.

Random Search: Samples random hyperparameter combinations, often faster than grid search.

Bayesian Optimization: Builds a probabilistic model of the objective function, intelligently picking hyperparameters based on past evaluation results.

### 3.2 Key Training Concepts

Learning Rate: Controls how quickly or slowly a model learns; too high can overshoot minima, too low can slow convergence.

Early Stopping: Halts training when validation performance ceases to improve, preventing overfitting.

Dropout Layers: Randomly "drops" neurons during training to reduce overfitting in neural networks.

### 3.3 SageMaker Managed Warm Pods

Managed Warm Pods: Pre-initialized containers in SageMaker (similar concept to serverless warm starts) that reduce cold-start times for training or inference.

### 3.4 AWS Trainium & AWS Inferentia

AWS Trainium: Custom ML training chips designed by AWS to deliver high-performance training at lower costs.

AWS Inferentia: Purpose-built chips optimized for high-performance ML inference in the cloud.

### 3.5 EMR Cluster Nodes

Primary, Core, and Task Nodes: In Amazon EMR, the primary node manages the cluster, core nodes store data in HDFS and run tasks, while task nodes only run tasks without storing data.

---

## 4. Inference & Deployment

### 4.1 SageMaker Real-Time Inference

Real-Time Inference: Deploy machine learning models to an HTTPS endpoint for sub-second latency predictions.

### 4.2 SageMaker Batch Transform

Batch Transform: Asynchronously runs high-volume inference on batch data stored in Amazon S3 without needing a persistent endpoint.

### 4.3 SageMaker Serverless Inference

Serverless Inference: Automatically provisions and scales compute resources to handle inference requests on demand, ideal for low-traffic or unpredictable workloads.

### 4.4 SageMaker Asynchronous Inference

Asynchronous Inference: Receives inference requests in a queue and processes them asynchronously, suitable for large payloads or long processing times.

---

## 5. Monitoring & Debugging

### 5.1 Model Monitor

Model Monitor: Automatically detects data and model-quality drift in production endpoints. You can configure alerts to identify anomalies early.

### 5.2 Concept Drift

Concept Drift: Occurs when the statistical properties of the target variable or features change over time, causing model degradation if left unchecked.

### 5.3 SageMaker Debugger

(Mentioned above, but worth repeating under monitoring for emphasis.)

Debugger: Captures model metrics during training, providing alerts if anomalies like vanishing gradients, overfitting, or poor GPU utilization occur.

---

## 6. Large Language Models (LLMs)

### 6.1 Fundamental LLM Concepts

Embedding: A learned representation of tokens or sequences in a continuous vector space.

Tokens: Units of text (words, subwords, or characters) used by language models during training and inference.

Temperature: Controls randomness in text generation; higher values produce more diverse outputs, lower values produce more deterministic outputs.

top_k / top_p (Nucleus Sampling): Sampling strategies that limit the model's next-token choices to the top-k predictions or the smallest set of top-p cumulative probability tokens.

### 6.2 Retrieval Augmented Generation (RAG)

RAG: Combines external knowledge retrieval (e.g., from a database or knowledge base) with a generative model, enhancing contextual accuracy and reducing hallucinations.

---

## 7. AWS AI Services

### 7.1 Amazon Comprehend

Comprehend: A natural language processing (NLP) service to extract insights from text (entity recognition, sentiment analysis, topic modeling, etc.).

### 7.2 Amazon Transcribe

Transcribe: Automatic speech recognition (ASR) service that converts audio to text, supporting multiple languages and real-time transcription.

### 7.3 Amazon Translate

Translate: Provides real-time and batch text translation, leveraging neural machine translation models for high-quality multilingual output.

### 7.4 Amazon Rekognition

Rekognition: Image and video analysis service for object detection, facial recognition, and content moderation.

### 7.5 Amazon Macie

Macie: A fully managed data security and privacy service, using ML to identify, categorize, and protect sensitive data (e.g., PII) in AWS.

### 7.6 Amazon Mechanical Turk

Mechanical Turk: A crowdsourcing platform to label and annotate data at scale, helpful for training supervised ML models.

### 7.7 Additional Services (Recommended)

Amazon Kendra: Intelligent search service powered by ML for enterprise data search.

Amazon Forecast: Uses ML to generate accurate forecasts (e.g., product demand, resource needs).

Amazon Personalize: Provides personalized recommendations, leveraging real-time user data.

Amazon Lookout for Vision / Metrics: Services for anomaly detection in images and numerical data, respectively.

---

## 8. Built-In Algorithms & Common ML Tasks

### 8.1 Amazon SageMaker Built-in Algorithms

LightGBM: Gradient boosting framework for classification and regression tasks, optimized for speed and memory usage.

Linear Learner: Performs linear regression or classification with automatic tuning of model weights.

K-Means Clustering: Unsupervised algorithm for grouping data points into K clusters.

Neural Topic Model (NTM): Identifies topics in documents using neural network-based topic modeling.

Random Cut Forest: Anomaly detection algorithm for streaming data, also available in Amazon Managed Service for Apache Flink.

### 8.2 Common ML Tasks

Anomaly Detection: Identifies unusual patterns, outliers, or suspicious events.

Linear Regression: Predicts a continuous value from input features.

Logistic Regression: Estimates the probability of a categorical outcome (e.g., binary classification).

Semantic Segmentation: Assigns labels to each pixel in an image, commonly used in computer vision.

Dimensionality Reduction: Reduces the number of features (e.g., PCA) to mitigate the curse of dimensionality and improve model performance.

---

## 9. Model Performance Metrics

### 9.1 Classification Metrics

Accuracy: The proportion of predictions that are correct out of all predictions made.

Precision: The proportion of true positives out of all predicted positives (true positives plus false positives).

Recall (Sensitivity): The proportion of true positives out of all actual positives (true positives plus false negatives).

F1 Score: The harmonic mean of Precision and Recall, balancing both metrics.

Specificity: The proportion of true negatives out of all actual negatives (true negatives plus false positives).

### 9.2 Regression Metrics

Mean Absolute Error (MAE): Average absolute difference between predictions and actual values.

Mean Squared Error (MSE): The average of the squared differences between the predicted and actual values. MSE heavily penalizes large errors and is commonly used for regression tasks.

R² (Coefficient of Determination): A measure of how much variance in the target variable is explained by the model. R² ranges from 0 to 1, where 1 indicates a perfect fit.

---

## Bonus: What You Might Have Missed

Here are a few optional but relevant services to keep in mind:

Amazon Fraud Detector: Detects potential fraudulent online activities using ML.

Amazon Lookout for Equipment: Identifies abnormal equipment behavior to minimize downtime.

Amazon HealthLake: Stores, transforms, queries, and analyzes health data at scale using ML.

---

## Conclusion

Use this cheatsheet as a reference to rapidly review the essential knowledge about for the AWS Certified Machine Learning Engineer — Associate MLA-C01 exam. Happy Certification!