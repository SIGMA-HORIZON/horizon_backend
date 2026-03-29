from typing import List
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
    async def send_new_account_request_email(
        self, 
        admin_emails: List[str], 
        request_data: dict,
        request_id: str
    ):
        """
        Send notification email to admins about a new account request.
        """
        if not admin_emails:
            logger.warning("No admin emails found to send registration request.")
            return

        html = f"""
        <html>
            <body>
                <h1>New Account Creation Request</h1>
                <p>A new account request has been submitted with the following details:</p>
                <ul>
                    <li><b>First Name:</b> {request_data.get('first_name')}</li>
                    <li><b>Last Name:</b> {request_data.get('last_name')}</li>
                    <li><b>Email:</b> {request_data.get('email')}</li>
                    <li><b>Organisation:</b> {request_data.get('organisation') or 'N/A'}</li>
                    <li><b>Justification:</b> {request_data.get('justification') or 'No justification provided.'}</li>
                </ul>
                <p><b>Request ID:</b> {request_id}</p>
                <p>Please log in to the admin panel to review and approve this request.</p>
            </body>
        </html>
        """

        message = MessageSchema(
            subject="[HORIZON] New Account Creation Request",
            recipients=admin_emails,
            body=html,
            subtype=MessageType.html
        )

        fm = FastMail(conf)
        try:
            await fm.send_message(message)
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            # Silent failure as per requirements
