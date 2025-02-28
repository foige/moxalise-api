"""
Data models for spreadsheet operations.

This module defines the Pydantic models for the data structures used in
spreadsheet operations, including request and response models.
"""
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class SheetRange(BaseModel):
    """
    Model representing a range in a spreadsheet.

    Attributes:
        sheet_name: The name of the sheet.
        start_cell: The starting cell of the range (e.g., "A1").
        end_cell: The ending cell of the range (e.g., "B10"). Optional.
    """

    sheet_name: str = Field(..., description="Name of the sheet")
    start_cell: str = Field(..., description="Starting cell (e.g., 'A1')")
    end_cell: Optional[str] = Field(None, description="Ending cell (e.g., 'B10')")

    def to_a1_notation(self) -> str:
        """
        Convert the range to A1 notation.

        Returns:
            str: The range in A1 notation (e.g., "Sheet1!A1:B10").
        """
        if self.end_cell:
            return f"'{self.sheet_name}'!{self.start_cell}:{self.end_cell}"
        return f"'{self.sheet_name}'!{self.start_cell}"


class SheetData(BaseModel):
    """
    Model representing data from a spreadsheet.

    Attributes:
        range: The range in A1 notation (e.g., "Sheet1!A1:B10").
        values: The values in the range as a 2D array.
    """

    range: str = Field(..., description="Range in A1 notation")
    values: List[List[Any]] = Field(..., description="Values in the range")


class SheetUpdateRequest(BaseModel):
    """
    Model for a request to update a spreadsheet.

    Attributes:
        range: The range to update.
        values: The values to update with.
        value_input_option: How the input should be interpreted.
    """

    range: SheetRange = Field(..., description="Range to update")
    values: List[List[Any]] = Field(..., description="Values to update with")
    value_input_option: str = Field(
        "USER_ENTERED",
        description="How the input should be interpreted (RAW or USER_ENTERED)",
    )


class SheetUpdateResponse(BaseModel):
    """
    Model for a response from updating a spreadsheet.

    Attributes:
        updated_cells: The number of cells updated.
        updated_range: The range that was updated.
    """

    updated_cells: int = Field(..., description="Number of cells updated")
    updated_range: str = Field(..., description="Range that was updated")


class SheetAppendRequest(BaseModel):
    """
    Model for a request to append data to a spreadsheet.

    Attributes:
        range: The range to append to.
        values: The values to append.
        value_input_option: How the input should be interpreted.
    """

    range: SheetRange = Field(..., description="Range to append to")
    values: List[List[Any]] = Field(..., description="Values to append")
    value_input_option: str = Field(
        "USER_ENTERED",
        description="How the input should be interpreted (RAW or USER_ENTERED)",
    )


class SheetAppendResponse(BaseModel):
    """
    Model for a response from appending to a spreadsheet.

    Attributes:
        appended_cells: The number of cells appended.
        appended_range: The range that was appended to.
    """

    appended_cells: int = Field(..., description="Number of cells appended")
    appended_range: str = Field(..., description="Range that was appended to")