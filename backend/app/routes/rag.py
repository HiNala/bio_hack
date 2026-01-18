"""
RAG Synthesis Endpoint

Retrieval-Augmented Generation for answering research questions.
"""

import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models import SearchQuery
from app.schemas import RAGQueryRequest, RAGResponse
from app.services.intelligence import RAGService
from app.config import get_settings

router = APIRouter()
settings = get_settings()


@router.post("/rag/query", response_model=RAGResponse, tags=["RAG"])
async def rag_query(
    request: RAGQueryRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Generate a synthesized answer using RAG.
    
    Pipeline:
    1. Retrieve relevant chunks via semantic search
    2. Assemble context from top chunks
    3. Generate answer with Claude
    4. Extract and validate citations
    
    Requires both OPENAI_API_KEY (embeddings) and ANTHROPIC_API_KEY (synthesis).
    """
    if not settings.openai_api_key:
        raise HTTPException(
            status_code=503,
            detail="OpenAI API key not configured for embeddings."
        )
    
    if not settings.anthropic_api_key:
        raise HTTPException(
            status_code=503,
            detail="Anthropic API key not configured for synthesis."
        )
    
    # Validate query_id if provided
    if request.query_id:
        try:
            query_uuid = uuid.UUID(request.query_id)
            result = await db.execute(
                select(SearchQuery).where(SearchQuery.id == query_uuid)
            )
            search_query = result.scalar_one_or_none()
            if not search_query:
                raise HTTPException(status_code=404, detail="Query not found")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid query_id format")
    
    # Run RAG pipeline
    rag_service = RAGService(db)
    
    try:
        response = await rag_service.answer(
            question=request.question,
            use_llm_parsing=True,
        )
        
        # Set query_id in response
        response.query_id = request.query_id
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"RAG synthesis failed: {str(e)}"
        )


@router.post("/rag/ask", response_model=RAGResponse, tags=["RAG"])
async def rag_ask(
    question: str = Query(..., min_length=10, description="Research question"),
    top_k: int = Query(10, ge=1, le=50, description="Number of sources to use"),
    db: AsyncSession = Depends(get_db),
):
    """
    Quick RAG endpoint without prior query setup.
    
    Simply ask a research question and get a synthesized answer.
    Great for demos and testing.
    """
    if not settings.openai_api_key or not settings.anthropic_api_key:
        raise HTTPException(
            status_code=503,
            detail="API keys not configured. Need both OPENAI_API_KEY and ANTHROPIC_API_KEY."
        )
    
    rag_service = RAGService(db)
    
    try:
        response = await rag_service.answer(
            question=question,
            top_k=top_k,
            use_llm_parsing=True,
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"RAG failed: {str(e)}"
        )
