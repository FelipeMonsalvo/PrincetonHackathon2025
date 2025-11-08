from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class ChatMessage(BaseModel):
    message: str

@app.get("/", response_class=HTMLResponse)
async def get_home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/chat")
async def chat_endpoint(chat: ChatMessage):
    """Handle the AI chat call."""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": chat.message}],
    )
    ai_reply = response.choices[0].message.content
    return JSONResponse({"reply": ai_reply})


# @app.post("/chat")
# async def chat_endpoint(chat: ChatMessage):
#     ai_reply = "Hello! This is a dummy AI reply. Your message was: " + chat.message
#     return JSONResponse({"reply": ai_reply})
