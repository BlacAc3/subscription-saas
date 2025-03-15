from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
import uvicorn
import os

load_dotenv()

# Create the FastAPI application
app = FastAPI(
    title="My FastAPI Server",
    description="A simple FastAPI server configuration",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Configuration settings using Pydantic
class Settings(BaseModel):
    app_name: str = "FastAPI Server"
    admin_email: str = "admin@example.com"
    debug: bool = True
    api_prefix: str = "/api/v1"
    allowed_hosts: list = ["127.0.0.1", "localhost"]
    secret_key: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    port: int = int(os.getenv("PORT", 8000))

# Initialize settings
settings = Settings()

# CORS configuration middleware
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_hosts,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Run the application if this file is executed directly
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=settings.debug)
