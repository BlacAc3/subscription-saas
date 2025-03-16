from fastapi import FastAPI
import uvicorn
from datetime import datetime

from database import init_db
from routes import user, tenant, subscription, auth

# Create FastAPI app
app = FastAPI(title="Sub-SaaS API",
              description="API for managing multi-tenant subscriptions",
              version="0.1.0")

# Include routers
app.include_router(auth.router)
app.include_router(user.router)
app.include_router(tenant.router)
app.include_router(subscription.router)

# Global database connection
db = None

# FastAPI startup event handler
@app.on_event("startup")
async def on_startup():
    """Initialize database connection on application startup."""
    global db
    db = await init_db()
    print("Database initialized and ready")

# Root endpoint
@app.get("/", tags=["status"])
async def root():
    """Return a simple greeting message."""
    return {
        "message": "Welcome to the Sub-SaaS API",
        "status": "operational",
        "time": datetime.utcnow()
    }

# Info endpoint
@app.get("/info", tags=["status"])
async def info():
    """Return application information."""
    return {
        "app_name": "Sub-SaaS API",
        "version": "0.1.0",
        "description": "API for managing multi-tenant subscriptions",
        "endpoints": {
            "users": "/users",
            "tenants": "/tenants",
            "subscriptions": "/subscriptions"
        }
    }

# Application entry point
if __name__ == "__main__":
    uvicorn.run(
        "main:app",  # Format: "{module_name}:{app_variable}"
        host="0.0.0.0",  # Default to all network interfaces
        port=8000,
        reload=True  # Auto-reload during development
    )
