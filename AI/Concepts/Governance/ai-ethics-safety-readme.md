# AI Ethics & Safety 

> Reference for fairness, explainability, bias, and responsible AI frameworks.
> See [ai-mlops.md](ai-mlops.md) for model cards and monitoring, [ai-readme.md](ai-readme.md) for the full AI overview.

## Why It Matters

AI systems can cause real harm if built without care:
- Biased hiring algorithms screen out qualified candidates
- Facial recognition misidentifies people of colour at higher rates
- Credit scoring models deny loans based on proxies for protected attributes
- LLMs generate misinformation or harmful content at scale

## Types of Bias

| Bias Type | Description | Example |
|---|---|---|
| Historical bias | Training data reflects past discrimination | Loan data with historic racial redlining |
| Representation bias | Certain groups under-represented in training data | Facial recognition trained mostly on light skin |
| Measurement bias | Different accuracy of measurements across groups | Medical sensors less accurate on darker skin |
| Aggregation bias | One model used for groups with different distributions | Using one diabetes model across all ethnicities |
| Evaluation bias | Benchmark doesn't represent all users | NLP benchmarks skewed toward English, Western culture |
| Deployment bias | Model used in ways not intended by designers | Using a recidivism model for sentencing rather than parole |

## Fairness Metrics

| Metric | Description | Formula |
|---|---|---|
| Demographic Parity | Equal positive prediction rates across groups | P(ŷ=1|A=0) = P(ŷ=1|A=1) |
| Equalized Odds | Equal TPR and FPR across groups | TPR and FPR equal across A=0, A=1 |
| Equal Opportunity | Equal TPR across groups | TPR₀ = TPR₁ |
| Calibration | Predicted probabilities match actual frequencies per group | P(y=1|ŷ=p, A=0) = P(y=1|ŷ=p, A=1) |
| Individual Fairness | Similar individuals receive similar predictions | d(x,x') small ⟹ d(f(x),f(x')) small |

> **Impossibility theorem:** Demographic parity, equalized odds, and calibration cannot all be satisfied simultaneously (except in degenerate cases).

## Explainability (XAI)

### Model-Agnostic Methods

| Method | Type | Description |
|---|---|---|
| SHAP (SHapley Additive exPlanations) | Local + Global | Game-theory-based feature attribution — gold standard |
| LIME | Local | Fits local linear model around a prediction |
| Integrated Gradients | Local | For neural networks — attribution along interpolation path |
| Permutation Importance | Global | Shuffle feature, measure performance drop |
| Partial Dependence Plots (PDP) | Global | Marginal effect of feature on prediction |
| SHAP Summary Plot | Global | Distribution of SHAP values per feature |

```python
import shap
explainer = shap.TreeExplainer(model)
shap_values = explainer.shap_values(X_test)
shap.summary_plot(shap_values, X_test)
```

### Inherently Interpretable Models
- Linear / Logistic Regression (coefficients)
- Decision Trees (rules)
- Rule-based systems
- Generalised Additive Models (GAMs)
- Monotone constraints in gradient boosting

## LLM Safety

| Risk | Description | Mitigation |
|---|---|---|
| Hallucination | Model generates confident but false statements | RAG → [ai-rag.md](ai-rag.md), self-consistency, human review |
| Prompt injection | Malicious input hijacks model behaviour | Input sanitisation, output validation |
| Jailbreaking | Bypassing safety guardrails | RLHF, Constitutional AI, output filters |
| Data leakage | Training data memorised and reproduced | Differential privacy, data deduplication |
| Bias amplification | LLM amplifies societal biases in training data | Diverse training data, fine-tuning, red-teaming |
| Misinformation | Generating false or misleading content at scale | Watermarking, detection tools, human oversight |

## Model Cards

A model card documents what a model does, its limitations, and appropriate use cases.

**Key sections:**
```
1. Model details (name, version, type, creator)
2. Intended use (primary use, out-of-scope use)
3. Factors (relevant demographic/environmental factors)
4. Metrics (performance metrics reported)
5. Evaluation data (datasets used for evaluation)
6. Training data (description of training data)
7. Quantitative analyses (disaggregated evaluation across groups)
8. Ethical considerations
9. Caveats and recommendations
```

## Responsible AI Frameworks

| Framework | Organisation | Principles |
|---|---|---|
| EU AI Act | European Union | Risk-based tiering: unacceptable → high → limited → minimal |
| NIST AI RMF | US NIST | Govern, Map, Measure, Manage |
| Google PAIR | Google | People + AI Research guidelines |
| Microsoft RAI | Microsoft | Fairness, reliability, privacy, inclusiveness, transparency, accountability |
| Anthropic Constitutional AI | Anthropic | Model trained to critique and revise its own outputs |

## EU AI Act Risk Tiers

| Tier | Description | Examples |
|---|---|---|
| Unacceptable | Banned outright | Social scoring, real-time biometric surveillance |
| High Risk | Strict requirements (conformity assessment, logging, human oversight) | CV screening, credit scoring, medical devices, law enforcement |
| Limited Risk | Transparency obligations | Chatbots must disclose they are AI |
| Minimal Risk | No obligations | Spam filters, AI in video games |

## Privacy

| Technique | Description |
|---|---|
| Differential Privacy | Add calibrated noise to protect individual data points |
| Federated Learning | Train on decentralised data without centralising it |
| Data Anonymisation | Remove PII, k-anonymity, l-diversity |
| Secure Multi-Party Computation | Compute on encrypted data |

## References

- [ai-mlops.md](ai-mlops.md) — Model cards, monitoring, retraining
- [ai-ml-readme.md](ai-ml-readme.md) — Feature selection (SHAP)
- [ai-llm-readme.md](ai-llm-readme.md) — LLM training (RLHF, DPO)
- [EU AI Act](https://artificialintelligenceact.eu/)
- [NIST AI RMF](https://www.nist.gov/system/files/documents/2023/01/26/AI%20RMF%201.0.pdf)
- [SHAP Documentation](https://shap.readthedocs.io/)
- [Fairlearn (Microsoft)](https://fairlearn.org/)
- [AI Fairness 360 (IBM)](https://aif360.mybluemix.net/)
