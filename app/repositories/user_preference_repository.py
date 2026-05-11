"""User preference repository implementations."""
from typing import Any

from app.core.exceptions import UserNotFoundException
from app.core.interfaces import IUserPreferenceRepository


class MockUserPreferenceRepository(IUserPreferenceRepository):
    """In-memory mock repository for user notification preferences.

    Dependency Inversion Principle: The service depends on IUserPreferenceRepository,
    not this concrete class. This allows swapping for a real database repository
    without touching business logic.
    """

    def __init__(self):
        # Mock data store
        self._store: dict[str, dict[str, Any]] = {
            "user_001": {
                "email": "user001@example.com",
                "phone": "+1234567890",
                "channels": {
                    "email": True,
                    "sms": True,
                    "whatsapp": False
                }
            },
            "user_002": {
                "email": "user002@example.com",
                "phone": "+0987654321",
                "channels": {
                    "email": True,
                    "sms": False,
                    "whatsapp": True
                }
            },
            "user_003": {
                "email": "user003@example.com",
                "phone": "+1122334455",
                "channels": {
                    "email": False,
                    "sms": False,
                    "whatsapp": False
                }
            }
        }

    async def get_preferences(self, user_id: str) -> dict[str, Any]:
        """Retrieve user preferences by ID."""
        if user_id not in self._store:
            raise UserNotFoundException(f"User {user_id} not found")
        return self._store[user_id]

    async def is_channel_enabled(self, user_id: str, channel: str) -> bool:
        """Check if a specific channel is enabled for the user."""
        prefs = await self.get_preferences(user_id)
        return prefs.get("channels", {}).get(channel, False)

    async def get_contact_address(self, user_id: str, channel: str) -> str:
        """Get the appropriate contact address for a channel."""
        prefs = await self.get_preferences(user_id)
        if channel == "email":
            return prefs["email"]
        elif channel in ("sms", "whatsapp"):
            return prefs["phone"]
        return ""
