import uvicorn
from config import settings, app
from database import init_db

# FastAPI startup event handler
@app.on_event("startup")
async def on_startup():
    """Initialize database connection on application startup."""
    await init_db()

# Root endpoint
@app.get("/")
async def root():
    """Return a simple greeting message."""
    return {"message": "Hello World"}

# Info endpoint - provides application configuration details
@app.get("/info")
async def info():
    """Return application configuration information. """
    return {
        "app_name": settings.app_name,
        "debug": settings.debug
    }

# Application entry point
if __name__ == "__main__":
    # TIP: In production, consider using a proper process manager
    # like systemd, supervisor, or docker instead of this direct invocation
    uvicorn.run(
        "main:app",  # Format: "{module_name}:{app_variable}"
        host="0.0.0.0",  # Default to all network interfaces for better container compatibility
        port=settings.port,
        reload=settings.debug  # Auto-reload should only be used during development
    )
