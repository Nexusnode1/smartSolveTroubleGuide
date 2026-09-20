"""FastAPI application entry point."""

from fastapi import FastAPI

from app.api.routes import router

app = FastAPI(title="Smart Guided Troubleshooting Engine")
app.include_router(router, prefix="/api/v1")


@app.get("/health")
def health() -> dict[str, str]:
    """Return the service health status."""
    return {"status": "ok"}
