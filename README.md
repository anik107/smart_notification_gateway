# 📬 Smart Notification Gateway

A notification service built with **FastAPI** that sends messages through Email, SMS, and WhatsApp. The project strictly follows **SOLID principles** and **Clean Architecture** to keep the code easy to understand, test, and extend.

---

## 📖 What Does This Project Do?

This is a backend API that lets you:

- **Send a notification** to a user through a specific channel (email, sms, or whatsapp)
- **Broadcast a message** to all channels a user has turned on
- **Check health** of the service and see which channels are available

Each user has preferences — they can turn channels on or off. The system checks these preferences before sending.

> **Note:** This is a demo project. It does not actually send real emails or SMS. It simulates the sending and returns mock results. You can plug in real providers (like SendGrid, Twilio, etc.) by creating new provider classes.

---

## 🗂️ Project Structure

```
smart_notification_gateway/
│
├── app/
│   ├── __init__.py
│   ├── main.py                          # App entry point — assembles everything
│   │
│   ├── api/                             # API layer (HTTP concerns only)
│   │   ├── routes.py                    # Notification endpoints
│   │   ├── health.py                    # Health check endpoint
│   │   ├── exception_handlers.py        # Maps errors to HTTP responses
│   │   └── dependencies.py             # Dependency injection wiring
│   │
│   ├── core/                            # Core abstractions (no business logic)
│   │   ├── interfaces.py               # Abstract classes / contracts
│   │   └── exceptions.py               # Custom error types
│   │
│   ├── models/                          # Data models
│   │   └── schemas.py                  # Pydantic request/response models
│   │
│   ├── providers/                       # Notification channel implementations
│   │   ├── base.py                     # Provider registry
│   │   ├── email_provider.py           # Email channel
│   │   ├── sms_provider.py             # SMS channel
│   │   ├── whatsapp_provider.py        # WhatsApp channel
│   │   └── __init__.py                 # Auto-discovers all providers
│   │
│   ├── repositories/                    # Data access layer
│   │   └── user_preference_repository.py  # User preferences (mock data)
│   │
│   └── services/                        # Business logic layer
│       └── notification_service.py      # Orchestrates the sending flow
│
└── requirements.txt
```

---

## 🚀 How to Run

### 1. Clone the project

```bash
git clone <your-repo-url>
cd smart_notification_gateway
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

### 3. Activate the virtual environment

**Windows (PowerShell):**
```bash
venv\Scripts\Activate
```

**Mac / Linux:**
```bash
source venv/bin/activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Start the server

```bash
uvicorn app.main:app --reload --port 8000
```

The API is now running at **http://localhost:8000**

### 6. Open the docs

Go to **http://localhost:8000/docs** in your browser. You will see an interactive Swagger UI where you can test all the endpoints.

---

## 📡 API Endpoints

### 1. Send a Notification

**POST** `/notifications/send`

Send a notification to one user through one channel.

**Request Body:**
```json
{
  "user_id": "user_001",
  "channel": "email",
  "subject": "Welcome!",
  "body": "Hello, welcome to our platform!",
  "priority": "normal"
}
```

**Response (202 Accepted):**
```json
{
  "status": "queued",
  "message": "Notification queued for user user_001 via email",
  "results": []
}
```

The notification is processed in the background. The API responds immediately.

### 2. Broadcast to All Channels

**POST** `/notifications/broadcast?user_id=user_001&body=Hello!&subject=Hi`

Send a message to every channel the user has turned on.

**Response:**
```json
{
  "status": "queued",
  "message": "Broadcast completed: 2/2 channels succeeded",
  "results": [
    {
      "success": true,
      "channel": "email",
      "provider": "EmailProvider",
      "message_id": "email_abc123def456",
      "timestamp": "2026-05-15T10:30:00",
      "error_message": null
    },
    {
      "success": true,
      "channel": "sms",
      "provider": "SMSProvider",
      "message_id": "sms_789ghi012jkl",
      "timestamp": "2026-05-15T10:30:00",
      "error_message": null
    }
  ]
}
```

### 3. Health Check

**GET** `/health`

Check if the service is running and see which channels are registered.

**Response:**
```json
{
  "status": "healthy",
  "channels": ["email", "sms", "whatsapp"]
}
```

---

## 👥 Mock Users

The project comes with three test users. You can use these user IDs in your requests:

| User ID    | Email                 | Phone          | Email | SMS  | WhatsApp |
|------------|----------------------|----------------|:-----:|:----:|:--------:|
| `user_001` | user001@example.com  | +1234567890    |  ✅   |  ✅  |    ❌    |
| `user_002` | user002@example.com  | +0987654321    |  ✅   |  ❌  |    ✅    |
| `user_003` | user003@example.com  | +1122334455    |  ❌   |  ❌  |    ❌    |

- `user_001` has email and sms turned on
- `user_002` has email and whatsapp turned on
- `user_003` has all channels turned off

---

## 🧱 SOLID Principles — How They Are Applied

This project follows all five SOLID principles. Here is how each one is used:

### S — Single Responsibility Principle

> "Every class should have only one job."

Each file and class does **one thing only**:

| Class / File | Its One Job |
|---|---|
| `NotificationService` | Orchestrate the send flow (validate → pick provider → send) |
| `EmailProvider` | Format and send email notifications |
| `SMSProvider` | Format and send SMS notifications |
| `MockUserPreferenceRepository` | Store and retrieve user preferences |
| `exception_handlers.py` | Map domain errors to HTTP responses |
| `health.py` | Handle the health check endpoint |
| `main.py` | Assemble the app (wire routers + handlers) |
| `schemas.py` | Define the shape of request and response data |

### O — Open/Closed Principle

> "You can add new features without changing existing code."

**Adding a new channel (e.g., Telegram) requires only one step:**

1. Create a new file `app/providers/telegram_provider.py`:

```python
from app.core.interfaces import NotificationProvider
from app.models.schemas import Notification, NotificationResult
from app.providers.base import provider_registry

@provider_registry.auto_register
class TelegramProvider(NotificationProvider):

    @property
    def channel_name(self) -> str:
        return "telegram"

    async def send(self, notification: Notification) -> NotificationResult:
        # Your Telegram sending logic here
        ...
```

That's it. **No other file needs to change.** The auto-discovery system in `providers/__init__.py` will find it, and the `@auto_register` decorator will register it.

### L — Liskov Substitution Principle

> "You can swap any implementation for its interface without breaking anything."

- All providers (`EmailProvider`, `SMSProvider`, `WhatsAppProvider`) implement the same `NotificationProvider` interface. You can swap one for another and the service keeps working.
- `MockUserPreferenceRepository` implements `IUserPreferenceRepository`. You can replace it with a database-backed repository and the service won't notice.

Every method in the interface is also present in the implementation — no surprises.

### I — Interface Segregation Principle

> "Don't force a class to implement methods it doesn't need."

- `NotificationProvider` has just 2 requirements: `channel_name` and `send()`. Every provider needs these.
- `IAttachmentCapable` is a **separate** interface for file attachments. Only `EmailProvider` implements it because only email supports attachments. SMS and WhatsApp are **not forced** to implement attachment methods.

### D — Dependency Inversion Principle

> "Depend on abstractions, not on concrete classes."

- `NotificationService` never imports any concrete provider or repository. It receives `IUserPreferenceRepository` and `IProviderRegistry` through its constructor.
- All the concrete wiring happens in **one place**: `dependencies.py` (the composition root). If you want to swap the mock repository for a real database, you change only `dependencies.py`.

```
Service layer  →  depends on  →  Interfaces (abstractions)
                                      ↑
Concrete classes (providers, repos)  implement  these interfaces
```

---

## 🔄 How the Notification Flow Works

Here is what happens when you send a notification:

```
1. API receives POST /notifications/send
          │
2. FastAPI injects NotificationService (with all dependencies)
          │
3. NotificationService checks: is this channel enabled for this user?
          │          │
          │    (No) → Throws ChannelDisabledException → 403 response
          │
4. Looks up the user's contact address (email or phone)
          │
5. Builds a Notification object
          │
6. Gets the right provider from the registry (e.g., EmailProvider)
          │
7. Provider formats and "sends" the message
          │
8. Returns NotificationResult (success/failure + message ID)
```

---

## ⚠️ Error Handling

The app has four custom error types. Each is mapped to a specific HTTP status code:

| Error | When It Happens | HTTP Status |
|---|---|---|
| `UserNotFoundException` | User ID does not exist | 404 Not Found |
| `ChannelDisabledException` | User has turned off that channel | 403 Forbidden |
| `ProviderException` | The provider failed to send | 502 Bad Gateway |
| `NotificationException` | Any other notification error | 500 Internal Server Error |

All error mappings live in `exception_handlers.py`.

---

## 🧪 Testing Tips

Because of the SOLID design, this project is easy to test:

- **Unit test the service** — Pass mock implementations of `IUserPreferenceRepository` and `IProviderRegistry` to `NotificationService`. No real database or API needed.
- **Unit test providers** — Each provider can be tested alone since it only depends on `Notification` and `NotificationResult` data models.
- **Swap implementations** — You can create a `FakeEmailProvider` for tests that always returns success or always throws an error.

Example:

```python
from app.services.notification_service import NotificationService

# Create mock implementations of the interfaces
mock_repo = MockUserPreferenceRepository()
mock_registry = MockProviderRegistry()

# Inject them into the service
service = NotificationService(
    preference_repo=mock_repo,
    provider_registry=mock_registry,
)

# Test the service
result = await service.send_notification(request)
```

---

## 📦 Dependencies

| Package | What It Does |
|---|---|
| `fastapi` | Web framework for building the API |
| `uvicorn` | ASGI server to run the app |
| `pydantic` | Data validation and serialization |

Install everything with:

```bash
pip install -r requirements.txt
```

---

## 📝 Key Design Decisions

1. **Channel is a plain string, not an enum** — This follows the Open/Closed Principle. Adding a new channel does not require editing any existing enum or model.

2. **Auto-discovery of providers** — The `providers/__init__.py` file scans for all provider modules automatically. You never need to manually register a new provider.

3. **Constructor injection** — `NotificationService` receives all its dependencies through the constructor. This makes it easy to test and swap implementations.

4. **Composition root** — `dependencies.py` is the only place where concrete classes are connected to interfaces. The rest of the app only knows about abstractions.

5. **Background tasks** — The `/send` endpoint returns immediately (202 Accepted) and processes the notification in the background using FastAPI's `BackgroundTasks`.

---

## 📄 License

This project is for learning and demonstration purposes.
