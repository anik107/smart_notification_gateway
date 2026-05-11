"""FastAPI routes for the notification gateway."""
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status

from app.api.dependencies import get_notification_service
from app.core.exceptions import (
    ChannelDisabledException,
    NotificationException,
    ProviderException,
    UserNotFoundException
)
from app.models.schemas import (
    NotificationRequest,
    NotificationResponse,
    NotificationResult
)
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.post("/send", response_model=NotificationResponse, status_code=status.HTTP_202_ACCEPTED)
async def send_notification(
    request: NotificationRequest,
    background_tasks: BackgroundTasks,
    service: NotificationService = Depends(get_notification_service)
) -> NotificationResponse:
    """Queue a notification to be sent asynchronously.

    The API returns immediately (202 Accepted) while the actual sending
    happens in the background via FastAPI's BackgroundTasks.
    """
    background_tasks.add_task(_process_notification, service, request)

    return NotificationResponse(
        status="queued",
        message=f"Notification queued for user {request.user_id} via {request.channel.value}"
    )


@router.post("/broadcast", response_model=NotificationResponse)
async def broadcast_notification(
    user_id: str,
    body: str,
    subject: str | None = None,
    background_tasks: BackgroundTasks = None,
    service: NotificationService = Depends(get_notification_service)
) -> NotificationResponse:
    """Broadcast a message to all enabled channels for a user."""
    # For broadcast, we run in background as well
    # Note: BackgroundTasks injected in signature for clarity
    results = await service.send_to_all_enabled_channels(
        user_id=user_id,
        subject=subject,
        body=body
    )

    success_count = sum(1 for r in results if r.success)

    if success_count == 0 and results:
        status_val = "failed"
    elif success_count < len(results):
        status_val = "partial"
    else:
        status_val = "queued"

    return NotificationResponse(
        status=status_val,
        message=f"Broadcast completed: {success_count}/{len(results)} channels succeeded",
        results=results
    )


async def _process_notification(
    service: NotificationService,
    request: NotificationRequest
) -> None:
    """Background task wrapper for sending notifications.

    Exceptions are caught and logged here to prevent crashing the background worker.
    """
    try:
        await service.send_notification(request)
    except NotificationException:
        # Log the error in production (e.g., structlog, sentry)
        # For now, we silently handle it to keep background tasks stable
        pass
