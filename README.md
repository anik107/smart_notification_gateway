# Smart Notification Gateway

A production-ready notification gateway built with **FastAPI**, **Pydantic v2**, and **Clean Architecture**. The system is designed to be fully extensible, following **SOLID** principles to ensure maintainability, testability, and scalability.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [SOLID Principles — Where & How](#solid-principles--where--how)
   - [S — Single Responsibility Principle (SRP)](#s--single-responsibility-principle-srp)
   - [O — Open/Closed Principle (OCP)](#o--openclosed-principle-ocp)
   - [L — Liskov Substitution Principle (LSP)](#l--liskov-substitution-principle-lsp)
   - [I — Interface Segregation Principle (ISP)](#i--interface-segregation-principle-isp)
   - [D — Dependency Inversion Principle (DIP)](#d--dependency-inversion-principle-dip)
3. [Folder Structure](#folder-structure)
4. [Quick Start](#quick-start)
5. [Adding a New Channel](#adding-a-new-channel)
6. [API Reference](#api-reference)
7. [Error Handling](#error-handling)

---

## Architecture Overview

The project follows a **layered Clean Architecture** with four distinct layers:

| Layer | Responsibility | Directory |
|-------|---------------|-----------|
| **API (Presentation)** | HTTP routing, request/response models, dependency injection | `app/api/` |
| **Services (Business Logic)** | Orchestration, validation, workflow coordination | `app/services/` |
| **Repositories (Data Access)** | Data persistence, user preference retrieval | `app/repositories/` |
| **Core (Domain/Abstractions)** | Abstract base classes, interfaces, exceptions | `app/core/` |
| **Providers (Infrastructure)** | Concrete notification delivery implementations | `app/providers/` |
| **Models** | Pydantic v2 schemas shared across layers | `app/models/` |

**Dependency Rule:** Dependencies always point inward. The API layer depends on Services. Services depend on Core abstractions. Providers and Repositories implement Core abstractions. Nothing in the inner layers knows about FastAPI, HTTP, or external APIs.

---

## SOLID Principles — Where & How

### S — Single Responsibility Principle (SRP)

> *"A class should have only one reason to change."*

#### Where it is maintained:

| File | Responsibility |
|------|---------------|
| `app/services/notification_service.py` | **Only** orchestrates the notification flow: validate preferences → resolve address → delegate to provider. It does NOT format messages, send HTTP requests, or query databases directly. |
| `app/providers/email_provider.py` | **Only** handles email-specific concerns: SMTP formatting, subject lines, attachments. |
| `app/providers/sms_provider.py` | **Only** handles SMS-specific concerns: body truncation, character limits. |
| `app/repositories/user_preference_repository.py` | **Only** handles data retrieval and user settings. No business logic. |
| `app/api/routes.py` | **Only** handles HTTP concerns: parsing JSON, returning status codes, triggering background tasks. |
| `app/models/schemas.py` | **Only** defines data structures and validation rules. |

#### Code Example — SRP in `NotificationService`:

```python
# app/services/notification_service.py
class NotificationService:
    """Core service responsible for notification orchestration.

    SRP: This service ONLY orchestrates the flow:
    validate preferences -> select provider -> send.
    It does NOT format messages (providers do) 
    nor access data directly (repositories do).
    """

    async def send_notification(self, request: NotificationRequest) -> list[NotificationResult]:
        # 1. Validate (delegated to repository)
        is_enabled = await self._preference_repo.is_channel_enabled(...)

        # 2. Resolve address (delegated to repository)
        recipient_address = await self._preference_repo.get_contact_address(...)

        # 3. Build domain object (model responsibility)
        notification = Notification(...)

        # 4. Send (delegated to provider)
        provider = provider_registry.get_provider(request.channel.value)
        result = await provider.send(notification)

        return [result]
```

**Why this is SRP:** If email formatting rules change, you edit `email_provider.py`, not the service. If user data moves from mock to PostgreSQL, you edit `user_preference_repository.py`, not the service. If the HTTP API changes, you edit `routes.py`, not the service.

---

### O — Open/Closed Principle (OCP)

> *"Software entities should be open for extension, but closed for modification."*

#### Where it is maintained:

| File | Role in OCP |
|------|-------------|
| `app/providers/base.py` | Contains `ProviderRegistry` — the extension point for new channels. |
| `app/providers/__init__.py` | Registration site for new providers. |
| `app/services/notification_service.py` | Uses the registry generically — **never** modified when adding channels. |

#### How it works:

The `ProviderRegistry` acts as a plugin system. New notification channels are added by:
1. Creating a new provider class.
2. Calling `provider_registry.register(NewProvider)`.

**Zero changes** are required in:
- `NotificationService`
- `NotificationService.send_to_all_enabled_channels()`
- FastAPI routes
- Exception handlers

#### Code Example — OCP in `ProviderRegistry`:

```python
# app/providers/base.py
class ProviderRegistry:
    """Registry for notification providers.

    OCP: New providers are registered here at runtime
    without modifying the core sending engine.
    """

    def __init__(self):
        self._providers: dict[str, Type[NotificationProvider]] = {}

    def register(self, provider_class: Type[NotificationProvider]) -> None:
        self._providers[provider_class.__name__.lower().replace("provider", "")] = provider_class

    def get_provider(self, channel: str) -> NotificationProvider:
        provider_class = self._providers.get(channel)
        if not provider_class:
            raise ValueError(f"No provider registered for channel: {channel}")
        return provider_class()
```

#### Code Example — OCP in `send_to_all_enabled_channels`:

```python
# app/services/notification_service.py
async def send_to_all_enabled_channels(self, user_id: str, ...) -> list[NotificationResult]:
    """Broadcast a message to all enabled channels for a user.

    OCP: This method iterates over the registry.
    Adding a new channel (e.g., Telegram) requires ZERO changes here.
    """
    enabled_channels = prefs.get("channels", {})

    for channel_name, is_enabled in enabled_channels.items():
        if not is_enabled:
            continue
        # Generic provider resolution — no hardcoded channels
        provider = provider_registry.get_provider(channel_name)
        result = await provider.send(notification)
        results.append(result)
```

#### To add Telegram (example):

```python
# app/providers/telegram_provider.py
class TelegramProvider(NotificationProvider):
    @property
    def channel_name(self) -> str:
        return "telegram"

    async def send(self, notification: Notification) -> NotificationResult:
        # ... implementation
```

```python
# app/providers/__init__.py
from app.providers.telegram_provider import TelegramProvider
provider_registry.register(TelegramProvider)  # ONE line added
```

**Files you do NOT touch:** `notification_service.py`, `routes.py`, `main.py`, `dependencies.py`.

---

### L — Liskov Substitution Principle (LSP)

> *"Objects of a superclass shall be replaceable with objects of its subclasses without affecting the correctness of the program."*

#### Where it is maintained:

| File | Role in LSP |
|------|-------------|
| `app/core/interfaces.py` | Defines `NotificationProvider` ABC — the contract all providers must honor. |
| `app/providers/email_provider.py` | Honors the contract. |
| `app/providers/sms_provider.py` | Honors the contract. |
| `app/providers/whatsapp_provider.py` | Honors the contract. |
| `app/services/notification_service.py` | Treats all providers polymorphically via `provider_registry.get_provider()`. |

#### The Contract (`NotificationProvider`):

```python
# app/core/interfaces.py
class NotificationProvider(ABC):
    """Abstract base class for all notification delivery methods.

    LSP: All concrete providers must be substitutable
    for this base class without altering correctness.
    """

    @property
    @abstractmethod
    def channel_name(self) -> str:
        """Return the unique channel identifier."""
        ...

    @abstractmethod
    async def send(self, notification: Notification) -> NotificationResult:
        """Send a notification and return the result.

        Raises:
            ProviderException: If the provider fails.
        """
        ...
```

#### LSP in Action — Polymorphic Dispatch:

```python
# app/services/notification_service.py
provider = provider_registry.get_provider(request.channel.value)

# LSP: We do not know (or care) if this is EmailProvider, SMSProvider,
# or WhatsAppProvider. All we know is it satisfies NotificationProvider.
result = await provider.send(notification)
```

**Why this is LSP:** You can swap `EmailProvider` for `SMSProvider` or a future `TelegramProvider` at runtime, and `NotificationService` continues to work correctly because every subclass honors the same contract (`channel_name` property + `send()` method + raises `ProviderException` on failure).

**LSP Violation to Avoid:** Never create a provider that returns `None` instead of `NotificationResult`, or raises a generic `Exception` instead of `ProviderException`. That would break the caller's expectations.

---

### I — Interface Segregation Principle (ISP)

> *"Clients should not be forced to depend on methods they do not use."*

#### Where it is maintained:

| File | Role in ISP |
|------|-------------|
| `app/core/interfaces.py` | Defines two separate interfaces: `NotificationProvider` (universal) and `IAttachmentCapable` (optional). |
| `app/providers/email_provider.py` | Implements **both** `NotificationProvider` AND `IAttachmentCapable` because email supports attachments. |
| `app/providers/sms_provider.py` | Implements **only** `NotificationProvider`. It is NOT forced to implement `add_attachment`. |
| `app/providers/whatsapp_provider.py` | Implements **only** `NotificationProvider`. |

#### The Segregated Interfaces:

```python
# app/core/interfaces.py

# Universal contract — ALL providers implement this
class NotificationProvider(ABC):
    @property
    @abstractmethod
    def channel_name(self) -> str: ...

    @abstractmethod
    async def send(self, notification: Notification) -> NotificationResult: ...

# Optional contract — ONLY providers that support attachments implement this
class IAttachmentCapable(ABC):
    """Interface for providers that support file attachments.

    ISP: Only email providers implement this.
    SMS providers are NOT forced to implement attachment methods.
    """

    @abstractmethod
    async def add_attachment(self, file_path: str, file_name: str, mime_type: str) -> None:
        ...
```

#### ISP in Action — Email vs SMS:

```python
# app/providers/email_provider.py
class EmailProvider(NotificationProvider, IAttachmentCapable):
    """Implements BOTH because email supports attachments."""

    async def add_attachment(self, file_path: str, file_name: str, mime_type: str) -> None:
        self._attachments.append({...})

    async def send(self, notification: Notification) -> NotificationResult:
        if notification.attachments:
            for att in notification.attachments:
                await self.add_attachment(...)
        # ... send logic

# app/providers/sms_provider.py
class SMSProvider(NotificationProvider):
    """Implements ONLY NotificationProvider.
    SMS does not support attachments, so it does NOT implement IAttachmentCapable.
    """

    async def send(self, notification: Notification) -> NotificationResult:
        # No attachment methods needed — ISP respected
        formatted_body = self._format_sms(notification)
        # ... send logic
```

**Why this is ISP:** If we had put `add_attachment()` inside `NotificationProvider`, then `SMSProvider` and `WhatsAppProvider` would be forced to implement a method they do not need (or raise `NotImplementedError`, which is an ISP violation). By splitting into two interfaces, each provider only depends on what it actually uses.

---

### D — Dependency Inversion Principle (DIP)

> *"High-level modules should not depend on low-level modules. Both should depend on abstractions."*

#### Where it is maintained:

| File | Role in DIP |
|------|-------------|
| `app/core/interfaces.py` | Defines the abstractions (`NotificationProvider`, `IUserPreferenceRepository`). |
| `app/services/notification_service.py` | High-level module. Depends ONLY on `IUserPreferenceRepository`, not on `MockUserPreferenceRepository`. |
| `app/repositories/user_preference_repository.py` | Low-level module. Implements `IUserPreferenceRepository`. |
| `app/api/dependencies.py` | **Wiring layer** — the ONLY place where concrete classes are instantiated and injected. |
| `app/api/routes.py` | Uses `Depends(get_notification_service)` to receive injected dependencies. |

#### High-Level Module — Service Layer:

```python
# app/services/notification_service.py
class NotificationService:
    """DIP: Depends on IUserPreferenceRepository abstraction,
    not on concrete repository implementations.
    """

    def __init__(self, preference_repo: IUserPreferenceRepository):
        # Constructor injection of abstraction
        self._preference_repo = preference_repo
```

**Notice:** `NotificationService` imports `IUserPreferenceRepository` from `app.core.interfaces`. It has **zero knowledge** of `MockUserPreferenceRepository`.

#### Low-Level Module — Repository:

```python
# app/repositories/user_preference_repository.py
class MockUserPreferenceRepository(IUserPreferenceRepository):
    """Concrete implementation. Implements the abstraction."""

    async def get_preferences(self, user_id: str) -> dict[str, Any]:
        ...

    async def is_channel_enabled(self, user_id: str, channel: str) -> bool:
        ...
```

#### Wiring Layer — Dependency Injection:

```python
# app/api/dependencies.py
"""FastAPI dependency injection configuration.

DIP: All concrete dependencies are wired here.
The rest of the application depends on abstractions (interfaces).
"""

def get_user_preference_repository() -> IUserPreferenceRepository:
    """Factory for user preference repository.

    In production, swap this to return a PostgreSQL/MongoDB repository
    without touching ANY business logic.
    """
    return MockUserPreferenceRepository()

def get_notification_service(
    repo: IUserPreferenceRepository = get_user_preference_repository()
) -> NotificationService:
    """Factory for NotificationService with injected repository."""
    return NotificationService(preference_repo=repo)
```

#### Presentation Layer — Routes:

```python
# app/api/routes.py
@router.post("/send", response_model=NotificationResponse, status_code=status.HTTP_202_ACCEPTED)
async def send_notification(
    request: NotificationRequest,
    background_tasks: BackgroundTasks,
    service: NotificationService = Depends(get_notification_service)  # Injected!
) -> NotificationResponse:
    ...
```

**Why this is DIP:**
- `NotificationService` (high-level) depends on `IUserPreferenceRepository` (abstraction).
- `MockUserPreferenceRepository` (low-level) depends on `IUserPreferenceRepository` (abstraction).
- Neither depends on the other directly.
- To switch from mock data to PostgreSQL, you only change **one function** (`get_user_preference_repository()` in `dependencies.py`). Zero changes to `NotificationService`, zero changes to routes.

---

## Folder Structure

```
smart_notification_gateway/
├── requirements.txt
├── README.md
└── app/
    ├── __init__.py
    ├── main.py                          # FastAPI app, lifespan, exception handlers
    ├── core/                            # Domain: abstractions & exceptions
    │   ├── __init__.py
    │   ├── exceptions.py                # NotificationException hierarchy
    │   └── interfaces.py                # ABCs: NotificationProvider, IUserPreferenceRepository, IAttachmentCapable
    ├── models/                          # Pydantic v2 schemas
    │   ├── __init__.py
    │   └── schemas.py                   # Notification, NotificationResult, NotificationRequest, etc.
    ├── providers/                       # Infrastructure: concrete delivery channels
    │   ├── __init__.py                  # Auto-registers all providers
    │   ├── base.py                      # ProviderRegistry (OCP)
    │   ├── email_provider.py            # Email + attachments (ISP)
    │   ├── sms_provider.py              # SMS (no attachments)
    │   └── whatsapp_provider.py         # WhatsApp
    ├── repositories/                    # Data access layer
    │   ├── __init__.py
    │   └── user_preference_repository.py # Mock repo with user/channel settings
    ├── services/                        # Business logic layer
    │   ├── __init__.py
    │   └── notification_service.py      # Orchestration engine
    └── api/                             # Presentation layer
        ├── __init__.py
        ├── dependencies.py              # FastAPI DI wiring (DIP)
        └── routes.py                    # HTTP endpoints + BackgroundTasks
```

---

## Quick Start

### 1. Install Dependencies

```bash
cd smart_notification_gateway
pip install -r requirements.txt
```

### 2. Run the Server

```bash
uvicorn app.main:app --reload --port 8000
```

### 3. Send a Notification

```bash
curl -X POST "http://localhost:8000/notifications/send" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_001",
    "channel": "email",
    "subject": "Welcome!",
    "body": "Hello from the Smart Notification Gateway."
  }'
```

**Response (202 Accepted):**
```json
{
  "status": "queued",
  "message": "Notification queued for user user_001 via email"
}
```

### 4. Broadcast to All Enabled Channels

```bash
curl -X POST "http://localhost:8000/notifications/broadcast?user_id=user_001&body=System+alert" \
  -H "Content-Type: application/json"
```

### 5. Health Check

```bash
curl "http://localhost:8000/health"
```

---

## Adding a New Channel (e.g., Telegram)

**Step 1:** Create the provider (honor `NotificationProvider` contract):

```python
# app/providers/telegram_provider.py
from app.core.interfaces import NotificationProvider
from app.core.exceptions import ProviderException
from app.models.schemas import Notification, NotificationResult, ChannelType

class TelegramProvider(NotificationProvider):
    @property
    def channel_name(self) -> str:
        return "telegram"

    async def send(self, notification: Notification) -> NotificationResult:
        try:
            # Call Telegram Bot API here
            return NotificationResult(
                success=True,
                channel=self.channel_name,
                provider="TelegramProvider",
                message_id=f"tg_{uuid.uuid4().hex[:12]}"
            )
        except Exception as exc:
            raise ProviderException(
                provider_name=self.channel_name,
                message="Telegram send failed",
                original_error=exc
            )
```

**Step 2:** Register it:

```python
# app/providers/__init__.py
from app.providers.telegram_provider import TelegramProvider
provider_registry.register(TelegramProvider)
```

**Done.** No changes to `NotificationService`, routes, or core logic. This is **OCP** in action.

---

## API Reference

| Method | Endpoint | Description | Status |
|--------|----------|-------------|--------|
| POST | `/notifications/send` | Queue a single-channel notification | 202 Accepted |
| POST | `/notifications/broadcast` | Broadcast to all enabled user channels | 200 OK |
| GET | `/health` | Health check & registered channels | 200 OK |

---

## Error Handling

Custom exception handlers in `app/main.py` map domain exceptions to precise HTTP status codes:

| Exception | HTTP Status | Meaning |
|-----------|-------------|---------|
| `UserNotFoundException` | `404 Not Found` | User ID does not exist in repository |
| `ChannelDisabledException` | `403 Forbidden` | Channel is disabled for this user |
| `ProviderException` | `502 Bad Gateway` | External provider (SMTP, SMS gateway) failed |
| `NotificationException` | `500 Internal Server Error` | Generic unexpected error |

---

## Background Processing

The `POST /notifications/send` endpoint uses FastAPI's `BackgroundTasks` to process notifications asynchronously. The API returns `202 Accepted` immediately, while the actual provider dispatch happens in the background. This prevents slow external APIs from blocking HTTP responses.

```python
# app/api/routes.py
@router.post("/send", status_code=status.HTTP_202_ACCEPTED)
async def send_notification(
    request: NotificationRequest,
    background_tasks: BackgroundTasks,
    service: NotificationService = Depends(get_notification_service)
):
    background_tasks.add_task(_process_notification, service, request)
    return NotificationResponse(status="queued", message="...")
```

---

## User Preferences (Mock Repository)

`MockUserPreferenceRepository` simulates a database with three test users:

| User ID | Email Enabled | SMS Enabled | WhatsApp Enabled | Contact |
|---------|--------------|-------------|------------------|---------|
| `user_001` | ✅ | ✅ | ❌ | user001@example.com / +1234567890 |
| `user_002` | ✅ | ❌ | ✅ | user002@example.com / +0987654321 |
| `user_003` | ❌ | ❌ | ❌ | user003@example.com / +1122334455 |

To swap to a real database, implement `IUserPreferenceRepository` and update **only** `app/api/dependencies.py`.
