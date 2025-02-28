"""
Integration tests for the API endpoints.

This module contains integration tests for the API endpoints.
"""
import pytest
from unittest.mock import patch

from moxalise.models.spreadsheet import SheetData


@pytest.mark.parametrize(
    "endpoint,expected_status,expected_response",
    [
        ("/", 200, {"status": "ok", "message": "Moxalise API is running"}),
    ],
)
def test_endpoints(client, endpoint, expected_status, expected_response):
    """
    Test API endpoints.

    Args:
        client: The test client.
        endpoint: The endpoint to test.
        expected_status: The expected status code.
        expected_response: The expected response.
    """
    response = client.get(endpoint)
    assert response.status_code == expected_status
    assert response.json() == expected_response


def test_get_sheet_names(client, mock_sheets_service):
    """
    Test getting sheet names.

    Args:
        client: The test client.
        mock_sheets_service: A mock Google Sheets service.
    """
    # Arrange
    mock_sheets_service.get_sheet_names.return_value = ["Sheet1", "Sheet2"]

    # Act
    response = client.get("/api/spreadsheet/sheets")

    # Assert
    assert response.status_code == 200
    assert response.json() == ["Sheet1", "Sheet2"]
    mock_sheets_service.get_sheet_names.assert_called_once()


def test_get_sheet_data(client, mock_sheets_service):
    """
    Test getting sheet data.

    Args:
        client: The test client.
        mock_sheets_service: A mock Google Sheets service.
    """
    # Arrange
    mock_values = [["Header1", "Header2"], ["Value1", "Value2"]]
    mock_sheets_service.get_sheet_data.return_value = SheetData(
        range="'Sheet1'!A1:B2", values=mock_values
    )

    # Act
    response = client.get(
        "/api/spreadsheet/data?sheet_name=Sheet1&start_cell=A1&end_cell=B2"
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "range": "'Sheet1'!A1:B2",
        "values": [["Header1", "Header2"], ["Value1", "Value2"]],
    }