"""FastAPI dependency injection configuration.

Dependency Inversion Principle: All concrete dependencies are wired here
at the composition root. The rest of the application depends on abstractions.
"""
from fastapi import Depends

from app.core.interfaces import IUserPreferenceRepository, IProviderRegistry
from app.providers.base import provider_registry
from app.repositories.user_preference_repository import MockUserPreferenceRepository
from app.services.notification_service import NotificationService


# Singleton repository instance (in real app, use connection pooling)
_preference_repo_singleton: IUserPreferenceRepository | None = None


def get_user_preference_repository() -> IUserPreferenceRepository:
    """Factory for user preference repository.

    In production, this could return a PostgreSQL/MongoDB repository.
    """
    global _preference_repo_singleton
    if _preference_repo_singleton is None:
        _preference_repo_singleton = MockUserPreferenceRepository()
    return _preference_repo_singleton


def get_provider_registry() -> IProviderRegistry:
    """Factory for the provider registry.

    Returns the global registry instance typed as the abstraction so
    consumers never depend on the concrete ProviderRegistry class.
    """
    return provider_registry


def get_notification_service(
    repo: IUserPreferenceRepository = Depends(get_user_preference_repository),
    registry: IProviderRegistry = Depends(get_provider_registry),
) -> NotificationService:
    """Factory for NotificationService with all dependencies injected."""
    return NotificationService(
        preference_repo=repo,
        provider_registry=registry,
    )
