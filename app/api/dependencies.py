"""FastAPI dependency injection configuration.

Dependency Inversion Principle: All concrete dependencies are wired here.
The rest of the application depends on abstractions (interfaces).
"""
from fastapi import Request

from app.core.interfaces import IUserPreferenceRepository
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


def get_notification_service(
    repo: IUserPreferenceRepository = get_user_preference_repository()
) -> NotificationService:
    """Factory for NotificationService with injected repository."""
    return NotificationService(preference_repo=repo)
