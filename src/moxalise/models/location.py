"""
Data models for location operations.

This module defines the Pydantic models for the data structures used in
location operations, including request and response models.
"""
from typing import Optional
from datetime import datetime, UTC, timezone, timedelta
from pydantic import BaseModel, Field


class LocationData(BaseModel):
    """
    Model representing geolocation data from a browser.

    Attributes:
        latitude: The latitude coordinate.
        longitude: The longitude coordinate.
        accuracy: The accuracy of the coordinates in meters.
        altitude: The altitude in meters above the WGS84 ellipsoid.
        altitude_accuracy: The accuracy of the altitude in meters.
        heading: The heading in degrees clockwise from true north.
        speed: The speed in meters per second.
        phone_number: The phone number of the user.
        timestamp: The time when the location was captured.
        user_agent: The user agent of the browser.
        ip_address: The IP address of the client.
    """

    latitude: float = Field(..., description="Latitude coordinate")
    longitude: float = Field(..., description="Longitude coordinate")
    accuracy: float = Field(..., description="Accuracy of the coordinates in meters")
    altitude: Optional[float] = Field(None, description="Altitude in meters above the WGS84 ellipsoid")
    altitude_accuracy: Optional[float] = Field(None, description="Accuracy of the altitude in meters")
    heading: Optional[float] = Field(None, description="Heading in degrees clockwise from true north")
    speed: Optional[float] = Field(None, description="Speed in meters per second")
    phone_number: str = Field(..., description="Phone number of the user")
    message: Optional[str] = Field(None, description="Optional message from the user")
    timestamp: Optional[datetime] = Field(None, description="Time when the location was captured")
    user_agent: Optional[str] = Field(None, description="User agent of the browser")
    ip_address: Optional[str] = Field(None, description="IP address of the client")


class LocationResponse(BaseModel):
    """
    Model for a response after storing location data.

    Attributes:
        success: Whether the location data was successfully stored.
        message: A message describing the result.
        timestamp: The time when the response was generated.
    """

    success: bool = Field(..., description="Whether the location data was successfully stored")
    message: str = Field(..., description="Message describing the result")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone(timedelta(hours=4))),
        description="Time when the response was generated in GMT+4 timezone"
    )