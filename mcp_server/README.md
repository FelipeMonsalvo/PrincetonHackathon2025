# MCP Server for Google Drive File Search

An MCP (Model Context Protocol) server for searching files. Currently uses dummy files for testing, will be integrated with Google Drive.

## Setup

### Prerequisites

- Python 3.10 or higher
- pip

### Installation

1. **Clone the repository** (if you haven't already):
```bash
git clone <repository-url>
cd PrincetonHackathon2025
```

2. **Navigate to the MCP server directory**:
```bash
cd mcp_server
```

3. **Create a virtual environment**:
```bash
python -m venv venv
```


5. **Install dependencies**:
```bash
pip install -r requirements.txt
```

## Running the Server

### Using FastMCP CLI (Recommended)

```bash
fastmcp run server.py
```

### Alternative: Direct Python

```bash
python server.py
```

The server will start and communicate via stdio, waiting for MCP client connections (like ChatGPT).

## Available Tools

- **search_files(query)**: Search for files by query string (searches both file names and content)
- **list_files()**: List all available files
- **get_file(file_id)**: Get the full content of a specific file by ID

## Available Resources

- **file://{file_id}**: Read a file by its ID via URI

## Testing with Dummy Files

The server currently uses dummy files:
- `meeting_notes.txt` - ID: 1
- `project_ideas.txt` - ID: 2
- `document3.txt` - ID: 3
- `tasks.txt` - ID: 4

## Connecting to ChatGPT

To connect this MCP server to ChatGPT, you'll need to configure ChatGPT's MCP settings to point to this server. The server runs via stdio and communicates using JSON-RPC.

## Next Steps

1. Integrate Google Drive API
2. Replace dummy files with real Google Drive file access
3. Add authentication for Google Drive
4. Connect to ChatGPT or other MCP clients

## Troubleshooting

- **Import errors**: Make sure you've activated your virtual environment and installed all dependencies
- **Server won't start**: Check that Python 3.10+ is installed and FastMCP is properly installed
- **Connection issues**: Ensure the server is running and configured correctly in your MCP client

