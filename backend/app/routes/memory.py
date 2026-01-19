"""
Research Memory API Routes

Endpoints for research sessions, insights, and memory management.
"""

from typing import Optional, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.memory import (
    ResearchSessionResponse, SessionTimeline, SessionDetectionRequest,
    SessionDetectionResponse, ContextRetrievalRequest, ContextRetrievalResponse,
    SessionTimelineRequest, SessionTimelineResponse, ResearchSessionCreate,
    ResearchSessionUpdate, ResearchInsightCreate, ResearchInsightResponse,
    SessionQueryResponse
)
from app.services.intelligence.research_memory import ResearchMemoryService
from app.services.embedding.service import EmbeddingService
from app.models.memory import ResearchSession, ResearchInsight

router = APIRouter(prefix="/memory", tags=["memory"])


async def get_memory_service(db: AsyncSession = Depends(get_db)) -> ResearchMemoryService:
    """Get research memory service instance."""
    embedding_service = EmbeddingService(db)
    return ResearchMemoryService(
        embedding_service=embedding_service,
        db=db
    )


@router.post("/sessions/detect", response_model=SessionDetectionResponse)
async def detect_or_create_session(
    request: SessionDetectionRequest,
    service: ResearchMemoryService = Depends(get_memory_service)
):
    """
    Detect existing session or create new one for a query.

    Automatically finds relevant research sessions or creates new ones
    based on query similarity and topic matching.
    """
    try:
        session = await service.get_or_create_session(
            workspace_id=str(request.workspace_id),
            query=request.query
        )

        is_new = session.created_at == session.last_activity_at

        # Check if context is available
        context = await service.get_relevant_context(
            session_id=str(session.id),
            current_query=request.query
        )
        context_available = len(context.context_text.strip()) > 0

        return SessionDetectionResponse(
            session=ResearchSessionResponse.from_orm(session),
            is_new=is_new,
            context_available=context_available,
            similar_sessions_found=0  # Would implement session similarity search
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Session detection failed: {str(e)}")


@router.post("/sessions", response_model=ResearchSessionResponse)
async def create_research_session(
    request: ResearchSessionCreate,
    service: ResearchMemoryService = Depends(get_memory_service)
):
    """Create a new research session."""
    try:
        # Create session manually since service method expects query
        from app.models.memory import ResearchSession
        from datetime import datetime

        session = ResearchSession(
            workspace_id=request.workspace_id,
            name=request.name,
            description=request.description,
            primary_topic=request.primary_topic,
            related_topics=request.related_topics
        )

        await service.db.add(session)
        await service.db.commit()
        await service.db.refresh(session)

        return ResearchSessionResponse.from_orm(session)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Session creation failed: {str(e)}")


@router.get("/sessions/{session_id}", response_model=ResearchSessionResponse)
async def get_research_session(
    session_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get a research session by ID."""
    session = await db.get(ResearchSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Research session not found")

    return ResearchSessionResponse.from_orm(session)


@router.put("/sessions/{session_id}", response_model=ResearchSessionResponse)
async def update_research_session(
    session_id: UUID,
    request: ResearchSessionUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a research session."""
    session = await db.get(ResearchSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Research session not found")

    # Update fields
    update_data = request.dict(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(session, field):
            setattr(session, field, value)

    await db.commit()
    await db.refresh(session)

    return ResearchSessionResponse.from_orm(session)


@router.get("/sessions", response_model=List[ResearchSessionResponse])
async def list_research_sessions(
    workspace_id: Optional[UUID] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(50, le=100),
    db: AsyncSession = Depends(get_db)
):
    """List research sessions with optional filtering."""
    try:
        from sqlalchemy import select, desc

        query = select(ResearchSession)

        if workspace_id:
            query = query.where(ResearchSession.workspace_id == workspace_id)

        if status:
            query = query.where(ResearchSession.status == status)

        query = query.order_by(desc(ResearchSession.last_activity_at)).limit(limit)

        result = await db.execute(query)
        sessions = result.scalars().all()

        return [ResearchSessionResponse.from_orm(session) for session in sessions]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list sessions: {str(e)}")


@router.post("/context/retrieve", response_model=ContextRetrievalResponse)
async def retrieve_research_context(
    request: ContextRetrievalRequest,
    service: ResearchMemoryService = Depends(get_memory_service)
):
    """
    Retrieve relevant research context for a query.

    Gets insights, summaries, and recent queries from the research session
    that are relevant to the current query.
    """
    try:
        import time
        start_time = time.time()

        context = await service.get_relevant_context(
            session_id=str(request.session_id),
            current_query=request.current_query,
            max_tokens=request.max_tokens
        )

        retrieval_time = int((time.time() - start_time) * 1000)

        return ContextRetrievalResponse(
            context=context,
            retrieval_time_ms=retrieval_time
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Context retrieval failed: {str(e)}")


@router.get("/sessions/{session_id}/timeline", response_model=SessionTimelineResponse)
async def get_session_timeline(
    session_id: UUID,
    service: ResearchMemoryService = Depends(get_memory_service)
):
    """Get the complete timeline of a research session."""
    try:
        import time
        start_time = time.time()

        timeline = await service.get_session_timeline(str(session_id))

        retrieval_time = int((time.time() - start_time) * 1000)

        return SessionTimelineResponse(
            timeline=timeline,
            retrieval_time_ms=retrieval_time
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Timeline retrieval failed: {str(e)}")


@router.post("/sessions/{session_id}/insights", response_model=ResearchInsightResponse)
async def create_research_insight(
    session_id: UUID,
    request: ResearchInsightCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new research insight for a session."""
    try:
        from app.models.memory import ResearchInsight

        insight = ResearchInsight(
            session_id=session_id,
            **request.dict()
        )

        db.add(insight)
        await db.commit()
        await db.refresh(insight)

        return ResearchInsightResponse.from_orm(insight)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Insight creation failed: {str(e)}")


@router.get("/sessions/{session_id}/insights", response_model=List[ResearchInsightResponse])
async def get_session_insights(
    session_id: UUID,
    confirmed_only: bool = Query(False),
    db: AsyncSession = Depends(get_db)
):
    """Get all insights for a research session."""
    try:
        from sqlalchemy import select

        query = select(ResearchInsight).where(ResearchInsight.session_id == session_id)

        if confirmed_only:
            query = query.where(ResearchInsight.user_confirmed == True)

        result = await db.execute(query)
        insights = result.scalars().all()

        return [ResearchInsightResponse.from_orm(insight) for insight in insights]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get insights: {str(e)}")


@router.get("/sessions/{session_id}/queries", response_model=List[SessionQueryResponse])
async def get_session_queries(
    session_id: UUID,
    limit: int = Query(50, le=200),
    db: AsyncSession = Depends(get_db)
):
    """Get all queries for a research session."""
    try:
        from sqlalchemy import select, desc
        from app.models.memory import SessionQuery

        result = await db.execute(
            select(SessionQuery)
            .where(SessionQuery.session_id == session_id)
            .order_by(desc(SessionQuery.created_at))
            .limit(limit)
        )

        queries = result.scalars().all()

        return [SessionQueryResponse.model_validate(query) for query in queries]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get queries: {str(e)}")


@router.get("/stats/overview")
async def get_memory_stats(db: AsyncSession = Depends(get_db)):
    """Get overview statistics about research memory usage."""
    try:
        from sqlalchemy import func, select
        from app.models.memory import ResearchSession, SessionQuery, ResearchInsight, MemorySummary

        # Session stats
        total_sessions = await db.scalar(select(func.count(ResearchSession.id)))
        active_sessions = await db.scalar(
            select(func.count(ResearchSession.id))
            .where(ResearchSession.status == "active")
        )

        # Query and insight stats
        total_queries = await db.scalar(select(func.count(SessionQuery.id)))
        total_insights = await db.scalar(select(func.count(ResearchInsight.id)))
        total_memory_summaries = await db.scalar(select(func.count(MemorySummary.id)))

        # Average session duration (simplified)
        avg_duration = 0  # Would calculate from timestamps

        return {
            "total_sessions": total_sessions,
            "active_sessions": active_sessions,
            "total_queries": total_queries,
            "total_insights": total_insights,
            "total_memory_summaries": total_memory_summaries,
            "average_session_duration_days": avg_duration
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


@router.delete("/sessions/{session_id}")
async def delete_research_session(
    session_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Delete a research session and all associated data."""
    session = await db.get(ResearchSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Research session not found")

    # Delete will cascade due to foreign key constraints
    await db.delete(session)
    await db.commit()

    return {"message": "Research session deleted successfully"}