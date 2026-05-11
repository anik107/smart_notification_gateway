"""Custom exceptions for the notification gateway."""


class NotificationException(Exception):
    """Base exception for notification-related errors."""
    pass


class ProviderException(NotificationException):
    """Raised when a notification provider fails to send a message."""

    def __init__(self, provider_name: str, message: str, original_error: Exception | None = None):
        self.provider_name = provider_name
        self.original_error = original_error
        super().__init__(f"[{provider_name}] {message}")


class UserNotFoundException(NotificationException):
    """Raised when a user preference lookup fails."""
    pass


class ChannelDisabledException(NotificationException):
    """Raised when a notification channel is disabled for a user."""
    pass
