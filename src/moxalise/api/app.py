"""
FastAPI application factory for Moxalise API.

This module provides a function to create and configure the FastAPI application
with all necessary middleware and routes.
"""
import os
import logging
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exception_handlers import http_exception_handler
from fastapi.exceptions import HTTPException

from moxalise.api.routes import spreadsheet, location
from moxalise.core.config import settings


# Configure logging
logging.basicConfig(
    level=logging.DEBUG if os.getenv("DEBUG") == "True" else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class LoggingMiddleware:
    """Middleware to log requests and responses."""

    async def __call__(self, request: Request, call_next):
        logger.debug(f"Request: {request.method} {request.url}")
        if os.getenv("DEBUG") == "True":
            body = await request.body()
            if body:
                logger.debug(f"Request body: {body.decode()}")
        
        response = await call_next(request)
        
        logger.debug(f"Response status: {response.status_code}")
        return response


async def exception_handler(request: Request, exc: Exception):
    """Global exception handler to log all exceptions."""
    import json
    
    if isinstance(exc, HTTPException):
        # Log HTTP exception with traceback
        logger.exception(f"HTTP {exc.status_code} exception: {exc.detail}")
        return await http_exception_handler(request, exc)
    
    # For all other exceptions
    logger.exception(f"Unhandled exception: {str(exc)}")
    
    # Return a simple error response
    return Response(
        content=json.dumps({
            "error": str(exc),
            "type": type(exc).__name__,
            "detail": "See server logs for more information"
        }),
        status_code=500,
        media_type="application/json"
    )


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.

    Returns:
        FastAPI: The configured FastAPI application.
    """
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description=settings.PROJECT_DESCRIPTION,
        version=settings.VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,  # Use configured origins from settings
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add logging middleware if DEBUG is enabled
    if os.getenv("DEBUG") == "True":
        app.middleware("http")(LoggingMiddleware())
    
    # Add exception handlers
    app.add_exception_handler(HTTPException, exception_handler)

    # Include routers
    #app.include_router(spreadsheet.router, prefix="/api/spreadsheet", tags=["spreadsheet"])
    app.include_router(location.router, prefix="/api/location", tags=["location"])

    @app.get("/", tags=["health"])
    async def health_check():
        """
        Health check endpoint.

        Returns:
            dict: A simple message indicating the API is running.
        """
        return {"status": "ok", "message": "Moxalise API is running"}

    return app