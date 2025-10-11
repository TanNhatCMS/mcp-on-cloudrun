import asyncio
from typing import Optional
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from fastmcp import Client as FastMCPClient

import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()  # load environment variables from .env

class MCPClient:
    def __init__(self):
        # Initialize session and client objects
        self.session: Optional[ClientSession] = None
        self.fastmcp_client: Optional[FastMCPClient] = None
        self.exit_stack = AsyncExitStack()
        self.is_remote = False
        # Configure Gemini - API key should be in GOOGLE_API_KEY environment variable
        genai.configure()
        self.model = genai.GenerativeModel('gemini-2.5-flash')

    async def connect_to_server(self, server_endpoint: str):
        """Connect to an MCP server
        
        Args:
            server_endpoint: Path to local server script (.py or .js) or HTTP URL for remote server
        """
        # Check if it's a URL (remote server)
        if server_endpoint.startswith(('http://', 'https://')):
            self.is_remote = True
            print(f"\nConnecting to remote MCP server: {server_endpoint}")
            
            # Ensure the URL has the /mcp endpoint
            mcp_url = server_endpoint
            if not mcp_url.endswith('/mcp'):
                mcp_url = mcp_url.rstrip('/') + '/mcp'
            
            # Connect using FastMCP client
            self.fastmcp_client = FastMCPClient(mcp_url)
            await self.fastmcp_client.__aenter__()
            
        else:
            # Local server connection via stdio
            self.is_remote = False
            print(f"\nConnecting to local MCP server: {server_endpoint}")
            
            is_python = server_endpoint.endswith('.py')
            is_js = server_endpoint.endswith('.js')
            if not (is_python or is_js):
                raise ValueError("Server script must be a .py or .js file")
                
            command = "python" if is_python else "node"
            server_params = StdioServerParameters(
                command=command,
                args=[server_endpoint],
                env=None
            )
            
            stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
            self.stdio, self.write = stdio_transport
            self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))
            
            await self.session.initialize()
        
        # List available tools
        tools = await self._list_tools()
        print("\nConnected to server with tools:", [tool.name for tool in tools])

    async def _list_tools(self):
        """List available tools from the server"""
        if self.is_remote and self.fastmcp_client:
            response = await self.fastmcp_client.list_tools()
            # FastMCP client returns tools directly as a list
            return response if isinstance(response, list) else response.tools
        elif self.session:
            response = await self.session.list_tools()
            return response.tools
        else:
            raise RuntimeError("No active server connection")

    async def _call_tool(self, tool_name: str, tool_args: dict):
        """Call a tool on the server"""
        if self.is_remote and self.fastmcp_client:
            return await self.fastmcp_client.call_tool(tool_name, tool_args)
        elif self.session:
            return await self.session.call_tool(tool_name, tool_args)
        else:
            raise RuntimeError("No active server connection")

    async def process_query(self, query: str) -> str:
        """Process a query using Claude and available tools"""
        messages = [
            {
                "role": "user",
                "content": query
            }
        ]

        tools = await self._list_tools()
        available_tools = [{ 
            "name": tool.name,
            "description": tool.description,
            "input_schema": tool.inputSchema
        } for tool in tools]

        # Initial Gemini API call
        # Convert MCP tools to Gemini function declarations
        tools_for_gemini = []
        for tool in available_tools:
            func_declaration = genai.protos.FunctionDeclaration(
                name=tool["name"],
                description=tool["description"],
                parameters=genai.protos.Schema(
                    type=genai.protos.Type.OBJECT,
                    properties={
                        prop_name: genai.protos.Schema(
                            type=genai.protos.Type.STRING,  # Simplified - assumes string types
                            description=prop_schema.get("description", "")
                        ) for prop_name, prop_schema in tool["input_schema"].get("properties", {}).items()
                    },
                    required=tool["input_schema"].get("required", [])
                )
            )
            tools_for_gemini.append(func_declaration)

        # Configure the model with tools
        model_with_tools = genai.GenerativeModel(
            'gemini-2.0-flash-exp',
            tools=tools_for_gemini if tools_for_gemini else None
        )
        
        response = model_with_tools.generate_content(
            messages[0]["content"],
            generation_config=genai.GenerationConfig(
                max_output_tokens=1000,
                temperature=0.1
            )
        )

        # Process response and handle tool calls
        final_text = []

        # Check if response has function calls
        if response.candidates and response.candidates[0].content.parts:
            for part in response.candidates[0].content.parts:
                if hasattr(part, 'text') and part.text:
                    final_text.append(part.text)
                elif hasattr(part, 'function_call') and part.function_call:
                    func_call = part.function_call
                    tool_name = func_call.name
                    tool_args = dict(func_call.args)
                    
                    # Execute tool call
                    result = await self._call_tool(tool_name, tool_args)
                    final_text.append(f"[Calling tool {tool_name} with args {tool_args}]")

                    # Create follow-up conversation with tool results
                    chat = model_with_tools.start_chat()
                    # Add the original query
                    chat.send_message(messages[0]["content"])
                    
                    # Add function response
                    function_response = genai.protos.Part(
                        function_response=genai.protos.FunctionResponse(
                            name=tool_name,
                            response={"result": str(result.content)}
                        )
                    )
                    
                    # Get next response from Gemini with function results
                    follow_up_response = chat.send_message([function_response])
                    
                    if follow_up_response.text:
                        final_text.append(follow_up_response.text)
        else:
            # No function calls, just return the text response
            if response.text:
                final_text.append(response.text)

        return "\n".join(final_text) if final_text else "No response generated"

    async def chat_loop(self):
        """Run an interactive chat loop"""
        print("\nMCP Client Started!")
        print("Type your queries or 'quit' to exit.")
        
        while True:
            try:
                query = input("\nQuery: ").strip()
                
                if query.lower() == 'quit':
                    break
                    
                response = await self.process_query(query)
                print("\n" + response)
                    
            except Exception as e:
                print(f"\nError: {str(e)}")
    
    async def cleanup(self):
        """Clean up resources"""
        if self.is_remote and self.fastmcp_client:
            await self.fastmcp_client.__aexit__(None, None, None)
        await self.exit_stack.aclose()

async def main():
    if len(sys.argv) < 2:
        print("Usage: python client.py <path_to_server_script_or_url>")
        print("Examples:")
        print("  python client.py ../mcp-server/weather.py")
        print("  python client.py https://your-server.com/mcp")
        sys.exit(1)
        
    client = MCPClient()
    try:
        await client.connect_to_server(sys.argv[1])
        await client.chat_loop()
    finally:
        await client.cleanup()

if __name__ == "__main__":
    import sys
    asyncio.run(main())