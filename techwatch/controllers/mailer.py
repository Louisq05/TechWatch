"""Send an e-mail over SMTP, using credentials from the environment/.env."""
import smtplib
from email.message import EmailMessage

from .. import config


def _settings():
    user = config.get("TECHWATCH_SMTP_USER")
    password = config.get("TECHWATCH_SMTP_PASSWORD")
    if not user or not password:
        raise RuntimeError(
            "SMTP non configuré : renseigne TECHWATCH_SMTP_USER et "
            "TECHWATCH_SMTP_PASSWORD dans le fichier .env (voir .env.example)."
        )
    return {
        "host": config.get("TECHWATCH_SMTP_HOST", "smtp.gmail.com"),
        "port": int(config.get("TECHWATCH_SMTP_PORT", "587")),
        "user": user,
        "password": password,
        "sender": config.get("TECHWATCH_MAIL_FROM", user),
        "to": config.get("TECHWATCH_MAIL_TO", user),
    }


def send(subject, text_body, html_body):
    """Send one multipart (text + HTML) message. Return the recipient."""
    s = _settings()
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = s["sender"]
    msg["To"] = s["to"]
    msg.set_content(text_body)
    msg.add_alternative(html_body, subtype="html")
    with smtplib.SMTP(s["host"], s["port"]) as server:
        server.starttls()
        server.login(s["user"], s["password"])
        server.send_message(msg)
    return s["to"]
