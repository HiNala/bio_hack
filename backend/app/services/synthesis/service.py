"""
Synthesis Service

Orchestrates the synthesis process from query to structured output.
"""

from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from collections import defaultdict
import uuid
import time
import json
import re
import math

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
import openai

from app.config import get_settings
from app.models.paper import Paper
from app.models.chunk import Chunk
from app.models.synthesis_result import SynthesisResult
from app.models.saved_query import SavedQuery
from app.schemas.synthesis import (
    SynthesisRequest, SynthesisResponse, SourceReference
)
from app.schemas.settings import SettingsResponse, DEFAULT_SETTINGS
from app.services.synthesis.prompts import get_prompt_for_mode, get_user_prompt
from app.services.embedding.service import EmbeddingService


class RetrievedChunk:
    """A chunk retrieved from vector search with metadata."""
    def __init__(
        self,
        chunk_id: uuid.UUID,
        paper_id: uuid.UUID,
        content: str,
        paper_title: str,
        paper_year: Optional[int],
        citation_count: int,
        similarity: float,
        section: Optional[str] = None
    ):
        self.chunk_id = chunk_id
        self.paper_id = paper_id
        self.content = content
        self.paper_title = paper_title
        self.paper_year = paper_year
        self.citation_count = citation_count
        self.similarity = similarity
        self.section = section


class SynthesisService:
    """
    Orchestrate the synthesis process from query to structured output.
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.embedding_service = EmbeddingService()
        settings = get_settings()
        self.openai_client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
    
    async def synthesize(
        self,
        request: SynthesisRequest,
        user_id: Optional[str] = None,
        user_settings: Optional[SettingsResponse] = None
    ) -> SynthesisResponse:
        """
        Generate synthesis for user query.
        """
        start_time = time.time()
        
        # Use provided settings or defaults
        effective_settings = user_settings or DEFAULT_SETTINGS
        
        # Stage 1: Embed query and retrieve chunks
        chunks = await self._retrieve_chunks(
            query=request.query,
            collection_ids=request.collection_ids,
            settings=effective_settings
        )
        
        if not chunks:
            # Return empty response if no relevant chunks found
            return self._create_empty_response(request, start_time)
        
        # Stage 2: Rerank if enabled
        if effective_settings.reranking_enabled:
            chunks = self._rerank_chunks(request.query, chunks, effective_settings)
        
        # Stage 3: Diversify sources if enabled
        if effective_settings.diversify_sources:
            chunks = self._diversify_sources(
                chunks,
                max_per_paper=3,
                min_unique_papers=5
            )
        
        # Limit to chunks_per_query
        chunks = chunks[:effective_settings.chunks_per_query]
        
        # Stage 4: Build context and sources
        context, sources = self._build_context(chunks)
        
        # Stage 5: Generate synthesis with LLM
        content, model, tokens = await self._generate_synthesis(
            request.query,
            context,
            request.mode,
            effective_settings
        )
        
        generation_time = int((time.time() - start_time) * 1000)
        
        # Calculate confidence score
        confidence = self._calculate_confidence(chunks, sources)
        
        # Build response
        synthesis_id = uuid.uuid4()
        
        response = SynthesisResponse(
            id=synthesis_id,
            mode=request.mode,
            query=request.query,
            created_at=datetime.utcnow(),
            sources=sources,
            total_papers_analyzed=len(set(c.paper_id for c in chunks)),
            total_chunks_used=len(chunks),
            content=content,
            model=model,
            tokens_used=tokens,
            generation_time_ms=generation_time,
            confidence_score=confidence,
            coverage_warning=self._get_coverage_warning(chunks, sources)
        )
        
        # Save to database if workspace provided
        if request.workspace_id:
            await self._save_synthesis(response, request.workspace_id, user_id)
        
        return response
    
    async def _retrieve_chunks(
        self,
        query: str,
        collection_ids: Optional[List[uuid.UUID]],
        settings: SettingsResponse
    ) -> List[RetrievedChunk]:
        """Retrieve relevant chunks using vector search."""
        # Embed query
        query_embedding = await self.embedding_service.embed_query(query)
        
        if query_embedding is None:
            return []
        
        # Build SQL query with filters
        # Get 2x the needed chunks for reranking
        limit = settings.chunks_per_query * 2
        
        # Build filter conditions
        filters = []
        params = {
            "embedding": query_embedding,
            "limit": limit,
            "threshold": settings.similarity_threshold
        }
        
        if settings.year_from:
            filters.append("p.year >= :year_from")
            params["year_from"] = settings.year_from
        
        if settings.year_to:
            filters.append("p.year <= :year_to")
            params["year_to"] = settings.year_to
        
        if settings.min_citations > 0:
            filters.append("p.citation_count >= :min_citations")
            params["min_citations"] = settings.min_citations
        
        filter_clause = " AND ".join(filters) if filters else "TRUE"
        
        # Vector search query
        sql = text(f"""
            SELECT 
                c.id as chunk_id,
                c.paper_id,
                c.content,
                c.section,
                p.title as paper_title,
                p.year as paper_year,
                p.citation_count,
                1 - (c.embedding <=> :embedding::vector) as similarity
            FROM chunks c
            JOIN papers p ON c.paper_id = p.id
            WHERE c.embedding IS NOT NULL
              AND {filter_clause}
            ORDER BY c.embedding <=> :embedding::vector
            LIMIT :limit
        """)
        
        result = await self.db.execute(sql, params)
        rows = result.fetchall()
        
        chunks = []
        for row in rows:
            if row.similarity >= settings.similarity_threshold:
                chunks.append(RetrievedChunk(
                    chunk_id=row.chunk_id,
                    paper_id=row.paper_id,
                    content=row.content,
                    paper_title=row.paper_title,
                    paper_year=row.paper_year,
                    citation_count=row.citation_count or 0,
                    similarity=row.similarity,
                    section=row.section
                ))
        
        return chunks
    
    def _rerank_chunks(
        self,
        query: str,
        chunks: List[RetrievedChunk],
        settings: SettingsResponse
    ) -> List[RetrievedChunk]:
        """Rerank chunks using multiple signals."""
        query_terms = set(query.lower().split())
        current_year = datetime.now().year
        
        # Calculate max citations for normalization
        max_citations = max((c.citation_count for c in chunks), default=1) or 1
        
        scored_chunks = []
        for chunk in chunks:
            # Term overlap score
            content_terms = set(chunk.content.lower().split())
            overlap = len(query_terms & content_terms) / len(query_terms) if query_terms else 0
            
            # Recency score (papers from last 5 years get bonus)
            recency = 1.0
            if chunk.paper_year:
                years_old = current_year - chunk.paper_year
                if years_old <= 2:
                    recency = 1.2
                elif years_old <= 5:
                    recency = 1.1
                elif years_old > 10:
                    recency = 0.9
            
            # Citation score (log scale)
            citation_score = math.log(chunk.citation_count + 1) / math.log(max_citations + 1)
            
            # Combined score
            score = (
                chunk.similarity * 0.4 +
                overlap * 0.2 +
                recency * 0.15 +
                citation_score * 0.15 +
                0.1  # Base diversity bonus
            )
            
            scored_chunks.append((chunk, score))
        
        # Sort by score
        scored_chunks.sort(key=lambda x: x[1], reverse=True)
        
        return [c for c, _ in scored_chunks]
    
    def _diversify_sources(
        self,
        chunks: List[RetrievedChunk],
        max_per_paper: int,
        min_unique_papers: int
    ) -> List[RetrievedChunk]:
        """Ensure diverse paper representation."""
        paper_counts = defaultdict(int)
        diversified = []
        
        for chunk in chunks:
            if paper_counts[chunk.paper_id] < max_per_paper:
                diversified.append(chunk)
                paper_counts[chunk.paper_id] += 1
        
        return diversified
    
    def _build_context(
        self,
        chunks: List[RetrievedChunk]
    ) -> Tuple[str, List[SourceReference]]:
        """Build context string and source references."""
        # Group chunks by paper
        paper_chunks = defaultdict(list)
        paper_info = {}
        
        for chunk in chunks:
            paper_chunks[chunk.paper_id].append(chunk)
            if chunk.paper_id not in paper_info:
                paper_info[chunk.paper_id] = {
                    "title": chunk.paper_title,
                    "year": chunk.paper_year,
                    "citation_count": chunk.citation_count,
                    "max_similarity": chunk.similarity,
                }
            else:
                paper_info[chunk.paper_id]["max_similarity"] = max(
                    paper_info[chunk.paper_id]["max_similarity"],
                    chunk.similarity
                )
        
        # Assign citation IDs to papers
        sorted_papers = sorted(
            paper_info.items(),
            key=lambda x: x[1]["max_similarity"],
            reverse=True
        )
        
        citation_map = {pid: i + 1 for i, (pid, _) in enumerate(sorted_papers)}
        
        # Build context string
        context_parts = []
        for pid, info in sorted_papers:
            cid = citation_map[pid]
            paper_chunks_list = paper_chunks[pid]
            
            for chunk in paper_chunks_list:
                context_parts.append(
                    f'<source id="{cid}" paper="{info["title"]}" '
                    f'year="{info["year"] or "unknown"}" citations="{info["citation_count"]}">\n'
                    f'{chunk.content}\n'
                    f'</source>'
                )
        
        context = "\n\n".join(context_parts)
        
        # Build source references
        sources = []
        for pid, info in sorted_papers:
            sources.append(SourceReference(
                citation_id=citation_map[pid],
                paper_id=pid,
                title=info["title"],
                authors=[],  # Would need to fetch from paper
                year=info["year"],
                venue=None,
                doi=None,
                url=None,
                citation_count=info["citation_count"],
                relevance_score=info["max_similarity"],
                chunks_used=len(paper_chunks[pid])
            ))
        
        return context, sources
    
    async def _generate_synthesis(
        self,
        query: str,
        context: str,
        mode: str,
        settings: SettingsResponse
    ) -> Tuple[Dict[str, Any], str, int]:
        """Generate synthesis using LLM."""
        system_prompt = get_prompt_for_mode(mode)
        user_prompt = get_user_prompt(query, context, mode)
        
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=4000,
                response_format={"type": "json_object"}
            )
            
            content_str = response.choices[0].message.content
            tokens = response.usage.total_tokens if response.usage else 0
            
            # Parse JSON response
            try:
                content = json.loads(content_str)
            except json.JSONDecodeError:
                # Try to extract JSON from response
                content = self._extract_json(content_str)
            
            return content, "gpt-4o-mini", tokens
            
        except Exception as e:
            # Return error content
            return {
                "error": str(e),
                "executive_summary": "Unable to generate synthesis due to an error.",
                "key_findings": [],
                "consensus": [],
                "contested": [],
                "limitations": ["Synthesis generation failed"],
                "suggested_readings": []
            }, "error", 0
    
    def _extract_json(self, text: str) -> Dict[str, Any]:
        """Try to extract JSON from text that may have extra content."""
        # Try to find JSON object
        match = re.search(r'\{[\s\S]*\}', text)
        if match:
            try:
                return json.loads(match.group())
            except:
                pass
        
        # Return minimal valid response
        return {
            "executive_summary": text[:500] if text else "No synthesis generated.",
            "key_findings": [],
            "consensus": [],
            "contested": [],
            "limitations": [],
            "suggested_readings": []
        }
    
    def _calculate_confidence(
        self,
        chunks: List[RetrievedChunk],
        sources: List[SourceReference]
    ) -> float:
        """Calculate confidence score based on source quality and quantity."""
        if not chunks or not sources:
            return 0.0
        
        # Factors:
        # - Number of unique sources (more is better, up to a point)
        # - Average similarity score
        # - Average citation count
        # - Recency
        
        n_sources = len(sources)
        source_factor = min(n_sources / 10, 1.0)  # Caps at 10 sources
        
        avg_similarity = sum(c.similarity for c in chunks) / len(chunks)
        
        avg_citations = sum(s.citation_count for s in sources) / len(sources)
        citation_factor = min(math.log(avg_citations + 1) / 5, 1.0)
        
        confidence = (
            source_factor * 0.3 +
            avg_similarity * 0.4 +
            citation_factor * 0.3
        )
        
        return round(confidence, 2)
    
    def _get_coverage_warning(
        self,
        chunks: List[RetrievedChunk],
        sources: List[SourceReference]
    ) -> Optional[str]:
        """Generate warning if source coverage is limited."""
        if len(sources) < 3:
            return "Limited sources found. Results may not be comprehensive."
        
        avg_similarity = sum(c.similarity for c in chunks) / len(chunks) if chunks else 0
        if avg_similarity < 0.6:
            return "Sources have moderate relevance. Consider refining your query."
        
        return None
    
    def _create_empty_response(
        self,
        request: SynthesisRequest,
        start_time: float
    ) -> SynthesisResponse:
        """Create response when no relevant chunks found."""
        return SynthesisResponse(
            id=uuid.uuid4(),
            mode=request.mode,
            query=request.query,
            created_at=datetime.utcnow(),
            sources=[],
            total_papers_analyzed=0,
            total_chunks_used=0,
            content={
                "executive_summary": "No relevant papers found for this query. Try broadening your search terms.",
                "key_findings": [],
                "consensus": [],
                "contested": [],
                "limitations": ["No sources available"],
                "suggested_readings": []
            },
            model=None,
            tokens_used=0,
            generation_time_ms=int((time.time() - start_time) * 1000),
            confidence_score=0.0,
            coverage_warning="No relevant papers found in the database."
        )
    
    async def _save_synthesis(
        self,
        response: SynthesisResponse,
        workspace_id: uuid.UUID,
        user_id: Optional[str]
    ):
        """Save synthesis result to database."""
        synthesis = SynthesisResult(
            id=response.id,
            workspace_id=workspace_id,
            mode=response.mode,
            input_query=response.query,
            source_papers=[s.paper_id for s in response.sources],
            content=response.content,
            sources_metadata=[s.model_dump() for s in response.sources],
            model_used=response.model,
            tokens_used=response.tokens_used,
            generation_time_ms=response.generation_time_ms,
            confidence_score=response.confidence_score,
        )
        
        self.db.add(synthesis)
        await self.db.commit()
    
    async def get_synthesis(
        self,
        synthesis_id: str
    ) -> Optional[SynthesisResponse]:
        """Get a saved synthesis by ID."""
        result = await self.db.execute(
            select(SynthesisResult)
            .where(SynthesisResult.id == uuid.UUID(synthesis_id))
        )
        synthesis = result.scalar_one_or_none()
        
        if not synthesis:
            return None
        
        # Reconstruct response
        sources = []
        if synthesis.sources_metadata:
            for s in synthesis.sources_metadata:
                sources.append(SourceReference(**s))
        
        return SynthesisResponse(
            id=synthesis.id,
            mode=synthesis.mode,
            query=synthesis.input_query,
            created_at=synthesis.created_at,
            sources=sources,
            total_papers_analyzed=len(synthesis.source_papers) if synthesis.source_papers else 0,
            total_chunks_used=len(synthesis.source_chunks) if synthesis.source_chunks else 0,
            content=synthesis.content,
            model=synthesis.model_used,
            tokens_used=synthesis.tokens_used,
            generation_time_ms=synthesis.generation_time_ms,
            confidence_score=synthesis.confidence_score,
        )
    
    async def get_workspace_syntheses(
        self,
        workspace_id: str,
        limit: int = 20
    ) -> List[SynthesisResponse]:
        """Get recent syntheses for a workspace."""
        result = await self.db.execute(
            select(SynthesisResult)
            .where(SynthesisResult.workspace_id == uuid.UUID(workspace_id))
            .order_by(SynthesisResult.created_at.desc())
            .limit(limit)
        )
        syntheses = result.scalars().all()
        
        responses = []
        for s in syntheses:
            sources = []
            if s.sources_metadata:
                for src in s.sources_metadata:
                    sources.append(SourceReference(**src))
            
            responses.append(SynthesisResponse(
                id=s.id,
                mode=s.mode,
                query=s.input_query,
                created_at=s.created_at,
                sources=sources,
                total_papers_analyzed=len(s.source_papers) if s.source_papers else 0,
                total_chunks_used=len(s.source_chunks) if s.source_chunks else 0,
                content=s.content,
                model=s.model_used,
                tokens_used=s.tokens_used,
                generation_time_ms=s.generation_time_ms,
                confidence_score=s.confidence_score,
            ))
        
        return responses
    
    async def add_feedback(
        self,
        synthesis_id: str,
        rating: int,
        feedback: Optional[str] = None
    ) -> bool:
        """Add user feedback to a synthesis."""
        result = await self.db.execute(
            select(SynthesisResult)
            .where(SynthesisResult.id == uuid.UUID(synthesis_id))
        )
        synthesis = result.scalar_one_or_none()
        
        if not synthesis:
            return False
        
        synthesis.user_rating = rating
        synthesis.user_feedback = feedback
        
        await self.db.commit()
        return True
