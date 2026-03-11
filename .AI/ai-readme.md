# AI

```
Artificial Intelligence (AI)
│
├── Machine Learning (ML)
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
│   └── Deep Learning
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
│           ├── Transformers
│           │     Metrics: Perplexity, BLEU/ROUGE/BERTScore (NLP), Top-1/5 Accuracy (vision), attention entropy
│           ├── Autoencoders
│           │     Metrics: Reconstruction Loss (MSE/BCE), FID score (generative), downstream task accuracy on latent space
│           ├── Generative Adversarial Networks (GANs)
│           │     Metrics: FID (Fréchet Inception Distance), IS (Inception Score), Precision/Recall, G/D loss balance
│           └── Graph Neural Networks (GNN)
│                 Metrics: Node classification: Accuracy, F1 | Link prediction: ROC-AUC, MRR
│                          Graph classification: Accuracy, F1 | Regression on graphs: MAE
```

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
