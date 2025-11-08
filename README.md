# Princeton Hackathon 2025

This repository contains the project for Princeton Hackathon 2025.

## Project Structure

- `llm_backend/` - LLM backend service
- `mcp_server/` - MCP (Model Context Protocol) server for file searching

## Quick Start

### MCP Server

See [mcp_server/README.md](mcp_server/README.md) for detailed setup instructions.

Quick setup:
```bash
cd mcp_server
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
fastmcp run server.py
```

### LLM Backend

See `llm_backend/` for backend setup instructions.

## Requirements

- Python 3.10 or higher
- pip

