"""
Configuration settings for the Moxalise API.

This module defines the settings for the application, including environment
variables for connecting to Google Sheets API.
"""
import os
from typing import List

from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings.

    Attributes:
        PROJECT_NAME: The name of the project.
        PROJECT_DESCRIPTION: A brief description of the project.
        VERSION: The version of the application.
        API_PREFIX: The prefix for all API endpoints.
        CORS_ORIGINS: List of origins that are allowed to make cross-origin requests.
        GOOGLE_SHEETS_CREDENTIALS_FILE: Path to the Google Sheets credentials file.
        GOOGLE_SHEETS_TOKEN_FILE: Path to the Google Sheets token file.
        GOOGLE_SHEETS_SPREADSHEET_ID: The ID of the Google Spreadsheet to interact with.
    """

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=True, extra="allow"
    )

    # Application settings
    PROJECT_NAME: str = "Moxalise API"
    PROJECT_DESCRIPTION: str = "API for interacting with Moxalise Google Spreadsheet"
    VERSION: str = "0.1.0"
    API_PREFIX: str = "/api"
    DEBUG: bool = False
    
    # CORS settings
    CORS_ORIGINS: List[str] = []  # Default to empty list

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: str | List[str]) -> List[str]:
        """
        Parse and validate CORS origins.

        Args:
            v: The CORS origins as a string or list of strings.

        Returns:
            List[str]: The validated CORS origins.
        """
        if isinstance(v, str):
            if v == "*":
                return ["*"]
            if "," in v:
                return [origin.strip() for origin in v.split(",") if origin.strip()]
            return [v]
        return v

    # Google Sheets settings
    GOOGLE_SHEETS_SPREADSHEET_ID: str = ""
    
    # Security settings
    IP_HASH_SALT: str = ""


# Create settings instance
settings = Settings()