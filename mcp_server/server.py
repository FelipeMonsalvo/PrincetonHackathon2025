from fastmcp import FastMCP

# Dummy files for hackathon testing
FILES = [
    {"id": "1", "name": "meeting_notes.txt", "content": "Discuss project deadlines and tasks"},
    {"id": "2", "name": "project_ideas.txt", "content": "Ideas for new hackathon projects"},
    {"id": "3", "name": "document3.txt", "content": "Random notes and reminders"},
    {"id": "4", "name": "tasks.txt", "content": "Finish report, call supplier, update slides"},
]

mcp = FastMCP(name="file-search-mcp")


@mcp.tool()
def search_files(query: str) -> str:
    """Search for files by query string. Searches both file names and content.
    
    Args:
        query: The search query to find matching files
        
    Returns:
        A formatted string with search results
    """
    query_lower = query.lower()
    
    results = [
        f for f in FILES 
        if query_lower in f["name"].lower() or query_lower in f["content"].lower()
    ]
    
    if results:
        result_text = f"Found {len(results)} file(s):\n\n"
        for file in results:
            result_text += f"ID: {file['id']}\n"
            result_text += f"Name: {file['name']}\n"
            result_text += f"Content: {file['content']}\n\n"
        return result_text
    else:
        return f"No files found matching query: {query}"


@mcp.tool()
def list_files() -> str:
    """List all available files.
    
    Returns:
        A formatted string listing all files
    """
    result_text = "Available files:\n\n"
    for file in FILES:
        result_text += f"ID: {file['id']}\n"
        result_text += f"Name: {file['name']}\n"
        result_text += f"Content preview: {file['content'][:50]}...\n\n"
    return result_text


@mcp.tool()
def get_file(file_id: str) -> str:
    file = next((f for f in FILES if f["id"] == file_id), None)
    if file:
        return f"File: {file['name']}\n\nContent:\n{file['content']}"
    else:
        return f"File with ID '{file_id}' not found"


@mcp.resource("file://{file_id}", name="file", description="Read a file by ID", mime_type="text/plain")
def get_file_resource(file_id: str) -> str:
    """Get file content by ID"""
    file = next((f for f in FILES if f["id"] == file_id), None)
    if file:
        return file['content']
    else:
        raise ValueError(f"File with ID '{file_id}' not found")

