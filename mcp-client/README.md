# Weather Agent - Google ADK with Remote MCP Server

AI agent built with **Google Agent Development Kit (ADK)** that uses remote tools from an **MCP server deployed on Cloud Run**.

## Architecture

```
┌─────────────────┐      ┌──────────────────┐      ┌─────────────────────┐
│   User Browser  │ ───> │  ADK Web UI      │ ───> │  Weather Agent      │
│   localhost:8000│      │  (Google ADK)    │      │  (Agent with MCP)   │
└─────────────────┘      └──────────────────┘      └─────────────────────┘
                                                              │
                                                              │ HTTP/SSE
                                                              ▼
                                                    ┌─────────────────────┐
                                                    │  MCP Server         │
                                                    │  Cloud Run          │
                                                    │  FastMCP + Tools    │
                                                    └─────────────────────┘
                                                              │
                                                              ▼
                                                    ┌─────────────────────┐
                                                    │  WeatherAPI.com     │
                                                    └─────────────────────┘
```

## Features

✅ **Remote MCP Tools**: Connects to MCP server deployed on Google Cloud Run  
✅ **3 Weather Tools**:
   - `get_current_weather(city)` - Real-time weather conditions
   - `get_forecast(city, days)` - Weather forecast up to 3 days
   - `health_check()` - Server health verification

✅ **Web Interface**: Beautiful UI via ADK web  
✅ **Streaming Responses**: Real-time AI responses  
✅ **Production Ready**: Deployed on Google Cloud infrastructure

## Quick Start

### 1. Prerequisites

```bash
# Required
- Python 3.12+
- Google API Key (for Gemini)
- Internet connection (to reach Cloud Run MCP server)

# The MCP server is already deployed at:
# https://weather-mcp-server-oze7nwnjba-as.a.run.app
```

### 2. Setup Environment

```bash
cd mcp-client

# Create .env file with your Google API key
echo "GOOGLE_API_KEY=your_google_api_key_here" > .env

# Get free key from: https://aistudio.google.com/apikey
```

### 3. Install Dependencies

```bash
# If using uv (recommended)
uv sync

# Or using pip
pip install google-adk google-generativeai python-dotenv
```

### 4. Run the Agent

```bash
# Start ADK web interface
uv run adk web

# Or with python
python -m adk web
```

### 5. Use the Agent

1. Open browser: http://localhost:8000
2. Select `weather_agent` from dropdown
3. Ask questions like:
   - "What's the weather in Brisbane?"
   - "Give me a 3-day forecast for Tokyo"
   - "How's the weather in New York?"

## Project Structure

```
mcp-client/
├── weather_agent/          # ADK Agent directory
│   ├── agent.py           # Main agent with MCP connection
│   └── __init__.py        # Package initialization
├── client.py              # Standalone MCP client (optional)
├── pyproject.toml         # Python dependencies
├── .env                   # Environment variables (create this)
└── README.md             # This file
```

## Configuration

### Remote MCP Server

The agent connects to:
```
URL: https://weather-mcp-server-oze7nwnjba-as.a.run.app
Protocol: HTTP with Server-Sent Events (SSE)
Tools: 3 weather-related functions
```

### Agent Configuration

In `weather_agent/agent.py`:

```python
MCP_SERVER_URL = "https://weather-mcp-server-oze7nwnjba-as.a.run.app"

connection_params = StreamableHTTPConnectionParams(
    url=MCP_SERVER_URL,
    timeout=30.0,
)

root_agent = Agent(
    name="weather_agent",
    model="gemini-2.5-flash",
    tools=[weather_tools],
)
```

## Troubleshooting

### Agent won't connect to MCP server

**Check logs in terminal:**
```bash
uv run adk web
# Watch for connection messages
```

**Common issues:**
1. **404 errors**: MCP server HTTP endpoint configuration
   - Check if server is deployed: `gcloud run services list`
   - Verify URL in agent.py matches deployed service

2. **Timeout errors**: Cloud Run cold start
   - First request may take longer
   - Try again after 30 seconds

3. **Session terminated**: MCP protocol mismatch
   - Ensure FastMCP version compatibility
   - Check server logs: `gcloud run services logs read weather-mcp-server`

### Fallback Mode

If MCP connection fails, agent runs in fallback mode without tools.
Fix connection and restart ADK web.

## Advanced Usage

### Using CLI Client

For direct MCP interaction without ADK:

```bash
# Connect to local MCP server
python client.py ../mcp-server/weather.py

# Connect to remote MCP server
python client.py https://weather-mcp-server-oze7nwnjba-as.a.run.app/mcp
```

### Environment Variables

Create `.env` file:
```bash
# Required
GOOGLE_API_KEY=your_gemini_api_key

# Optional (for direct API usage)
WEATHERAPI_KEY=your_weatherapi_key
```

## API Reference

### Available Tools

**1. get_current_weather**
```python
Args:
    city (str): City name (e.g., "Brisbane", "Tokyo", "London")
    
Returns:
    str: Current weather conditions including:
         - Temperature (°C/°F)
         - Feels like temperature
         - Weather condition
         - Humidity, Wind, Pressure
         - UV Index, Visibility
```

**2. get_forecast**
```python
Args:
    city (str): City name
    days (int): Number of days (1-3, default: 3)
    
Returns:
    str: Weather forecast with daily:
         - High/Low temperatures
         - Weather conditions
         - Chance of rain
         - Max wind speed
         - UV Index
```

**3. health_check**
```python
Args: None

Returns:
    str: Server status message
```

## Deployment Info

### MCP Server (Already Deployed)
- **Platform**: Google Cloud Run
- **Region**: asia-southeast1
- **URL**: https://weather-mcp-server-oze7nwnjba-as.a.run.app
- **Framework**: FastMCP
- **Data Source**: WeatherAPI.com

### Local Development
- **ADK Web**: http://localhost:8000
- **Framework**: Google ADK
- **LLM**: Gemini 2.5 Flash

## Resources

- [Google ADK Documentation](https://google.github.io/adk-docs/)
- [MCP Specification](https://modelcontextprotocol.io/)
- [FastMCP GitHub](https://github.com/jlowin/fastmcp)
- [WeatherAPI](https://www.weatherapi.com/)

## License

MIT License - See parent directory for details.

