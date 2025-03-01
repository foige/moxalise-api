#!/bin/bash
# Entrypoint script for Moxalise API container
# It can either start the API server or run a scheduled job

set -e

# Make scripts executable
chmod +x /app/src/moxalise/scripts/*.py

# If JOB_NAME is set, run the specified job
if [ -n "$JOB_NAME" ]; then
  echo "Running job: $JOB_NAME"
  python -m moxalise.scripts.job_runner run "$JOB_NAME"
else
  # Otherwise, start the API server
  echo "Starting API server"
  uvicorn main:app --host 0.0.0.0 --port 8080
fi