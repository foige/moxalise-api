# Moxalise API

A FastAPI application that provides endpoints for collecting and storing volunteer geolocation data for moxalise.ge. The application stores location data from volunteers in a Google Sheet for coordination and management purposes.

## Features

- Store browser geolocation data in Google Sheets
- Timezone-aware timestamps (GMT+4)

> **Note:** Spreadsheet routes are currently disabled. The API focuses exclusively on location data collection.

## Prerequisites

- Python 3.12 or higher
- Poetry (for dependency management)
- Google Cloud Platform account with Google Sheets API enabled
- Google API credentials

## Setup

1. Clone the repository:

```bash
git clone https://github.com/yourusername/moxalise-api.git
cd moxalise-api
```

2. Install dependencies using Poetry:

```bash
poetry install
```

3. Set up Google Sheets API:

   a. Go to the [Google Cloud Console](https://console.cloud.google.com/)
   
   b. Create a new project or select an existing one
   
   c. Enable the Google Sheets API for your project
   
   d. Set up Application Default Credentials:
      - For local development: `gcloud auth application-default login`
      - For production: Create a service account with appropriate permissions

5. Create a `.env` file based on the provided `.env.example`:

```bash
cp .env.example .env
# Edit .env with your specific configuration
```

6. Update the `GOOGLE_SHEETS_SPREADSHEET_ID` in your `.env` file with the ID of your Google Spreadsheet.

## Running the Application

Start the development server:

```bash
poetry run python main.py
```

Or using uvicorn directly:

```bash
poetry run uvicorn main:app --reload
```

The API will be available at http://localhost:8000.

## API Documentation

Once the application is running, you can access the API documentation at:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Endpoints

All API endpoints are public and do not require authentication.

### Health Check

- `GET /`: Check if the API is running

### Location Operations

- `POST /api/location/`: Store browser geolocation data

The location endpoint collects the following data:
- Geographic coordinates (latitude, longitude)
- Accuracy of coordinates
- Optional altitude data
- Optional speed and heading information
- Phone number of the volunteer
- Optional message from the volunteer
- Timestamp (automatically set to GMT+4 timezone)

> **Note:** Spreadsheet operations are currently disabled. The API code still contains the following endpoints, but they are not accessible:
> - `GET /api/spreadsheet/sheets`: Get all sheet names in the spreadsheet
> - `GET /api/spreadsheet/data`: Get data from a sheet
> - `POST /api/spreadsheet/update`: Update data in a sheet
> - `POST /api/spreadsheet/append`: Append data to a sheet
> - `DELETE /api/spreadsheet/clear`: Clear data from a sheet


## Development

### Project Structure

```
moxalise-api/
├── credentials/           # Google API credentials
├── src/
│   └── moxalise/          # Main package
│       ├── api/           # API routes and application
│       ├── core/          # Core functionality
│       ├── models/        # Data models
│       └── services/      # Service implementations
├── .env                   # Environment variables
├── .env.example           # Example environment variables
├── main.py                # Application entry point
├── pyproject.toml         # Poetry configuration
└── README.md              # Project documentation
```

### Testing

Run tests using pytest:

```bash
poetry run pytest
```

## License

[MIT](LICENSE)