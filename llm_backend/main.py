import os
import xml.etree.ElementTree as ET
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def load_system_prompt():
    path = os.path.join(os.path.dirname(__file__), "prompts", "system_prompt.xml")
    tree = ET.parse(path)
    root = tree.getroot()
    purpose = root.findtext("Purpose", default="")
    guidelines = root.findtext("Guidelines", default="")
    return f"{purpose.strip()}\n\nGuidelines:\n{guidelines.strip()}"

SYSTEM_PROMPT = load_system_prompt()

class ChatMessage(BaseModel):
    message: str

@app.get("/", response_class=HTMLResponse)
async def get_home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/chat")
async def chat_endpoint(chat: ChatMessage):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": chat.message},
        ],
        max_tokens=500,
    )
    ai_reply = response.choices[0].message.content
    return JSONResponse({"reply": ai_reply})

