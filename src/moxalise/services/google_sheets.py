"""
Google Sheets service for interacting with Google Sheets API.

This module provides a service for interacting with Google Sheets API,
including authentication and operations like reading, updating, and appending data.
"""
from typing import List, Optional

from google.auth import default
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from moxalise.core.config import settings
from moxalise.models.spreadsheet import (
    SheetAppendRequest,
    SheetAppendResponse,
    SheetData,
    SheetRange,
    SheetUpdateRequest,
    SheetUpdateResponse,
)


class GoogleSheetsService:
    """
    Service for interacting with Google Sheets API.

    This class provides methods for authenticating with Google Sheets API
    and performing operations like reading, updating, and appending data.
    
    Authentication is handled using Application Default Credentials (ADC),
    which is ideal for Cloud Run and other Google Cloud environments.
    """

    # Define the scopes for Google Sheets API
    SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

    def __init__(self, spreadsheet_id: Optional[str] = None):
        """
        Initialize the Google Sheets service.

        Args:
            spreadsheet_id: The ID of the spreadsheet to interact with.
                If not provided, the value from settings will be used.
        """
        self.spreadsheet_id = spreadsheet_id or settings.GOOGLE_SHEETS_SPREADSHEET_ID
        self.service = self._authenticate()

    def _authenticate(self):
        """
        Authenticate with Google Sheets API using Application Default Credentials.
        
        In Cloud Run, this will automatically use the service account assigned to the service.
        For local development, you'll need to set up ADC using gcloud CLI:
        `gcloud auth application-default login`

        Returns:
            The authenticated Google Sheets API service.

        Raises:
            Exception: If authentication fails.
        """
        try:
            # Use Application Default Credentials
            credentials, project = default(scopes=self.SCOPES)
            service = build("sheets", "v4", credentials=credentials)
            return service
        except Exception as e:
            raise Exception(f"Failed to authenticate with Google Sheets API: {str(e)}")

    def get_sheet_data(self, range_obj: SheetRange) -> SheetData:
        """
        Get data from a sheet.

        Args:
            range_obj: The range to get data from.

        Returns:
            SheetData: The data from the sheet.

        Raises:
            HttpError: If the API request fails.
        """
        try:
            range_a1 = range_obj.to_a1_notation()
            result = (
                self.service.spreadsheets()
                .values()
                .get(spreadsheetId=self.spreadsheet_id, range=range_a1)
                .execute()
            )
            values = result.get("values", [])
            return SheetData(range=range_a1, values=values)
        except HttpError as error:
            raise HttpError(
                error.resp, error.content, f"Failed to get sheet data: {str(error)}"
            )

    def update_sheet_data(self, request: SheetUpdateRequest) -> SheetUpdateResponse:
        """
        Update data in a sheet.

        Args:
            request: The request containing the range and values to update.

        Returns:
            SheetUpdateResponse: The response from the update operation.

        Raises:
            HttpError: If the API request fails.
        """
        try:
            range_a1 = request.range.to_a1_notation()
            result = (
                self.service.spreadsheets()
                .values()
                .update(
                    spreadsheetId=self.spreadsheet_id,
                    range=range_a1,
                    valueInputOption=request.value_input_option,
                    body={"values": request.values},
                )
                .execute()
            )
            return SheetUpdateResponse(
                updated_cells=result.get("updatedCells", 0),
                updated_range=result.get("updatedRange", ""),
            )
        except HttpError as error:
            raise HttpError(
                error.resp, error.content, f"Failed to update sheet data: {str(error)}"
            )

    def append_sheet_data(self, request: SheetAppendRequest) -> SheetAppendResponse:
        """
        Append data to a sheet.

        Args:
            request: The request containing the range and values to append.

        Returns:
            SheetAppendResponse: The response from the append operation.

        Raises:
            HttpError: If the API request fails.
        """
        try:
            range_a1 = request.range.to_a1_notation()
            result = (
                self.service.spreadsheets()
                .values()
                .append(
                    spreadsheetId=self.spreadsheet_id,
                    range=range_a1,
                    valueInputOption=request.value_input_option,
                    body={"values": request.values},
                )
                .execute()
            )
            return SheetAppendResponse(
                appended_cells=result.get("updates", {}).get("updatedCells", 0),
                appended_range=result.get("updates", {}).get("updatedRange", ""),
            )
        except HttpError as error:
            raise HttpError(
                error.resp, error.content, f"Failed to append sheet data: {str(error)}"
            )

    def get_sheet_names(self) -> List[str]:
        """
        Get the names of all sheets in the spreadsheet.

        Returns:
            List[str]: The names of all sheets in the spreadsheet.

        Raises:
            HttpError: If the API request fails.
        """
        try:
            result = (
                self.service.spreadsheets()
                .get(spreadsheetId=self.spreadsheet_id)
                .execute()
            )
            sheets = result.get("sheets", [])
            return [sheet.get("properties", {}).get("title", "") for sheet in sheets]
        except HttpError as error:
            raise HttpError(
                error.resp, error.content, f"Failed to get sheet names: {str(error)}"
            )

    def clear_sheet_data(self, range_obj: SheetRange) -> int:
        """
        Clear data from a sheet.

        Args:
            range_obj: The range to clear.

        Returns:
            int: The number of cells cleared.

        Raises:
            HttpError: If the API request fails.
        """
        try:
            range_a1 = range_obj.to_a1_notation()
            result = (
                self.service.spreadsheets()
                .values()
                .clear(spreadsheetId=self.spreadsheet_id, range=range_a1, body={})
                .execute()
            )
            return result.get("clearedRange", "")
        except HttpError as error:
            raise HttpError(
                error.resp, error.content, f"Failed to clear sheet data: {str(error)}"
            )