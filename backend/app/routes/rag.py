"""
RAG Synthesis Endpoint

Retrieval-Augmented Generation for answering research questions.
"""

import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.database import get_db
from app.models import SearchQuery
from app.schemas import RAGQueryRequest, RAGResponse
from app.services.intelligence import RAGService
from app.config import get_settings

router = APIRouter()
settings = get_settings()


class SimpleRAGRequest(BaseModel):
    """Simple RAG request body."""
    question: str
    top_k: int = 10


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
    3. Generate answer with LLM (OpenAI or Anthropic)
    4. Extract and validate citations
    
    Requires OPENAI_API_KEY. ANTHROPIC_API_KEY is optional (uses OpenAI if not set).
    """
    if not settings.openai_api_key:
        raise HTTPException(
            status_code=503,
            detail="OpenAI API key not configured."
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
    request: SimpleRAGRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Quick RAG endpoint - ask a research question and get a synthesized answer.
    
    Great for demos and testing. Uses JSON body.
    """
    if not settings.openai_api_key:
        raise HTTPException(
            status_code=503,
            detail="OpenAI API key not configured."
        )
    
    rag_service = RAGService(db)
    
    try:
        response = await rag_service.answer(
            question=request.question,
            top_k=request.top_k,
            use_llm_parsing=True,
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"RAG failed: {str(e)}"
        )


@router.get("/rag/ask", response_model=RAGResponse, tags=["RAG"])
async def rag_ask_get(
    question: str = Query(..., min_length=5, description="Research question"),
    top_k: int = Query(10, ge=1, le=50, description="Number of sources to use"),
    db: AsyncSession = Depends(get_db),
):
    """
    Quick RAG endpoint using GET with query parameters.
    
    Useful for browser testing.
    """
    if not settings.openai_api_key:
        raise HTTPException(
            status_code=503,
            detail="OpenAI API key not configured."
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
