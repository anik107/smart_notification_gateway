"""FastAPI application entry point.

Single Responsibility Principle: This module is solely responsible for
assembling the application — wiring routers, exception handlers, and
lifespan events. Each concern lives in its own module.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.exception_handlers import register_exception_handlers
from app.api.health import router as health_router
from app.api.routes import router as notification_router
from app.providers import provider_registry  # noqa: F401 — triggers auto-discovery


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
app.include_router(health_router)

# Register exception handlers
register_exception_handlers(app)
