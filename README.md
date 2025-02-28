# Moxalise API

A FastAPI application that provides endpoints for interacting with a Google spreadsheet for moxalise.ge.

## Features

- Read data from Google Sheets
- Update data in Google Sheets
- Append data to Google Sheets
- Clear data from Google Sheets
- Get sheet names from a spreadsheet

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
   
   d. Create credentials (OAuth 2.0 Client ID) for a desktop application
   
   e. Download the credentials JSON file

4. Create a `credentials` directory in the project root and place your credentials file there:

```bash
mkdir -p credentials
# Move your downloaded credentials file to credentials/credentials.json
```

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

### Health Check

- `GET /`: Check if the API is running

### Spreadsheet Operations

- `GET /api/spreadsheet/sheets`: Get all sheet names in the spreadsheet
- `GET /api/spreadsheet/data`: Get data from a sheet
- `POST /api/spreadsheet/update`: Update data in a sheet
- `POST /api/spreadsheet/append`: Append data to a sheet
- `DELETE /api/spreadsheet/clear`: Clear data from a sheet

## First-time Authentication

When you first run the application, it will attempt to authenticate with Google Sheets API. If you haven't authenticated before, it will open a browser window asking you to authorize the application. After authorization, a token file will be saved in the `credentials` directory for future use.

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