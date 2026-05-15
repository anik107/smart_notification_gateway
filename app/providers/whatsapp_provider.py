"""WhatsApp notification provider implementation."""
import uuid
from datetime import datetime

from app.core.exceptions import ProviderException
from app.core.interfaces import NotificationProvider
from app.models.schemas import Notification, NotificationResult
from app.providers.base import provider_registry


@provider_registry.auto_register
class WhatsAppProvider(NotificationProvider):
    """Mock WhatsApp Business API provider."""

    @property
    def channel_name(self) -> str:
        return "whatsapp"

    async def send(self, notification: Notification) -> NotificationResult:
        """Mock sending a WhatsApp message."""
        try:
            message_id = f"wa_{uuid.uuid4().hex[:12]}"

            return NotificationResult(
                success=True,
                channel=self.channel_name,
                provider="WhatsAppProvider",
                message_id=message_id,
                timestamp=datetime.utcnow()
            )
        except Exception as exc:
            raise ProviderException(
                provider_name=self.channel_name,
                message=f"Failed to send WhatsApp message to {notification.recipient_address}",
                original_error=exc
            )
