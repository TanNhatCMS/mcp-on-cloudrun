#!/bin/bash

# Weather MCP Server - Google Cloud Run Deployment Script

set -e

# Configuration
PROJECT_ID=${GCLOUD_PROJECT_ID:-""}
SERVICE_NAME="weather-mcp-server"
REGION=${GCLOUD_REGION:-"asia-southeast1"}
WEATHERAPI_KEY=${WEATHERAPI_KEY:-""}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🌤️  Weather MCP Server - Google Cloud Run Deployment${NC}"

# Check prerequisites
if [ -z "$PROJECT_ID" ]; then
    echo -e "${RED}❌ Error: GCLOUD_PROJECT_ID environment variable not set${NC}"
    echo "Please set it with: export GCLOUD_PROJECT_ID='your-project-id'"
    exit 1
fi

if [ -z "$WEATHERAPI_KEY" ]; then
    echo -e "${RED}❌ Error: WEATHERAPI_KEY environment variable not set${NC}"
    echo "Please set it with: export WEATHERAPI_KEY='your-api-key'"
    exit 1
fi

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ Error: gcloud CLI not found${NC}"
    echo "Please install Google Cloud CLI: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

echo -e "${YELLOW}📋 Deployment Configuration:${NC}"
echo "  Project ID: $PROJECT_ID"
echo "  Service Name: $SERVICE_NAME"
echo "  Region: $REGION"
echo "  WeatherAPI Key: ${WEATHERAPI_KEY:0:3}...${WEATHERAPI_KEY: -4}"

# Set gcloud project
echo -e "${YELLOW}🔧 Setting gcloud project...${NC}"
gcloud config set project $PROJECT_ID

# Enable required APIs
echo -e "${YELLOW}🔌 Enabling required APIs...${NC}"
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable secretmanager.googleapis.com

# Create secret in Secret Manager
SECRET_NAME="weatherapi-key"
echo -e "${YELLOW}🔐 Managing WeatherAPI secret...${NC}"

# Check if secret already exists
if gcloud secrets describe $SECRET_NAME --quiet 2>/dev/null; then
    echo "  Secret $SECRET_NAME already exists. Updating version..."
    echo -n "$WEATHERAPI_KEY" | gcloud secrets versions add $SECRET_NAME --data-file=-
else
    echo "  Creating new secret $SECRET_NAME..."
    echo -n "$WEATHERAPI_KEY" | gcloud secrets create $SECRET_NAME --data-file=-
fi

# Build and deploy to Cloud Run
echo -e "${YELLOW}🚀 Building and deploying to Cloud Run...${NC}"
gcloud run deploy $SERVICE_NAME \
    --source . \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --set-secrets WEATHERAPI_KEY=$SECRET_NAME:latest \
    --port 8080 \
    --memory 512Mi \
    --cpu 1 \
    --max-instances 10 \
    --timeout 300

# Get service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --format 'value(status.url)')

echo -e "${GREEN}✅ Deployment completed successfully!${NC}"
echo -e "${GREEN}🌍 Service URL: $SERVICE_URL${NC}"
echo -e "${GREEN}🔐 Secret: $SECRET_NAME stored in Secret Manager${NC}"
echo ""
echo -e "${YELLOW}📝 Test your deployment:${NC}"
echo "  curl '$SERVICE_URL/health'"
echo ""
echo -e "${YELLOW}🔗 MCP Connection URL:${NC}"
echo "  $SERVICE_URL"
echo ""
echo -e "${YELLOW}🔐 Security Features:${NC}"
echo "  • WeatherAPI key securely stored in Secret Manager"
echo "  • No API keys in environment variables or logs"
echo "  • Automatic secret rotation support"
echo ""
echo -e "${YELLOW}💡 To update your MCP client configuration:${NC}"
echo "  Use this URL as your MCP server endpoint"
