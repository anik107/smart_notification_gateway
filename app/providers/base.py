"""Base provider implementations and registries."""
from typing import Type

from app.core.interfaces import IProviderRegistry, NotificationProvider


class ProviderRegistry(IProviderRegistry):
    """Registry for notification providers.

    Open/Closed Principle: New providers self-register via the @auto_register
    decorator — no modification to this class or any central list is needed.

    Dependency Inversion Principle: Implements the IProviderRegistry abstraction
    so that high-level services never depend on this concrete class directly.
    """

    def __init__(self):
        self._providers: dict[str, Type[NotificationProvider]] = {}

    def register(self, provider_class: Type[NotificationProvider]) -> None:
        """Register a provider class by its canonical channel_name property."""
        instance = provider_class()
        self._providers[instance.channel_name] = provider_class

    def get_provider(self, channel: str) -> NotificationProvider:
        """Instantiate and return a provider for the given channel."""
        provider_class = self._providers.get(channel)
        if not provider_class:
            raise ValueError(f"No provider registered for channel: {channel}")
        return provider_class()

    def list_channels(self) -> list[str]:
        """Return all registered channel names."""
        return list(self._providers.keys())

    def auto_register(
        self, provider_class: Type[NotificationProvider]
    ) -> Type[NotificationProvider]:
        """Class decorator that auto-registers a provider on definition.

        Usage::

            @provider_registry.auto_register
            class TelegramProvider(NotificationProvider):
                ...
        """
        self.register(provider_class)
        return provider_class


# Global registry instance (composition-root level singleton)
provider_registry = ProviderRegistry()
