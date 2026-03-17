# NannyML

NannyML is an open-source Python library for **post-deployment model monitoring**. It detects data drift, concept drift, and estimates model performance without requiring ground truth labels — making it ideal for monitoring ML models in production.

## Key Features

- **CBPE (Confidence-Based Performance Estimation)** – Estimates model performance metrics without ground truth.
- **DLE (Direct Loss Estimation)** – Estimates regression model performance without labels.
- **Data Drift Detection** – Detects changes in feature distributions using statistical tests.
- **Multivariate Drift** – Uses PCA-based reconstruction error to detect multivariate drift.
- **Concept Drift Detection** – Identifies when the relationship between features and targets shifts.
- **Ranking** – Ranks features by their contribution to drift.
- **Alerts** – Configurable thresholds that trigger alerts when drift or performance degrades.

## Installation

<details>
<summary>📦 Install via pip</summary>

```bash
pip install nannyml
```

</details>

<details>
<summary>📦 Install with extras (for Slack alerting, cloud storage, etc.)</summary>

```bash
pip install nannyml[slack]
pip install nannyml[gcs]
pip install nannyml[s3]
```

</details>

## Quick Start

<details>
<summary>🚀 Load example dataset and run CBPE</summary>

```python
import nannyml as nml

# Load built-in binary classification dataset
reference, analysis, analysis_targets = nml.load_synthetic_binary_classification_dataset()

# Define metadata
metadata = nml.extract_metadata(reference, model_type='classification_binary')
metadata.target_column_name = 'work_home_actual'

# Estimate performance using CBPE
estimator = nml.CBPE(
    model_metadata=metadata,
    chunk_size=5000,
    metrics=['roc_auc', 'f1']
)
estimator.fit(reference)
results = estimator.estimate(analysis)

# Plot results
results.plot(kind='performance', metric='roc_auc').show()
```

</details>

## Data Drift Detection

<details>
<summary>📊 Univariate drift detection</summary>

```python
import nannyml as nml

reference, analysis, _ = nml.load_synthetic_binary_classification_dataset()
metadata = nml.extract_metadata(reference, model_type='classification_binary')

# Univariate drift detector
univariate_calculator = nml.UnivariateDriftCalculator(
    model_metadata=metadata,
    chunk_size=5000
)
univariate_calculator.fit(reference)
results = univariate_calculator.calculate(analysis)

# Plot drift for a specific feature
results.plot(kind='drift', metric='statistic', feature='salary_range').show()
```

</details>

<details>
<summary>📊 Multivariate drift detection (PCA-based)</summary>

```python
import nannyml as nml

reference, analysis, _ = nml.load_synthetic_binary_classification_dataset()
metadata = nml.extract_metadata(reference, model_type='classification_binary')

# Multivariate drift using reconstruction error
multivariate_calculator = nml.DataReconstructionDriftCalculator(
    model_metadata=metadata,
    chunk_size=5000
)
multivariate_calculator.fit(reference)
results = multivariate_calculator.calculate(analysis)

results.plot(kind='drift').show()
```

</details>

## Performance Estimation

<details>
<summary>📈 DLE for regression models</summary>

```python
import nannyml as nml

reference, analysis, _ = nml.load_synthetic_car_price_dataset()
metadata = nml.extract_metadata(reference, model_type='regression')
metadata.target_column_name = 'y'

# Direct Loss Estimation
estimator = nml.DLE(
    model_metadata=metadata,
    chunk_size=6000,
    metrics=['rmse', 'mae']
)
estimator.fit(reference)
results = estimator.estimate(analysis)

results.plot(kind='performance', metric='rmse').show()
```

</details>

## Ranking Features by Drift

<details>
<summary>🏆 Rank features contributing most to drift</summary>

```python
import nannyml as nml

reference, analysis, _ = nml.load_synthetic_binary_classification_dataset()
metadata = nml.extract_metadata(reference, model_type='classification_binary')

univariate_calculator = nml.UnivariateDriftCalculator(
    model_metadata=metadata,
    chunk_size=5000
)
univariate_calculator.fit(reference)
univariate_results = univariate_calculator.calculate(analysis)

# Rank features by alert count
ranker = nml.AlertCountRanker()
ranked = ranker.rank(univariate_results, metadata)
print(ranked)
```

</details>

## Chunking Strategies

NannyML splits data into **chunks** for monitoring. Available strategies:

- **Size-based** – Fixed number of rows per chunk (`chunk_size=5000`)
- **Count-based** – Fixed number of chunks (`chunk_number=10`)
- **Period-based** – Chunks based on time period (`chunk_period='M'` for monthly)

<details>
<summary>🗂️ Using period-based chunking</summary>

```python
estimator = nml.CBPE(
    model_metadata=metadata,
    chunk_period='W',   # Weekly chunks
    metrics=['roc_auc']
)
estimator.fit(reference)
results = estimator.estimate(analysis)
```

</details>

## Notes

- Always fit on **reference data** (pre-deployment/training period) before calling `.calculate()` or `.estimate()`.
- NannyML requires a **predicted probability column** (`y_pred_proba`) for classification performance estimation.
- Use `nml.extract_metadata()` to auto-detect column types, then manually set `target_column_name`.

## References

- [Official Docs](https://nannyml.readthedocs.io/en/stable/)
- [GitHub Repository](https://github.com/NannyML/nannyml)
- [PyPI](https://pypi.org/project/nannyml/)
- [NannyML Blog](https://www.nannyml.com/blog)
