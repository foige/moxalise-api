"""
Unit tests for the Google Sheets service.

This module contains unit tests for the GoogleSheetsService class.
"""
import pytest
from unittest.mock import MagicMock, patch

from moxalise.models.spreadsheet import SheetRange, SheetData
from moxalise.services.google_sheets import GoogleSheetsService


@pytest.fixture
def mock_sheets_service():
    """
    Fixture to create a mock Google Sheets service with properly configured method chains.

    Returns:
        MagicMock: A mock Google Sheets service.
    """
    # Mock the Application Default Credentials
    with patch("moxalise.services.google_sheets.default") as mock_default:
        # Set up the mock credentials
        mock_credentials = MagicMock()
        mock_project = "test-project"
        mock_default.return_value = (mock_credentials, mock_project)
        
        # Mock the build function
        with patch("moxalise.services.google_sheets.build") as mock_build:
            # Create the mock service with proper method chain
            mock_service = MagicMock()
            
            # Configure the spreadsheets chain
            spreadsheets_mock = MagicMock()
            mock_service.spreadsheets.return_value = spreadsheets_mock
            
            # Configure the values chain for spreadsheets
            values_mock = MagicMock()
            spreadsheets_mock.values.return_value = values_mock
            
            # Configure the get/update/append/clear methods
            get_mock = MagicMock()
            update_mock = MagicMock()
            append_mock = MagicMock()
            clear_mock = MagicMock()
            
            values_mock.get.return_value = get_mock
            values_mock.update.return_value = update_mock
            values_mock.append.return_value = append_mock
            values_mock.clear.return_value = clear_mock
            
            # Configure the execute methods
            get_mock.execute.return_value = {}
            update_mock.execute.return_value = {}
            append_mock.execute.return_value = {}
            clear_mock.execute.return_value = {}
            
            # Configure the get method for spreadsheets (for get_sheet_names)
            spreadsheet_get_mock = MagicMock()
            spreadsheets_mock.get.return_value = spreadsheet_get_mock
            spreadsheet_get_mock.execute.return_value = {}
            
            mock_build.return_value = mock_service
            
            # Create the service with the mocked dependencies
            service = GoogleSheetsService(spreadsheet_id="test_spreadsheet_id")
            
            # Ensure the service is using our mock
            service.service = mock_service
            
            yield service


def test_get_sheet_data(mock_sheets_service):
    """
    Test getting data from a sheet.

    Args:
        mock_sheets_service: The mock Google Sheets service.
    """
    # Arrange
    mock_values = [["Header1", "Header2"], ["Value1", "Value2"]]
    mock_result = {"values": mock_values}
    
    mock_sheets_service.service.spreadsheets().values().get().execute.return_value = mock_result
    
    range_obj = SheetRange(sheet_name="Sheet1", start_cell="A1", end_cell="B2")
    
    # Act
    result = mock_sheets_service.get_sheet_data(range_obj)
    
    # Assert
    assert isinstance(result, SheetData)
    assert result.values == mock_values
    assert result.range == "'Sheet1'!A1:B2"
    
    # Verify the API was called with the correct parameters
    # Instead of asserting on the intermediate method, check that the chain was called correctly
    spreadsheets_mock = mock_sheets_service.service.spreadsheets.return_value
    values_mock = spreadsheets_mock.values.return_value
    get_mock = values_mock.get.return_value
    
    # Verify the get method was called with the correct parameters
    values_mock.get.assert_called_with(
        spreadsheetId="test_spreadsheet_id",
        range="'Sheet1'!A1:B2"
    )
    
    # Verify execute was called
    get_mock.execute.assert_called_once()


def test_get_sheet_names(mock_sheets_service):
    """
    Test getting sheet names.

    Args:
        mock_sheets_service: The mock Google Sheets service.
    """
    # Arrange
    mock_sheets = [
        {"properties": {"title": "Sheet1"}},
        {"properties": {"title": "Sheet2"}}
    ]
    mock_result = {"sheets": mock_sheets}
    
    mock_sheets_service.service.spreadsheets().get().execute.return_value = mock_result
    
    # Act
    result = mock_sheets_service.get_sheet_names()
    
    # Assert
    assert result == ["Sheet1", "Sheet2"]
    
    # Verify the API was called with the correct parameters
    # Instead of asserting on the intermediate method, check that the chain was called correctly
    spreadsheets_mock = mock_sheets_service.service.spreadsheets.return_value
    get_mock = spreadsheets_mock.get.return_value
    
    # Verify the get method was called with the correct parameters
    spreadsheets_mock.get.assert_called_with(
        spreadsheetId="test_spreadsheet_id"
    )
    
    # Verify execute was called
    get_mock.execute.assert_called_once()