"""
Contradictions API Routes

Endpoints for contradiction detection and consensus analysis.
"""

from typing import Optional, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.contradiction import (
    ContradictionResponse, ConsensusReport, ConsensusReportRequest,
    ConsensusReportResponse, ContradictionAnalysisRequest,
    ContradictionAnalysisResponse, ContradictionDetectionRequest,
    ContradictionDetectionResponse
)
from app.services.intelligence.contradiction_detection import ContradictionDetectionService
from app.models.claim import Contradiction

router = APIRouter(prefix="/contradictions", tags=["contradictions"])


async def get_contradiction_service(db: AsyncSession = Depends(get_db)) -> ContradictionDetectionService:
    """Get contradiction detection service instance."""
    return ContradictionDetectionService(db=db)


@router.post("/analyze/{claim_id}", response_model=ContradictionAnalysisResponse)
async def analyze_claim_contradictions(
    claim_id: UUID,
    service: ContradictionDetectionService = Depends(get_contradiction_service)
):
    """
    Analyze contradictions for a specific claim.

    Finds all contradictory evidence pairs and generates explanations.
    """
    try:
        import time
        start_time = time.time()

        contradictions = await service.detect_contradictions(str(claim_id))

        # Get simplified evidence map
        evidence_map = await service.get_claim_evidence_map(str(claim_id))
        consensus_score = evidence_map.consensus_score

        analysis_time = int((time.time() - start_time) * 1000)

        return ContradictionAnalysisResponse(
            claim_id=claim_id,
            contradictions=[ContradictionResponse.from_orm(c) for c in contradictions],
            evidence_map={},  # Simplified - would include full evidence map
            consensus_score=consensus_score,
            analysis_time_ms=analysis_time
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Contradiction analysis failed: {str(e)}")


@router.post("/consensus", response_model=ConsensusReportResponse)
async def generate_consensus_report(
    request: ConsensusReportRequest,
    service: ContradictionDetectionService = Depends(get_contradiction_service)
):
    """
    Generate a consensus report for a research topic.

    Analyzes all relevant claims to identify areas of agreement,
    disagreement, and conditional findings.
    """
    try:
        import time
        start_time = time.time()

        report = await service.get_consensus_report(
            topic=request.topic,
            workspace_id=str(request.workspace_id) if request.workspace_id else None
        )

        generation_time = int((time.time() - start_time) * 1000)

        return ConsensusReportResponse(
            report=report,
            generation_time_ms=generation_time,
            claims_analyzed=len(report.consensus) + len(report.contested) + len(report.conditional),
            papers_covered=0  # Would calculate from claims
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Consensus report generation failed: {str(e)}")


@router.post("/detect", response_model=ContradictionDetectionResponse)
async def detect_contradictions(
    request: ContradictionDetectionRequest,
    service: ContradictionDetectionService = Depends(get_contradiction_service)
):
    """
    Detect contradictions across multiple claims.

    Analyzes pairs of claims for potential contradictions and conflicts.
    """
    try:
        import time
        start_time = time.time()

        all_contradictions = []
        pairs_compared = 0

        # Analyze each claim individually (simplified approach)
        for claim_id in request.claim_ids:
            contradictions = await service.detect_contradictions(str(claim_id))
            all_contradictions.extend(contradictions)
            pairs_compared += len(contradictions)

        detection_time = int((time.time() - start_time) * 1000)

        return ContradictionDetectionResponse(
            contradictions=[ContradictionResponse.from_orm(c) for c in all_contradictions],
            claims_analyzed=len(request.claim_ids),
            pairs_compared=pairs_compared,
            detection_time_ms=detection_time
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Contradiction detection failed: {str(e)}")


@router.get("/{contradiction_id}", response_model=ContradictionResponse)
async def get_contradiction(
    contradiction_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific contradiction by ID."""
    contradiction = await db.get(Contradiction, contradiction_id)
    if not contradiction:
        raise HTTPException(status_code=404, detail="Contradiction not found")

    return ContradictionResponse.from_orm(contradiction)


@router.get("/claim/{claim_id}", response_model=List[ContradictionResponse])
async def get_contradictions_for_claim(
    claim_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get all contradictions for a specific claim."""
    try:
        from sqlalchemy import select
        result = await db.execute(
            select(Contradiction).where(Contradiction.claim_id == claim_id)
        )
        contradictions = result.scalars().all()

        return [ContradictionResponse.from_orm(c) for c in contradictions]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get contradictions: {str(e)}")


@router.get("/stats/disagreements")
async def get_disagreement_stats(db: AsyncSession = Depends(get_db)):
    """Get statistics about disagreements and contradictions."""
    try:
        from sqlalchemy import func, select

        # Get total contradictions
        total_contradictions = await db.scalar(select(func.count(Contradiction.id)))

        # Get contradictions by type
        type_counts = await db.execute(
            select(Contradiction.contradiction_type, func.count(Contradiction.id))
            .group_by(Contradiction.contradiction_type)
        )
        contradictions_by_type = dict(type_counts.all())

        # Severity distribution (simplified)
        severity_distribution = {}

        return {
            "total_contradictions": total_contradictions or 0,
            "contradictions_by_type": contradictions_by_type,
            "severity_distribution": severity_distribution,
            "most_common_type": max(contradictions_by_type.items(), key=lambda x: x[1], default=(None, 0))[0] if contradictions_by_type else None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


@router.get("/topic/{topic}/summary")
async def get_topic_disagreements(
    topic: str,
    workspace_id: Optional[UUID] = Query(None),
    service: ContradictionDetectionService = Depends(get_contradiction_service)
):
    """
    Get disagreement summary for a research topic.

    Provides overview of contested claims, resolution opportunities, etc.
    """
    try:
        report = await service.get_consensus_report(topic, str(workspace_id) if workspace_id else None)

        return {
            "topic": topic,
            "total_contested_claims": len(report.contested),
            "total_consensus_claims": len(report.consensus),
            "total_conditional_claims": len(report.conditional),
            "overall_consensus_score": report.overall_consensus_score,
            "top_contested_claims": [
                {
                    "claim_id": str(item.claim.id),
                    "text": item.claim.canonical_text[:100] + "...",
                    "severity": item.severity,
                    "contradictions_count": len(item.contradictions)
                }
                for item in report.contested[:5]  # Top 5
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get topic summary: {str(e)}")