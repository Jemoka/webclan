import os
import uuid
import re
import subprocess
import shutil
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel, validator

app = FastAPI()

# Constants
WORK_DIR = Path("/webclan/work")
BIN_DIR = Path("/webclan/unix/bin")
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
COMMAND_TIMEOUT = 300  # 5 minutes
ALLOWED_EXTENSION = ".cha"

# Ensure directories exist
WORK_DIR.mkdir(parents=True, exist_ok=True)


class CommandRequest(BaseModel):
    unique_id: str
    binary: str
    args: list[str] = []

    @validator('unique_id')
    def validate_unique_id(cls, v):
        # Must be a valid UUID to prevent path traversal
        try:
            uuid.UUID(v)
        except ValueError:
            raise ValueError("unique_id must be a valid UUID")
        return v

    @validator('binary')
    def validate_binary(cls, v):
        # Only allow alphanumeric, dash, and underscore (no path separators)
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError("binary name contains invalid characters")
        return v

    @validator('args')
    def validate_args(cls, v):
        # Check each argument for potential injection attempts
        for arg in v:
            # Reject args with suspicious patterns
            if any(char in arg for char in [';', '&', '|', '`', '$', '\n', '\r']):
                raise ValueError(f"argument contains forbidden characters: {arg}")
            # Reject args trying to escape working directory (except relative refs within)
            if arg.startswith('/') or '..' in arg:
                raise ValueError(f"argument contains forbidden path traversal: {arg}")
        return v


def validate_filename(filename: str) -> bool:
    """Validate uploaded filename is safe"""
    # Check extension
    if not filename.lower().endswith(ALLOWED_EXTENSION):
        return False

    # Prevent path traversal in filename
    if '/' in filename or '\\' in filename or '..' in filename:
        return False

    # Only allow safe characters in filename
    if not re.match(r'^[a-zA-Z0-9_.-]+$', filename):
        return False

    return True


def validate_file_content(content: bytes) -> bool:
    """Basic content validation for .cha files"""
    try:
        # .cha files should be text-based, try to decode
        content.decode('utf-8')
        return True
    except UnicodeDecodeError:
        return False


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)) -> JSONResponse:
    """
    Upload a .cha file and get a unique_id for subsequent operations
    """
    # Validate filename
    if not file.filename or not validate_filename(file.filename):
        raise HTTPException(
            status_code=400,
            detail="Invalid filename. Must be alphanumeric with .cha extension and no path separators"
        )

    # Read file content
    content = await file.read()

    # Check file size
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail=f"File too large. Max size: {MAX_FILE_SIZE} bytes")

    # Validate content
    if not validate_file_content(content):
        raise HTTPException(status_code=400, detail="File content validation failed. Must be valid UTF-8 text.")

    # Generate unique ID
    unique_id = str(uuid.uuid4())
    work_path = WORK_DIR / unique_id

    # Create working directory
    try:
        work_path.mkdir(parents=True, exist_ok=False)
    except FileExistsError:
        # Extremely unlikely with UUID, but handle it
        raise HTTPException(status_code=500, detail="Failed to create unique workspace")

    # Write file to disk
    file_path = work_path / file.filename
    try:
        with open(file_path, 'wb') as f:
            f.write(content)
    except Exception as e:
        # Clean up on failure
        shutil.rmtree(work_path, ignore_errors=True)
        raise HTTPException(status_code=500, detail="Failed to save file")

    return JSONResponse({
        "unique_id": unique_id,
        "filename": file.filename,
        "size": len(content),
        "path": str(file_path)
    })


@app.post("/execute")
async def execute_command(request: CommandRequest) -> JSONResponse:
    """
    Execute a binary from /webclan/unix/bin with the given arguments
    in the context of the unique_id workspace
    """
    # Validate unique_id workspace exists
    work_path = WORK_DIR / request.unique_id
    if not work_path.exists() or not work_path.is_dir():
        raise HTTPException(status_code=404, detail="Workspace not found")

    # Construct binary path - only basename is used to prevent traversal
    binary_name = os.path.basename(request.binary)
    binary_path = BIN_DIR / binary_name

    # Verify binary exists and is executable
    if not binary_path.exists():
        raise HTTPException(status_code=400, detail=f"Binary '{binary_name}' not found")

    if not os.access(binary_path, os.X_OK):
        raise HTTPException(status_code=400, detail=f"Binary '{binary_name}' is not executable")

    # Ensure binary is actually in the bin directory (no symlinks escaping)
    try:
        binary_path_resolved = binary_path.resolve()
        if not str(binary_path_resolved).startswith(str(BIN_DIR.resolve())):
            raise HTTPException(status_code=403, detail="Access denied: binary outside allowed directory")
    except Exception:
        raise HTTPException(status_code=403, detail="Failed to resolve binary path")

    # Execute command with strict security controls
    try:
        result = subprocess.run(
            [str(binary_path)] + request.args,
            cwd=str(work_path),  # Run in isolated workspace
            capture_output=True,
            timeout=COMMAND_TIMEOUT,
            shell=False,  # Critical: prevent shell injection
            text=True,
            env={  # Minimal environment
                "PATH": str(BIN_DIR),
                "HOME": str(work_path),
                "LANG": "C.UTF-8"
            }
        )

        return JSONResponse({
            "unique_id": request.unique_id,
            "binary": binary_name,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr
        })

    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=408, detail=f"Command timed out after {COMMAND_TIMEOUT} seconds")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Command execution failed")


@app.get("/list/{unique_id}")
async def list_files(unique_id: str) -> JSONResponse:
    """
    List files in the workspace for a given unique_id
    """
    # Validate UUID format
    try:
        uuid.UUID(unique_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid unique_id format")

    work_path = WORK_DIR / unique_id
    if not work_path.exists():
        raise HTTPException(status_code=404, detail="Workspace not found")

    try:
        files = []
        for item in work_path.iterdir():
            files.append({
                "name": item.name,
                "size": item.stat().st_size if item.is_file() else None,
                "type": "file" if item.is_file() else "directory"
            })

        return JSONResponse({
            "unique_id": unique_id,
            "files": files
        })
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to list files")


@app.get("/download/{unique_id}/{filename}")
async def download_file(unique_id: str, filename: str) -> JSONResponse:
    """
    Download a file from the workspace as UTF-8 text in JSON response
    """
    # Validate UUID format
    try:
        uuid.UUID(unique_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid unique_id format")

    # Validate filename (prevent path traversal)
    if '/' in filename or '\\' in filename or '..' in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")

    # Only allow safe characters
    if not re.match(r'^[a-zA-Z0-9_.-]+$', filename):
        raise HTTPException(status_code=400, detail="Filename contains invalid characters")

    work_path = WORK_DIR / unique_id
    if not work_path.exists():
        raise HTTPException(status_code=404, detail="Workspace not found")

    file_path = work_path / filename

    # Ensure file exists and is actually a file
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    if not file_path.is_file():
        raise HTTPException(status_code=400, detail="Not a file")

    # Security: ensure resolved path is within workspace
    try:
        if not str(file_path.resolve()).startswith(str(work_path.resolve())):
            raise HTTPException(status_code=403, detail="Access denied")
    except Exception:
        raise HTTPException(status_code=403, detail="Failed to resolve file path")

    # Read file content as UTF-8
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        return JSONResponse({
            "unique_id": unique_id,
            "filename": filename,
            "size": len(content.encode('utf-8')),
            "content": content
        })
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File is not valid UTF-8 text")
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to read file")


@app.delete("/cleanup/{unique_id}")
async def cleanup_workspace(unique_id: str) -> JSONResponse:
    """
    Delete the workspace for a given unique_id
    """
    # Validate UUID format
    try:
        uuid.UUID(unique_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid unique_id format")

    work_path = WORK_DIR / unique_id
    if not work_path.exists():
        raise HTTPException(status_code=404, detail="Workspace not found")

    # Extra safety: ensure we're deleting within WORK_DIR
    try:
        if not str(work_path.resolve()).startswith(str(WORK_DIR.resolve())):
            raise HTTPException(status_code=403, detail="Access denied")

        shutil.rmtree(work_path)
        return JSONResponse({"message": "Workspace deleted", "unique_id": unique_id})
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to delete workspace")


@app.get("/binaries")
async def list_binaries() -> JSONResponse:
    """
    List available binaries that can be executed
    """
    try:
        if not BIN_DIR.exists():
            return JSONResponse({"binaries": []})

        binaries = []
        for item in BIN_DIR.iterdir():
            if item.is_file() and os.access(item, os.X_OK):
                binaries.append(item.name)

        return JSONResponse({"binaries": sorted(binaries)})
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to list binaries")
