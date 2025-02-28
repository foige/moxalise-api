"""
Pytest configuration file.

This module contains shared fixtures for tests.
"""
import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient

from moxalise.api.app import create_app
from moxalise.core.dependencies import get_sheets_service
from moxalise.models.spreadsheet import SheetAppendResponse


@pytest.fixture
def mock_sheets_service():
    """
    Fixture to create a mock Google Sheets service.

    Returns:
        MagicMock: A mock Google Sheets service.
    """
    mock_service = MagicMock()
    
    # Configure default behavior for the mock service
    mock_service.append_sheet_data.return_value = SheetAppendResponse(
        appended_cells=11,  # 11 cells for all fields including phone_number
        appended_range="'Locations'!A1:K1"
    )
    
    return mock_service


@pytest.fixture
def app(mock_sheets_service):
    """
    Fixture to create a FastAPI application for testing with dependency overrides.

    Args:
        mock_sheets_service: A mock Google Sheets service.

    Returns:
        FastAPI: A FastAPI application instance with dependency overrides.
    """
    app = create_app()
    
    # Override the dependency
    app.dependency_overrides[get_sheets_service] = lambda: mock_sheets_service
    
    return app


@pytest.fixture
def client(app):
    """
    Fixture to create a test client for the FastAPI application.

    Args:
        app: The FastAPI application.

    Returns:
        TestClient: A test client for the FastAPI application.
    """
    return TestClient(app)