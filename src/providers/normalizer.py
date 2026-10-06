from __future__ import annotations

from datetime import datetime

from src.domain.models import AttachmentMetadata, EmailMessage, HeaderData, Sender


def normalize_generic_message(*, message_id: str, sender_address: str, sender_name: str = "", recipients: tuple[str, ...] | list[str], subject: str = "", text_body: str = "", html_body: str = "", headers: dict[str, str] | None = None, attachments: tuple[AttachmentMetadata, ...] | list[AttachmentMetadata] = (), received_at: datetime | None = None, urls=()) -> EmailMessage:
    domain = sender_address.rsplit("@", 1)[1].lower().rstrip(".") if "@" in sender_address else ""
    if not domain:
        raise ValueError("Provider message has no valid sender domain")
    return EmailMessage(
        message_id=message_id,
        sender=Sender(sender_address, sender_name, domain),
        recipients=tuple(recipients),
        subject=subject,
        text_body=text_body,
        html_body=html_body,
        headers=HeaderData({str(k).lower(): str(v) for k, v in (headers or {}).items()}),
        attachments=tuple(attachments),
        urls=tuple(urls),
        received_at=received_at,
    )
