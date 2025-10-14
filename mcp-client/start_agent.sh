#!/bin/bash

echo "🌤️  Weather Agent - Starting ADK Web Interface"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  No .env file found!"
    echo ""
    echo "Creating .env file template..."
    cat > .env << 'EOL'
# Google API Key for Gemini (Required)
# Get from: https://aistudio.google.com/apikey
GOOGLE_API_KEY=your_google_api_key_here
EOL
    echo "✅ Created .env file"
    echo ""
    echo "📝 Please edit .env and add your Google API key:"
    echo "   1. Get key from: https://aistudio.google.com/apikey"
    echo "   2. Edit .env file"
    echo "   3. Run this script again"
    echo ""
    exit 1
fi

# Check if GOOGLE_API_KEY is set in .env
source .env
if [ "$GOOGLE_API_KEY" = "your_google_api_key_here" ] || [ -z "$GOOGLE_API_KEY" ]; then
    echo "❌ GOOGLE_API_KEY not configured in .env file"
    echo ""
    echo "Please:"
    echo "  1. Get API key from: https://aistudio.google.com/apikey"
    echo "  2. Edit .env file and replace 'your_google_api_key_here'"
    echo "  3. Run this script again"
    echo ""
    exit 1
fi

echo "✅ Environment configured"
echo ""

# Check if dependencies are installed
echo "📦 Checking dependencies..."
if command -v uv &> /dev/null; then
    echo "   Using uv package manager"
    uv sync --quiet
else
    echo "   Using pip"
    pip install -q google-adk google-generativeai python-dotenv httpx
fi
echo "✅ Dependencies ready"
echo ""

# Display connection info
echo "🌐 MCP Server Configuration:"
echo "   URL: https://weather-mcp-server-oze7nwnjba-as.a.run.app"
echo "   Tools: get_current_weather, get_forecast, health_check"
echo ""

echo "🚀 Starting ADK Web Interface..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📍 Open your browser at: http://localhost:8000"
echo "🤖 Select 'weather_agent' from the dropdown"
echo "💬 Try asking: 'What's the weather in Brisbane?'"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start ADK web
if command -v uv &> /dev/null; then
    uv run adk web
else
    python -m adk web
fi

