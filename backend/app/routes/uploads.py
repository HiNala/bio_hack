"""
File Upload API Routes

Endpoints for uploading and processing documents.
"""

import asyncio
import os
import shutil
from typing import Optional, List
from uuid import uuid4
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.errors import ValidationError, NotFoundError
from app.config import get_settings

router = APIRouter(prefix="/uploads", tags=["Uploads"])
settings = get_settings()


# Create uploads directory if it doesn't exist
UPLOAD_DIR = Path("/app/uploads")
try:
    UPLOAD_DIR.mkdir(exist_ok=True)
except PermissionError:
    # Fall back to a temp directory if we can't create the uploads dir
    import tempfile
    UPLOAD_DIR = Path(tempfile.gettempdir()) / "uploads"
    UPLOAD_DIR.mkdir(exist_ok=True)

# Allowed file types
ALLOWED_EXTENSIONS = {'.pdf', '.txt', '.md', '.html', '.docx', '.doc'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


def validate_file(file: UploadFile) -> None:
    """Validate uploaded file."""
    # Check file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise ValidationError(
            f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}",
            "file"
        )

    # Check file size
    if hasattr(file, 'size') and file.size > MAX_FILE_SIZE:
        raise ValidationError(
            f"File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB",
            "file"
        )


@router.post("/documents")
async def upload_document(
    file: UploadFile = File(...),
    workspace_id: Optional[str] = Query(None, description="Workspace to associate with"),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload a document file for processing.

    Supports PDF, TXT, MD, HTML, DOCX files.
    Document will be processed and added to the knowledge base.
    """
    validate_file(file)

    # Generate unique filename
    file_id = str(uuid4())
    file_ext = Path(file.filename).suffix.lower()
    filename = f"{file_id}{file_ext}"
    file_path = UPLOAD_DIR / filename

    try:
        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Start background processing
        background_tasks.add_task(
            process_uploaded_document,
            file_path,
            file.filename,
            workspace_id,
            db
        )

        return {
            "file_id": file_id,
            "filename": file.filename,
            "size": file_path.stat().st_size,
            "message": "File uploaded successfully. Processing started in background.",
            "workspace_id": workspace_id
        }

    except Exception as e:
        # Clean up file if something went wrong
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.post("/batch")
async def upload_batch_documents(
    files: List[UploadFile] = File(...),
    workspace_id: Optional[str] = Query(None, description="Workspace to associate with"),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload multiple documents at once.

    All files will be processed in parallel.
    """
    if len(files) > 10:
        raise ValidationError("Maximum 10 files allowed per batch upload", "files")

    uploaded_files = []
    file_paths = []

    try:
        for file in files:
            validate_file(file)

            # Generate unique filename
            file_id = str(uuid4())
            file_ext = Path(file.filename).suffix.lower()
            filename = f"{file_id}{file_ext}"
            file_path = UPLOAD_DIR / filename

            # Save file
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            uploaded_files.append({
                "file_id": file_id,
                "filename": file.filename,
                "size": file_path.stat().st_size,
            })
            file_paths.append((file_path, file.filename))

        # Start background processing for all files
        background_tasks.add_task(
            process_batch_documents,
            file_paths,
            workspace_id,
            db
        )

        return {
            "files": uploaded_files,
            "count": len(uploaded_files),
            "message": f"{len(uploaded_files)} files uploaded successfully. Processing started in background.",
            "workspace_id": workspace_id
        }

    except Exception as e:
        # Clean up files if something went wrong
        for file_path, _ in file_paths:
            if file_path.exists():
                file_path.unlink()
        raise HTTPException(status_code=500, detail=f"Batch upload failed: {str(e)}")


@router.get("/status/{file_id}")
async def get_upload_status(file_id: str, db: AsyncSession = Depends(get_db)):
    """
    Get the processing status of an uploaded file.
    """
    # In a real implementation, you'd check a processing status table
    # For now, return a placeholder response
    return {
        "file_id": file_id,
        "status": "processing",  # processing, completed, failed
        "progress": 0.5,
        "message": "Document is being processed"
    }


async def process_uploaded_document(file_path: Path, original_filename: str, workspace_id: Optional[str], db):
    """
    Process a single uploaded document.

    This would typically involve:
    1. Text extraction (for PDFs, DOCX)
    2. Text chunking
    3. Embedding generation
    4. Database storage
    """
    try:
        print(f"Processing uploaded document: {original_filename}")

        # TODO: Implement actual document processing
        # This is where you'd integrate with document processing libraries
        # like PyPDF2, python-docx, etc.

        # For now, just simulate processing
        await asyncio.sleep(2)

        print(f"Completed processing: {original_filename}")

    except Exception as e:
        print(f"Failed to process {original_filename}: {str(e)}")
    finally:
        # Clean up the uploaded file
        if file_path.exists():
            file_path.unlink()


async def process_batch_documents(file_paths: List[tuple], workspace_id: Optional[str], db):
    """
    Process multiple uploaded documents in parallel.
    """
    tasks = []
    for file_path, filename in file_paths:
        task = process_uploaded_document(file_path, filename, workspace_id, db)
        tasks.append(task)

    await asyncio.gather(*tasks, return_exceptions=True)