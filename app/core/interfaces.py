"""Core abstractions and interfaces following the Interface Segregation Principle."""
from abc import ABC, abstractmethod
from typing import Any, Type

from app.models.schemas import Notification, NotificationResult


class NotificationProvider(ABC):
    """Abstract base class for all notification delivery methods.

    Liskov Substitution Principle: All concrete providers must be substitutable
    for this base class without altering the correctness of the program.
    """

    @property
    @abstractmethod
    def channel_name(self) -> str:
        """Return the unique channel identifier."""
        ...

    @abstractmethod
    async def send(self, notification: Notification) -> NotificationResult:
        """Send a notification and return the result.

        Args:
            notification: The notification payload to deliver.

        Returns:
            NotificationResult containing success status and metadata.

        Raises:
            ProviderException: If the provider fails to send the notification.
        """
        ...


class IAttachmentCapable(ABC):
    """Interface for providers that support file attachments.

    Interface Segregation Principle: Only email providers implement this.
    SMS providers are not forced to implement attachment methods.
    """

    @abstractmethod
    async def add_attachment(self, file_path: str, file_name: str, mime_type: str) -> None:
        """Attach a file to the notification context."""
        ...


class IUserPreferenceRepository(ABC):
    """Repository abstraction for user notification preferences.

    Dependency Inversion Principle: The service layer depends on this abstraction,
    not on concrete repository implementations.
    """

    @abstractmethod
    async def get_preferences(self, user_id: str) -> dict[str, Any]:
        """Retrieve notification preferences for a given user."""
        ...

    @abstractmethod
    async def is_channel_enabled(self, user_id: str, channel: str) -> bool:
        """Check if a specific notification channel is enabled for the user."""
        ...

    @abstractmethod
    async def get_contact_address(self, user_id: str, channel: str) -> str:
        """Get the appropriate contact address for a given channel."""
        ...


class IProviderRegistry(ABC):
    """Abstraction for the provider registry.

    Dependency Inversion Principle: High-level services depend on this
    abstraction rather than a concrete global singleton.
    """

    @abstractmethod
    def register(self, provider_class: Type["NotificationProvider"]) -> None:
        """Register a provider class."""
        ...

    @abstractmethod
    def get_provider(self, channel: str) -> "NotificationProvider":
        """Return a provider instance for the given channel."""
        ...

    @abstractmethod
    def list_channels(self) -> list[str]:
        """Return all registered channel names."""
        ...
