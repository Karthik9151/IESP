# IESP ML Methodology

## M1 data contract

Accepted project fingerprint: `34d78adcbf9a0b4033bf47a768eea0ce42b7e1536fdad523327c2a05c4fb4582`. Split sizes: train 76,069; validation 16,300; test 16,301. Structural preparation occurs before splitting.

## Phishing model

TF-IDF word analyzer with unigrams/bigrams, lowercase, accent stripping and sublinear TF feeds LinearSVC. Fitting occurs only on train data through an sklearn Pipeline. Evaluation code reports accuracy, precision, recall, F1, ROC-AUC, PR-AUC and confusion-matrix counts. `decision_function` is a ranking margin, not a probability.

## Priority model

VADER sentiment plus engineered message/urgency/deadline/action/time features feeds Logistic Regression. P1/P2/P3 are deterministic proxy/project labels and must not be presented as human annotations.

## Reproducibility

YAML configuration and training scripts are versioned; generated binaries remain outside Git. Real-data performance must be regenerated from the accepted dataset contract.
