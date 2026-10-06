from __future__ import annotations

import mimetypes
import re

from src.domain.models import AttachmentMetadata, SecuritySignal, Severity

DANGEROUS_EXTENSIONS = {".exe",".dll",".scr",".com",".msi",".hta",".cpl",".jar",".js",".jse",".vbs",".vbe",".wsf",".wsh",".bat",".cmd",".ps1",".lnk",".reg",".docm",".xlsm",".pptm",".xlam",".xltm"}
_DOUBLE_EXT_RE = re.compile(r"\.(pdf|docx?|xlsx?|pptx?|txt|jpg|png|zip|html?)\.(exe|js|vbs|bat|cmd|scr|lnk|msi)$", re.I)


def _signal(code, severity, message, **evidence):
    return SecuritySignal(code, severity, "ATTACHMENT_POLICY", message, evidence)


def analyze_attachment(attachment: AttachmentMetadata, config: dict | None = None) -> list[SecuritySignal]:
    cfg = config or {}
    filename = (attachment.filename or "").strip()
    lower = filename.lower()
    suffixes = [part for part in lower.split(".") if part]
    ext = "." + suffixes[-1] if suffixes else ""
    signals = []
    if "/" in filename or "\\" in filename or ".." in lower or filename in {".", ".."}:
        signals.append(_signal("ATTACHMENT_PATH_TRAVERSAL", Severity.HIGH, "Attachment filename contains path-like traversal characters."))
    if ext in DANGEROUS_EXTENSIONS:
        signals.append(_signal("DANGEROUS_EXTENSION", Severity.HIGH, "Attachment extension is restricted by policy.", extension=ext))
    if _DOUBLE_EXT_RE.search(lower):
        signals.append(_signal("DOUBLE_EXTENSION", Severity.HIGH, "Attachment uses a suspicious double-extension naming pattern."))
    if attachment.size_bytes is not None and attachment.size_bytes > int(cfg.get("max_size_bytes", 10 * 1024 * 1024)):
        signals.append(_signal("ATTACHMENT_SIZE_LIMIT", Severity.HIGH, "Attachment exceeds the configured metadata size limit.", size_bytes=attachment.size_bytes))
    guessed, _ = mimetypes.guess_type(filename)
    if guessed and attachment.content_type and guessed.lower() != attachment.content_type.lower():
        signals.append(_signal("MIME_EXTENSION_MISMATCH", Severity.MEDIUM, "Filename extension and declared MIME type do not match.", extension_mime=guessed, declared_mime=attachment.content_type))
    return signals


def analyze_attachments(attachments: tuple[AttachmentMetadata, ...], config: dict | None = None) -> list[SecuritySignal]:
    cfg = config or {}
    max_count = int(cfg.get("max_count", 25))
    signals = []
    if len(attachments) > max_count:
        signals.append(_signal("EXCESSIVE_ATTACHMENT_COUNT", Severity.HIGH, "Attachment count exceeds policy limit.", count=len(attachments)))
        attachments = attachments[:max_count]
    for item in attachments:
        signals.extend(analyze_attachment(item, cfg))
    return signals
