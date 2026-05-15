"""Global exception handlers for the FastAPI application.

Single Responsibility Principle: Exception-to-HTTP-response mapping
is isolated here, separate from application bootstrap and routing.
"""
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.core.exceptions import (
    ChannelDisabledException,
    NotificationException,
    ProviderException,
    UserNotFoundException,
)


def register_exception_handlers(app: FastAPI) -> None:
    """Register all domain exception handlers on the FastAPI app."""

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
