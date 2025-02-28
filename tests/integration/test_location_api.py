"""
Integration tests for the location API endpoints.

This module contains integration tests for the location API endpoints.
"""
import pytest
import sys
import json
from unittest.mock import patch, ANY, MagicMock
from datetime import datetime, UTC

from moxalise.models.location import LocationData, LocationResponse
from moxalise.models.spreadsheet import SheetAppendResponse, SheetAppendRequest, SheetRange
from moxalise.core.security import hash_ip_address, sanitize_object

@patch("moxalise.api.routes.location.hash_ip_address")
def test_store_location(mock_hash_ip, client, mock_sheets_service):
    """
    Test storing location data.

    Args:
        mock_hash_ip: Mock for the hash_ip_address function.
        client: The test client.
        mock_sheets_service: A mock Google Sheets service.
    """
    # Setup mock for IP hashing
    mock_hash_ip.return_value = "hashed_ip"

    # Create test location data
    location_data = {
        "latitude": 37.7749,
        "longitude": -122.4194,
        "accuracy": 10.0,
        "altitude": 100.0,
        "altitude_accuracy": 5.0,
        "heading": 90.0,
        "speed": 0.0,
        "phone_number": "+1234567890",
        "message": "Test message"
    }
    
    # Act
    response = client.post("/api/location/", json=location_data)

    # Assert
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["success"] is True
    assert "Location data stored successfully" in response_data["message"]
    assert "timestamp" in response_data

    # Verify the service was called with the correct data
    mock_sheets_service.append_sheet_data.assert_called_once()
    
    # Verify the sheet name is correct
    args, _ = mock_sheets_service.append_sheet_data.call_args
    append_request = args[0]
    assert isinstance(append_request, SheetAppendRequest)
    assert append_request.range.sheet_name == "მოხალისეთა კოორდინატები"
    
    # Verify that the IP address was hashed
    mock_hash_ip.assert_called_once()
    
    # Verify the hashed IP is in the values
    values = append_request.values[0]
    assert "hashed_ip" in values  # The hashed IP should be in the values list
    # We don't check all values because user_agent and ip_address are added in the endpoint


@patch("moxalise.api.routes.location.sanitize_object")
@patch("moxalise.api.routes.location.hash_ip_address")
def test_store_location_with_malicious_data(mock_hash_ip, mock_sanitize, client, mock_sheets_service):
    """
    Test storing location data with potentially malicious content.

    Args:
        mock_hash_ip: Mock for the hash_ip_address function.
        mock_sanitize: Mock for the sanitize_object function.
        client: The test client.
        mock_sheets_service: A mock Google Sheets service.
    """
    # Setup mocks
    mock_hash_ip.return_value = "hashed_ip"
    
    # Mock sanitize_object to return a sanitized version of the input
    def sanitize_side_effect(obj):
        if isinstance(obj, dict):
            result = {}
            for k, v in obj.items():
                if isinstance(v, str) and "<script>" in v:
                    result[k] = "SANITIZED"
                else:
                    result[k] = v
            return result
        elif isinstance(obj, str) and "<script>" in obj:
            return "SANITIZED"
        else:
            return obj
    
    mock_sanitize.side_effect = sanitize_side_effect

    # Create test location data with malicious content
    location_data = {
        "latitude": 37.7749,
        "longitude": -122.4194,
        "accuracy": 10.0,
        "phone_number": "<script>alert('XSS')</script>+1234567890",
        "message": "<script>alert('Message XSS')</script>"
    }
    
    # Act
    response = client.post("/api/location/", json=location_data)

    # Assert
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["success"] is True
    
    # Verify sanitize_object was called with the location data
    mock_sanitize.assert_called()
    
    # Verify the service was called with sanitized data
    mock_sheets_service.append_sheet_data.assert_called_once()
    
    # Get the values that were sent to the spreadsheet
    args, _ = mock_sheets_service.append_sheet_data.call_args
    append_request = args[0]
    values = append_request.values[0]
    
    # The phone number should be sanitized
    assert "SANITIZED" in values


def test_store_location_error(client, mock_sheets_service):
    """
    Test storing location data with an error.

    Args:
        client: The test client.
        mock_sheets_service: A mock Google Sheets service.
    """
    # Arrange
    mock_sheets_service.append_sheet_data.side_effect = Exception("Test error")

    # Create test location data
    location_data = {
        "latitude": 37.7749,
        "longitude": -122.4194,
        "accuracy": 10.0,
        "phone_number": "+1234567890",
        "message": "Error test message"
    }

    # Act
    response = client.post("/api/location/", json=location_data)

    # Assert
    assert response.status_code == 200  # We still return 200 but with success=False
    response_data = response.json()
    assert response_data["success"] is False
    assert "Failed to store location data" in response_data["message"]
    assert "timestamp" in response_data


@pytest.mark.parametrize(
    "missing_field",
    ["latitude", "longitude", "accuracy", "phone_number"]
)
def test_store_location_missing_required_field(client, missing_field):
    """
    Test storing location data with missing required fields.

    Args:
        client: The test client.
        missing_field: The field to omit from the request.
    """
    # Create test location data with all required fields
    location_data = {
        "latitude": 37.7749,
        "longitude": -122.4194,
        "accuracy": 10.0,
        "phone_number": "+1234567890",
        "message": "Optional message"
    }
    
    # Remove the specified field
    del location_data[missing_field]

    # Act
    response = client.post("/api/location/", json=location_data)

    # Assert
    assert response.status_code == 422  # Unprocessable Entity
    response_data = response.json()
    assert "detail" in response_data
    # Check that the error message mentions the missing field
    assert any(missing_field in str(error["loc"]) for error in response_data["detail"])