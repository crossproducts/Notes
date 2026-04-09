# AI

> A complete reference for Artificial Intelligence concepts, algorithms, evaluation metrics, and tooling.
> Cross-links to other notes in this repo are provided where relevant.

## Directory Index

| File | Description |
|---|---|
| [ai-readme.md](ai-readme.md) | AI taxonomy tree with evaluation metrics (this file) |
| [ai-ml-readme.md](ai-ml-readme.md) | ML algorithms cheatsheet — use cases, pros/cons, hyperparameters |
| [ai-ml-dl-readme.md](ai-ml-dl-readme.md) | Deep Learning — architectures, embeddings, Transformers, LLMs |
| [ai-llm-readme.md](ai-llm-readme.md) | LLM reference — model families, fine-tuning, quantisation, benchmarks |
| [ai-prompt-engineering.md](ai-prompt-engineering.md) | Prompt engineering patterns and techniques |
| [ai-rag.md](ai-rag.md) | Retrieval-Augmented Generation pipeline and evaluation |
| [ai-agent-readme.md](ai-agent-readme.md) | AI agents — loops, memory, tools, multi-agent frameworks |
| [ai-mlops.md](ai-mlops.md) | MLOps — experiment tracking, CI/CD, deployment, monitoring |
| [ai-nlp-readme.md](ai-nlp-readme.md) | NLP — tokenisation, tasks, models, benchmarks |
| [ai-computer-vision.md](ai-computer-vision.md) | Computer Vision — detection, segmentation, generation |
| [ai-time-series.md](ai-time-series.md) | Time series — forecasting, decomposition, models |
| [ai-ethics-and-safety.md](ai-ethics-and-safety.md) | AI ethics — fairness, explainability, responsible AI |
| [ai-data-readme.md](ai-data-readme.md) | Data fundamentals — collection, labelling, versioning, splits |

## Related Repo Notes

| Topic | Link |
|---|---|
| LangChain | [!LangChain](../!LangChain/) |
| LangGraph | [!LangGraph](../!LangGraph/) |
| LangSmith | [!LangSmith](../!LangSmith/) |
| HuggingFace | [!HuggingFace](../!HuggingFace/) |
| Pinecone (Vector DB) | [!Pinecone](../!Pinecone/) |
| Chroma (Vector DB) | [!Chroma](../!Chroma/) |
| NannyML (Model Monitoring) | [!NannyML](../!NannyML/) |
| MLflow (Experiment Tracking) | [✔MLflow](../✔MLflow/) |
| Knowledge Graphs | [!Knowledge-Graphs](../!Knowledge-Graphs/) |
| MCP | [!MCP](../!MCP/) |
| Ollama (Local AI Models) | [!Ollama](../Infrastructure/Ollama/) |

---

## AI Taxonomy Tree

```
Artificial Intelligence (AI)
│
├── Machine Learning (ML)                         → see ai-ml-readme.md
│   │
│   ├── Supervised Learning
│   │   │
│   │   ├── Regression
│   │   │   ├── Linear Regression
│   │   │   │     Metrics: MAE, MSE, RMSE, R², Adjusted R²
│   │   │   ├── Polynomial Regression
│   │   │   │     Metrics: MAE, MSE, RMSE, R², Adjusted R²
│   │   │   ├── Ridge Regression
│   │   │   │     Metrics: MAE, MSE, RMSE, R², cross-validated MSE vs. λ
│   │   │   ├── Lasso Regression
│   │   │   │     Metrics: MAE, MSE, RMSE, R², number of non-zero coefficients
│   │   │   ├── Elastic Net
│   │   │   │     Metrics: MAE, MSE, RMSE, R², sparsity ratio
│   │   │   ├── Support Vector Regression (SVR)
│   │   │   │     Metrics: MAE, MSE, RMSE, R², ε-insensitive loss
│   │   │   ├── Decision Tree Regressor
│   │   │   │     Metrics: MAE, MSE, RMSE, R², tree depth / complexity
│   │   │   ├── Random Forest Regressor
│   │   │   │     Metrics: MAE, MSE, RMSE, R², OOB error, feature importance
│   │   │   ├── Gradient Boosting Regressor
│   │   │   │     Metrics: MAE, MSE, RMSE, R², learning curve loss, feature importance
│   │   │   ├── XGBoost Regressor
│   │   │   │     Metrics: MAE, MSE, RMSE, R², log-loss on validation set, feature importance
│   │   │   └── Neural Network Regressor
│   │   │         Metrics: MAE, MSE, RMSE, R², training/validation loss curve
│   │   │
│   │   └── Classification
│   │       ├── Logistic Regression
│   │       │     Metrics: Accuracy, Precision, Recall, F1, ROC-AUC, Log-Loss, Confusion Matrix
│   │       ├── k-Nearest Neighbors (kNN)
│   │       │     Metrics: Accuracy, Precision, Recall, F1, ROC-AUC, Confusion Matrix
│   │       ├── Support Vector Machine (SVM)
│   │       │     Metrics: Accuracy, Precision, Recall, F1, ROC-AUC, Hinge Loss
│   │       ├── Decision Tree Classifier
│   │       │     Metrics: Accuracy, Precision, Recall, F1, ROC-AUC, Gini Impurity / Entropy
│   │       ├── Random Forest Classifier
│   │       │     Metrics: Accuracy, Precision, Recall, F1, ROC-AUC, OOB error, feature importance
│   │       ├── Gradient Boosting
│   │       │     Metrics: Accuracy, Precision, Recall, F1, ROC-AUC, Log-Loss, feature importance
│   │       ├── XGBoost
│   │       │     Metrics: Accuracy, Precision, Recall, F1, ROC-AUC, Log-Loss, feature importance
│   │       ├── Naive Bayes
│   │       │     Metrics: Accuracy, Precision, Recall, F1, ROC-AUC, Log-Loss
│   │       └── Neural Network Classifier
│   │             Metrics: Accuracy, Precision, Recall, F1, ROC-AUC, Cross-Entropy Loss
│   │
│   ├── Unsupervised Learning
│   │   │
│   │   ├── Clustering
│   │   │   ├── K-Means
│   │   │   │     Metrics: Inertia (WCSS), Silhouette Score, Davies-Bouldin Index, Calinski-Harabasz Index, Elbow curve
│   │   │   ├── Hierarchical Clustering
│   │   │   │     Metrics: Silhouette Score, Cophenetic Correlation, Davies-Bouldin Index
│   │   │   ├── DBSCAN
│   │   │   │     Metrics: Silhouette Score, noise ratio, number of clusters found, Davies-Bouldin Index
│   │   │   ├── Gaussian Mixture Models (GMM)
│   │   │   │     Metrics: BIC, AIC, Log-Likelihood, Silhouette Score
│   │   │   ├── Mean Shift
│   │   │   │     Metrics: Silhouette Score, number of clusters found, Davies-Bouldin Index
│   │   │   └── Spectral Clustering
│   │   │         Metrics: Silhouette Score, Normalized Cut value, Davies-Bouldin Index
│   │   │         (with labels: ARI, NMI, Homogeneity, Completeness, V-Measure)
│   │   │
│   │   └── Dimensionality Reduction
│   │       ├── Principal Component Analysis (PCA)
│   │       │     Metrics: Explained Variance Ratio (per component & cumulative), Reconstruction Error
│   │       ├── t-SNE
│   │       │     Metrics: KL Divergence (stress), qualitative cluster separation in 2D/3D plot
│   │       ├── UMAP
│   │       │     Metrics: Trustworthiness score, qualitative cluster separation, reconstruction fidelity
│   │       ├── Linear Discriminant Analysis (LDA)
│   │       │     Metrics: Between-class / within-class variance ratio, classification accuracy on projected data
│   │       ├── Independent Component Analysis (ICA)
│   │       │     Metrics: Kurtosis of components, Negentropy, reconstruction MSE
│   │       └── Autoencoders
│   │             Metrics: Reconstruction Loss (MSE/BCE), latent space visualisation (t-SNE/UMAP of embeddings)
│   │
│   ├── Reinforcement Learning
│   │   ├── Q-Learning
│   │   │     Metrics: Cumulative reward, average episode reward, Q-value convergence, sample efficiency
│   │   ├── Deep Q Networks (DQN)
│   │   │     Metrics: Cumulative/average reward, TD error, loss curve, epsilon decay curve
│   │   ├── Policy Gradient Methods
│   │   │     Metrics: Average return, policy entropy, baseline variance reduction
│   │   ├── Actor-Critic Methods
│   │   │     Metrics: Average return, critic loss (TD/MSE), actor loss, advantage estimates
│   │   ├── SARSA
│   │   │     Metrics: Cumulative reward, Q-value convergence, on-policy TD error
│   │   ├── Monte Carlo Methods
│   │   │     Metrics: Average episode return, variance of returns, convergence rate
│   │   └── Proximal Policy Optimization (PPO)
│   │         Metrics: Average return, surrogate policy loss, KL divergence (old/new policy), entropy bonus, clipping ratio
│   │
│   └── Deep Learning                             → see ai-ml-dl-readme.md
│       │
│       └── Neural Networks
│           ├── Feedforward Neural Networks (FNN)
│           │     Metrics: Task-specific (see Classification/Regression) + training/validation loss curve, gradient norms
│           ├── Convolutional Neural Networks (CNN)
│           │     Metrics: Accuracy, Top-5 Accuracy, Precision/Recall/F1, IoU & mAP (detection), training/validation loss
│           ├── Recurrent Neural Networks (RNN)
│           │     Metrics: Perplexity (language), BLEU/ROUGE (seq2seq), MAE/RMSE (time series), Cross-Entropy Loss
│           ├── Long Short-Term Memory (LSTM)
│           │     Metrics: Perplexity, BLEU/ROUGE, MAE/RMSE, Cross-Entropy Loss, gradient norm check
│           ├── Gated Recurrent Units (GRU)
│           │     Metrics: Perplexity, BLEU/ROUGE, MAE/RMSE, Cross-Entropy Loss (vs LSTM: speed/accuracy trade-off)
│           ├── Transformers                      → see ai-llm-readme.md, ai-ml-dl-readme.md
│           │     Metrics: Perplexity, BLEU/ROUGE/BERTScore (NLP), Top-1/5 Accuracy (vision), attention entropy
│           ├── Autoencoders
│           │     Metrics: Reconstruction Loss (MSE/BCE), FID score (generative), downstream task accuracy on latent space
│           ├── Generative Adversarial Networks (GANs)
│           │     Metrics: FID (Fréchet Inception Distance), IS (Inception Score), Precision/Recall, G/D loss balance
│           └── Graph Neural Networks (GNN)
│                 Metrics: Node classification: Accuracy, F1 | Link prediction: ROC-AUC, MRR
│                          Graph classification: Accuracy, F1 | Regression on graphs: MAE
```

---

## Hyperparameter Tuning

| Method | Description | Best For |
|---|---|---|
| Grid Search | Exhaustive search over a defined parameter grid | Small search spaces |
| Random Search | Random sampling over parameter distributions | Medium search spaces |
| Bayesian Optimisation | Probabilistic model guides search (Optuna, Hyperopt) | Expensive models |
| Hyperband | Early stopping of poor trials (ASHA scheduler) | Neural networks |
| Population-Based Training | Evolves hyperparameters during training | RL / large models |

## Cross-Validation Strategies

| Strategy | When to Use |
|---|---|
| K-Fold | Default for most tabular tasks |
| Stratified K-Fold | Classification with class imbalance |
| Leave-One-Out (LOO) | Very small datasets |
| Group K-Fold | Grouped/subject data (prevent data leakage) |
| Time-Series Split | Sequential data — never shuffle |

## Bias–Variance Tradeoff

```
Error
  │
  │  Total Error = Bias² + Variance + Irreducible Noise
  │
  │   High Bias          Optimal          High Variance
  │   (Underfitting)     Region           (Overfitting)
  │       ↓                ↓                  ↓
  │   ──────────────────────────────────────────────
  │   Linear Reg      Random Forest      Deep NN (no reg)
  │   Naive Bayes      XGBoost           Decision Tree (deep)
  │   Small NN         SVMs
```

- Reduce bias: more complex model, more features, less regularisation
- Reduce variance: regularisation, dropout, early stopping, more data, ensemble methods

## Feature Engineering

**Encoding**
- One-Hot Encoding — nominal categories with no order
- Ordinal Encoding — categories with natural order
- Target Encoding — high-cardinality categoricals
- Embeddings — very high-cardinality (learned representations)

**Scaling**
- StandardScaler — zero mean, unit variance (SVM, PCA, kNN)
- MinMaxScaler — scales to [0,1] (neural networks)
- RobustScaler — uses median/IQR, robust to outliers

**Feature Selection**
- Filter: mutual information, chi², correlation
- Wrapper: Recursive Feature Elimination (RFE)
- Embedded: Lasso (L1), tree feature importance, SHAP values → see [ai-ethics-and-safety.md](ai-ethics-and-safety.md)

## Handling Class Imbalance

| Technique | Description |
|---|---|
| Class Weights | Penalise misclassification of minority class more |
| Oversampling (SMOTE) | Synthesise new minority-class samples |
| Undersampling | Remove majority-class samples |
| Threshold Tuning | Adjust decision threshold on predicted probabilities |
| Use better metrics | Prefer F1, PR-AUC, MCC over accuracy |

## Model Selection Quick Guide

| Scenario | Start With |
|---|---|
| Tabular, <10k rows | Gradient Boosting (XGBoost/LightGBM), Random Forest |
| Tabular, interpretability required | Logistic/Linear Regression, Decision Tree |
| Text / NLP | Transformers (BERT, RoBERTa) → see [ai-nlp-readme.md](ai-nlp-readme.md) |
| Images | CNN / Vision Transformer → see [ai-computer-vision.md](ai-computer-vision.md) |
| Time series | LSTM / Temporal CNN / Prophet → see [ai-time-series.md](ai-time-series.md) |
| Sequences / language generation | GPT-style Transformers → see [ai-llm-readme.md](ai-llm-readme.md) |
| No labels available | Clustering, Autoencoders, Self-supervised learning |
| Sequential decision-making | Reinforcement Learning |

---

## Metric Legend

| Abbreviation | Full Name |
|---|---|
| MAE | Mean Absolute Error |
| MSE | Mean Squared Error |
| RMSE | Root Mean Squared Error |
| R² | Coefficient of Determination |
| AUC / ROC-AUC | Area Under the ROC Curve |
| MCC | Matthews Correlation Coefficient |
| OOB | Out-of-Bag error (ensemble methods) |
| BIC / AIC | Bayesian / Akaike Information Criterion |
| WCSS | Within-Cluster Sum of Squares (Inertia) |
| ARI | Adjusted Rand Index |
| NMI | Normalized Mutual Information |
| FID | Fréchet Inception Distance |
| IS | Inception Score |
| IoU / mAP | Intersection over Union / Mean Average Precision |
| BLEU / ROUGE | Machine translation / summarisation overlap metrics |
| BERTScore | Embedding-based semantic similarity for NLP |
| MRR | Mean Reciprocal Rank (link prediction / ranking) |
| TD error | Temporal Difference error (reinforcement learning) |
| KL Divergence | Kullback-Leibler Divergence |

## References

- [ai-ml-readme.md](ai-ml-readme.md) — ML algorithm cheatsheet
- [ai-ml-dl-readme.md](ai-ml-dl-readme.md) — Deep learning architectures
- [ai-llm-readme.md](ai-llm-readme.md) — LLM reference
- [ai-prompt-engineering.md](ai-prompt-engineering.md) — Prompt engineering
- [ai-rag.md](ai-rag.md) — RAG pipeline
- [ai-agent-readme.md](ai-agent-readme.md) — AI agents
- [ai-mlops.md](ai-mlops.md) — MLOps
- [Scikit-learn Docs](https://scikit-learn.org/stable/)
- [Papers With Code](https://paperswithcode.com/)
