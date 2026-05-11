"""Pydantic v2 models for the notification gateway."""
from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, EmailStr


class ChannelType(str, Enum):
    """Supported notification channels.

    Open/Closed Principle: Adding a new channel only requires extending this enum
    and creating a new provider. No existing code needs modification.
    """
    EMAIL = "email"
    SMS = "sms"
    WHATSAPP = "whatsapp"


class NotificationPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class Attachment(BaseModel):
    """Represents a file attachment for email notifications."""
    file_path: str
    file_name: str
    mime_type: str = "application/octet-stream"


class Notification(BaseModel):
    """Core notification payload.

    Single Responsibility Principle: This model only defines the structure
    of a notification. Formatting logic lives in the providers.
    """
    recipient_id: str = Field(..., description="Target user identifier")
    recipient_address: str = Field(..., description="Email, phone number, etc.")
    channel: ChannelType
    subject: str | None = Field(None, description="Required for email")
    body: str = Field(..., min_length=1)
    priority: NotificationPriority = NotificationPriority.NORMAL
    attachments: list[Attachment] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class NotificationResult(BaseModel):
    """Result of a notification delivery attempt."""
    success: bool
    channel: str
    provider: str
    message_id: str | None = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    error_message: str | None = None


class NotificationRequest(BaseModel):
    """Incoming API request to send a notification."""
    user_id: str
    channel: ChannelType
    subject: str | None = None
    body: str = Field(..., min_length=1)
    priority: NotificationPriority = NotificationPriority.NORMAL
    attachments: list[Attachment] = Field(default_factory=list)


class NotificationResponse(BaseModel):
    """API response after processing a notification request."""
    status: Literal["queued", "failed", "partial"]
    message: str
    results: list[NotificationResult] = Field(default_factory=list)
