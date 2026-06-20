"""Main application entry point for the AI LMS backend.

This module initializes the FastAPI app, configures CORS origins, registers the
slowapi rate-limiter, integrates structlog structured JSON logging, includes v1 routers,
and sets up global exception overrides for consistent JSON response wrappers.
"""

import logging
import sys
import structlog
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler

from app.api.v1.api import api_router
from app.api.v1.routes.ai import limiter
from app.core.config import settings

# 1. Configure Structured Logging with structlog
structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# 2. Initialize FastAPI Application
app = FastAPI(
    title=settings.APP_NAME,
    description="FastAPI Backend for AI Learning Management System",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Bind slowapi limiter instance to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# 3. Configure CORS Middleware
# Restricted to localhost:3000 for local UI development, with wildcard backup for other services
origins = [
    "http://localhost:3000",
    "https://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 4. Standard Base Exception Handlers for Envelope Consistency
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Wraps FastAPI HTTPExceptions inside the standard ApiResponse format."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "data": None,
            "message": exc.detail
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Wraps request format errors inside the standard ApiResponse format."""
    logger.warning("request_validation_failed", errors=exc.errors())
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "data": exc.errors(),
            "message": "Input validation failed"
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Wraps unhandled system runtime errors inside the standard ApiResponse format."""
    logger.error("unhandled_server_exception", error=str(exc))
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "data": None,
            "message": "An unexpected internal server error occurred"
        }
    )


# 5. Core Root & Health Check Endpoints
@app.get("/")
async def root():
    """Application root welcome message."""
    return {
        "success": True,
        "data": {
            "application": settings.APP_NAME,
            "status": "online"
        },
        "message": "Welcome to the AI LMS Backend API"
    }


@app.get("/health")
async def health_check():
    """API health status audits for container orchestration hooks."""
    return {
        "success": True,
        "data": {
            "status": "healthy",
            "environment": settings.APP_ENV
        },
        "message": "Service status is healthy"
    }


# 6. Mount consolidated API Routers
app.include_router(api_router, prefix="/api/v1")


if __name__ == "__main__":
    import uvicorn
    # Execute web app listener locally
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
