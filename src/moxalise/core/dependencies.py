"""
Common dependencies for the Moxalise API.

This module defines dependencies that can be used across different routes.
"""
from fastapi import HTTPException

from moxalise.services.google_sheets import GoogleSheetsService


def get_sheets_service() -> GoogleSheetsService:
    """
    Dependency to get the Google Sheets service.

    Returns:
        GoogleSheetsService: An instance of the Google Sheets service.
    """
    try:
        return GoogleSheetsService()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Google Sheets service error: {str(e)}")