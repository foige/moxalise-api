"""
Moxalise API - Main entry point

This script starts the FastAPI application for the Moxalise API,
which provides endpoints for interacting with Google Spreadsheets.
"""
import uvicorn
from moxalise.api.app import create_app

app = create_app()

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)