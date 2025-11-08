import os
import xml.etree.ElementTree as ET
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Mount static files here
app.mount("/static", StaticFiles(directory="static"), name="static")

class ChatMessage(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    reply: str
    session_id: str

@app.get("/", response_class=HTMLResponse)
async def get_home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(chat: ChatMessage):
    """Handle the AI chat call."""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": chat.message}],
        max_tokens=500,
    )
    
    # Extract AI reply
    ai_reply = response.choices[0].message.content
    
    # Add AI response to conversation history
    conversations[session_id].append({"role": "assistant", "content": ai_reply})
    
    return ChatResponse(reply=ai_reply, session_id=session_id)

@app.post("/chat/new")
async def new_chat():
    """Create a new chat session."""
    session_id = str(uuid.uuid4())
    conversations[session_id] = []
    return JSONResponse({"session_id": session_id})

