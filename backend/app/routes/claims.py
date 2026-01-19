"""
Claims API Routes

Endpoints for claim extraction, evidence mapping, and claim clustering.
"""

from typing import Optional, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.claim import (
    ClaimResponse, ClaimEvidenceMap, ClaimExtractionRequest,
    ClaimExtractionResponse, ClaimSearchRequest, ClaimSearchResponse,
    ClaimClusteringRequest, ClaimClusteringResponse, ClaimCreate,
    ClaimUpdate, EvidenceCreate, EvidenceResponse
)
from app.services.intelligence.claim_extraction import ClaimExtractionService
from app.services.embedding.service import EmbeddingService
from app.models.claim import Claim, ClaimEvidence

router = APIRouter(prefix="/claims", tags=["claims"])


async def get_claim_service(db: AsyncSession = Depends(get_db)) -> ClaimExtractionService:
    """Get claim extraction service instance."""
    embedding_service = EmbeddingService(db)
    return ClaimExtractionService(embedding_service=embedding_service, db=db)


@router.post("/extract", response_model=ClaimExtractionResponse)
async def extract_claims(
    request: ClaimExtractionRequest,
    service: ClaimExtractionService = Depends(get_claim_service),
    db: AsyncSession = Depends(get_db)
):
    """
    Extract claims from paper chunks.

    Analyzes the specified chunks and extracts scientific claims,
    creating new claims or linking to existing similar claims.
    """
    try:
        import time
        start_time = time.time()

        # Get chunks (simplified - would need actual chunk retrieval)
        # For now, assume chunks are accessible via chunk_ids
        chunks = []  # await get_chunks_by_ids(request.chunk_ids, db)

        # Extract claims from chunks
        claims = await service.extract_claims_from_paper(
            paper_id=str(request.paper_id),
            chunks=chunks
        )

        processing_time = int((time.time() - start_time) * 1000)

        return ClaimExtractionResponse(
            claims=[ClaimResponse.from_orm(claim) for claim in claims],
            evidence_links=[],  # Would populate with actual evidence links
            processing_time_ms=processing_time
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Claim extraction failed: {str(e)}")


@router.get("/{claim_id}", response_model=ClaimResponse)
async def get_claim(
    claim_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific claim by ID."""
    claim = await db.get(Claim, claim_id)
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    return ClaimResponse.from_orm(claim)


@router.get("/{claim_id}/evidence", response_model=ClaimEvidenceMap)
async def get_claim_evidence(
    claim_id: UUID,
    service: ClaimExtractionService = Depends(get_claim_service)
):
    """Get full evidence map for a claim."""
    try:
        evidence_map = await service.get_claim_evidence_map(str(claim_id))
        return evidence_map
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get evidence map: {str(e)}")


@router.post("/search", response_model=ClaimSearchResponse)
async def search_claims(
    request: ClaimSearchRequest,
    service: ClaimExtractionService = Depends(get_claim_service),
    db: AsyncSession = Depends(get_db)
):
    """
    Search for claims by text similarity and filters.

    Supports semantic search with optional domain and type filtering.
    """
    try:
        import time
        from sqlalchemy import select
        start_time = time.time()

        # For now, implement basic filtering
        # In production, this would use vector search
        query = select(Claim)

        if request.domain_filter:
            # Filter by domain tags
            query = query.where(Claim.domain_tags.overlap(request.domain_filter))

        if request.claim_type_filter:
            query = query.where(Claim.claim_type.in_(request.claim_type_filter))

        if request.min_evidence_strength and request.min_evidence_strength > 0:
            query = query.where(Claim.evidence_strength >= request.min_evidence_strength)

        query = query.limit(request.limit or 50)

        result = await db.execute(query)
        claims = result.scalars().all()

        search_time = int((time.time() - start_time) * 1000)

        return ClaimSearchResponse(
            claims=[ClaimResponse.model_validate(claim) for claim in claims],
            total_count=len(claims),  # Simplified - would need actual count
            search_time_ms=search_time
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Claim search failed: {str(e)}")


@router.post("/cluster", response_model=ClaimClusteringResponse)
async def cluster_claims(
    request: ClaimClusteringRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Cluster semantically similar claims.

    Groups claims by meaning and creates canonical representations.
    """
    try:
        import time
        start_time = time.time()

        # Simplified clustering - in production would use ML clustering
        # For now, just return the input claims as unclustered

        processing_time = int((time.time() - start_time) * 1000)

        return ClaimClusteringResponse(
            clusters=[],  # Would populate with actual clusters
            unclustered_claims=request.claim_ids,
            processing_time_ms=processing_time
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Claim clustering failed: {str(e)}")


@router.put("/{claim_id}", response_model=ClaimResponse)
async def update_claim(
    claim_id: UUID,
    request: ClaimUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update claim metadata."""
    claim = await db.get(Claim, claim_id)
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    # Update fields
    update_data = request.dict(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(claim, field):
            setattr(claim, field, value)

    await db.commit()
    await db.refresh(claim)

    return ClaimResponse.from_orm(claim)


@router.post("/{claim_id}/evidence", response_model=EvidenceResponse)
async def add_claim_evidence(
    claim_id: UUID,
    request: EvidenceCreate,
    db: AsyncSession = Depends(get_db)
):
    """Add new evidence to a claim."""
    claim = await db.get(Claim, claim_id)
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    evidence = ClaimEvidence(
        claim_id=claim_id,
        **request.dict()
    )

    db.add(evidence)
    await db.commit()
    await db.refresh(evidence)

    return EvidenceResponse.from_orm(evidence)


@router.get("/stats/summary")
async def get_claims_summary(db: AsyncSession = Depends(get_db)):
    """Get summary statistics about claims in the system."""
    try:
        from sqlalchemy import func, select

        # Get basic counts
        total_claims = await db.scalar(select(func.count(Claim.id)))
        total_evidence = await db.scalar(select(func.count(ClaimEvidence.id)))

        # Get claims by type
        type_counts = await db.execute(
            select(Claim.claim_type, func.count(Claim.id))
            .group_by(Claim.claim_type)
        )
        claims_by_type = dict(type_counts.all())

        # Get top domains (simplified - avoid unnest for cross-DB compatibility)
        top_domains = {}  # Would implement proper domain counting

        return {
            "total_claims": total_claims or 0,
            "total_evidence": total_evidence or 0,
            "claims_by_type": claims_by_type,
            "top_domains": top_domains
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get summary: {str(e)}")