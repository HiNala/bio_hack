"""
Query Analysis Endpoint

Parses natural language queries into structured search parameters.
"""

import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import SearchQuery
from app.schemas import AnalyzeRequest, AnalyzeResponse, ParsedQuery
from app.services.intelligence import QueryParser
from app.config import get_settings

router = APIRouter()
settings = get_settings()


@router.post("/analyze", response_model=AnalyzeResponse, tags=["Query"])
async def analyze_query(
    request: AnalyzeRequest,
    use_llm: bool = Query(True, description="Use Claude for enhanced parsing"),
    db: AsyncSession = Depends(get_db),
):
    """
    Analyze a natural language research query.
    
    Uses Claude to extract:
    - Primary search terms
    - Expanded/related terms
    - Time bounds
    - Academic fields
    - Query type (factual, synthesis, comparison, survey)
    
    The query is stored in the database and a query_id is returned
    for use in subsequent ingestion and RAG operations.
    
    Set use_llm=false for basic parsing without Claude (faster, no API key needed).
    """
    # Parse the query
    if use_llm and settings.anthropic_api_key:
        try:
            parser = QueryParser()
            parsed = await parser.parse(request.query)
        except Exception as e:
            print(f"LLM parsing failed: {e}, falling back to basic")
            parsed = _basic_parse(request.query)
    else:
        parsed = _basic_parse(request.query)
    
    # Create search query record in database
    search_query = SearchQuery(
        id=uuid.uuid4(),
        raw_query=request.query,
        parsed_query=parsed.model_dump(),
        status="parsed",
        created_at=datetime.utcnow(),
    )
    
    db.add(search_query)
    await db.commit()
    await db.refresh(search_query)
    
    return AnalyzeResponse(
        query_id=str(search_query.id),
        parsed_query=parsed,
        status="parsed",
    )


def _basic_parse(query: str) -> ParsedQuery:
    """
    Basic query parsing without LLM.
    
    Extracts information using regex patterns.
    """
    import re
    
    words = query.lower().split()
    stopwords = {"what", "where", "when", "which", "that", "this", "have", "been",
                 "with", "from", "they", "their", "about", "would", "could", "should",
                 "there", "these", "those", "then", "than", "some", "into", "over"}
    
    primary_terms = [
        w for w in words
        if len(w) > 4 and w not in stopwords and w.isalpha()
    ][:5]
    
    # Year extraction
    year_from = None
    year_to = None
    
    since_match = re.search(r'(?:since|after|from)\s+(\d{4})', query.lower())
    if since_match:
        year_from = int(since_match.group(1))
    
    before_match = re.search(r'(?:before|until|to)\s+(\d{4})', query.lower())
    if before_match:
        year_to = int(before_match.group(1))
    
    range_match = re.search(r'(\d{4})\s*[-–to]+\s*(\d{4})', query.lower())
    if range_match:
        year_from = int(range_match.group(1))
        year_to = int(range_match.group(2))
    
    # Query type detection
    query_type = "synthesis"
    if any(w in query.lower() for w in ["compare", "versus", "vs", "difference"]):
        query_type = "comparison"
    elif any(w in query.lower() for w in ["what is", "define", "explain"]):
        query_type = "factual"
    elif any(w in query.lower() for w in ["survey", "review", "overview", "leading"]):
        query_type = "survey"
    
    return ParsedQuery(
        primary_terms=primary_terms if primary_terms else query.split()[:3],
        expanded_terms=[],
        year_from=year_from,
        year_to=year_to,
        fields=[],
        query_type=query_type,
    )
