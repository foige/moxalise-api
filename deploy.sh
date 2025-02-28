#!/bin/bash
set -e

# Configuration
# Get PROJECT_ID from environment variable
PROJECT_ID=${PROJECT_ID:-""}
REGION="europe-west3"
SERVICE_NAME="moxalise-api"
IMAGE_NAME="gcr.io/$PROJECT_ID/$SERVICE_NAME"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${YELLOW}Google Cloud SDK (gcloud) is not installed. Please install it first:${NC}"
    echo "https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${YELLOW}Docker is not installed. Please install it first:${NC}"
    echo "https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if PROJECT_ID is set
if [ -z "$PROJECT_ID" ]; then
    echo -e "${YELLOW}Please set your Google Cloud PROJECT_ID in this script.${NC}"
    exit 1
fi

# Ensure we're logged in to gcloud
echo -e "${GREEN}Checking gcloud authentication...${NC}"
gcloud auth print-access-token &> /dev/null || gcloud auth login

# Set the project
echo -e "${GREEN}Setting gcloud project to $PROJECT_ID...${NC}"
gcloud config set project $PROJECT_ID

# Configure Docker to use gcloud as a credential helper
echo -e "${GREEN}Configuring Docker to use gcloud credentials...${NC}"
gcloud auth configure-docker

# Build the Docker image
echo -e "${GREEN}Building Docker image for linux/amd64 platform...${NC}"
docker build --platform linux/amd64 -t $IMAGE_NAME .

# Push the image to Google Container Registry
echo -e "${GREEN}Pushing image to Google Container Registry...${NC}"
docker push $IMAGE_NAME

# Deploy to Cloud Run
echo -e "${GREEN}Deploying to Cloud Run...${NC}"
gcloud run deploy $SERVICE_NAME \
  --image $IMAGE_NAME \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated

echo -e "${GREEN}Deployment completed successfully!${NC}"
echo -e "Your service is available at: $(gcloud run services describe $SERVICE_NAME --platform managed --region $REGION --format 'value(status.url)')"