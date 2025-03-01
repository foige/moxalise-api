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
  --role="roles/storage.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:github-actions-deployer@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"

# Add Artifact Registry permissions (needed for pushing Docker images)
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:github-actions-deployer@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/artifactregistry.admin"
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

## How It Works

The GitHub Actions workflow will:

1. Trigger automatically when you push to the `master` branch
2. Authenticate with Google Cloud using the service account key
3. Build a Docker image of your application
4. Push the image to Google Container Registry
5. Deploy the image to Google Cloud Run

### Authentication Flow

The workflow uses two GitHub Actions for Google Cloud authentication:

1. `google-github-actions/auth@v1`: Authenticates with Google Cloud using the service account key
2. `google-github-actions/setup-gcloud@v1`: Sets up the Google Cloud SDK with the authenticated credentials

You can also manually trigger the workflow from the "Actions" tab in your GitHub repository.

## Troubleshooting

If the deployment fails, check the GitHub Actions logs for error messages. Common issues include:

- Insufficient permissions for the service account
- Missing required secrets
- Docker build failures

For Cloud Run service issues, check the Cloud Run logs in the Google Cloud Console.