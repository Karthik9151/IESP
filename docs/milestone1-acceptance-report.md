# IESP — Milestone 1 Final Acceptance Audit

**Status:** COMPLETE  
**Audit environment:** Google Colab  
**Random state:** 42  
**Stratification:** label

## Acceptance checks

| Check | Result |
|---|---|
| Source verified | PASS |
| Schema verified | PASS |
| Missing values handled | PASS |
| Labels validated | PASS |
| Class distribution verified | PASS |
| Exact duplicates handled | PASS |
| Text normalization | PASS |
| Raw text preserved | PASS |
| Final dataset count verified | PASS |
| Dataset fingerprint | PASS |
| Train/validation/test split | PASS |
| Split stratification | PASS |
| Split leakage check | PASS |
| Reproducibility | PASS |
| Documentation information | PASS |

## Final dataset

| Metric | Value |
|---|---:|
| Raw records | 108,685 |
| Usable labeled-text records | 108,683 |
| Exact duplicate copies | 13 |
| Final unique records | 108,670 |
| Benign | 60,636 |
| Phishing | 48,034 |

## Split

| Split | Records |
|---|---:|
| Train | 76,069 |
| Validation | 16,300 |
| Test | 16,301 |

## Fingerprints

Project:

```text
34d78adcbf9a0b4033bf47a768eea0ce42b7e1536fdad523327c2a05c4fb4582
```

Train:

```text
ec36c169d5fc0aa576ee9a6d2bac3e7e3da69b169b801fe1696c4630b9db9593
```

Validation:

```text
fad1023e52f78f883e991febc4addbade88a60f2514b0aecdfe5b50684be6d46
```

Test:

```text
2035a79e167f8ad10612bcb4dd7c0bbf22d0b7c980de734b37ae1b4ad2643c46
```

## Preprocessing boundary

Structural cleaning/validation and exact deduplication occur before splitting. ML preprocessing such as TF-IDF must be fitted only on the training set and then used to transform validation/test.

TF-IDF fitted in Milestone 1: **False**

## Completion statement

Milestone 1 is complete at the dataset-validation level. Milestone 2 may begin only after the repository implementation is verified locally against the authoritative dataset and this acceptance record.
