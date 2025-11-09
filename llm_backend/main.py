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
from mcp_client import get_mcp_tools_for_openai, execute_mcp_tool

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Initialize OpenAI client
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable is required")

client = OpenAI(api_key=OPENAI_API_KEY)

# Load system prompt
def load_system_prompt():
    """Load system prompt from XML file."""
    path = os.path.join(os.path.dirname(__file__), "prompts", "system_prompt.xml")
    tree = ET.parse(path)
    root = tree.getroot()
    purpose = root.findtext("Purpose", default="")
    guidelines = root.findtext("Guidelines", default="")
    return f"{purpose.strip()}\n\nGuidelines:\n{guidelines.strip()}"

SYSTEM_PROMPT = load_system_prompt()

# In-memory conversation storage
conversations = {}

# Pydantic models for request/response validation
class ChatMessage(BaseModel):
    message: str
    session_id: str | None = None

class ChatResponse(BaseModel):
    reply: str
    session_id: str

@app.get("/", response_class=HTMLResponse)
async def get_home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/chat/new")
async def new_chat():
    """Create a new chat session."""
    session_id = str(uuid.uuid4())
    conversations[session_id] = []
    return JSONResponse({"session_id": session_id})


@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(chat: ChatMessage):
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
    
    try:
        while iteration < max_iterations:
            iteration += 1
            
            # Call OpenAI API with tools available
            try:
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=messages,
                    tools=mcp_tools if mcp_tools else None,  
                    tool_choice="auto" if mcp_tools else None,  # Let AI decide when to use tools
                    max_tokens=500,
                )
            except Exception as e:
                error_msg = f"OpenAI API error: {str(e)}"
                conversations[session_id].append({"role": "assistant", "content": error_msg})
                return ChatResponse(reply=error_msg, session_id=session_id)

            response_message = response.choices[0].message
            
            # Add assistant's response to messages ( conversation flow)
            messages.append(response_message)

            # Check if the AI wants to call a tool
            if response_message.tool_calls:
                for tool_call in response_message.tool_calls:
                    tool_name = tool_call.function.name
                    try:
                        tool_args = json.loads(tool_call.function.arguments)
                    except json.JSONDecodeError as e:
                        tool_result = f"Error parsing tool arguments: {str(e)}"
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "name": tool_name,
                            "content": tool_result
                        })
                        continue
                    
                    # Execute the MCP tool
                    tool_result = await execute_mcp_tool(tool_name, tool_args)
                    
                    # Add tool result to messages so AI can use it
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": tool_name,
                        "content": tool_result
                    })
                
                # Continue the loop 
                continue
            else:
                # No tool calls
                ai_reply = response_message.content
                
                # Save assistant message to conversation history
                conversations[session_id].append({"role": "assistant", "content": ai_reply})
                
                return ChatResponse(reply=ai_reply, session_id=session_id)

        # If we hit max iterations, raise an error
        raise Exception("MAX_ITERATIONS")
    
    except Exception as e:
        if str(e) == "MAX_ITERATIONS":
            error_msg = "ERROR: MAX ITERATIONS REACHED"
        else:
            error_msg = f"An unexpected error occurred: {str(e)}"
        conversations[session_id].append({"role": "assistant", "content": error_msg})
        return ChatResponse(reply=error_msg, session_id=session_id)
