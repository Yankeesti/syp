from email.message import EmailMessage
from typing import Optional
import logging
import aiosmtplib
from .config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class MailService:
    def __init__(
        self,
        host: str = settings.SMTP_HOST,
        port: int = settings.SMTP_PORT,
        username: Optional[str] = settings.SMTP_USER,
        password: Optional[str] = settings.SMTP_PASSWORD,
        use_tls: bool = settings.SMTP_USE_TLS,
        sender: str = settings.SMTP_FROM,
    ):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.use_tls = use_tls
        self.sender = sender

    async def send(self, to: str, subject: str, html: str, text: Optional[str] = None):
        """
        Send email via SMTP.

        Args:
            to: Recipient email address
            subject: Email subject
            html: HTML email content
            text: Optional plain text email content

        Raises:
            Exception: If email sending fails
        """
        if not self.username or not self.password:
            raise ValueError("SMTP_USER and SMTP_PASSWORD must be configured")

        msg = EmailMessage()
        msg["From"] = self.sender
        msg["To"] = to
        msg["Subject"] = subject
        if text:
            msg.set_content(text)
            msg.add_alternative(html, subtype="html")
        else:
            msg.set_content(html, subtype="html")

        await aiosmtplib.send(
            msg,
            hostname=self.host,
            port=self.port,
            username=self.username,
            password=self.password,
            start_tls=self.use_tls,
        )

    def build_magic_link_email(self, email: str, magiclink: str):
        """
        Returns (subject, html_body, text_body)
        """
        subject = "Ihr Login-Link"
        text = (
            "Sehr geehrter KI-Tutor Nutzer,"
            f"Nutzen Sie folgenden Link, um sich anzumelden:\n{magiclink}\n\n"
            "Wenn Sie diese Anfrage nicht gestellt haben, ignorieren Sie diese E-Mail."
        )
        html = (
            "<html><body>"
            "<p>Sehr geehrter KI-Tutor Nutzer,</p>"
            "<p>Nutzen Sie folgenden Link, um sich anzumelden:</p>"
            f'<p><a href="{magiclink}">Hier klicken, um einzuloggen</a></p>'
            "<p>Wenn Sie diese Anfrage nicht gestellt haben, ignorieren Sie diese E-Mail.</p>"
            "</body></html>"
        )
        return subject, html, text
