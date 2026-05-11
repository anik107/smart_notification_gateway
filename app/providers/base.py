"""Base provider implementations and registries."""
from typing import Type

from app.core.interfaces import NotificationProvider


class ProviderRegistry:
    """Registry for notification providers.

    Open/Closed Principle: New providers are registered here at runtime
    without modifying the core sending engine.
    """

    def __init__(self):
        self._providers: dict[str, Type[NotificationProvider]] = {}

    def register(self, provider_class: Type[NotificationProvider]) -> None:
        """Register a provider class by its channel_name."""
        # Instantiate temporarily to get channel name
        # In production, use a factory pattern or classmethod
        self._providers[provider_class.__name__.lower().replace("provider", "")] = provider_class

    def get_provider(self, channel: str) -> NotificationProvider:
        """Instantiate and return a provider for the given channel."""
        provider_class = self._providers.get(channel)
        if not provider_class:
            raise ValueError(f"No provider registered for channel: {channel}")
        return provider_class()

    def list_channels(self) -> list[str]:
        """Return all registered channel names."""
        return list(self._providers.keys())


# Global registry instance
provider_registry = ProviderRegistry()
