from fastmcp import FastMCP
from drive_utils import get_drive_service, get_first_5_folders, get_first_5_folders_with_names, find_folder_by_name

mcp = FastMCP(name="google-drive-mcp")


@mcp.tool()
def list_files(folder_id: str = None, folder_name: str = None) -> str:
    """
    List files in a specific folder or let the user pick from first 5 folders.
    Returns up to 10 files per folder.
    """
    service = get_drive_service()
    folder_ids = []

    # If user provided folder_name or folder_id, use it
    if folder_name:
        target_folder_id = find_folder_by_name(service, folder_name)
        if not target_folder_id:
            folders = get_first_5_folders_with_names(service)
            folder_names = [f.get("name", "Unknown") for f in folders]
            return f"Folder '{folder_name}' not found. Available folders: {', '.join(folder_names)}"
        folder_ids = [target_folder_id]
    elif folder_id:
        folder_ids = [folder_id]
    else:
        # No folder specified → list the first 5 folders for user to choose
        folders = get_first_5_folders_with_names(service)
        if not folders:
            return "No folders found in Google Drive."
        result_text = "First 5 folders:\n\n"
        for f in folders:
            result_text += f"- {f.get('name', 'Unknown')} (ID: {f['id']})\n"
        result_text += "\nPlease pick a folder by providing its name or ID."
        return result_text

    # Now list files in the chosen folder(s)
    results_text = []
    for f_id in folder_ids[:5]:
        try:
            results = service.files().list(
                q=f"'{f_id}' in parents and trashed=false",
                pageSize=10,
                fields="files(id, name, mimeType, modifiedTime)"
            ).execute()
            files = results.get("files", [])
            folder_name_display = next(
                (f.get("name") for f in get_first_5_folders_with_names(service) if f["id"] == f_id),
                "Unknown Folder"
            )
            results_text.append(f"\n📁 Folder: {folder_name_display}\n")
            for f in files:
                results_text.append(
                    f"- {f['name']} (ID: {f['id']}, Type: {f['mimeType']}, Modified: {f['modifiedTime']})"
                )
        except Exception as e:
            results_text.append(f"⚠️ Error listing files in folder {f_id}: {e}")

    return "\n".join(results_text) if results_text else "No files found."


@mcp.tool()
def search_files(query: str, folder_id: str = None, folder_name: str = None) -> str:
    """
    Search for files with a query in a specific folder or let the user pick from first 5 folders.
    Returns up to 10 matching files per folder.
    """
    service = get_drive_service()
    folder_ids = []

    if folder_name:
        target_folder_id = find_folder_by_name(service, folder_name)
        if not target_folder_id:
            folders = get_first_5_folders_with_names(service)
            folder_names = [f.get("name", "Unknown") for f in folders]
            return f"Folder '{folder_name}' not found. Available folders: {', '.join(folder_names)}"
        folder_ids = [target_folder_id]
    elif folder_id:
        folder_ids = [folder_id]
    else:
        # No folder specified → list first 5 folders for user
        folders = get_first_5_folders_with_names(service)
        if not folders:
            return "No folders found in Google Drive."
        result_text = "First 5 folders:\n\n"
        for f in folders:
            result_text += f"- {f.get('name', 'Unknown')} (ID: {f['id']})\n"
        result_text += "\nPlease pick a folder by providing its name or ID."
        return result_text

    # Search in chosen folder(s)
    results_text = []
    total_files = 0
    for f_id in folder_ids[:5]:
        try:
            full_query = f"'{f_id}' in parents and (name contains '{query}' or fullText contains '{query}') and trashed=false"
            results = service.files().list(
                q=full_query,
                pageSize=10,
                fields="files(id, name, mimeType, modifiedTime)"
            ).execute()
            files = results.get("files", [])
            if files:
                total_files += len(files)
                folder_name_display = next(
                    (f.get("name") for f in get_first_5_folders_with_names(service) if f["id"] == f_id),
                    "Unknown Folder"
                )
                results_text.append(f"\n📁 Folder: {folder_name_display}\n")
                for f in files:
                    results_text.append(
                        f"- {f['name']} (ID: {f['id']}, Type: {f['mimeType']}, Modified: {f['modifiedTime']})"
                    )
        except Exception as e:
            results_text.append(f"⚠️ Error searching in folder {f_id}: {e}")

    return "\n".join(results_text) if results_text else f"No files found matching '{query}'"

@mcp.tool()
def get_target_folders() -> str:
    """
    Get the first 5 folders from Google Drive that are being used for file operations.
    This helps save API credits by limiting operations to these folders.
    Uses cached folder data to minimize API calls.
    """
    service = get_drive_service()
    folders = get_first_5_folders_with_names(service)
    
    if not folders:
        return "No folders found in Google Drive."
    
    # Use cached folder names, but get modifiedTime if needed (one API call per folder)
    try:
        result_text = "Target folders (first 5 folders for API credit optimization):\n\n"
        for folder in folders:
            folder_id = folder["id"]
            folder_name = folder.get("name", "Unknown")
            # Get modifiedTime (requires API call, but we cache the rest)
            try:
                folder_info = service.files().get(
                    fileId=folder_id,
                    fields="modifiedTime"
                ).execute()
                modified_time = folder_info.get('modifiedTime', 'N/A')
            except:
                modified_time = 'N/A'
            
            result_text += f"ID: {folder_id}\n"
            result_text += f"Name: {folder_name}\n"
            result_text += f"Modified: {modified_time}\n\n"
        return result_text
    except Exception as e:
        # Fallback to cached data only
        result_text = "Target folders (first 5 folders for API credit optimization):\n\n"
        for folder in folders:
            result_text += f"ID: {folder['id']}\n"
            result_text += f"Name: {folder.get('name', 'Unknown')}\n\n"
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

@mcp.tool()
def summarize_file(file_id: str) -> str:
    """
    Fetch a file from Google Drive and return the first 100 characters of text.
    Supports Google Docs, .txt, .md, and .docx.
    """
    service = get_drive_service()
    
    # Get file metadata
    file = service.files().get(fileId=file_id, fields="id, name, mimeType").execute()
    mime = file["mimeType"]
    file_name = file["name"]
    text = ""

    from googleapiclient.http import MediaIoBaseDownload
    import io

    try:
        # Google Docs
        if mime == "application/vnd.google-apps.document":
            request = service.files().export_media(fileId=file_id, mimeType="text/plain")
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                _, done = downloader.next_chunk()
            fh.seek(0)
            text = fh.read().decode("utf-8")

        # Plain text or Markdown
        elif mime == "text/plain" or file_name.lower().endswith(".md"):
            request = service.files().get_media(fileId=file_id)
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                _, done = downloader.next_chunk()
            fh.seek(0)
            text = fh.read().decode("utf-8")

        # DOCX - Fixed condition check
        elif (mime == "application/vnd.openxmlformats-officedocument.wordprocessingml.document" or 
              file_name.lower().endswith(".docx")):
            from docx import Document
            request = service.files().get_media(fileId=file_id)
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                _, done = downloader.next_chunk()
            fh.seek(0)
            doc = Document(fh)
            text = "\n".join([p.text for p in doc.paragraphs])

        # Unsupported file types
        else:
            return f"File type not supported for summarization: {file_name} (MIME type: {mime})"

        # Truncate to first 100 characters
        truncated_text = text[:100].replace("\n", " ").strip()
        return f"File: {file_name}\nFirst 100 characters:\n{truncated_text}"

    except Exception as e:
        return f"Error reading file {file_name}: {str(e)}"
    
@mcp.resource("drive://{file_id}", name="drive-file", description="Read a file by ID", mime_type="text/plain")
def get_file_resource(file_id: str) -> str:
    """Return raw file content from Google Drive."""
    return get_file(file_id)

