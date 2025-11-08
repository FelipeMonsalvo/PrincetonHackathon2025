import os
import json
import uuid
import xml.etree.ElementTree as ET
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv
from fastmcp import Client

# Load environment variables
load_dotenv()

# MCP server URL (HTTP transport - server runs separately)
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL")

# Initialize FastAPI app
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Load system prompt from XML
def load_system_prompt():
    """Load system prompt from XML file."""
    path = os.path.join(os.path.dirname(__file__), "prompts", "system_prompt.xml")
    tree = ET.parse(path)
    root = tree.getroot()
    purpose = root.findtext("Purpose", default="")
    guidelines = root.findtext("Guidelines", default="")
    return f"{purpose.strip()}\n\nGuidelines:\n{guidelines.strip()}"

SYSTEM_PROMPT = load_system_prompt()

# In-memory conversation storage (per session)
conversations = {}

# Pydantic models for request/response validation
class ChatMessage(BaseModel):
    message: str
    session_id: str | None = None

class ChatResponse(BaseModel):
    reply: str
    session_id: str

class ToolCallRequest(BaseModel):
    tool_name: str
    parameters: dict

@app.get("/", response_class=HTMLResponse)
async def get_home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/chat/new")
async def new_chat():
    """Create a new chat session."""
    session_id = str(uuid.uuid4())
    conversations[session_id] = []
    return JSONResponse({"session_id": session_id})

# Helper functions for MCP tool integration
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
            return result.content[0].text
    except Exception as e:
        return f"Error calling tool {tool_name}: {str(e)}"

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(chat: ChatMessage):
    """
    Handle AI chat with per-session conversation memory and MCP tool support.
    
    This endpoint:
    1. Gets MCP tools and makes them available to the AI
    2. Allows the AI to call MCP tools during conversation
    3. Executes tool calls and continues the conversation with results
    """
    # Create or get existing session
    session_id = chat.session_id or str(uuid.uuid4())
    if session_id not in conversations:
        conversations[session_id] = []

    # Get MCP tools and convert to OpenAI format
    # This discovers all available tools from the MCP server dynamically
    mcp_tools = await get_mcp_tools_for_openai()

    # Build conversation history
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(conversations[session_id])
    messages.append({"role": "user", "content": chat.message})

    # Save user message to conversation history
    conversations[session_id].append({"role": "user", "content": chat.message})

    # Loop to handle tool calls (AI might call tools multiple times)
    # Max 5 iterations to prevent infinite loops
    max_iterations = 5
    iteration = 0
    
    while iteration < max_iterations:
        iteration += 1
        
        # Call OpenAI API with tools available
        # If mcp_tools is empty, OpenAI won't use function calling
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            tools=mcp_tools if mcp_tools else None,  # Pass tools to OpenAI
            tool_choice="auto" if mcp_tools else None,  # Let AI decide when to use tools
            max_tokens=500,
        )

        response_message = response.choices[0].message
        
        # Add assistant's response to messages (needed for conversation flow)
        messages.append(response_message)

        # Check if the AI wants to call a tool
        if response_message.tool_calls:
            # AI wants to call one or more tools
            # Execute each tool call
            for tool_call in response_message.tool_calls:
                tool_name = tool_call.function.name
                # Parse the arguments (OpenAI sends them as JSON string)
                tool_args = json.loads(tool_call.function.arguments)
                
                # Execute the MCP tool
                tool_result = await execute_mcp_tool(tool_name, tool_args)
                
                # Add tool result to messages so AI can use it
                # OpenAI expects this format for tool results
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": tool_name,
                    "content": tool_result
                })
            
            # Continue the loop - AI will get the tool results and respond
            continue
        else:
            # No tool calls - we have the final AI response
            ai_reply = response_message.content
            
            # Save assistant message to conversation history
            conversations[session_id].append({"role": "assistant", "content": ai_reply})
            
            return ChatResponse(reply=ai_reply, session_id=session_id)
    
    # If we hit max iterations (shouldn't happen normally)
    ai_reply = messages[-1].get("content", "I apologize, but I encountered an issue processing your request.")
    conversations[session_id].append({"role": "assistant", "content": ai_reply})
    return ChatResponse(reply=ai_reply, session_id=session_id)


# MCP Server Test Endpoints
@app.get("/test/mcp/tools")
async def list_mcp_tools():
    """List all available tools from the MCP server (discovered dynamically)."""
    try:
        async with Client(MCP_SERVER_URL) as mcp_client:
            tools = await mcp_client.list_tools()
            return JSONResponse({
                "status": "connected",
                "transport": "http",
                "mcp_server_url": MCP_SERVER_URL,
                "tools_count": len(tools),
                "tools": [
                    {
                        "name": tool.name,
                        "description": tool.description,
                        "input_schema": tool.inputSchema if hasattr(tool, 'inputSchema') else None
                    }
                    for tool in tools
                ]
            })
    except Exception as e:
        return JSONResponse({"status": "error", "error": str(e)}, status_code=500)


@app.post("/test/mcp/call-tool")
async def call_mcp_tool(request: ToolCallRequest):
    """Call any tool on the MCP server dynamically."""
    try:
        async with Client(MCP_SERVER_URL) as mcp_client:
            result = await mcp_client.call_tool(request.tool_name, request.parameters)
            return JSONResponse({
                "status": "success",
                "transport": "http",
                "mcp_server_url": MCP_SERVER_URL,
                "tool_name": request.tool_name,
                "parameters": request.parameters,
                "result": result.content[0].text
            })
    except Exception as e:
        return JSONResponse({"status": "error", "error": str(e)}, status_code=500)
