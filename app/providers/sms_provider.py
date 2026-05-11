"""SMS notification provider implementation."""
import uuid
from datetime import datetime

from app.core.exceptions import ProviderException
from app.core.interfaces import NotificationProvider
from app.models.schemas import Notification, NotificationResult, ChannelType


class SMSProvider(NotificationProvider):
    """Mock SMS provider.

    Interface Segregation Principle: SMSProvider does NOT implement
    IAttachmentCapable because SMS does not support attachments.
    """

    @property
    def channel_name(self) -> str:
        return ChannelType.SMS.value

    async def send(self, notification: Notification) -> NotificationResult:
        """Mock sending an SMS via an external gateway."""
        try:
            # SMS-specific formatting: truncate long bodies
            formatted_body = self._format_sms(notification)

            # Mock external API call
            message_id = f"sms_{uuid.uuid4().hex[:12]}"

            return NotificationResult(
                success=True,
                channel=self.channel_name,
                provider="SMSProvider",
                message_id=message_id,
                timestamp=datetime.utcnow()
            )
        except Exception as exc:
            raise ProviderException(
                provider_name=self.channel_name,
                message=f"Failed to send SMS to {notification.recipient_address}",
                original_error=exc
            )

    def _format_sms(self, notification: Notification) -> str:
        """SMS-specific formatting: enforce character limits."""
        max_length = 1600  # Modern SMS segment limit
        body = notification.body
        if len(body) > max_length:
            body = body[:max_length - 3] + "..."
        return body
