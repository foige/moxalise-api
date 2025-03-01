# Cloud Run Job Deployment Guide

This guide explains how to deploy the data transfer job to Google Cloud Run.

## Overview

The job transfers data from "დაზარალებულთა შევსებული ინფორმაცია" to "დაზარალებულთა სია" tab in the Google Spreadsheet. It runs every 5 minutes and ensures that only one instance runs at a time. The job includes time tracking to ensure graceful shutdown before the task timeout is reached.

## Requirements

- Google Cloud project with Cloud Run, Cloud Scheduler, and Artifact Registry enabled
- Google Cloud SDK installed locally
- Default service account with necessary permissions:
  - Cloud Run Admin
  - Artifact Registry Writer
  - Cloud Scheduler Admin
  - Google Sheets API access

## Deployment Steps

1. **Setup Google Cloud environment variables**:

```bash
export PROJECT_ID=$(gcloud config get-value project)
export REGION=europe-west1
export REPOSITORY=moxalise-containers
export IMAGE=moxalise-api
export TAG=latest
export JOB_NAME=moxalise-data-transfer
export SCHEDULER_NAME=moxalise-data-transfer-scheduler
export SPREADSHEET_ID=<your-spreadsheet-id>  # Replace with your actual spreadsheet ID
```

2. **Create Artifact Registry repository** (if not already created):

```bash
gcloud artifacts repositories create $REPOSITORY \
    --repository-format=docker \
    --location=$REGION \
    --description="Moxalise container repository"
```

3. **Build and deploy using Cloud Build**:

```bash
gcloud builds submit --config=cloudbuild-job.yaml --substitutions=_SPREADSHEET_ID=$SPREADSHEET_ID
```

This will:
- Build the Docker image
- Push it to Artifact Registry
- Create the Cloud Run job
- Create a Cloud Scheduler job to run it every 5 minutes

## Concurrency Control

The job is configured with `--max-instances=1` to ensure only one instance runs at a time. This prevents duplicate data processing if a previous job is still running when a new scheduled execution is triggered.

## Graceful Shutdown

The job implements graceful shutdown to handle Cloud Run timeout scenarios:

1. The job monitors execution time and will exit cleanly after finishing the current row if approaching the 4-minute mark
2. The task timeout is set to 5 minutes, giving the job 1 minute of buffer to complete the current operation
3. Signal handlers are in place to catch termination signals and gracefully shut down
4. Each row is processed atomically - a row is either fully processed or not processed at all

## Manual Execution

To manually trigger the job:

```bash
gcloud run jobs execute $JOB_NAME --region=$REGION
```

## Viewing Logs

To view the job execution logs:

```bash
gcloud logging read "resource.type=cloud_run_job AND resource.labels.job_name=$JOB_NAME" --limit=50
```

## Job Configuration Details

The job configuration includes:
- Memory: 1GB
- CPU: 1
- Max retries: 3
- Task timeout: 5 minutes
- Cloud Scheduler: Runs every 5 minutes
- Execution time limit: 4 minutes (self-imposed for graceful shutdown)

## Troubleshooting

If you encounter issues:

1. Check the job execution logs
2. Verify that the service account has the required permissions
3. Ensure the Google Sheets API is enabled and the credentials are properly configured
4. Check that the spreadsheet ID is correctly set in the environment variables