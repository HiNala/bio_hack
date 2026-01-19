"""
Export and Import API Routes

Endpoints for exporting data and importing documents.
"""

import json
from typing import Optional, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
import io
import csv

from app.database import get_db
from app.models import Paper, Workspace, Collection
from app.errors import NotFoundError, ValidationError
from app.utils.validation import validate_paper_metadata

router = APIRouter(prefix="/export", tags=["Export/Import"])


@router.get("/workspace/{workspace_id}/papers")
async def export_workspace_papers(
    workspace_id: str,
    format: str = "json",
    include_abstracts: bool = True,
    db: AsyncSession = Depends(get_db)
):
    """
    Export all papers from a workspace.

    Supports JSON and CSV formats.
    """
    try:
        workspace_uuid = UUID(workspace_id)
    except ValueError:
        raise ValidationError("Invalid workspace ID format", "workspace_id")

    # Check if workspace exists
    workspace = await db.get(Workspace, workspace_uuid)
    if not workspace:
        raise NotFoundError("Workspace", workspace_id)

    # Get papers in workspace (through collections)
    from sqlalchemy import select
    from app.models import CollectionPaper

    result = await db.execute(
        select(Paper)
        .join(CollectionPaper, Paper.id == CollectionPaper.paper_id)
        .join(Collection, CollectionPaper.collection_id == Collection.id)
        .where(Collection.workspace_id == workspace_uuid)
        .distinct()
    )
    papers = result.scalars().all()

    if format == "json":
        # Export as JSON
        data = []
        for paper in papers:
            paper_data = {
                "id": str(paper.id),
                "title": paper.title,
                "authors": paper.authors,
                "year": paper.year,
                "doi": paper.doi,
                "url": paper.landing_url,
                "citation_count": paper.citation_count,
                "venue": paper.venue,
            }
            if include_abstracts and paper.abstract:
                paper_data["abstract"] = paper.abstract

            data.append(paper_data)

        json_data = json.dumps(data, indent=2, ensure_ascii=False)

        def generate():
            yield json_data

        return StreamingResponse(
            generate(),
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename=workspace-{workspace_id}-papers.json"}
        )

    elif format == "csv":
        # Export as CSV
        output = io.StringIO()
        writer = csv.writer(output)

        # Write header
        header = ["ID", "Title", "Authors", "Year", "DOI", "URL", "Citations", "Venue"]
        if include_abstracts:
            header.append("Abstract")
        writer.writerow(header)

        # Write data
        for paper in papers:
            row = [
                str(paper.id),
                paper.title,
                "; ".join(paper.authors) if paper.authors else "",
                str(paper.year) if paper.year else "",
                paper.doi or "",
                paper.landing_url or "",
                str(paper.citation_count or 0),
                paper.venue or "",
            ]
            if include_abstracts:
                row.append(paper.abstract or "")
            writer.writerow(row)

        output.seek(0)

        def generate():
            yield output.getvalue()

        return StreamingResponse(
            generate(),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=workspace-{workspace_id}-papers.csv"}
        )

    else:
        raise ValidationError("Format must be 'json' or 'csv'", "format")


@router.post("/import/papers")
async def import_papers(
    file: UploadFile = File(...),
    workspace_id: Optional[str] = None,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: AsyncSession = Depends(get_db)
):
    """
    Import papers from a JSON or CSV file.

    Creates papers and optionally adds them to a workspace.
    """
    if not file.filename:
        raise ValidationError("No file provided", "file")

    file_extension = file.filename.split('.')[-1].lower()

    if file_extension not in ['json', 'csv']:
        raise ValidationError("File must be JSON or CSV format", "file")

    # Validate workspace if provided
    workspace_uuid = None
    if workspace_id:
        try:
            workspace_uuid = UUID(workspace_id)
            workspace = await db.get(Workspace, workspace_uuid)
            if not workspace:
                raise NotFoundError("Workspace", workspace_id)
        except ValueError:
            raise ValidationError("Invalid workspace ID format", "workspace_id")

    # Read file content
    content = await file.read()
    content_str = content.decode('utf-8')

    try:
        if file_extension == 'json':
            papers_data = json.loads(content_str)
        else:
            # Parse CSV
            import csv
            reader = csv.DictReader(io.StringIO(content_str))
            papers_data = list(reader)

        # Process papers in background
        background_tasks.add_task(
            process_imported_papers,
            papers_data,
            workspace_uuid,
            db
        )

        return {
            "message": f"Import started for {len(papers_data)} papers",
            "papers_count": len(papers_data),
            "workspace_id": workspace_id
        }

    except json.JSONDecodeError:
        raise ValidationError("Invalid JSON format", "file")
    except Exception as e:
        raise ValidationError(f"Failed to parse file: {str(e)}", "file")


async def process_imported_papers(papers_data: List[dict], workspace_uuid: Optional[UUID], db):
    """
    Process imported papers in the background.

    This function handles the actual import logic.
    """
    from app.models import Source
    from datetime import datetime
    from sqlalchemy import select

    try:
        # Get or create a generic source for imported papers
        result = await db.execute(
            select(Source).where(Source.name == "Imported")
        )
        source = result.scalar_one_or_none()

        if not source:
            source = Source(
                name="Imported",
                base_url="https://imported.local",
                is_active=True,
                created_at=datetime.utcnow()
            )
            db.add(source)
            await db.commit()

        imported_count = 0

        for paper_data in papers_data:
            # Validate and sanitize paper data
            validated_data = validate_paper_metadata(paper_data)

            # Create paper from validated data
            paper = Paper(
                source_id=source.id,
                external_id=validated_data.get('doi') or f"imported-{datetime.utcnow().timestamp()}",
                title=validated_data['title'],
                abstract=validated_data.get('abstract'),
                authors=validated_data.get('authors', []),
                year=validated_data.get('year'),
                doi=validated_data.get('doi'),
                landing_url=validated_data.get('url'),
                citation_count=paper_data.get('citation_count', 0),  # Not validated, just a number
                venue=validated_data.get('venue'),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )

            db.add(paper)
            imported_count += 1

        await db.commit()

        print(f"Successfully imported {imported_count} papers")

    except Exception as e:
        print(f"Failed to import papers: {str(e)}")
        await db.rollback()