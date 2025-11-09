from fastmcp import FastMCP
from drive_utils import get_drive_service

mcp = FastMCP(name="google-drive-mcp")


@mcp.tool()
def list_files() -> str:
    """List first 10 files in Google Drive."""
    service = get_drive_service()
    results = service.files().list(
        pageSize=10, fields="files(id, name, mimeType, modifiedTime)"
    ).execute()
    files = results.get("files", [])
    if not files:
        return "No files found in Google Drive."
    
    result_text = "Available Google Drive files:\n\n"
    for f in files:
        result_text += f"ID: {f['id']}\n"
        result_text += f"Name: {f['name']}\n"
        result_text += f"Type: {f['mimeType']}\n"
        result_text += f"Modified: {f['modifiedTime']}\n\n"
    return result_text


@mcp.tool()
def search_files(query: str) -> str:
    """Search Google Drive for files matching a query string."""
    service = get_drive_service()
    results = service.files().list(
        q=f"name contains '{query}' or fullText contains '{query}'",
        fields="files(id, name, mimeType, modifiedTime)",
        pageSize=10,
    ).execute()
    files = results.get("files", [])
    if not files:
        return f"No files found matching query: {query}"

    result_text = f"Found {len(files)} file(s) matching '{query}':\n\n"
    for f in files:
        result_text += f"ID: {f['id']}\n"
        result_text += f"Name: {f['name']}\n"
        result_text += f"Type: {f['mimeType']}\n"
        result_text += f"Modified: {f['modifiedTime']}\n\n"
    return result_text


@mcp.tool()
def get_file(file_id: str) -> str:
    """Read a Google Drive file by ID (Google Docs or plain text)."""
    service = get_drive_service()
    file = service.files().get(fileId=file_id, fields="id, name, mimeType").execute()
    mime = file["mimeType"]

    # Handle Google Docs (convert to plain text)
    if mime == "application/vnd.google-apps.document":
        from googleapiclient.http import MediaIoBaseDownload
        import io

        request = service.files().export_media(fileId=file_id, mimeType="text/plain")
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
        fh.seek(0)
        return f"File: {file['name']}\n\n{fh.read().decode('utf-8')}"

    else:
        # For non-Google Docs, just return metadata for now
        return f"File: {file['name']} (type: {mime})\n\nContent preview not supported yet."


@mcp.resource("drive://{file_id}", name="drive-file", description="Read a file by ID", mime_type="text/plain")
def get_file_resource(file_id: str) -> str:
    """Return raw file content from Google Drive."""
    return get_file(file_id)

