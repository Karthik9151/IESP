from __future__ import annotations

import logging

SENSITIVE_KEYS = {"password", "api_key", "access_token", "refresh_token", "authorization", "secret", "raw_body", "attachment"}


def sanitize_log_fields(fields: dict) -> dict:
    result = {}
    for key, value in fields.items():
        if key.lower() in SENSITIVE_KEYS:
            continue
        if isinstance(value, (str, bytes)) and len(value) > 512:
            result[key] = str(value)[:512] + "…"
        else:
            result[key] = value
    return result


def log_decision(logger: logging.Logger, *, request_id: str, message_id: str, decision: str, reason_codes: list[str], duration_ms: float) -> None:
    payload = sanitize_log_fields({
        "request_id": request_id, "message_id": message_id, "decision": decision,
        "reason_codes": reason_codes, "duration_ms": round(duration_ms, 2),
    })
    logger.info("analysis_completed %s", payload)
