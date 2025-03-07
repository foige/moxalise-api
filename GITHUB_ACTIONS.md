# GitHub Actions Deployment for Moxalise API

This guide explains how to set up automatic deployment to Google Cloud Run using GitHub Actions.

## Prerequisites

Before setting up GitHub Actions deployment, ensure you have:

1. A Google Cloud project with billing enabled
2. Google Sheets API enabled in your project
3. A GitHub repository containing your Moxalise API code

## Setup Steps

### 1. Create a Service Account for Deployment

Create a service account in Google Cloud that GitHub Actions will use to deploy your application:

```bash
# Set your project ID as a variable (replace with your actual project ID)
export PROJECT_ID="your-project-id"

# Create a new service account
gcloud iam service-accounts create github-actions-deployer \
  --display-name="GitHub Actions Deployer"

# Grant necessary permissions to the service account
# Note: Make sure to wait a few seconds after creating the service account before adding permissions
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:github-actions-deployer@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:github-actions-deployer@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:github-actions-deployer@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/iam.workloadIdentityUser"

# Add Artifact Registry permissions (needed for pushing Docker images)
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:github-actions-deployer@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/artifactregistry.writer"
```

### 2. Create and Download Service Account Key

```bash
gcloud iam service-accounts keys create key.json \
  --iam-account=github-actions-deployer@$PROJECT_ID.iam.gserviceaccount.com
```

This will download a file named `key.json` containing the service account credentials.

### 3. Add GitHub Secrets

In your GitHub repository:

1. Go to Settings > Secrets and variables > Actions
2. Add the following secrets:
   - `GCP_PROJECT_ID`: Your Google Cloud project ID
   - `GCP_SA_KEY`: The entire content of the `key.json` file (including all curly braces and quotes)
   - `GOOGLE_SHEETS_SPREADSHEET_ID`: The ID of your Google Spreadsheet
   - `CORS_ORIGINS`: Allowed CORS origins (comma-separated)
   - `IP_HASH_SALT`: Salt used for hashing IP addresses

### 4. Configure Runtime Service Account Permissions

The Cloud Run service will use the default compute service account. Make sure it has permission to access Google Sheets:

```bash
# Get the default compute service account
SERVICE_ACCOUNT=$(gcloud iam service-accounts list --filter="name:compute@developer.gserviceaccount.com" --format="value(email)")

# Grant the service account permission to access Google Sheets
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SERVICE_ACCOUNT" \
  --role="roles/sheets.editor"
```

### 5. Set Environment Variables in Cloud Run

After the first deployment, set the required environment variables in the Cloud Run console:

1. Go to the [Cloud Run console](https://console.cloud.google.com/run)
2. Click on your service (moxalise-api)
3. Go to the "Variables & Secrets" tab
4. Click "Edit and deploy new revision"
5. Add the environment variables from your `.env` file
6. Click "Deploy"

## GitHub Actions Workflows

### CI Workflow (ci.yml)

The CI workflow is responsible for running tests to ensure code quality:

1. **When it runs:**
   - Automatically on all pull requests to `main` or `master` branches
   - Automatically on all pushes to `main` or `master` branches

2. **What it does:**
   - Checks out the code repository
   - Sets up Python with the correct version
   - Installs project dependencies using Poetry
   - Sets up Google Cloud credentials for accessing Google Sheets API
   - Runs tests using pytest

3. **Benefits:**
   - Ensures all code changes in pull requests are automatically tested before merging
   - Catches issues early in the development process
   - Maintains code quality standards
   - Provides feedback to developers before code review

### Deployment Workflows

The GitHub Actions workflows handle two deployment processes:

### Main Service Deployment

The main deployment workflow (`deploy.yml`) will:

1. Trigger automatically when you push to the `master` branch
2. Authenticate with Google Cloud using the service account key
3. Create Artifact Registry repository if it doesn't exist yet
4. Build a Docker image of your application
5. Push the image to Artifact Registry (europe-west3-docker.pkg.dev)
6. Deploy the image to Google Cloud Run

### Job Deployment

The job deployment workflow (`deploy-job.yml`) will:

1. Trigger automatically after the main deployment workflow completes successfully
2. Deploy a Cloud Run job using the same Docker image that was built by the main workflow
3. Set up a Cloud Scheduler job to run the Cloud Run job on a regular schedule (every 5 minutes)

This ensures that both the service and the scheduled jobs use the same codebase and configuration.

### Authentication Flow

Both workflows use the same GitHub Actions for Google Cloud authentication:

1. `google-github-actions/auth@v1`: Authenticates with Google Cloud using the service account key
2. `google-github-actions/setup-gcloud@v1`: Sets up the Google Cloud SDK with the authenticated credentials

You can also manually trigger either workflow from the "Actions" tab in your GitHub repository.

## Troubleshooting

If the deployment fails, check the GitHub Actions logs for error messages. Common issues include:

- Insufficient permissions for the service account
- Missing required secrets
- Docker build failures

For Cloud Run service issues, check the Cloud Run logs in the Google Cloud Console.