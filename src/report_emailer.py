from __future__ import annotations

import os
import smtplib
from email.message import EmailMessage
from pathlib import Path
from typing import Iterable, Optional


def _truthy(value: str | None) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "y", "on"}


def send_email_with_attachments(
    *,
    subject: str,
    body_text: str,
    to_addrs: list[str],
    from_addr: str,
    attachments: Iterable[Path] = (),
) -> None:
    """Send an email via SMTP using env-based configuration.

    Required env:
      - SMTP_HOST
      - SMTP_PORT (default 587)
      - SMTP_USERNAME (optional)
      - SMTP_PASSWORD (optional)

    TLS:
      - SMTP_USE_TLS (default true for port 587)
      - SMTP_USE_SSL (default false)

    Notes:
      - If username/password are empty, attempts unauthenticated send.
    """

    smtp_host = os.getenv("SMTP_HOST", "").strip()
    if not smtp_host:
        raise RuntimeError("SMTP_HOST is not set")

    smtp_port_raw = os.getenv("SMTP_PORT", "587").strip()
    try:
        smtp_port = int(smtp_port_raw)
    except ValueError as e:
        raise RuntimeError(f"Invalid SMTP_PORT: {smtp_port_raw!r}") from e

    smtp_user = os.getenv("SMTP_USERNAME", "").strip()
    smtp_pass = os.getenv("SMTP_PASSWORD", "").strip()

    use_ssl = _truthy(os.getenv("SMTP_USE_SSL"))
    use_tls_env = os.getenv("SMTP_USE_TLS")
    use_tls = _truthy(use_tls_env) if use_tls_env is not None else (smtp_port == 587 and not use_ssl)

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = ", ".join(to_addrs)
    msg.set_content(body_text)

    for path in attachments:
        p = Path(path)
        if not p.exists() or not p.is_file():
            continue
        data = p.read_bytes()
        # These are simple reports; text/plain is good enough.
        msg.add_attachment(
            data,
            maintype="text",
            subtype="plain",
            filename=p.name,
        )

    if use_ssl:
        with smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=60) as server:
            if smtp_user and smtp_pass:
                server.login(smtp_user, smtp_pass)
            server.send_message(msg)
    else:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=60) as server:
            server.ehlo()
            if use_tls:
                server.starttls()
                server.ehlo()
            if smtp_user and smtp_pass:
                server.login(smtp_user, smtp_pass)
            server.send_message(msg)


def maybe_email_quality_report(*, run_id: str, markdown_path: Optional[str], json_path: Optional[str]) -> bool:
    """Email the quality report if configured.

    Controlled by env vars:
      - MMM_REPORT_EMAIL_TO (comma-separated)
      - MMM_REPORT_EMAIL_FROM
      - MMM_REPORT_EMAIL_ENABLED (optional; default true if TO is set)

    Returns True if email was attempted and sent, False if skipped.
    """

    to_raw = os.getenv("MMM_REPORT_EMAIL_TO", "").strip()
    enabled_raw = os.getenv("MMM_REPORT_EMAIL_ENABLED", "").strip()

    if not to_raw:
        return False
    if enabled_raw and not _truthy(enabled_raw):
        return False

    from_addr = os.getenv("MMM_REPORT_EMAIL_FROM", "").strip() or os.getenv("PODCAST_EMAIL", "").strip()
    if not from_addr:
        raise RuntimeError("MMM_REPORT_EMAIL_FROM (or PODCAST_EMAIL) must be set when MMM_REPORT_EMAIL_TO is set")

    to_addrs = [a.strip() for a in to_raw.split(",") if a.strip()]
    if not to_addrs:
        return False

    attachments: list[Path] = []
    if markdown_path:
        attachments.append(Path(markdown_path))
    if json_path:
        attachments.append(Path(json_path))

    subject = f"MMM kvalitetsrapport – körning {run_id}"
    body = (
        "Här kommer automatiskt genererad kvalitetsrapport för senaste MMM Senaste Nytt-körningen.\n"
        "\n"
        "(Om detta mejl kom oväntat: stäng av via MMM_REPORT_EMAIL_ENABLED=false.)\n"
    )

    send_email_with_attachments(
        subject=subject,
        body_text=body,
        to_addrs=to_addrs,
        from_addr=from_addr,
        attachments=attachments,
    )
    return True
