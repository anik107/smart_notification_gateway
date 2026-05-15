"""Notification service orchestrating business logic."""
from typing import Any

from app.core.exceptions import (
    ChannelDisabledException,
    ProviderException,
    UserNotFoundException
)
from app.core.interfaces import IUserPreferenceRepository, IProviderRegistry
from app.models.schemas import (
    Notification,
    NotificationRequest,
    NotificationResult,
)


class NotificationService:
    """Core service responsible for notification orchestration.

    Single Responsibility Principle: This service only orchestrates the flow:
    validate preferences -> select provider -> send. It does not format messages
    (providers do) nor does it access data directly (repositories do).

    Dependency Inversion Principle: Depends on IUserPreferenceRepository and
    IProviderRegistry abstractions, both injected via constructor.
    """

    def __init__(
        self,
        preference_repo: IUserPreferenceRepository,
        provider_registry: IProviderRegistry,
    ):
        self._preference_repo = preference_repo
        self._provider_registry = provider_registry

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
            request.user_id, request.channel
        )
        if not is_enabled:
            raise ChannelDisabledException(
                f"Channel '{request.channel}' is disabled for user {request.user_id}"
            )

        # 2. Resolve recipient address
        recipient_address = await self._preference_repo.get_contact_address(
            request.user_id, request.channel
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
        provider = self._provider_registry.get_provider(request.channel)
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

                notification_kwargs = {
                    "recipient_id": user_id,
                    "recipient_address": recipient_address,
                    "channel": channel_name,
                    "subject": subject,
                    "body": body,
                }
                if priority is not None:
                    notification_kwargs["priority"] = priority

                notification = Notification(**notification_kwargs)

                provider = self._provider_registry.get_provider(channel_name)
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
