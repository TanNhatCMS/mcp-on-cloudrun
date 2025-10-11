import asyncio
import logging
from typing import Any, Sequence
import httpx
import os

from mcp.server.models import InitializeResult
from mcp.server import NotificationOptions, Server
from mcp.types import Resource, Tool, TextContent, ImageContent, EmbeddedResource
import mcp.types as types

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
WEATHERAPI_BASE = "https://api.weatherapi.com/v1"
USER_AGENT = "weather-app/1.0"

# Get API key from environment variable
API_KEY = os.getenv("WEATHERAPI_KEY")

async def make_weather_request(endpoint: str, params: dict[str, str]) -> dict[str, Any] | None:
    """Make a request to the WeatherAPI with proper error handling."""
    if not API_KEY:
        logger.error("WeatherAPI key not set. Please set WEATHERAPI_KEY environment variable.")
        return None
        
    headers = {
        "User-Agent": USER_AGENT,
    }
    params["key"] = API_KEY
    url = f"{WEATHERAPI_BASE}/{endpoint}"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, params=params, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP Error {e.response.status_code}: {e.response.text}")
            return None
        except httpx.RequestError as e:
            logger.error(f"Request Error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return None

# Initialize the MCP server
server = Server("weather")

@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """List available weather tools."""
    return [
        Tool(
            name="get_current_weather",
            description="Get current weather for a city",
            inputSchema={
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "City name to get weather for"
                    }
                },
                "required": ["city"]
            }
        ),
        Tool(
            name="get_weather_forecast",
            description="Get weather forecast for a city",
            inputSchema={
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "City name to get forecast for"
                    },
                    "days": {
                        "type": "integer",
                        "description": "Number of forecast days (1-10)",
                        "default": 3
                    }
                },
                "required": ["city"]
            }
        ),
        Tool(
            name="health_check",
            description="Health check for the weather service",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict[str, Any]) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """Handle tool calls."""
    
    if name == "get_current_weather":
        city = arguments.get("city", "")
        if not city:
            return [types.TextContent(type="text", text="Error: City parameter is required")]
        
        data = await make_weather_request("current.json", {"q": city})
        if not data:
            return [types.TextContent(type="text", text=f"Error: Could not fetch weather data for {city}")]
        
        current = data["current"]
        location = data["location"]
        result = f"Current weather in {location['name']}, {location['country']}:\n"
        result += f"Temperature: {current['temp_c']}°C ({current['temp_f']}°F)\n"
        result += f"Condition: {current['condition']['text']}\n"
        result += f"Humidity: {current['humidity']}%\n"
        result += f"Wind: {current['wind_kph']} km/h from {current['wind_dir']}\n"
        result += f"Feels like: {current['feelslike_c']}°C ({current['feelslike_f']}°F)\n"
        result += f"UV Index: {current['uv']}"
        
        return [types.TextContent(type="text", text=result)]
    
    elif name == "get_weather_forecast":
        city = arguments.get("city", "")
        days = arguments.get("days", 3)
        
        if not city:
            return [types.TextContent(type="text", text="Error: City parameter is required")]
        
        if not isinstance(days, int) or days < 1 or days > 10:
            days = 3
        
        data = await make_weather_request("forecast.json", {"q": city, "days": str(days)})
        if not data:
            return [types.TextContent(type="text", text=f"Error: Could not fetch weather forecast for {city}")]
        
        location = data["location"]
        forecast = data["forecast"]["forecastday"]
        
        result = f"Weather forecast for {location['name']}, {location['country']}:\n\n"
        
        for day in forecast:
            date = day["date"]
            day_data = day["day"]
            result += f"📅 {date}:\n"
            result += f"  High: {day_data['maxtemp_c']}°C ({day_data['maxtemp_f']}°F)\n"
            result += f"  Low: {day_data['mintemp_c']}°C ({day_data['mintemp_f']}°F)\n"
            result += f"  Condition: {day_data['condition']['text']}\n"
            result += f"  Rain chance: {day_data['daily_chance_of_rain']}%\n"
            result += f"  Max wind: {day_data['maxwind_kph']} km/h\n\n"
        
        return [types.TextContent(type="text", text=result.strip())]
    
    elif name == "health_check":
        return [types.TextContent(
            type="text", 
            text="✅ Weather MCP Server is running! Ready to provide weather data for cities worldwide."
        )]
    
    else:
        return [types.TextContent(type="text", text=f"Unknown tool: {name}")]

async def main():
    # Import here to avoid issues if not using in HTTP mode
    from mcp.server.stdio import stdio_server
    
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializeResult(
                protocolVersion="2024-11-05",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={}
                )
            )
        )

if __name__ == "__main__":
    asyncio.run(main())
