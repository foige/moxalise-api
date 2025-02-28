"""
API routes for spreadsheet operations.

This module defines the FastAPI routes for interacting with Google Sheets,
including endpoints for reading, updating, and appending data.
"""
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from googleapiclient.errors import HttpError

from moxalise.models.spreadsheet import (
    SheetAppendRequest,
    SheetAppendResponse,
    SheetData,
    SheetRange,
    SheetUpdateRequest,
    SheetUpdateResponse,
)
from moxalise.services.google_sheets import GoogleSheetsService
from moxalise.core.dependencies import get_sheets_service

router = APIRouter()


@router.get("/sheets", response_model=List[str])
async def get_sheet_names(
    service: GoogleSheetsService = Depends(get_sheets_service),
):
    """
    Get the names of all sheets in the spreadsheet.

    Args:
        service: The Google Sheets service.

    Returns:
        List[str]: The names of all sheets in the spreadsheet.
    """
    try:
        return service.get_sheet_names()
    except HttpError as e:
        raise HTTPException(status_code=500, detail=f"Google Sheets API error: {str(e)}")


@router.get("/data", response_model=SheetData)
async def get_sheet_data(
    sheet_name: str = Query(..., description="Name of the sheet"),
    start_cell: str = Query(..., description="Starting cell (e.g., 'A1')"),
    end_cell: str = Query(None, description="Ending cell (e.g., 'B10')"),
    service: GoogleSheetsService = Depends(get_sheets_service),
):
    """
    Get data from a sheet.

    Args:
        sheet_name: The name of the sheet.
        start_cell: The starting cell of the range.
        end_cell: The ending cell of the range. Optional.
        service: The Google Sheets service.

    Returns:
        SheetData: The data from the sheet.
    """
    try:
        range_obj = SheetRange(
            sheet_name=sheet_name, start_cell=start_cell, end_cell=end_cell
        )
        return service.get_sheet_data(range_obj)
    except HttpError as e:
        raise HTTPException(status_code=500, detail=f"Google Sheets API error: {str(e)}")


@router.post("/update", response_model=SheetUpdateResponse)
async def update_sheet_data(
    request: SheetUpdateRequest,
    service: GoogleSheetsService = Depends(get_sheets_service),
):
    """
    Update data in a sheet.

    Args:
        request: The request containing the range and values to update.
        service: The Google Sheets service.

    Returns:
        SheetUpdateResponse: The response from the update operation.
    """
    try:
        return service.update_sheet_data(request)
    except HttpError as e:
        raise HTTPException(status_code=500, detail=f"Google Sheets API error: {str(e)}")


@router.post("/append", response_model=SheetAppendResponse)
async def append_sheet_data(
    request: SheetAppendRequest,
    service: GoogleSheetsService = Depends(get_sheets_service),
):
    """
    Append data to a sheet.

    Args:
        request: The request containing the range and values to append.
        service: The Google Sheets service.

    Returns:
        SheetAppendResponse: The response from the append operation.
    """
    try:
        return service.append_sheet_data(request)
    except HttpError as e:
        raise HTTPException(status_code=500, detail=f"Google Sheets API error: {str(e)}")


@router.delete("/clear")
async def clear_sheet_data(
    sheet_name: str = Query(..., description="Name of the sheet"),
    start_cell: str = Query(..., description="Starting cell (e.g., 'A1')"),
    end_cell: str = Query(None, description="Ending cell (e.g., 'B10')"),
    service: GoogleSheetsService = Depends(get_sheets_service),
):
    """
    Clear data from a sheet.

    Args:
        sheet_name: The name of the sheet.
        start_cell: The starting cell of the range.
        end_cell: The ending cell of the range. Optional.
        service: The Google Sheets service.

    Returns:
        dict: A message indicating the range that was cleared.
    """
    try:
        range_obj = SheetRange(
            sheet_name=sheet_name, start_cell=start_cell, end_cell=end_cell
        )
        cleared_range = service.clear_sheet_data(range_obj)
        return {"message": f"Range {cleared_range} cleared successfully"}
    except HttpError as e:
        raise HTTPException(status_code=500, detail=f"Google Sheets API error: {str(e)}")