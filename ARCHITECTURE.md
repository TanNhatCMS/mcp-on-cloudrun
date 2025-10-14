# Architecture - Google ADK Agent with Remote MCP on Cloud Run

## 🏛️ System Overview

This project demonstrates a production-ready AI agent architecture using:
- **Google Agent Development Kit (ADK)** - Agent framework with web UI
- **Model Context Protocol (MCP)** - Standard protocol for AI tool integration
- **Google Cloud Run** - Serverless deployment platform
- **Custom HTTP Endpoints** - MCP-over-HTTPS implementation

## 📐 Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER INTERFACE                            │
│                                                                   │
│  Browser (localhost:8000)                                        │
│  ┌──────────────────────────────────────────────────┐           │
│  │  ADK Web UI                                       │           │
│  │  - Agent Selection Dropdown                      │           │
│  │  - Chat Interface                                │           │
│  │  - Streaming Responses                           │           │
│  └──────────────────────────────────────────────────┘           │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                      AGENT LAYER (LOCAL)                         │
│                                                                   │
│  weather_agent/agent.py                                          │
│  ┌──────────────────────────────────────────────────┐           │
│  │  Google ADK Agent                                 │           │
│  │  ┌────────────────────────────────────────────┐  │           │
│  │  │  Gemini 2.5 Flash                          │  │           │
│  │  │  - Natural language understanding          │  │           │
│  │  │  - Tool selection logic                    │  │           │
│  │  │  - Response generation                     │  │           │
│  │  └────────────────────────────────────────────┘  │           │
│  │                                                   │           │
│  │  MCP Toolset (StreamableHTTPConnectionParams)    │           │
│  │  ┌────────────────────────────────────────────┐  │           │
│  │  │  Connection: HTTPS to Cloud Run            │  │           │
│  │  │  URL: weather-mcp-server-*.run.app         │  │           │
│  │  │  Timeout: 30s (for cold starts)            │  │           │
│  │  └────────────────────────────────────────────┘  │           │
│  └──────────────────────────────────────────────────┘           │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            │ HTTPS/MCP Protocol
                            │ (Over Internet)
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│              MCP SERVER (GOOGLE CLOUD RUN)                       │
│              Region: asia-southeast1                             │
│                                                                   │
│  weather.py                                                      │
│  ┌──────────────────────────────────────────────────┐           │
│  │  Starlette ASGI Application                       │           │
│  │  ┌────────────────────────────────────────────┐  │           │
│  │  │  HTTP Endpoints (POST)                     │  │           │
│  │  │  - /     : MCP protocol handler            │  │           │
│  │  │  - /sse  : MCP protocol handler            │  │           │
│  │  └────────────────────────────────────────────┘  │           │
│  │                                                   │           │
│  │  MCP Protocol Handler                             │           │
│  │  ┌────────────────────────────────────────────┐  │           │
│  │  │  Methods:                                   │  │           │
│  │  │  - initialize: Server handshake            │  │           │
│  │  │  - tools/list: Return available tools      │  │           │
│  │  │  - tools/call: Execute tool function       │  │           │
│  │  └────────────────────────────────────────────┘  │           │
│  │                                                   │           │
│  │  FastMCP Tools                                    │           │
│  │  ┌────────────────────────────────────────────┐  │           │
│  │  │  @mcp.tool()                                │  │           │
│  │  │  - get_current_weather(city)                │  │           │
│  │  │  - get_forecast(city, days)                 │  │           │
│  │  │  - health_check()                           │  │           │
│  │  └────────────────────────────────────────────┘  │           │
│  └──────────────────────────────────────────────────┘           │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            │ HTTPS API Calls
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    EXTERNAL DATA SOURCE                          │
│                                                                   │
│  WeatherAPI.com                                                  │
│  - Current weather data                                          │
│  - Weather forecasts                                             │
│  - Global coverage                                               │
└─────────────────────────────────────────────────────────────────┘
```

## 🔄 Request Flow Example

### User Query: "What's the weather in Brisbane?"

```
1. USER BROWSER
   └─> Types query in ADK web UI (localhost:8000)

2. ADK WEB UI
   └─> Sends query to weather_agent

3. WEATHER AGENT (Local)
   ├─> Passes query to Gemini 2.5 Flash
   └─> Gemini analyzes query + available MCP tools

4. GEMINI DECISION
   ├─> Tool: get_current_weather
   ├─> Parameter: {"city": "Brisbane"}
   └─> Returns function call to ADK

5. ADK MCP TOOLSET
   ├─> Constructs MCP request:
   │   {
   │     "jsonrpc": "2.0",
   │     "method": "tools/call",
   │     "params": {
   │       "name": "get_current_weather",
   │       "arguments": {"city": "Brisbane"}
   │     }
   │   }
   └─> POST to https://weather-mcp-server-*.run.app

6. CLOUD RUN MCP SERVER
   ├─> Receives MCP request
   ├─> Routes to mcp_handler()
   ├─> Calls get_current_weather("Brisbane")
   └─> Makes HTTPS request to WeatherAPI.com

7. WEATHERAPI.COM
   ├─> Returns weather data for Brisbane
   └─> JSON response with temp, conditions, etc.

8. MCP SERVER RESPONSE
   ├─> Formats data into readable text
   └─> Returns MCP response:
       {
         "jsonrpc": "2.0",
         "result": {
           "content": [{"type": "text", "text": "Weather data..."}]
         }
       }

9. ADK AGENT
   ├─> Receives MCP response
   ├─> Passes tool result to Gemini
   └─> Gemini formats natural language response

10. USER BROWSER
    └─> Displays: "The current weather in Brisbane is 28°C, sunny..."
```

## 🛠️ Technology Stack

### Frontend/Agent Layer
| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Agent Framework** | Google ADK | Agent orchestration, web UI |
| **Web Interface** | ADK Web | Chat UI at localhost:8000 |
| **LLM** | Gemini 2.5 Flash | Natural language understanding |
| **MCP Client** | McpToolset | Connect to remote MCP servers |
| **HTTP Client** | StreamableHTTPConnectionParams | HTTPS to Cloud Run |

### Backend/Server Layer
| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Platform** | Google Cloud Run | Serverless deployment |
| **Web Framework** | Starlette (ASGI) | HTTP request handling |
| **MCP Framework** | FastMCP | Tool definition with decorators |
| **Protocol** | Custom MCP Handler | JSON-RPC 2.0 over HTTP |
| **API Client** | httpx | Calls to WeatherAPI.com |
| **Secrets** | Google Secret Manager | Secure API key storage |

### External Services
| Service | Purpose |
|---------|---------|
| WeatherAPI.com | Weather data provider |
| Google AI | Gemini API hosting |

## 🔐 Security Architecture

```
User Request (Browser)
    ↓
ADK Agent (Local)
    ↓ [HTTPS - TLS 1.3]
Cloud Run (Public Endpoint)
    ↓ [IAM Authentication]
Secret Manager
    ↓ [Encrypted Key Retrieval]
WeatherAPI.com
```

### Security Features

1. **HTTPS Everywhere**: All communications encrypted
2. **Secret Manager**: API keys never in code or environment
3. **IAM Controls**: Google Cloud identity and access management
4. **No Credentials in Logs**: Secrets masked in all outputs
5. **Automatic Updates**: Cloud Run handles security patches

## 📡 Protocol Details

### MCP Protocol Implementation

**Supported Methods:**
```json
{
  "initialize": "Server handshake and capability exchange",
  "tools/list": "List all available tools",
  "tools/call": "Execute a specific tool"
}
```

**Message Format (JSON-RPC 2.0):**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "get_current_weather",
    "arguments": {
      "city": "Brisbane"
    }
  }
}
```

**Response Format:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "Current Weather for Brisbane..."
      }
    ]
  }
}
```

## 🎯 Key Design Decisions

### Why Google ADK?
- ✅ Professional web UI out of the box
- ✅ Built-in streaming support
- ✅ Native Gemini integration
- ✅ Agent framework handles complexity
- ✅ Easy to extend with more tools

### Why Custom HTTP Endpoints?
- ✅ FastMCP's `streamable_http_app()` doesn't expose routes correctly
- ✅ Custom implementation gives full control
- ✅ Direct JSON-RPC 2.0 over HTTP is simpler
- ✅ Works seamlessly with ADK's `StreamableHTTPConnectionParams`

### Why Cloud Run?
- ✅ Scales to zero (costs $0 when idle)
- ✅ Infinite scale (handles any traffic)
- ✅ Zero maintenance (no servers to manage)
- ✅ Integrated with Google Cloud ecosystem

### Why MCP Protocol?
- ✅ Standard protocol for AI-tool communication
- ✅ Works with multiple AI frameworks
- ✅ Separates agent logic from tool implementation
- ✅ Tools can be shared across different agents

## 📊 Performance Characteristics

### Cold Start (First Request)
- **Time**: ~2-5 seconds
- **Reason**: Cloud Run container initialization
- **Mitigation**: Timeout set to 30s in agent config

### Warm Requests
- **Time**: ~300-800ms
- **Breakdown**:
  - ADK to Cloud Run: 50-100ms
  - Cloud Run processing: 50-100ms
  - WeatherAPI call: 200-500ms
  - Response processing: 50-100ms

### Concurrent Requests
- **Capacity**: Auto-scales to handle traffic
- **Instances**: 0 (idle) to 10 (configured max)
- **Cost**: Pay only for actual request time

## 💡 Extension Points

### Add More Tools
```python
# In mcp-server/weather.py
@mcp.tool()
async def get_air_quality(city: str) -> str:
    """Get air quality index for a city."""
    # Implementation here
    pass
```

### Add More Agents
```python
# Create mcp-client/finance_agent/agent.py
from google.adk import Agent

root_agent = Agent(
    name="finance_agent",
    model="gemini-2.5-flash",
    tools=[finance_tools],
)
```

### Multiple MCP Servers
```python
# Connect to multiple MCP servers
weather_tools = McpToolset(connection_params=weather_params)
finance_tools = McpToolset(connection_params=finance_params)

root_agent = Agent(
    name="multi_agent",
    model="gemini-2.5-flash",
    tools=[weather_tools, finance_tools],
)
```

## 🧪 Testing

### Test MCP Server Directly

**Initialize:**
```bash
curl -X POST https://weather-mcp-server-583791017886.asia-southeast1.run.app \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}'
```

**List Tools:**
```bash
curl -X POST https://weather-mcp-server-583791017886.asia-southeast1.run.app \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}'
```

**Call Tool:**
```bash
curl -X POST https://weather-mcp-server-583791017886.asia-southeast1.run.app \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"get_current_weather","arguments":{"city":"Brisbane"}}}'
```

### Test ADK Agent

```bash
cd mcp-client
python verify_setup.py  # Run all checks
uv run adk web          # Start agent
```

## 📝 Configuration Files

### Agent Configuration (`mcp-client/weather_agent/agent.py`)

```python
from google.adk import Agent
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset, StreamableHTTPConnectionParams

MCP_SERVER_URL = "https://weather-mcp-server-583791017886.asia-southeast1.run.app"

connection_params = StreamableHTTPConnectionParams(
    url=MCP_SERVER_URL,
    timeout=30.0,
)

weather_tools = McpToolset(connection_params=connection_params)

root_agent = Agent(
    name="weather_agent",
    model="gemini-2.5-flash",
    tools=[weather_tools],
)
```

### Server Configuration (`mcp-server/weather.py`)

```python
from mcp.server.fastmcp import FastMCP
from starlette.applications import Starlette

mcp = FastMCP("weather")

@mcp.tool()
async def get_current_weather(city: str) -> str:
    """Get current weather conditions for a city."""
    # Implementation...
    return weather_data

# Custom MCP HTTP handler
async def mcp_handler(request):
    # Implements MCP protocol over HTTP
    # Handles: initialize, tools/list, tools/call
    pass

app = Starlette(routes=[
    Route('/', mcp_handler, methods=['POST']),
    Route('/sse', mcp_handler, methods=['POST']),
])
```

## 🔍 Monitoring & Debugging

### View Cloud Run Logs
```bash
gcloud run services logs read weather-mcp-server \
  --region=asia-southeast1 \
  --project=gdgcloudhanoi-fb \
  --limit=50
```

### Check Service Status
```bash
gcloud run services describe weather-mcp-server \
  --region=asia-southeast1 \
  --format="value(status.url,status.conditions)"
```

### Monitor Costs
```bash
gcloud run services describe weather-mcp-server \
  --region=asia-southeast1 \
  --format="value(spec.template.spec.containers[0].resources)"
```

## 🚀 Deployment Pipeline

```
1. Code Changes
   └─> mcp-server/weather.py

2. Build Container
   └─> Docker build from Dockerfile

3. Push to Container Registry
   └─> Google Cloud Build

4. Deploy to Cloud Run
   └─> New revision created

5. Traffic Migration
   └─> 100% traffic to new revision

6. Old Revision Cleanup
   └─> Previous revisions retained for rollback

Total Time: ~2-3 minutes
```

## 📈 Scalability

| Metric | Configuration | Notes |
|--------|--------------|-------|
| **Min Instances** | 0 | Scales to zero when idle |
| **Max Instances** | 10 | Can be increased |
| **Concurrent Requests** | 80 per instance | Default |
| **Memory** | 512Mi | Per instance |
| **CPU** | 1 vCPU | Per instance |
| **Timeout** | 300s | Request timeout |
| **Cold Start** | 2-5s | First request |
| **Warm Request** | 300-800ms | Subsequent requests |

## 💰 Cost Analysis

### Google Cloud Run (Free Tier)
- **2M requests/month** free
- **360,000 vCPU-seconds/month** free
- **180,000 GiB-seconds/month** free
- **After free tier**: $0.00002400/vCPU-second

### Estimated Monthly Cost (100K requests)
- **Scenario**: 100,000 weather queries/month
- **Avg Request Time**: 500ms
- **Total Compute**: 50,000 vCPU-seconds
- **Cost**: **FREE** (within free tier)

### WeatherAPI.com (Free Tier)
- **1M calls/month** free
- **Cost**: $0 for this project

## 🎓 Learning Outcomes

From this architecture, you learned:

1. ✅ **Google ADK** - Building AI agents with web UI
2. ✅ **MCP Protocol** - Standard for AI-tool communication
3. ✅ **Remote Tool Execution** - Agents calling cloud services
4. ✅ **Cloud Run Deployment** - Serverless containers
5. ✅ **Custom Protocol Implementation** - MCP over HTTP
6. ✅ **Security Best Practices** - Secret management
7. ✅ **Production Architecture** - Scalable, reliable systems

## 🔗 Related Documentation

- **SETUP_GUIDE.md** - Step-by-step setup instructions
- **SUCCESS.md** - What was achieved and how
- **STATUS.md** - Technical details and alternatives
- **mcp-client/README.md** - Client-specific documentation
- **presentation.md** - Presentation outline

## 🌟 Why This Architecture Matters

This project demonstrates:

1. **Separation of Concerns**: Agent logic separate from tool implementation
2. **Cloud-Native**: Built for scale from day one
3. **Standard Protocols**: Uses MCP for interoperability
4. **Developer Experience**: ADK provides great DX with web UI
5. **Production Ready**: Not a toy - ready for real users

You can extend this pattern to build:
- Code assistants with GitHub integration
- Research agents with web search
- Finance tools with market data
- Customer service bots with CRM integration
- And much more!

---

**Built with** ❤️ **using Google ADK, MCP, and Cloud Run**

