# Machine Learning — Algorithm Cheatsheet

> Quick reference for every ML algorithm: use case, pros, cons, key hyperparameters, and typical data size.
> See [ai-readme.md](ai-readme.md) for the full taxonomy tree and evaluation metrics.

## Regression Algorithms

| Algorithm | Best Use Case | Pros | Cons | Key Hyperparameters |
|---|---|---|---|---|
| Linear Regression | Continuous target, linear relationships | Fast, interpretable, no hyperparameters | Assumes linearity, sensitive to outliers | — |
| Polynomial Regression | Non-linear relationships | Fits curves | Overfits easily at high degree | degree |
| Ridge (L2) | Multicollinear features | Shrinks coefficients, stable | Doesn't zero out features | alpha (λ) |
| Lasso (L1) | Feature selection + regression | Zeroes out irrelevant features | Can drop correlated features arbitrarily | alpha (λ) |
| Elastic Net | High-dimensional, correlated features | Combines L1+L2 benefits | Two regularisation params to tune | alpha, l1_ratio |
| SVR | Small-medium datasets, non-linear | Robust to outliers (ε-tube) | Slow on large data, needs feature scaling | C, ε, kernel |
| Decision Tree Regressor | Interpretable non-linear | No scaling needed, handles mixed types | High variance, overfits | max_depth, min_samples_split |
| Random Forest Regressor | General-purpose tabular | Low variance, robust | Slow inference, not interpretable | n_estimators, max_features, max_depth |
| Gradient Boosting Regressor | Tabular competitions | High accuracy | Slower to train, many hyperparameters | n_estimators, learning_rate, max_depth |
| XGBoost Regressor | Large tabular datasets | Fast, regularisation built-in | Complex to tune | n_estimators, learning_rate, subsample, colsample_bytree |
| Neural Network Regressor | Very large data, complex patterns | Universal approximator | Data hungry, slow, hard to interpret | layers, units, lr, dropout |

## Classification Algorithms

| Algorithm | Best Use Case | Pros | Cons | Key Hyperparameters |
|---|---|---|---|---|
| Logistic Regression | Binary/multiclass, baseline | Fast, probabilistic output, interpretable | Assumes linear boundary | C, penalty, solver |
| kNN | Small datasets, non-linear boundary | No training phase, simple | Slow at inference, sensitive to scale | k, metric |
| SVM | High-dimensional, small-medium data | Effective in high dims, kernel trick | Slow on large data, no probability output natively | C, kernel, gamma |
| Decision Tree Classifier | Interpretable rules | White-box, handles mixed types | High variance | max_depth, min_samples_split, criterion |
| Random Forest Classifier | General-purpose | Robust, handles missing vals | Not interpretable, memory heavy | n_estimators, max_features, max_depth |
| Gradient Boosting | Tabular, imbalanced classes | State-of-the-art accuracy | Slow training, needs tuning | n_estimators, learning_rate, max_depth |
| XGBoost | Large tabular, competitions | Fast, built-in regularisation, handles missing | Complex API | n_estimators, learning_rate, scale_pos_weight |
| LightGBM | Very large datasets | Faster than XGBoost, low memory | Sensitive to overfitting on small data | num_leaves, learning_rate, min_data_in_leaf |
| CatBoost | Datasets with many categoricals | Native categorical support, no encoding | Slow to train | depth, learning_rate, iterations |
| Naive Bayes | Text classification, very fast baseline | Extremely fast, works well with small data | Assumes feature independence | var_smoothing (Gaussian), alpha (Multinomial) |
| Neural Network Classifier | Images, text, audio, large tabular | Universal approximator | Data hungry, computationally expensive | layers, units, lr, dropout, batch_size |

## Unsupervised — Clustering

| Algorithm | Best Use Case | Pros | Cons | Key Hyperparameters |
|---|---|---|---|---|
| K-Means | Spherical, well-separated clusters | Fast, scalable | Must specify k, assumes spherical clusters | n_clusters, init, n_init |
| Hierarchical | Unknown k, interpretable dendrograms | No k needed, deterministic | O(n²) memory, slow | linkage, distance_threshold |
| DBSCAN | Arbitrary shapes, noise/outlier detection | Finds arbitrary shapes, handles noise | Struggles with varying density | eps, min_samples |
| GMM | Soft cluster assignments, elliptical clusters | Probabilistic output, flexible shapes | Assumes Gaussian, needs k | n_components, covariance_type |
| Mean Shift | Unknown k, blob-shaped clusters | No k needed | Slow on large data | bandwidth |
| Spectral Clustering | Graph/manifold data, non-convex shapes | Handles complex shapes | Expensive, needs k | n_clusters, affinity |

## Unsupervised — Dimensionality Reduction

| Algorithm | Best Use Case | Pros | Cons | Key Hyperparameters |
|---|---|---|---|---|
| PCA | Pre-processing, visualisation | Fast, interpretable variance | Only linear | n_components |
| t-SNE | 2D/3D visualisation | Reveals cluster structure | Slow, non-parametric (can't transform new data) | perplexity, learning_rate, n_iter |
| UMAP | Visualisation + downstream tasks | Faster than t-SNE, preserves global structure | Stochastic, harder to interpret | n_neighbors, min_dist, metric |
| LDA | Supervised dim reduction (classification) | Maximises class separability | Assumes Gaussian, linear | n_components |
| ICA | Signal separation (audio, finance) | Recovers independent sources | Assumes statistical independence | n_components |
| Autoencoders | Non-linear dim reduction, anomaly detection | Learns non-linear manifolds | Needs training, architecture choices | latent_dim, layers, lr |

## Reinforcement Learning Algorithms

| Algorithm | Best Use Case | Pros | Cons | Key Hyperparameters |
|---|---|---|---|---|
| Q-Learning | Small discrete action spaces | Simple, convergence guarantees | Doesn't scale to large state spaces | α (learning rate), γ (discount), ε (exploration) |
| DQN | Discrete actions, raw pixel inputs | Scales Q-learning with neural nets | Unstable training, experience replay needed | lr, replay_buffer_size, target_update_freq |
| Policy Gradient | Continuous action spaces | Direct policy optimisation | High variance | lr, baseline |
| Actor-Critic (A2C/A3C) | Continuous / large action spaces | Lower variance than PG, parallel actors | Complex implementation | lr, entropy_coef, value_loss_coef |
| SARSA | On-policy control | Safer (on-policy) than Q-Learning | Slower convergence | α, γ, ε |
| PPO | Most RL tasks, stable training | Simple, stable, widely used | Less sample efficient than SAC | clip_ratio, lr, n_epochs, entropy_coef |
| SAC | Continuous control (robotics) | Sample efficient, entropy regularisation | Complex, sensitive to hyperparameters | lr, alpha (temperature), tau |

---

## Model Selection Flowchart

```
Start
  │
  ├─ Do you have labels?
  │     Yes → Supervised Learning
  │     No  → Unsupervised / Self-supervised
  │
  ├─ Supervised:
  │     ├─ Target is continuous?  → Regression algorithms
  │     └─ Target is categorical? → Classification algorithms
  │           ├─ Need interpretability?  → Logistic Regression, Decision Tree
  │           ├─ Best accuracy (tabular)? → XGBoost / LightGBM
  │           ├─ Text / sequences?        → Transformers → ai-llm-readme.md
  │           └─ Images?                  → CNNs / ViT   → ai-computer-vision.md
  │
  └─ Unsupervised:
        ├─ Find groups?            → Clustering
        ├─ Reduce dimensions?      → PCA / UMAP / Autoencoders
        └─ Generate new data?      → GANs / VAEs / Diffusion models
```

---

## Key Python Libraries

| Library | Purpose | Install |
|---|---|---|
| scikit-learn | Classical ML algorithms | `pip install scikit-learn` |
| XGBoost | Gradient boosting | `pip install xgboost` |
| LightGBM | Fast gradient boosting | `pip install lightgbm` |
| CatBoost | Categorical gradient boosting | `pip install catboost` |
| Optuna | Hyperparameter optimisation | `pip install optuna` |
| imbalanced-learn | SMOTE and resampling | `pip install imbalanced-learn` |
| SHAP | Model explainability | `pip install shap` |

## References

- [ai-readme.md](ai-readme.md) — Full taxonomy and evaluation metrics
- [ai-mlops.md](ai-mlops.md) — Training pipelines, experiment tracking
- [✔MLflow](../✔MLflow/) — Experiment tracking notes
- [!NannyML](../!NannyML/) — Model monitoring in production
- [Scikit-learn User Guide](https://scikit-learn.org/stable/user_guide.html)
- [XGBoost Docs](https://xgboost.readthedocs.io/)
- [Papers With Code — Methods](https://paperswithcode.com/methods)
