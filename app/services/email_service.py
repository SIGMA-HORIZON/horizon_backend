from typing import List, Optional
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from pydantic import EmailStr
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

conf = ConnectionConfig(
    MAIL_USERNAME=settings.SMTP_USER,
    MAIL_PASSWORD=settings.SMTP_PASSWORD,
    MAIL_FROM=settings.EMAILS_FROM_EMAIL,
    MAIL_PORT=settings.SMTP_PORT,
    MAIL_SERVER=settings.SMTP_HOST,
    MAIL_STARTTLS=settings.SMTP_TLS,
    MAIL_SSL_TLS=not settings.SMTP_TLS,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)

class EmailService:
    async def _send(self, subject: str, recipients: List[str], html: str):
        message = MessageSchema(
            subject=f"[HORIZON] {subject}",
            recipients=recipients,
            body=html,
            subtype=MessageType.html
        )
        fm = FastMail(conf)
        try:
            await fm.send_message(message)
        except Exception as e:
            logger.error(f"Failed to send email to {recipients}: {str(e)}")

    async def send_new_account_request_email(self, admin_emails: List[str], request_data: dict, request_id: str):
        if not admin_emails: return
        html = f"""
        <h1>New Account Creation Request</h1>
        <p>Details:</p>
        <ul>
            <li><b>Email:</b> {request_data.get('email')}</li>
            <li><b>Name:</b> {request_data.get('first_name')} {request_data.get('last_name')}</li>
        </ul>
        <p><b>Request ID:</b> {request_id}</p>
        """
        await self._send("New Account Creation Request", admin_emails, html)

    async def send_account_approved_email(self, email: str, password: str):
        html = f"""
        <h1>Account Approved</h1>
        <p>Your account has been approved. You can now log in using the following credentials:</p>
        <p><b>Email:</b> {email}</p>
        <p><b>Provisional Password:</b> {password}</p>
        <p>You will be required to change your password upon your first login.</p>
        """
        await self._send("Account Approved", [email], html)

    async def send_account_rejected_email(self, email: str, reason: Optional[str]):
        html = f"""
        <h1>Account Request Rejected</h1>
        <p>Your account request has been rejected.</p>
        {f"<p><b>Reason:</b> {reason}</p>" if reason else ""}
        """
        await self._send("Account Request Rejected", [email], html)

    async def send_password_reset_email(self, email: str, password: str):
        html = f"""
        <h1>Password Reset</h1>
        <p>Your password has been reset. Your new provisional password is:</p>
        <p><b>Password:</b> {password}</p>
        <p>You will be required to change your password upon your next login.</p>
        """
        await self._send("Password Reset", [email], html)
