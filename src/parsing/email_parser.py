from __future__ import annotations

import re
from email import policy
from email.header import decode_header
from email.parser import BytesParser
from email.utils import getaddresses, parseaddr

from src.domain.models import AttachmentMetadata, EmailMessage, HeaderData, Sender, UrlMetadata

_URL_RE = re.compile(r"https?://[^\s<>\"']+", re.IGNORECASE)
_HEADER_NAME_RE = re.compile(r"^[!#$%&'*+.^_`|~0-9A-Za-z-]+$")


class EmailParseError(ValueError):
    pass


def decode_header_value(value: str | None, max_length: int = 8192) -> str:
    if not value:
        return ""
    parts = []
    for part, encoding in decode_header(value):
        if isinstance(part, bytes):
            try:
                parts.append(part.decode(encoding or "utf-8", errors="replace"))
            except LookupError:
                parts.append(part.decode("utf-8", errors="replace"))
        else:
            parts.append(part)
    return "".join(parts)[:max_length]


def _normalize_address(value: str) -> tuple[str, str]:
    _, address = parseaddr(value)
    address = address.strip()
    if not address or "\r" in address or "\n" in address or "@" not in address:
        raise EmailParseError("Invalid sender address")
    local, domain = address.rsplit("@", 1)
    if not local or not domain:
        raise EmailParseError("Invalid sender address")
    return address, domain.lower().rstrip(".")


def _extract_urls(text: str) -> tuple[UrlMetadata, ...]:
    from urllib.parse import urlsplit
    seen, result = set(), []
    for raw in _URL_RE.findall(text or ""):
        url = raw.rstrip(".,;:!?)]}")
        if url in seen:
            continue
        seen.add(url)
        try:
            split = urlsplit(url)
            try:
                port = split.port
            except ValueError:
                port = None
            result.append(
                UrlMetadata(
                    url=url,
                    scheme=split.scheme.lower() or None,
                    hostname=split.hostname.lower() if split.hostname else None,
                    port=port,
                    userinfo_present=bool(split.username or split.password),
                )
            )
        except ValueError:
            result.append(UrlMetadata(url=url))
    return tuple(result)


def _part_body(part, max_chars: int = 500_000) -> str:
    try:
        return str(part.get_content())[:max_chars]
    except Exception as exc:
        raise EmailParseError("Body decoding failed") from exc


def parse_email_bytes(raw_message: bytes, *, max_bytes: int = 2_000_000) -> EmailMessage:
    if not isinstance(raw_message, (bytes, bytearray)):
        raise EmailParseError("Raw email must be bytes")
    if len(raw_message) > max_bytes:
        raise EmailParseError("Raw email exceeds size limit")
    try:
        message = BytesParser(policy=policy.default).parsebytes(bytes(raw_message))
    except Exception as exc:
        raise EmailParseError("MIME parsing failed") from exc
    if message.defects:
        raise EmailParseError("MIME parser reported malformed input")

    values = {}
    for name, value in message.items():
        if not _HEADER_NAME_RE.fullmatch(name):
            raise EmailParseError("Invalid header name")
        values[name.lower()] = decode_header_value(value)

    sender_address, sender_domain = _normalize_address(values.get("from", ""))
    sender_name = decode_header_value(parseaddr(values.get("from", ""))[0], 256)
    recipients = tuple(addr.strip() for _, addr in getaddresses([values.get("to", ""), values.get("cc", "")]) if addr.strip())
    if not recipients:
        raise EmailParseError("No valid recipients found")

    message_id = values.get("message-id", "").strip("<>")[:512] or "generated-local-id"
    text_body, html_body, attachments = "", "", []

    parts = message.walk() if message.is_multipart() else [message]
    for part in parts:
        if part.is_multipart():
            continue
        filename = decode_header_value(part.get_filename(), 512)
        disposition = part.get_content_disposition()
        if filename or disposition == "attachment":
            raw_payload = part.get_payload(decode=False)
            size = len(raw_payload) if isinstance(raw_payload, (bytes, str)) else None
            attachments.append(AttachmentMetadata(
                filename=filename or "unnamed",
                content_type=part.get_content_type(),
                size_bytes=size,
                disposition=disposition,
            ))
            continue
        if part.get_content_type() == "text/plain" and not text_body:
            text_body = _part_body(part)
        elif part.get_content_type() == "text/html" and not html_body:
            html_body = _part_body(part)

    return EmailMessage(
        message_id=message_id,
        sender=Sender(address=sender_address, display_name=sender_name, domain=sender_domain),
        recipients=recipients,
        subject=decode_header_value(values.get("subject", ""), 1000),
        text_body=text_body,
        html_body=html_body,
        headers=HeaderData(values=values),
        attachments=tuple(attachments),
        urls=_extract_urls(f"{text_body}\n{html_body}"),
    )


def parse_email_text(raw_message: str, *, max_chars: int = 2_000_000) -> EmailMessage:
    if not isinstance(raw_message, str):
        raise EmailParseError("Raw email must be text")
    if len(raw_message) > max_chars:
        raise EmailParseError("Raw email exceeds size limit")
    return parse_email_bytes(raw_message.encode("utf-8"), max_bytes=max_chars * 2)
