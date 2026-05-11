"""Email notification provider implementation."""
import uuid
from datetime import datetime

from app.core.exceptions import ProviderException
from app.core.interfaces import NotificationProvider, IAttachmentCapable
from app.models.schemas import Notification, NotificationResult, ChannelType


class EmailProvider(NotificationProvider, IAttachmentCapable):
    """Mock email provider supporting attachments.

    Liskov Substitution Principle: Substitutable for NotificationProvider.
    Interface Segregation Principle: Implements IAttachmentCapable since
    email supports attachments, unlike SMS.
    """

    @property
    def channel_name(self) -> str:
        return ChannelType.EMAIL.value

    def __init__(self):
        self._attachments: list[dict] = []

    async def add_attachment(self, file_path: str, file_name: str, mime_type: str) -> None:
        """Stage an attachment for the next email send."""
        self._attachments.append({
            "file_path": file_path,
            "file_name": file_name,
            "mime_type": mime_type
        })

    async def send(self, notification: Notification) -> NotificationResult:
        """Mock sending an email via an external SMTP service."""
        try:
            # Simulate email-specific formatting
            formatted_body = self._format_email(notification)

            # Simulate attachment processing
            if notification.attachments:
                for att in notification.attachments:
                    await self.add_attachment(att.file_path, att.file_name, att.mime_type)

            # Mock external API call
            message_id = f"email_{uuid.uuid4().hex[:12]}"

            # Clear attachments after send
            self._attachments.clear()

            return NotificationResult(
                success=True,
                channel=self.channel_name,
                provider="EmailProvider",
                message_id=message_id,
                timestamp=datetime.utcnow()
            )
        except Exception as exc:
            raise ProviderException(
                provider_name=self.channel_name,
                message=f"Failed to send email to {notification.recipient_address}",
                original_error=exc
            )

    def _format_email(self, notification: Notification) -> str:
        """Email-specific formatting logic.

        Single Responsibility Principle: Formatting is separated from
        the generic sending orchestration.
        """
        subject = notification.subject or "No Subject"
        return f"Subject: {subject}\n\n{notification.body}"
