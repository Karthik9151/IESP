from __future__ import annotations

import ipaddress
import re
from urllib.parse import urlsplit

from src.domain.models import SecuritySignal, Severity, UrlMetadata

_SHORTENERS = {"bit.ly", "tinyurl.com", "t.co", "goo.gl", "ow.ly", "is.gd", "buff.ly", "rebrand.ly"}
_PCT_RE = re.compile(r"%[0-9A-Fa-f]{2}")


def _signal(code: str, severity: Severity, message: str, **evidence) -> SecuritySignal:
    return SecuritySignal(code, severity, "URL_ANOMALY", message, evidence)


def analyze_url(url: str | UrlMetadata, config: dict | None = None) -> list[SecuritySignal]:
    cfg = config or {}
    raw = url.url if isinstance(url, UrlMetadata) else str(url)
    try:
        parsed = urlsplit(raw)
    except ValueError:
        return [_signal("MALFORMED_URL", Severity.HIGH, "URL cannot be parsed structurally.")]
    signals = []
    scheme = (parsed.scheme or "").lower()
    if scheme not in {"http", "https"}:
        signals.append(_signal("UNSAFE_URL_SCHEME", Severity.HIGH, "URL uses a non-web scheme.", scheme=scheme))
    if not parsed.hostname:
        signals.append(_signal("MALFORMED_URL", Severity.HIGH, "URL does not contain a hostname."))
        return signals

    hostname = parsed.hostname.lower().rstrip(".")
    if parsed.username is not None or parsed.password is not None:
        signals.append(_signal("URL_USERINFO", Severity.MEDIUM, "URL contains userinfo before the hostname."))
    try:
        port = parsed.port
    except ValueError:
        signals.append(_signal("MALFORMED_URL_PORT", Severity.HIGH, "URL contains an invalid port."))
        port = None
    if port is not None and port not in {80, 443}:
        signals.append(_signal("NONSTANDARD_URL_PORT", Severity.LOW, "URL uses a non-standard web port.", port=port))

    try:
        ip = ipaddress.ip_address(hostname)
    except ValueError:
        ip = None
    if ip is not None:
        if not ip.is_global:
            signals.append(_signal("SSRF_SENSITIVE_DESTINATION", Severity.CRITICAL, "URL uses a non-public IP-literal destination.", host=hostname))
        signals.append(_signal("IP_LITERAL_HOST", Severity.MEDIUM, "URL uses an IP-literal host.", host=hostname))
    else:
        labels = hostname.split(".")
        if len(labels) - 2 > int(cfg.get("max_subdomains", 4)):
            signals.append(_signal("EXCESSIVE_SUBDOMAINS", Severity.LOW, "Hostname contains an unusually deep subdomain chain.", subdomains=max(0, len(labels) - 2)))
        if hostname.startswith("xn--") or ".xn--" in hostname:
            signals.append(_signal("PUNYCODE_HOST", Severity.MEDIUM, "Hostname contains a punycode label."))
        if hostname in _SHORTENERS:
            signals.append(_signal("SHORTENED_URL", Severity.MEDIUM, "Hostname matches a common URL shortener.", host=hostname))
        if hostname == "localhost" or hostname.endswith(".localhost") or hostname.endswith(".local"):
            signals.append(_signal("SSRF_SENSITIVE_DESTINATION", Severity.CRITICAL, "Hostname targets a local name.", host=hostname))

    if _PCT_RE.search(parsed.netloc) or _PCT_RE.search(parsed.path):
        signals.append(_signal("SUSPICIOUS_URL_ENCODING", Severity.LOW, "URL contains percent-encoded characters requiring review."))
    if len(raw) > int(cfg.get("max_length", 2048)):
        signals.append(_signal("EXCESSIVE_URL_LENGTH", Severity.LOW, "URL exceeds the configured length limit.", length=len(raw)))
    return signals


def analyze_urls(urls: tuple[UrlMetadata, ...], config: dict | None = None) -> list[SecuritySignal]:
    cfg = config or {}
    max_count = int(cfg.get("max_count", 50))
    if len(urls) > max_count:
        extra = [_signal("EXCESSIVE_URL_COUNT", Severity.HIGH, "Message contains more URLs than the configured limit.", count=len(urls))]
        urls = urls[:max_count]
    else:
        extra = []
    signals = extra
    for item in urls:
        signals.extend(analyze_url(item, cfg))
    return signals
