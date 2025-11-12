🧠 Princeton Hackathon 2025 — MCP File Search + LLM Backend

This repository contains our project for Princeton Hackathon 2025, integrating an MCP (Model Context Protocol) server for file storage and retrieval with an LLM backend for intelligent query handling.

🚀 Overview

This project enables seamless interaction between a Large Language Model (LLM) backend and a custom MCP server that connects to Google Drive.
Users can store, search, and retrieve files through natural language, with the LLM interpreting requests and the MCP server handling the underlying API calls.

🔧 Key Features

MCP Server Integration: Uses Google Drive API for file storage, retrieval, and search.

LLM Backend: Processes natural language input using a customizable system prompt.

Web Interface: Simple HTML/JS frontend for interacting with the backend.

Secure Credentials: Uses .env and credentials.json for protected API access.

Modular Design: Clean structure for easy debugging and scalability.

📁 Project Structure
.
├── llm_backend/
│   ├── prompts/
│   │   └── system_prompt.xml         # System prompt configuration for the LLM
│   ├── static/
│   │   ├── script.js                 # Handles frontend-backend communication
│   │   └── style.css                 # Basic frontend styling
│   ├── templates/
│   │   └── index.html                # Web interface template
│   ├── main.py                       # Entry point for the backend
│   ├── mcp_client.py                 # Client that connects to the MCP server
│   ├── requirements.txt              # Python dependencies for LLM backend
│   ├── .env                          # Environment variables
│   └── .gitignore                    # Files to ignore in Git
│
├── mcp_server/
│   ├── credentials.json              # Google Drive API credentials
│   ├── drive_utils.py                # Utility functions for Drive API
│   ├── server.py                     # Core MCP server script
│   ├── token.pickle                  # Stores user access tokens
│   ├── requirements.txt              # MCP server dependencies
│   └── README.md                     # Server-specific documentation
│
├── README.md                         # Main project documentation (you are here)
└── requirements.txt                  # Combined requirements (optional)

⚙️ Setup Guide
1. Clone the Repository
git clone https://github.com/yourusername/princeton-hackathon-2025.git
cd princeton-hackathon-2025

2. Set Up MCP Server

This handles Google Drive communication.

cd mcp_server
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt


Run the MCP server:

fastmcp run server.py:mcp --transport http --port 8001


If using Google Drive:

Place your credentials.json file in the mcp_server/ directory.

The first run will open a browser window for Google authentication.

A token.pickle file will be generated automatically.

3. Set Up LLM Backend
cd llm_backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt


Run the backend:

uvicorn main:app --reload 


This starts the LLM service, which can communicate with the MCP server.

4. Run the Web Interface

Once the backend is running, open:

http://localhost:5000


You can now interact with the LLM through the web interface.

🔒 Environment Variables

Your .env file should include:

OPENAI_API_KEY=your_openai_api_key_here
MCP_SERVER_URL=http://localhost:8000

🧩 Tech Stack

Python 3.10+

FastAPI – for both LLM backend and MCP server

Google Drive API – for file management

FastMCP – to run the MCP service

HTML, CSS, JS – frontend interaction

🤝 Contributors

TheJos — Princeton Hackathon 2025


🧠 Future Improvements

Add multiple storage backends (Dropbox, OneDrive)

Enhance UI for document visualization

Add user authentication

Implement caching for faster retrieval

