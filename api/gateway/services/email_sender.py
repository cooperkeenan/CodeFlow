import asyncio
import logging
import smtplib
from email.message import EmailMessage
from typing import Protocol

logger = logging.getLogger(__name__)


class EmailSender(Protocol):
    async def send(self, to: str, subject: str, body: str) -> None: ...


class SmtpEmailSender:
    def __init__(
        self, host: str, port: int, username: str, password: str, sender: str
    ) -> None:
        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self._sender = sender

    async def send(self, to: str, subject: str, body: str) -> None:
        await asyncio.to_thread(self._send_blocking, to, subject, body)

    def _send_blocking(self, to: str, subject: str, body: str) -> None:
        message = EmailMessage()
        message["From"] = self._sender
        message["To"] = to
        message["Subject"] = subject
        message.set_content(body)
        with smtplib.SMTP(self._host, self._port, timeout=20) as server:
            server.starttls()
            if self._username:
                server.login(self._username, self._password)
            server.send_message(message)


class LoggingEmailSender:
    async def send(self, to: str, subject: str, body: str) -> None:
        logger.warning(
            "SMTP is not configured; email to %s was not sent.\nSubject: %s\n%s",
            to,
            subject,
            body,
        )
