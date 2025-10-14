from typing import Any
import asyncio
import httpx
import os
import logging
from mcp.server.fastmcp import FastMCP

# Configure logging based on environment
if not os.getenv("PORT"):  # Local development
    # Suppress noisy INFO logs during local development
    logging.getLogger("mcp.server").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING) 
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    
# Initialize FastMCP server
mcp = FastMCP("weather")

# Constants
WEATHERAPI_BASE = "https://api.weatherapi.com/v1"
USER_AGENT = "weather-app/1.0"

# Get API key from environment variable
API_KEY = os.getenv("WEATHERAPI_KEY")

async def make_weather_request(endpoint: str, params: dict[str, str]) -> dict[str, Any] | None:
    """Make a request to the WeatherAPI with proper error handling."""
    # Check if API key is set
    if not API_KEY:
        print("ERROR: WeatherAPI key not set. Please set WEATHERAPI_KEY environment variable.")
        return None
        
    headers = {
        "User-Agent": USER_AGENT,
    }
    # Add API key to parameters
    params["key"] = API_KEY
    
    url = f"{WEATHERAPI_BASE}/{endpoint}"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, params=params, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            print(f"HTTP Error {e.response.status_code}: {e.response.text}")
            return None
        except httpx.RequestError as e:
            print(f"Request Error: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error: {e}")
            return None

@mcp.tool()
async def get_current_weather(city: str) -> str:
    """Get current weather conditions for a city.

    Args:
        city: City name (e.g., "Sydney", "Melbourne", "Perth", "Brisbane", "Canberra")
    """
    params = {
        "q": city,
        "aqi": "no"
    }
    
    data = await make_weather_request("current.json", params)

    if not data:
        if not API_KEY:
            return f"❌ WeatherAPI key not configured. Please set WEATHERAPI_KEY environment variable with your API key from weatherapi.com"
        return f"Unable to fetch current weather data for {city}. Please check the city name and API key configuration."

    current = data["current"]
    location = data["location"]
    
    return f"""
Current Weather for {location['name']}, {location['region']}, {location['country']}:

Temperature: {current['temp_c']}°C ({current['temp_f']}°F)
Feels like: {current['feelslike_c']}°C ({current['feelslike_f']}°F)
Condition: {current['condition']['text']}
Humidity: {current['humidity']}%
Wind: {current['wind_kph']} km/h ({current['wind_mph']} mph) {current['wind_dir']}
Pressure: {current['pressure_mb']} mb
UV Index: {current['uv']}
Visibility: {current['vis_km']} km

Last updated: {current['last_updated']}
"""

@mcp.tool()
async def get_forecast(city: str, days: int = 3) -> str:
    """Get weather forecast for a city.

    Args:
        city: City name (e.g., "Sydney", "Melbourne", "Perth", "Brisbane")
        days: Number of days to forecast (1-3 for free tier, max 10 for paid)
    """
    # Limit days to 3 for free tier
    days = min(days, 3)
    
    params = {
        "q": city,
        "days": str(days),
        "aqi": "no",
        "alerts": "no"
    }
    
    data = await make_weather_request("forecast.json", params)

    if not data:
        if not API_KEY:
            return f"❌ WeatherAPI key not configured. Please set WEATHERAPI_KEY environment variable with your API key from weatherapi.com"
        return f"Unable to fetch forecast data for {city}. Please check the city name and API key configuration."

    location = data["location"]
    forecast_days = data["forecast"]["forecastday"]
    
    forecasts = []
    forecasts.append(f"Weather Forecast for {location['name']}, {location['region']}, {location['country']}:")
    
    for day in forecast_days:
        day_data = day["day"]
        date = day["date"]
        
        forecast = f"""
{date}:
High: {day_data['maxtemp_c']}°C ({day_data['maxtemp_f']}°F)
Low: {day_data['mintemp_c']}°C ({day_data['mintemp_f']}°F)
Condition: {day_data['condition']['text']}
Chance of Rain: {day_data['daily_chance_of_rain']}%
Max Wind: {day_data['maxwind_kph']} km/h
UV Index: {day_data['uv']}
"""
        forecasts.append(forecast)

    return "\n---\n".join(forecasts)

@mcp.tool()
async def health_check() -> str:
    """Health check endpoint for deployment verification."""
    return "✅ Weather MCP Server is running! Ready to provide weather data for Australian cities and worldwide."

# For Cloud Run, we need to create a custom app with proper MCP endpoints
# FastMCP's streamable_http_app() doesn't expose routes correctly for remote access
from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.responses import JSONResponse, StreamingResponse
import json

async def mcp_handler(request):
    """Handle MCP protocol requests"""
    try:
        # Get the request body
        body = await request.body()
        data = json.loads(body)
        
        method = data.get("method")
        params = data.get("params", {})
        request_id = data.get("id")
        
        # Handle initialize
        if method == "initialize":
            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {}
                    },
                    "serverInfo": {
                        "name": "weather",
                        "version": "1.0.0"
                    }
                }
            }
            return JSONResponse(response)
        
        # Handle tools/list
        elif method == "tools/list":
            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "tools": [
                        {
                            "name": "get_current_weather",
                            "description": "Get current weather conditions for a city.",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "city": {
                                        "type": "string",
                                        "description": "City name"
                                    }
                                },
                                "required": ["city"]
                            }
                        },
                        {
                            "name": "get_forecast",
                            "description": "Get weather forecast for a city.",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "city": {
                                        "type": "string",
                                        "description": "City name"
                                    },
                                    "days": {
                                        "type": "integer",
                                        "description": "Number of days (1-3)",
                                        "default": 3
                                    }
                                },
                                "required": ["city"]
                            }
                        },
                        {
                            "name": "health_check",
                            "description": "Health check endpoint for deployment verification.",
                            "inputSchema": {
                                "type": "object",
                                "properties": {}
                            }
                        }
                    ]
                }
            }
            return JSONResponse(response)
        
        # Handle tools/call
        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            
            result = None
            if tool_name == "get_current_weather":
                result = await get_current_weather(arguments.get("city"))
            elif tool_name == "get_forecast":
                result = await get_forecast(
                    arguments.get("city"),
                    arguments.get("days", 3)
                )
            elif tool_name == "health_check":
                result = await health_check()
            else:
                return JSONResponse({
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": f"Tool not found: {tool_name}"
                    }
                }, status_code=404)
            
            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": result
                        }
                    ]
                }
            }
            return JSONResponse(response)
        
        else:
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }
            }, status_code=404)
            
    except Exception as e:
        return JSONResponse({
            "jsonrpc": "2.0",
            "error": {
                "code": -32603,
                "message": f"Internal error: {str(e)}"
            }
        }, status_code=500)

# Create Starlette app with MCP endpoint
app = Starlette(
    routes=[
        Route('/', mcp_handler, methods=['POST']),
        Route('/sse', mcp_handler, methods=['POST']),
    ]
)

print("✅ Custom MCP server initialized with HTTP endpoints")
print("🔧 Available tools: get_current_weather, get_forecast, health_check")
print("📡 Endpoints: / and /sse")

if __name__ == "__main__":
    import sys
    import uvicorn
    
    # Check if PORT environment variable is set (Cloud Run) or if explicitly run standalone
    # but NOT when run as MCP subprocess (which has sys.argv == 1 but should use stdio)
    is_cloud_run = bool(os.getenv("PORT"))
    is_standalone = len(sys.argv) == 1 and sys.stdin.isatty()  # Interactive terminal
    
    if is_cloud_run or is_standalone:
        # HTTP mode for Cloud Run or standalone server
        print("🚀 Starting FastMCP server in HTTP mode for Cloud Run")
        port = int(os.getenv("PORT", 8080))
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=port,
            log_level="info"
        )
    else:
        # Stdio mode for local MCP client connections
        print("Starting FastMCP server in stdio mode for local client", file=sys.stderr)
        mcp.run()