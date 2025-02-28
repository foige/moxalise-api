# Deploying Moxalise API to Google Cloud Run

This guide provides step-by-step instructions for deploying the Moxalise API to Google Cloud Run.

## Prerequisites

Before you begin, make sure you have the following:

1. [Google Cloud SDK](https://cloud.google.com/sdk/docs/install) installed and configured
2. [Docker](https://docs.docker.com/get-docker/) installed
3. A Google Cloud project with billing enabled
4. Google Sheets API enabled in your Google Cloud project
5. The ID of the Google Spreadsheet you want to interact with

## Setup Google Cloud Project

1. Create a new Google Cloud project or use an existing one:
   ```bash
   gcloud projects create [PROJECT_ID] --name="Moxalise API"
   # or use an existing project
   gcloud config set project [PROJECT_ID]
   ```

2. Enable the required APIs:
   ```bash
   gcloud services enable cloudbuild.googleapis.com
   gcloud services enable run.googleapis.com
   gcloud services enable sheets.googleapis.com
   ```

## Configure Service Account Permissions

The default service account used by Cloud Run needs permission to access Google Sheets:

1. Get the default service account email:
   ```bash
   SERVICE_ACCOUNT=$(gcloud iam service-accounts list --filter="name:compute@developer.gserviceaccount.com" --format="value(email)")
   ```

2. Grant the service account the necessary permissions:
   ```bash
   # Grant the service account permission to access Google Sheets
   gcloud projects add-iam-policy-binding [PROJECT_ID] \
     --member="serviceAccount:$SERVICE_ACCOUNT" \
     --role="roles/sheets.editor"
   ```

## Deployment

1. Set your Google Cloud project ID as an environment variable:
   ```bash
   export PROJECT_ID="your-project-id"
   ```

2. Run the deployment script:
   ```bash
   ./deploy.sh
   ```

The script will:
- Build a Docker image of your application
- Push the image to Google Container Registry
- Deploy the image to Google Cloud Run
- Configure the necessary environment variables

## Verify Deployment

After deployment, the script will output the URL of your deployed service. You can verify the deployment by visiting:

- The service URL: `https://moxalise-api-[hash].a.run.app`
- The health check endpoint: `https://moxalise-api-[hash].a.run.app/`
- The API documentation: `https://moxalise-api-[hash].a.run.app/docs`

## Troubleshooting

If you encounter issues with the deployment:

1. Check the Cloud Run logs:
   ```bash
   gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=moxalise-api" --limit=50
   ```

2. Verify the service account has the correct permissions:
   ```bash
   gcloud projects get-iam-policy [PROJECT_ID] \
     --flatten="bindings[].members" \
     --format="table(bindings.role,bindings.members)" \
     --filter="bindings.members:$SERVICE_ACCOUNT"
   ```

3. Make sure the Google Sheets API is enabled:
   ```bash
   gcloud services list --enabled --filter="name:sheets.googleapis.com"
   ```

4. If you encounter an "exec format error" during deployment, it's likely due to an architecture mismatch. This happens when building on Apple Silicon (M1/M2/M3) Macs and deploying to Cloud Run's x86_64 infrastructure. The deployment script already includes the `--platform linux/amd64` flag to address this issue, but ensure Docker has emulation support enabled:
   ```bash
   # Check if QEMU is installed for cross-platform emulation
   docker run --rm --privileged multiarch/qemu-user-static --reset -p yes
   ```

## Updating the Deployment

To update your deployment after making changes to the code:

1. Run the deployment script again:
   ```bash
   ./deploy.sh
   ```

Cloud Run will automatically route traffic to the new revision once it's ready.

## Setting Environment Variables

After deploying your service, you need to set the required environment variables:

1. **Using the Google Cloud Console:**
   - Go to the [Cloud Run console](https://console.cloud.google.com/run)
   - Click on your service (moxalise-api)
   - Go to the "Variables & Secrets" tab
   - Click "Edit and deploy new revision"
   - Add the environment variable:
     - Name: `GOOGLE_SHEETS_SPREADSHEET_ID`
     - Value: Your Google Spreadsheet ID
   - Click "Deploy"

2. **Using gcloud CLI:**
   ```bash
   gcloud run services update moxalise-api \
     --region=europe-west3 \
     --set-env-vars="GOOGLE_SHEETS_SPREADSHEET_ID=your-spreadsheet-id"
   ```

This will create a new revision of your service with the updated environment variables.