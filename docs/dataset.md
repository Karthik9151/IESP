# IESP Dataset — Milestone 1

## Authoritative source

IESP uses the **MeAJOR — Merged email Assets from Joint Open-source Repositories** dataset.

Source record:

- Zenodo record: `18471483`
- DOI: `10.5281/zenodo.18471483`
- File: `meajor_cleaned_preprocessed.parquet.gzip`
- Official source: https://zenodo.org/records/18471483
- Dataset records reported by Zenodo: 108,685
- Official label mapping: `0 = benign`, `1 = phishing`

The Zenodo record describes MeAJOR as a preprocessed email dataset with engineered features and anonymized email content. The project does **not** commit the source dataset to GitHub.

## Why the dataset is not stored in GitHub

The source Parquet file is approximately 86 MB. The repository also excludes `data/raw/*` and `data/processed/*` from version control.

Use the authoritative Zenodo download in Colab or another controlled environment, then point the repository pipeline at the local file.

Example:

```bash
python scripts/run_dataset_pipeline.py \
  --input /path/to/meajor_cleaned_preprocessed.parquet.gzip
```

## Original schema

Milestone 1 preserves the complete authoritative 20-column schema:

```text
sender
sender_domain
receiver
receiver_domain
date
subject
content_types
body
urls
url_count
url_length_max
url_length_avg
url_subdom_max
url_subdom_avg
attachment_count
has_attachments
attachment_types
language
source
label
```

No original source column is silently discarded.

## Structural preparation

The repository pipeline performs only dataset-level preparation:

1. Validate the authoritative 20-column schema.
2. Remove rows missing either `label` or `body`.
3. Validate labels against `{0, 1}`.
4. Create a deterministic full-record fingerprint using all original source columns.
5. Remove exact duplicate full records, keeping the first occurrence.
6. Preserve the original body in `text_raw`.
7. Create conservative `text_normalized` text.

Normalization is deliberately conservative. It normalizes Unicode, line endings, tabs and whitespace while preserving URLs, domains, numbers, punctuation, special characters, placeholders, and suspicious terms.

The body and subject are **not** used as standalone deduplication keys. Repeated bodies or subjects may be legitimate dataset characteristics.

## Verified Milestone 1 acceptance results

These values were independently measured in the Milestone 1 Colab audit:

| Metric | Verified result |
|---|---:|
| Raw records | 108,685 |
| Usable labeled-text records | 108,683 |
| Exact duplicate copies | 13 |
| Final unique records | 108,670 |
| Benign | 60,636 |
| Phishing | 48,034 |
| Train | 76,069 |
| Validation | 16,300 |
| Test | 16,301 |
| Random state | 42 |
| Stratification | label |

Class distribution in the final unique dataset:

- Benign: 55.7983%
- Phishing: 44.2017%

No class balancing, oversampling, or undersampling was applied.

## Verified project fingerprint

The accepted Milestone 1 dataset fingerprint is:

```text
34d78adcbf9a0b4033bf47a768eea0ce42b7e1536fdad523327c2a05c4fb4582
```

This is the **IESP project fingerprint**, not an official Zenodo checksum. It was defined as SHA-256 over the sorted final `record_fingerprint` values, joined with newline separators and encoded as UTF-8.

The accepted split fingerprints are:

| Split | SHA-256 |
|---|---|
| Train | `ec36c169d5fc0aa576ee9a6d2bac3e7e3da69b169b801fe1696c4630b9db9593` |
| Validation | `fad1023e52f78f883e991febc4addbade88a60f2514b0aecdfe5b50684be6d46` |
| Test | `2035a79e167f8ad10612bcb4dd7c0bbf22d0b7c980de734b37ae1b4ad2643c46` |

The repository implementation uses a documented deterministic per-record fingerprint serializer in `src/ml/data/pipeline.py`. The accepted fingerprints above remain the audit reference. An exact fingerprint match should only be claimed after verifying the repository serializer against the accepted Colab artifact.

## Leakage checks completed in Milestone 1

Exact record fingerprints had zero overlap between:

- train and validation;
- train and test;
- validation and test.

Every final record appeared in exactly one split.

Additional advisory screening found repeated normalized bodies and subjects across splits. These are not treated as exact-record leakage because deduplication was intentionally performed on complete original records only.

## Preprocessing boundary

The order is:

```text
Structural validation
        ↓
Missing label/body handling
        ↓
Exact full-record deduplication
        ↓
text_raw + text_normalized
        ↓
Train / validation / test split
        ↓
Fit ML preprocessing on TRAIN only
        ↓
Transform validation/test with the fitted training preprocessing
```

**TF-IDF was not fitted in Milestone 1.**

TF-IDF fitting belongs to Milestone 2 and must use the training split only.

## Reproducibility contract

The split implementation uses:

```text
train = 70%
validation = 15%
test = 15%
random_state = 42
stratify = label
```

Using the same seed must reproduce the same split. A different seed must produce a different split while preserving stratification.

## Dataset handling rule

Do not add the 86 MB source dataset, generated processed Parquet files, or model artifacts to GitHub. Keep them in controlled local/Colab storage and version the code, configuration, manifests, and audit documentation instead.
