"""
MCP Client utilities for connecting to MCP servers and converting tools to OpenAI format.
"""
import os
from fastmcp import Client
from dotenv import load_dotenv

load_dotenv()

# MCP server URL (HTTP transport - server runs separately)
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL")

if not MCP_SERVER_URL:
    print("Warning: MCP_SERVER_URL not set. MCP tools will not be available.")


async def get_mcp_tools_for_openai():
    if not MCP_SERVER_URL:
        return []
    
    try:
        async with Client(MCP_SERVER_URL) as mcp_client:
            tools = await mcp_client.list_tools()
            openai_tools = []
            for tool in tools:
                # Convert MCP tool to OpenAI function format
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
    except ConnectionError as e:
        print(f"Error connecting to MCP server at {MCP_SERVER_URL}: {e}")
        return []
    except Exception as e:
        print(f"Error getting MCP tools: {e}")
        return []


async def execute_mcp_tool(tool_name: str, parameters: dict):
    if not MCP_SERVER_URL:
        return f"Error: MCP server not configured. Cannot call tool {tool_name}"
    
    try:
        async with Client(MCP_SERVER_URL) as mcp_client:
            result = await mcp_client.call_tool(tool_name, parameters)
            if result.content and len(result.content) > 0:
                return result.content[0].text
            else:
                return f"Tool {tool_name} returned empty result"
    except ConnectionError as e:
        return f"Error: Could not connect to MCP server. {str(e)}"
    except Exception as e:
        return f"Error calling tool {tool_name}: {str(e)}"

