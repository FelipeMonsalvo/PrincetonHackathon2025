import os
import uuid
import xml.etree.ElementTree as ET
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 🔹 Load system prompt from XML
def load_system_prompt():
    path = os.path.join(os.path.dirname(__file__), "prompts", "system_prompt.xml")
    tree = ET.parse(path)
    root = tree.getroot()
    purpose = root.findtext("Purpose", default="")
    guidelines = root.findtext("Guidelines", default="")
    return f"{purpose.strip()}\n\nGuidelines:\n{guidelines.strip()}"

SYSTEM_PROMPT = load_system_prompt()
print("✅ Loaded system prompt:")
print(SYSTEM_PROMPT[:200], "...\n")

# 🔹 Store conversations in memory
conversations = {}

# 🔹 Data models
class ChatMessage(BaseModel):
    message: str
    session_id: str | None = None  # optional: assign later

class ChatResponse(BaseModel):
    reply: str
    session_id: str

# 🔹 Home route
@app.get("/", response_class=HTMLResponse)
async def get_home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# 🔹 Create a new chat session
@app.post("/chat/new")
async def new_chat():
    session_id = str(uuid.uuid4())
    conversations[session_id] = []
    print(f"🆕 Created session: {session_id}")
    return JSONResponse({"session_id": session_id})

# 🔹 Chat endpoint
@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(chat: ChatMessage):
    """Handle the AI chat call with per-session memory."""

    # If no session exists, create one
    session_id = chat.session_id or str(uuid.uuid4())
    if session_id not in conversations:
        conversations[session_id] = []

    # Build the conversation history
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(conversations[session_id])
    messages.append({"role": "user", "content": chat.message})

    # Send to OpenAI
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        max_tokens=500,
    )

    # Extract reply
    ai_reply = response.choices[0].message.content

    # Save both user and assistant messages
    conversations[session_id].append({"role": "user", "content": chat.message})
    conversations[session_id].append({"role": "assistant", "content": ai_reply})

    # Return to frontend
    return ChatResponse(reply=ai_reply, session_id=session_id)
