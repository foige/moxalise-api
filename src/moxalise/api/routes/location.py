"""
API routes for location operations.

This module defines the FastAPI routes for handling browser geolocation data,
including endpoints for storing location information.
"""
from fastapi import APIRouter, Depends, Request
from typing import List, Dict, Any
from datetime import datetime, timezone, timedelta

from moxalise.models.location import LocationData, LocationResponse
from moxalise.models.spreadsheet import SheetAppendRequest, SheetRange, SheetAppendResponse
from moxalise.services.google_sheets import GoogleSheetsService
from moxalise.core.dependencies import get_sheets_service
from moxalise.core.security import hash_ip_address, sanitize_object

router = APIRouter()


@router.post("/", response_model=LocationResponse)
async def store_location(
    location_data: LocationData,
    request: Request,
    service: GoogleSheetsService = Depends(get_sheets_service),
):
    """
    Store browser geolocation data.

    This endpoint receives geolocation data from the browser and stores it
    in the 'gps_logs' Google Sheet for further analysis.
    All string inputs are sanitized to prevent XSS and other injection attacks.

    Args:
        location_data: The geolocation data from the browser.
        request: The FastAPI request object.
        service: The Google Sheets service.

    Returns:
        LocationResponse: A response indicating whether the data was stored successfully.
    """
    try:
        # Sanitize the entire location_data object to prevent injection attacks
        # Convert to dict, sanitize, and convert back to LocationData
        location_dict = location_data.model_dump()
        sanitized_dict = sanitize_object(location_dict)
        location_data = LocationData(**sanitized_dict)
        
        # Update client information in the location data
        user_agent = request.headers.get("user-agent")
        location_data.user_agent = sanitize_object(user_agent)
        
        ip_address = None
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            ip_address = forwarded_for.split(",")[0].strip()
        else:
            ip_address = request.client.host if request.client else None
        
        location_data.ip_address = hash_ip_address(ip_address)
        
        # Generate timestamp on server in GMT+4 timezone
        tbilisi_tz = timezone(timedelta(hours=4))
        server_timestamp = datetime.now(tbilisi_tz)

        # Prepare data for Google Sheets
        # Format: [timestamp, latitude, longitude, accuracy, altitude, altitude_accuracy, heading, speed, phone_number, message, user_agent, ip_address]
        values = [[
            server_timestamp.isoformat(),
            location_data.latitude,
            location_data.longitude,
            location_data.accuracy,
            location_data.altitude,
            location_data.altitude_accuracy,
            location_data.heading,
            location_data.speed,
            location_data.phone_number,
            location_data.message,
            location_data.user_agent,
            location_data.ip_address
        ]]

        # Append to the "gps_logs" sheet, starting from cell A1, with a range of 3000
        append_request = SheetAppendRequest(
            range=SheetRange(sheet_name="gps_logs", start_cell="A1", end_cell="L3000"),
            values=values,
            value_input_option="USER_ENTERED"
        )

        result = service.append_sheet_data(append_request)
        
        return LocationResponse(
            success=True,
            message=f"Location data stored successfully. Appended to {result.appended_range}."
        )
    except Exception as e:
        return LocationResponse(
            success=False,
            message=f"Failed to store location data: {str(e)}"
        )