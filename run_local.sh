#!/bin/bash
set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
IMAGE_NAME="moxalise-api-local"
CONTAINER_NAME="moxalise-api-container"
PORT=8080

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${YELLOW}Docker is not installed. Please install it first:${NC}"
    echo "https://docs.docker.com/get-docker/"
    exit 1
fi

# Stop and remove existing container if it exists
if docker ps -a | grep -q $CONTAINER_NAME; then
    echo -e "${YELLOW}Stopping and removing existing container...${NC}"
    docker stop $CONTAINER_NAME >/dev/null 2>&1 || true
    docker rm $CONTAINER_NAME >/dev/null 2>&1 || true
fi

# Build the Docker image
echo -e "${GREEN}Building Docker image...${NC}"
docker build -t $IMAGE_NAME .

# Check if GOOGLE_SHEETS_SPREADSHEET_ID is set
if [ -z "$GOOGLE_SHEETS_SPREADSHEET_ID" ]; then
    echo -e "${YELLOW}Warning: GOOGLE_SHEETS_SPREADSHEET_ID environment variable is not set.${NC}"
    echo -e "${YELLOW}Some functionality may not work correctly.${NC}"
    echo -e "${YELLOW}You can set it with: export GOOGLE_SHEETS_SPREADSHEET_ID=your-spreadsheet-id${NC}"
    echo ""
fi

# Run the container
echo -e "${GREEN}Running container...${NC}"
docker run --name $CONTAINER_NAME \
    -p $PORT:$PORT \
    -e GOOGLE_SHEETS_SPREADSHEET_ID=${GOOGLE_SHEETS_SPREADSHEET_ID:-""} \
    -d $IMAGE_NAME

echo -e "${GREEN}Container is running!${NC}"
echo -e "You can access the API at: http://localhost:$PORT"
echo -e "API documentation is available at: http://localhost:$PORT/docs"
echo ""
echo -e "To view logs: ${YELLOW}docker logs $CONTAINER_NAME${NC}"
echo -e "To stop the container: ${YELLOW}docker stop $CONTAINER_NAME${NC}"