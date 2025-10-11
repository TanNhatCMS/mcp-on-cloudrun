# Weather MCP Server on Google Cloud Run 🌤️

A Model Context Protocol (MCP) server that provides weather information for Australian cities and worldwide locations using WeatherAPI.com.

## Features

- 🌡️ **Current Weather**: Get real-time weather conditions for any city
- 📊 **Weather Forecasts**: Get 1-3 day weather forecasts  
- 🇦🇺 **Australian Cities**: Optimized for Sydney, Melbourne, Brisbane, Perth, Adelaide, Darwin, Canberra
- 🌍 **Global Coverage**: Works with cities worldwide
- ☁️ **Cloud Deployed**: Ready for Google Cloud Run deployment

## Available Tools

### `get_current_weather(city: str)`
Get current weather conditions including:
- Temperature (Celsius/Fahrenheit)
- Feels-like temperature
- Humidity, wind speed/direction
- Atmospheric pressure
- UV index and visibility
- Current conditions

### `get_forecast(city: str, days: int = 3)`
Get weather forecast including:
- Daily high/low temperatures
- Weather conditions
- Chance of rain
- Maximum wind speeds
- UV index


## Local Development

### Prerequisites

1. **WeatherAPI Key**: Get free API key from [weatherapi.com](https://www.weatherapi.com/signup.aspx)
2. **Python 3.10+**: Required for the application
3. **Dependencies**: Install via `pip install -e .`

### Setup

```bash
# Clone and navigate to project
cd /path/to/mcp-server

# Set your WeatherAPI key
export WEATHERAPI_KEY="your_api_key_here"

# Install dependencies
pip install -e .

# Run locally
python weather.py
```

## Google Cloud Run Deployment

### Prerequisites

1. **Google Cloud Account**: Set up billing and project
2. **gcloud CLI**: Install [Google Cloud CLI](https://cloud.google.com/sdk/docs/install)
3. **WeatherAPI Key**: From [weatherapi.com](https://www.weatherapi.com/signup.aspx)

### Quick Deployment

```bash
# Set required environment variables
export GCLOUD_PROJECT_ID="your-google-cloud-project-id"
export WEATHERAPI_KEY="your_weatherapi_key_here"
export GCLOUD_REGION="us-central1"  # Optional, defaults to us-central1

# Run deployment script
./deploy.sh
```

### Manual Deployment

```bash
# Set gcloud project
gcloud config set project YOUR_PROJECT_ID

# Enable required APIs
gcloud services enable cloudbuild.googleapis.com run.googleapis.com secretmanager.googleapis.com

# Create secret in Secret Manager
echo -n "your_api_key_here" | gcloud secrets create weatherapi-key --data-file=-

# Deploy to Cloud Run
gcloud run deploy weather-mcp-server \
    --source . \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --set-secrets WEATHERAPI_KEY=weatherapi-key:latest \
    --port 8080 \
    --memory 512Mi \
    --cpu 1 \
    --max-instances 10
```

## Usage Examples

### Australian Cities
- "What's the current weather in Sydney?"
- "Get the forecast for Melbourne"
- "Show me weather conditions in Brisbane"
- "What's the 3-day forecast for Perth?"

### International Cities  
- "Current weather in London"
- "Tokyo weather forecast"
- "New York conditions"

## Configuration

### Environment Variables

- `WEATHERAPI_KEY`: **Required** - Your WeatherAPI.com API key (stored in Secret Manager when deployed)
- `PORT`: Optional - Server port (default: 8080)
- `GCLOUD_PROJECT_ID`: For deployment - Your Google Cloud project ID
- `GCLOUD_REGION`: For deployment - Deployment region (default: us-central1)

### Secret Management

**Production Deployment (Google Cloud Run):**
- WeatherAPI key is securely stored in Google Cloud Secret Manager
- No API keys in environment variables, logs, or container images
- Supports automatic secret rotation
- Access controlled via IAM permissions

**Managing Secrets:**
```bash
# Update the WeatherAPI key
echo -n "new_api_key_here" | gcloud secrets versions add weatherapi-key --data-file=-

# View secret metadata (not the actual secret value)
gcloud secrets describe weatherapi-key

# List secret versions
gcloud secrets versions list weatherapi-key
```

## API Limits

**WeatherAPI.com Free Tier:**
- 1 million API calls per month
- 3-day forecasts
- Current weather conditions
- No credit card required

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   MCP Client    │───▶│  Weather Server  │───▶│  WeatherAPI.com │
│                 │    │ (Google Cloud    │    │                 │
│                 │    │  Run)            │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## Client Connection

```console
cd mcp-client
export GOOGLE_API_KEY=your_actual_api_key
uv run python client.py {YOUR-mcp-server-endpoint (Cloud Run Url)}
```



## Security & Support

### Security Features
- 🔐 **Secret Manager Integration**: API keys stored securely, never in code or logs
- 🛡️ **IAM Controlled Access**: Fine-grained permissions for secret access
- 🔄 **Secret Rotation**: Support for seamless API key updates
- 🌐 **HTTPS Only**: All communications encrypted in transit


## License

MIT License - see LICENSE file for details.
