import pandas as pd

from src.ml.data.pipeline import (
    ORIGINAL_COLUMNS,
    normalize_text,
    prepare_dataset,
    project_fingerprint,
    row_fingerprint,
    split_dataset,
    split_fingerprint,
    validate_split_integrity,
)


def make_row(label: int, body: str, subject: str = "Subject") -> dict:
    row = {column: None for column in ORIGINAL_COLUMNS}
    row.update(
        {
            "sender": "sender@example.com",
            "sender_domain": "example.com",
            "receiver": "receiver@example.com",
            "receiver_domain": "example.com",
            "date": "2026-01-01",
            "subject": subject,
            "content_types": "text/plain",
            "body": body,
            "urls": [],
            "url_count": 0,
            "url_length_max": 0,
            "url_length_avg": 0,
            "url_subdom_max": 0,
            "url_subdom_avg": 0,
            "attachment_count": 0,
            "has_attachments": False,
            "attachment_types": [],
            "language": "en",
            "source": "trec5",
            "label": label,
        }
    )
    return row


def test_record_fingerprint_matches_m1_colab_canonicalization():
    frame = pd.DataFrame([make_row(0, "benign")])
    row = frame.iloc[0]

    # This expected value is the deterministic SHA-256 of the accepted
    # Milestone 1 canonical JSON-object serialization for this fixture.
    assert row_fingerprint(row) == (
        "f07e1c736fa31b007a48624725c717a6c2d642801702a7da321848f298cf1a2e"
    )


def test_normalize_text_preserves_security_tokens():
    raw = "https://Example.com/a?x=1\r\n\r\n\t[URL]   urgent"
    assert normalize_text(raw) == "https://Example.com/a?x=1\n\n[URL] urgent"


def test_prepare_dataset_removes_only_missing_label_body_and_exact_duplicates():
    rows = [
        make_row(0, "benign"),
        make_row(1, "phishing"),
        make_row(0, "benign"),
        make_row(0, None),
        make_row(None, "no label"),
    ]
    frame = pd.DataFrame(rows)

    prepared, summary = prepare_dataset(frame)

    assert summary["raw_records"] == 5
    assert summary["usable_labeled_text_records"] == 3
    assert summary["exact_duplicate_copies"] == 1
    assert summary["final_unique_records"] == 2
    assert prepared["text_raw"].tolist() == ["benign", "phishing"]
    assert prepared["label"].tolist() == [0, 1]


def test_stratified_split_is_conserved_and_leakage_free():
    rows = [make_row(index % 2, f"body-{index}") for index in range(100)]
    frame, _ = prepare_dataset(pd.DataFrame(rows))

    train_a, validation_a, test_a = split_dataset(frame, random_state=42)
    train_b, validation_b, test_b = split_dataset(frame, random_state=42)

    validate_split_integrity(frame, train_a, validation_a, test_a)

    assert len(train_a) == 70
    assert len(validation_a) == 15
    assert len(test_a) == 15

    assert train_a["record_fingerprint"].tolist() == train_b["record_fingerprint"].tolist()
    assert validation_a["record_fingerprint"].tolist() == validation_b["record_fingerprint"].tolist()
    assert test_a["record_fingerprint"].tolist() == test_b["record_fingerprint"].tolist()

    train_c, validation_c, test_c = split_dataset(frame, random_state=12345)
    assert train_a["record_fingerprint"].tolist() != train_c["record_fingerprint"].tolist()
    assert validation_a["record_fingerprint"].tolist() != validation_c["record_fingerprint"].tolist()
    assert test_a["record_fingerprint"].tolist() != test_c["record_fingerprint"].tolist()


def test_fingerprints_are_deterministic():
    rows = [make_row(0, "a"), make_row(1, "b")]
    frame, _ = prepare_dataset(pd.DataFrame(rows))
    assert project_fingerprint(frame) == project_fingerprint(frame.copy())
    train, validation, test = split_dataset(frame, random_state=42)
    assert split_fingerprint(train) == split_fingerprint(train.copy())
    assert split_fingerprint(validation) == split_fingerprint(validation.copy())
    assert split_fingerprint(test) == split_fingerprint(test.copy())
