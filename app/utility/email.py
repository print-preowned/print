import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from urllib.parse import quote

import certifi

from app.utility.config import get_settings


class EmailDeliveryError(Exception):
    """Raised when an outbound email could not be delivered."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


def _smtp_ssl_context() -> ssl.SSLContext:
    """Use certifi CA bundle — default context often fails on macOS Python installs."""
    settings = get_settings()
    if not settings.smtp_ssl_verify:
        if settings.app_env != "development":
            raise EmailDeliveryError(
                "SMTP_SSL_VERIFY=false is only allowed when APP_ENV=development"
            )
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        return ctx
    return ssl.create_default_context(cafile=certifi.where())


def send_email(*, to: str, subject: str, html_body: str, text_body: str) -> None:
    settings = get_settings()

    if settings.app_env == "development" and not settings.smtp_host:
        print(
            f"\n=== EMAIL (dev — configure SMTP_* to send for real) ===\n"
            f"To: {to}\n"
            f"Subject: {subject}\n\n"
            f"{text_body}\n"
            f"=======================================================\n"
        )
        return

    if not settings.smtp_host:
        raise EmailDeliveryError(
            "SMTP is not configured. Set SMTP_HOST or use APP_ENV=development without SMTP_HOST."
        )

    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = settings.smtp_from
    message["To"] = to
    message.attach(MIMEText(text_body, "plain"))
    message.attach(MIMEText(html_body, "html"))

    try:
        context = _smtp_ssl_context()
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as server:
            if settings.smtp_use_tls:
                server.starttls(context=context)
            if settings.smtp_user and settings.smtp_password:
                server.login(settings.smtp_user, settings.smtp_password)
            server.sendmail(settings.smtp_from, [to], message.as_string())
    except TimeoutError as exc:
        raise EmailDeliveryError(
            "Could not reach the mail server (timed out). Check SMTP_HOST and SMTP_PORT."
        ) from exc
    except ssl.SSLError as exc:
        raise EmailDeliveryError(
            "TLS/SSL error connecting to the mail server. Check SMTP_USE_TLS and SMTP_SSL_VERIFY."
        ) from exc
    except smtplib.SMTPAuthenticationError as exc:
        raise EmailDeliveryError(
            "Mail server rejected the SMTP credentials. Check SMTP_USER and SMTP_PASSWORD."
        ) from exc
    except smtplib.SMTPException as exc:
        raise EmailDeliveryError(f"Mail server rejected the message: {exc}") from exc
    except OSError as exc:
        raise EmailDeliveryError(
            f"Could not connect to the mail server ({settings.smtp_host}:{settings.smtp_port})."
        ) from exc


def send_platform_invite_email(*, to: str, raw_token: str, expires_at_iso: str) -> None:
    settings = get_settings()
    encoded_token = quote(raw_token, safe="")
    accept_url = f"{settings.web_app_url}/admin/invite/accept?token={encoded_token}"
    reject_url = f"{settings.web_app_url}/admin/invite/reject?token={encoded_token}"

    subject = "You're invited to PRINT Platform Admin"
    text_body = (
        "You have been invited to join the PRINT platform administration team.\n\n"
        f"Accept invitation: {accept_url}\n"
        f"Decline invitation: {reject_url}\n\n"
        f"This invitation expires on {expires_at_iso}.\n"
    )
    html_body = (
        "<p>You have been invited to join the PRINT platform administration team.</p>"
        f'<p><a href="{accept_url}">Accept invitation</a></p>'
        f'<p><a href="{reject_url}">Decline invitation</a></p>'
        f"<p>This invitation expires on {expires_at_iso}.</p>"
    )

    send_email(to=to, subject=subject, html_body=html_body, text_body=text_body)
