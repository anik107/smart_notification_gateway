"""Notification service orchestrating business logic."""
from typing import Any

from app.core.exceptions import (
    ChannelDisabledException,
    ProviderException,
    UserNotFoundException
)
from app.core.interfaces import IUserPreferenceRepository
from app.models.schemas import (
    Notification,
    NotificationRequest,
    NotificationResult,
    ChannelType
)
from app.providers.base import provider_registry


class NotificationService:
    """Core service responsible for notification orchestration.

    Single Responsibility Principle: This service only orchestrates the flow:
    validate preferences -> select provider -> send. It does not format messages
    (providers do) nor does it access data directly (repositories do).

    Dependency Inversion Principle: Depends on IUserPreferenceRepository abstraction,
    injected via constructor.
    """

    def __init__(self, preference_repo: IUserPreferenceRepository):
        self._preference_repo = preference_repo

    async def send_notification(
        self,
        request: NotificationRequest
    ) -> list[NotificationResult]:
        """Process and send a notification request.

        Args:
            request: The incoming notification request.

        Returns:
            List of results (one per channel, or multiple if broadcasting).

        Raises:
            UserNotFoundException: If the user does not exist.
            ChannelDisabledException: If the requested channel is disabled.
            ProviderException: If the provider fails to send.
        """
        # 1. Validate user and channel preference
        is_enabled = await self._preference_repo.is_channel_enabled(
            request.user_id, request.channel.value
        )
        if not is_enabled:
            raise ChannelDisabledException(
                f"Channel '{request.channel.value}' is disabled for user {request.user_id}"
            )

        # 2. Resolve recipient address
        recipient_address = await self._preference_repo.get_contact_address(
            request.user_id, request.channel.value
        )

        # 3. Build notification domain object
        notification = Notification(
            recipient_id=request.user_id,
            recipient_address=recipient_address,
            channel=request.channel,
            subject=request.subject,
            body=request.body,
            priority=request.priority,
            attachments=request.attachments
        )

        # 4. Resolve provider and send
        provider = provider_registry.get_provider(request.channel.value)
        result = await provider.send(notification)

        return [result]

    async def send_to_all_enabled_channels(
        self,
        user_id: str,
        subject: str | None,
        body: str,
        priority: Any = None
    ) -> list[NotificationResult]:
        """Broadcast a message to all enabled channels for a user.

        Open/Closed Principle: This method iterates over the registry.
        Adding a new channel (e.g., Telegram) requires zero changes here.
        """
        results: list[NotificationResult] = []

        try:
            prefs = await self._preference_repo.get_preferences(user_id)
        except UserNotFoundException:
            raise

        enabled_channels = prefs.get("channels", {})

        for channel_name, is_enabled in enabled_channels.items():
            if not is_enabled:
                continue

            try:
                recipient_address = await self._preference_repo.get_contact_address(
                    user_id, channel_name
                )

                notification = Notification(
                    recipient_id=user_id,
                    recipient_address=recipient_address,
                    channel=ChannelType(channel_name),
                    subject=subject,
                    body=body,
                    priority=priority
                )

                provider = provider_registry.get_provider(channel_name)
                result = await provider.send(notification)
                results.append(result)
            except (ProviderException, ValueError) as exc:
                # Log but continue broadcasting to other channels
                results.append(NotificationResult(
                    success=False,
                    channel=channel_name,
                    provider="Unknown",
                    error_message=str(exc)
                ))

        return results
