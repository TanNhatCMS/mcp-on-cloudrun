# Complete Setup Guide - Weather Agent with Google ADK + Remote MCP

This guide shows how to build and run an AI agent using **Google Agent Development Kit (ADK)** that connects to **remote MCP tools deployed on Cloud Run**.

## 🎯 What We Built

An AI weather assistant that:
- Uses **Google ADK** for agent framework
- Connects to **remote MCP server** on Cloud Run (not local)
- Provides **3 weather tools** via MCP protocol
- Has a **web UI** for easy interaction

## 📁 Project Structure

```
mcp-on-cloudrun/
├── mcp-server/              # MCP Server (deployed to Cloud Run)
│   ├── weather.py          # FastMCP server with 3 tools
│   ├── Dockerfile          # Container configuration
│   ├── deploy.sh           # Deployment script
│   └── pyproject.toml      # Dependencies
│
└── mcp-client/             # ADK Agent (runs locally)
    ├── weather_agent/      # Agent package
    │   ├── agent.py       # Main agent with MCP connection
    │   └── __init__.py    # Package exports
    ├── client.py          # Standalone MCP client (optional)
    ├── start_agent.sh     # Quick start script
    ├── verify_setup.py    # Setup verification
    ├── pyproject.toml     # Dependencies
    ├── .env               # Environment variables (create this!)
    └── README.md          # Documentation
```

## 🚀 Quick Start (5 Minutes)

### Step 1: Get Google API Key

1. Go to https://aistudio.google.com/apikey
2. Click "Create API Key"
3. Copy the key

### Step 2: Configure Environment

```bash
cd mcp-client

# Create .env file
echo "GOOGLE_API_KEY=paste_your_key_here" > .env
```

### Step 3: Install Dependencies

```bash
# Using uv (recommended)
uv sync

# Or using pip
pip install google-adk google-generativeai mcp fastmcp python-dotenv httpx
```

### Step 4: Verify Setup

```bash
python verify_setup.py
```

This checks:
- ✅ Environment variables
- ✅ Dependencies installed  
- ✅ Agent structure
- ✅ MCP server connectivity
- ✅ Agent can be imported

### Step 5: Start the Agent

```bash
# Easy way - use the script
./start_agent.sh

# Or manually
uv run adk web
```

### Step 6: Use the Agent

1. Open http://localhost:8000 in your browser
2. Select **`weather_agent`** from the dropdown
3. Ask questions:
   - "What's the weather in Brisbane?"
   - "Give me a 3-day forecast for Tokyo"
   - "How's the weather looking in London?"

## 🔧 How It Works

### Architecture Flow

```
User Browser (localhost:8000)
    ↓
ADK Web Interface
    ↓
weather_agent (Google ADK)
    ↓ [HTTP/SSE over Internet]
MCP Server (Cloud Run)
    ↓
WeatherAPI.com
```

### Key Components

**1. MCP Server (Remote - Cloud Run)**
- **URL**: `https://weather-mcp-server-oze7nwnjba-as.a.run.app`
- **Framework**: FastMCP
- **Tools Provided**:
  ```python
  - get_current_weather(city: str) -> str
  - get_forecast(city: str, days: int) -> str
  - health_check() -> str
  ```

**2. ADK Agent (Local)**
- **Framework**: Google ADK
- **Model**: Gemini 2.5 Flash
- **Connection**: Connects to remote MCP server via HTTP
- **Code**:
  ```python
  connection_params = StreamableHTTPConnectionParams(
      url="https://weather-mcp-server-oze7nwnjba-as.a.run.app",
      timeout=30.0,
  )
  
  weather_tools = McpToolset(connection_params=connection_params)
  
  root_agent = Agent(
      name="weather_agent",
      model="gemini-2.5-flash",
      tools=[weather_tools],
  )
  ```

**3. Web Interface**
- **Tech**: ADK Web (built-in)
- **Port**: 8000
- **Features**: Chat UI, streaming responses, agent selection

## 📊 Example Interaction

**User**: "What's the weather in San Francisco?"

**Flow**:
1. User types query in web UI
2. ADK sends query to Gemini
3. Gemini decides to use `get_current_weather` tool
4. ADK agent calls MCP server on Cloud Run
5. MCP server fetches weather from WeatherAPI
6. Data flows back through MCP → ADK → Gemini
7. Gemini formats natural language response
8. User sees: "The weather in San Francisco is currently 18°C..."

## 🔍 Verification Commands

```bash
# Check MCP server is running
curl https://weather-mcp-server-oze7nwnjba-as.a.run.app

# Check MCP server logs
gcloud run services logs read weather-mcp-server --region=asia-southeast1

# Verify agent can import
cd mcp-client && python -c "from weather_agent import root_agent; print(root_agent.name)"

# Run full verification
python verify_setup.py
```

## 🐛 Troubleshooting

### "Session terminated" Error

**Cause**: MCP client can't connect to server

**Solutions**:
1. Check if MCP server is deployed:
   ```bash
   gcloud run services list --region=asia-southeast1
   ```

2. Verify URL in `weather_agent/agent.py` matches:
   ```python
   MCP_SERVER_URL = "https://weather-mcp-server-oze7nwnjba-as.a.run.app"
   ```

3. Check server logs:
   ```bash
   gcloud run services logs read weather-mcp-server --region=asia-southeast1 --limit=50
   ```

### "API Key Not Found" Error

**Cause**: GOOGLE_API_KEY not set

**Solution**:
```bash
# Check if .env exists
ls -la .env

# Check if key is set
cat .env | grep GOOGLE_API_KEY

# Set it correctly
echo "GOOGLE_API_KEY=your_actual_key" > .env
```

### Agent in Fallback Mode

**Symptom**: Agent loads but doesn't have weather tools

**Solution**:
1. Check terminal logs when ADK starts
2. Look for "MCP toolset created successfully"
3. If you see errors, the MCP connection failed
4. Verify network connectivity and MCP server status

## 📚 Files Reference

### Core Agent Files

**`weather_agent/agent.py`**
```python
# Main agent definition
# Connects to remote MCP server
# Creates ADK agent with MCP tools
```

**`weather_agent/__init__.py`**
```python
# Exports root_agent for ADK discovery
from .agent import root_agent
__all__ = ["root_agent"]
```

**`.env`**
```bash
# Environment configuration
GOOGLE_API_KEY=your_google_api_key_here
```

### Utility Scripts

**`start_agent.sh`**
- Quick start script
- Checks environment
- Installs dependencies
- Starts ADK web

**`verify_setup.py`**
- Comprehensive verification
- Checks all requirements
- Tests connectivity
- Validates imports

**`client.py`**
- Standalone MCP client (optional)
- For direct MCP interaction
- Useful for debugging

## 🎓 Learning Resources

- **Google ADK**: https://google.github.io/adk-docs/
- **MCP Protocol**: https://modelcontextprotocol.io/
- **FastMCP**: https://github.com/jlowin/fastmcp
- **Google Cloud Run**: https://cloud.google.com/run

## ✅ Success Checklist

- [ ] Google API key obtained
- [ ] `.env` file created with API key
- [ ] Dependencies installed (`uv sync`)
- [ ] Verification passed (`python verify_setup.py`)
- [ ] ADK web started (`./start_agent.sh`)
- [ ] Browser opened at http://localhost:8000
- [ ] Agent selected from dropdown
- [ ] Weather query successful

## 🎉 You're Done!

You now have a fully functional AI agent using:
- ✅ Google ADK for agent framework
- ✅ Remote MCP server on Cloud Run
- ✅ Gemini 2.5 Flash for AI
- ✅ Beautiful web interface
- ✅ Real weather data

Enjoy building more AI agents! 🚀

