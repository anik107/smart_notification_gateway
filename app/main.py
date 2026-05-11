"""FastAPI application entry point."""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.api.routes import router as notification_router
from app.core.exceptions import (
    ChannelDisabledException,
    NotificationException,
    ProviderException,
    UserNotFoundException
)
from app.providers import provider_registry  # noqa: F401 - triggers registration


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    print(f"Registered channels: {provider_registry.list_channels()}")
    yield
    # Shutdown


app = FastAPI(
    title="Smart Notification Gateway",
    description="A SOLID-compliant, Clean Architecture notification service",
    version="1.0.0",
    lifespan=lifespan
)

# Register routes
app.include_router(notification_router)


# ───────────────────────────────────────────────
# Global Exception Handlers
# ───────────────────────────────────────────────

@app.exception_handler(UserNotFoundException)
async def user_not_found_handler(request: Request, exc: UserNotFoundException):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": str(exc), "error_code": "USER_NOT_FOUND"}
    )


@app.exception_handler(ChannelDisabledException)
async def channel_disabled_handler(request: Request, exc: ChannelDisabledException):
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={"detail": str(exc), "error_code": "CHANNEL_DISABLED"}
    )


@app.exception_handler(ProviderException)
async def provider_exception_handler(request: Request, exc: ProviderException):
    return JSONResponse(
        status_code=status.HTTP_502_BAD_GATEWAY,
        content={
            "detail": str(exc),
            "error_code": "PROVIDER_FAILURE",
            "provider": exc.provider_name
        }
    )


@app.exception_handler(NotificationException)
async def generic_notification_handler(request: Request, exc: NotificationException):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": str(exc), "error_code": "NOTIFICATION_ERROR"}
    )


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "channels": provider_registry.list_channels()}
