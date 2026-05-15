"""Health check endpoint.

Single Responsibility Principle: Infrastructure health probes are
separated from business-logic notification routes.
"""
from fastapi import APIRouter, Depends

from app.api.dependencies import get_provider_registry
from app.core.interfaces import IProviderRegistry

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check(
    registry: IProviderRegistry = Depends(get_provider_registry),
):
    """Health check endpoint."""
    return {"status": "healthy", "channels": registry.list_channels()}
