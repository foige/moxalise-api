#!/bin/bash
# Script to run the data transfer job locally for testing

set -e

echo "Running data transfer job locally..."

# Make the script executable if it's not already
chmod +x ./src/moxalise/scripts/job_runner.py
chmod +x ./src/moxalise/scripts/transfer_data.py

# Run the job
python -m moxalise.scripts.job_runner run transfer_data

echo "Job completed!"