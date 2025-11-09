"""
MCP Client utilities for connecting to MCP servers and converting tools to OpenAI format.
"""
import os
from fastmcp import Client
from dotenv import load_dotenv

load_dotenv()

# MCP server URL (HTTP transport - server runs separately)
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL")


async def get_mcp_tools_for_openai():
    """
    Get MCP tools and convert them to OpenAI function calling format.
    
    This function:
    1. Connects to the MCP server
    2. Lists all available tools
    3. Converts each MCP tool to OpenAI's function format
    4. Returns a list of tools that OpenAI can use
    
    Returns:
        List of tools in OpenAI function format
    """
    try:
        async with Client(MCP_SERVER_URL) as mcp_client:
            tools = await mcp_client.list_tools()
            openai_tools = []
            for tool in tools:
                # Convert MCP tool to OpenAI function format
                # OpenAI expects: type="function", function={name, description, parameters}
                openai_tool = {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description or f"Tool: {tool.name}",
                        "parameters": tool.inputSchema if hasattr(tool, 'inputSchema') and tool.inputSchema else {
                            "type": "object",
                            "properties": {},
                            "required": []
                        }
                    }
                }
                openai_tools.append(openai_tool)
            return openai_tools
    except Exception as e:
        print(f"Error getting MCP tools: {e}")
        return []


async def execute_mcp_tool(tool_name: str, parameters: dict):
    """
    Execute an MCP tool and return the result.
    
    This function:
    1. Connects to the MCP server
    2. Calls the specified tool with the given parameters
    3. Returns the tool's result as a string
    
    Args:
        tool_name: Name of the MCP tool to call (e.g., "list_files", "search_files")
        parameters: Dictionary of parameters for the tool
    
    Returns:
        String result from the tool execution
    """
    try:
        async with Client(MCP_SERVER_URL) as mcp_client:
            result = await mcp_client.call_tool(tool_name, parameters)
            if result.content and len(result.content) > 0:
                return result.content[0].text
            else:
                return f"Tool {tool_name} returned empty result"
    except Exception as e:
        return f"Error calling tool {tool_name}: {str(e)}"

