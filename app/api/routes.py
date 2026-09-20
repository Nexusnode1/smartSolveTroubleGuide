"""HTTP routes for the troubleshooting API."""

from fastapi import APIRouter

from app.models.schemas import PlaceholderTroubleshootResponse, TroubleshootRequest

router = APIRouter(tags=["troubleshooting"])


@router.post("/troubleshoot", response_model=PlaceholderTroubleshootResponse)
def troubleshoot(request: TroubleshootRequest) -> PlaceholderTroubleshootResponse:
    """Return a bootstrap placeholder without fabricating a troubleshooting plan."""
    # TODO: Delegate to the validated troubleshooting engine after official inputs exist.
    return PlaceholderTroubleshootResponse(
        status="placeholder",
        detail="Troubleshooting is not implemented until official requirements and datasets are supplied.",
        query=request.query,
    )
