# Model artifacts

Generated phishing and priority model binaries intentionally stay out of Git.

After the accepted M1 dataset is prepared:

python scripts/run_phishing_model.py
python scripts/run_priority_model.py

Expected runtime artifacts:
- models/phishing/phishing_pipeline.joblib
- models/priority/priority_pipeline.joblib

The API remains fail-closed when model artifacts are unavailable.
