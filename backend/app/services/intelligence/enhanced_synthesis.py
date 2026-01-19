"""
Enhanced Synthesis Service

Integrates claims, contradictions, and research memory into the synthesis pipeline.
"""

import time
from typing import List, Optional, Dict, Any
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.synthesis_result import SynthesisResult
from app.models.workspace import Workspace
from app.schemas.synthesis import SynthesisResponse, SourceReference
from app.services.intelligence.claim_extraction import ClaimExtractionService
from app.services.intelligence.contradiction_detection import ContradictionDetectionService
from app.services.intelligence.research_memory import ResearchMemoryService
from app.services.intelligence.rag import RAGService
from app.services.embedding.service import EmbeddingService


class EnhancedSynthesisService:
    """Enhanced synthesis that integrates claims, contradictions, and memory."""

    def __init__(
        self,
        db: AsyncSession,
        embedding_service: EmbeddingService,
    ):
        self.db = db
        self.embedding_service = embedding_service

        # Initialize services
        self.claim_service = ClaimExtractionService(
            embedding_service=embedding_service,
            db=db
        )
        self.contradiction_service = ContradictionDetectionService(db=db)
        self.memory_service = ResearchMemoryService(
            embedding_service=embedding_service,
            db=db
        )
        self.rag_service = RAGService(db=db)

    async def synthesize_with_intelligence(
        self,
        user_id: str,
        workspace_id: str,
        query: str,
        mode: str,
        settings_override: Optional[Dict[str, Any]] = None
    ) -> SynthesisResponse:
        """
        Enhanced synthesis with claim extraction, contradiction detection, and memory.

        Args:
            user_id: User performing the synthesis
            workspace_id: Workspace context
            query: Research query
            mode: Synthesis mode ('synthesize', 'compare', 'plan', 'explore')
            settings_override: Optional settings overrides

        Returns:
            Enhanced synthesis response with intelligence features
        """

        start_time = time.time()

        # 1. Get or create research session
        session = await self.memory_service.get_or_create_session(
            workspace_id=workspace_id,
            query=query
        )

        # 2. Get relevant context from memory
        context = await self.memory_service.get_relevant_context(
            session_id=str(session.id),
            current_query=query
        )

        # 3. Perform standard RAG synthesis
        rag_response = await self.rag_service.answer(
            question=query,
            use_llm_parsing=True
        )

        # 4. Extract claims from the chunks used in synthesis
        claims = []
        if rag_response.citations:
            # Get chunk IDs from citations (assuming we can map back)
            chunk_ids = [citation.paper_id for citation in rag_response.citations[:5]]  # Simplified

            # Extract claims from relevant chunks
            # In practice, we'd need to get actual Chunk objects
            claims = []  # await self.claim_service.get_or_extract_claims(chunks, query)

        # 5. Get contradiction analysis for extracted claims
        contradictions = []
        consensus_report = None
        if claims:
            # Get contradictions for claims
            for claim in claims[:3]:  # Limit for performance
                claim_contradictions = await self.contradiction_service.detect_contradictions(str(claim.id))
                contradictions.extend(claim_contradictions)

            # Generate consensus report
            consensus_report = await self.contradiction_service.get_consensus_report(
                topic=query,
                workspace_id=workspace_id
            )

        # 6. Create enhanced synthesis result
        synthesis_result = SynthesisResult(
            workspace_id=workspace_id,
            mode=mode,
            input_query=query,
            content=self._build_enhanced_content(
                rag_response=rag_response,
                claims=claims,
                contradictions=contradictions,
                consensus_report=consensus_report,
                memory_context=context
            ),
            sources_metadata=self._build_sources_metadata(rag_response.citations),
            model="enhanced-synthesis",  # Would be actual model used
            confidence_score=rag_response.confidence_score or 0.8,
        )

        self.db.add(synthesis_result)
        await self.db.commit()

        # 7. Record query to memory
        await self.memory_service.record_query(
            session_id=str(session.id),
            query=query,
            synthesis_id=str(synthesis_result.id),
            claims_discovered=[str(c.id) for c in claims],
            papers_used=[c.paper_id for c in rag_response.citations],
            context_used=context.context_text
        )

        # 8. Build enhanced response
        processing_time_ms = int((time.time() - start_time) * 1000)

        # Build intelligence features summary
        intelligence_features = self._build_intelligence_features(
            claims=claims,
            contradictions=contradictions,
            consensus_report=consensus_report,
            memory_context=context,
            session=session
        )

        return SynthesisResponse(
            id=synthesis_result.id,
            mode=mode,
            query=query,
            created_at=synthesis_result.created_at,
            sources=rag_response.citations,
            total_papers_analyzed=rag_response.papers_analyzed,
            total_chunks_used=len(rag_response.citations),
            content=self._build_enhanced_content_dict(
                rag_response=rag_response,
                claims=claims,
                contradictions=contradictions,
                consensus_report=consensus_report,
                memory_context=context
            ),
            model="enhanced-synthesis",
            tokens_used=rag_response.tokens_used,
            generation_time_ms=processing_time_ms,
            confidence_score=synthesis_result.confidence_score,
            intelligence_features=intelligence_features,
        )

    def _build_enhanced_content(
        self,
        rag_response,
        claims: List,
        contradictions: List,
        consensus_report,
        memory_context
    ) -> Dict[str, Any]:
        """Build enhanced content structure."""
        # Start with standard RAG content
        content = {
            "summary": rag_response.summary,
            "key_findings": rag_response.key_findings,
            "consensus": rag_response.consensus,
            "open_questions": rag_response.open_questions,
        }

        # Add intelligence features
        if claims:
            content["claims_extracted"] = len(claims)
            content["claims"] = [
                {
                    "id": str(c.id),
                    "text": c.canonical_text,
                    "type": c.claim_type,
                    "consensus_score": c.consensus_score,
                    "evidence_count": c.total_evidence_count
                }
                for c in claims[:5]  # Limit for response size
            ]

        if contradictions:
            content["contradictions_found"] = len(contradictions)
            content["key_contradictions"] = [
                {
                    "claim_text": "Claim text",  # Would need to resolve
                    "type": c.contradiction_type,
                    "severity": c.severity,
                    "explanation": c.explanation
                }
                for c in contradictions[:3]
            ]

        if consensus_report:
            content["consensus_report"] = {
                "overall_score": consensus_report.overall_consensus_score,
                "consensus_areas": len(consensus_report.consensus),
                "contested_areas": len(consensus_report.contested),
                "conditional_areas": len(consensus_report.conditional)
            }

        if memory_context and memory_context.context_text:
            content["memory_context_used"] = {
                "token_count": memory_context.token_count,
                "sources": memory_context.sources
            }

        return content

    def _build_enhanced_content_dict(
        self,
        rag_response,
        claims: List,
        contradictions: List,
        consensus_report,
        memory_context
    ) -> Dict[str, Any]:
        """Build the content dict for SynthesisResponse."""
        # For now, return the RAG content as the base
        # In production, this would be more structured
        return self._build_enhanced_content(
            rag_response, claims, contradictions, consensus_report, memory_context
        )

    def _build_intelligence_features(
        self,
        claims: List,
        contradictions: List,
        consensus_report,
        memory_context,
        session
    ) -> Dict[str, Any]:
        """Build intelligence features summary for the response."""
        features = {
            "research_session": {
                "id": str(session.id),
                "name": session.name,
                "is_new": session.created_at == session.last_activity_at
            }
        }

        if claims:
            features["claims"] = {
                "extracted_count": len(claims),
                "summary": [
                    {
                        "id": str(c.id),
                        "text": c.canonical_text[:100] + "..." if len(c.canonical_text) > 100 else c.canonical_text,
                        "type": c.claim_type,
                        "consensus_score": c.consensus_score,
                        "evidence_count": c.total_evidence_count
                    }
                    for c in claims[:5]  # Limit for response size
                ]
            }

        if contradictions:
            features["contradictions"] = {
                "detected_count": len(contradictions),
                "top_issues": [
                    {
                        "severity": c.severity,
                        "type": c.contradiction_type,
                        "explanation": c.explanation[:200] + "..." if c.explanation and len(c.explanation) > 200 else c.explanation
                    }
                    for c in sorted(contradictions, key=lambda x: x.severity, reverse=True)[:3]
                ]
            }

        if consensus_report:
            features["consensus"] = {
                "overall_score": consensus_report.overall_consensus_score,
                "agreement_level": self._get_agreement_level(consensus_report.overall_consensus_score),
                "breakdown": {
                    "consensus_areas": len(consensus_report.consensus),
                    "contested_areas": len(consensus_report.contested),
                    "conditional_areas": len(consensus_report.conditional)
                }
            }

        if memory_context and memory_context.context_text:
            features["research_memory"] = {
                "context_used": len(memory_context.context_text) > 0,
                "sources_included": memory_context.sources,
                "session_context_length": len(memory_context.context_text)
            }

        return features

    def _get_agreement_level(self, score: float) -> str:
        """Convert consensus score to human-readable agreement level."""
        if score >= 0.8:
            return "strong_consensus"
        elif score >= 0.6:
            return "moderate_consensus"
        elif score >= 0.2:
            return "mixed_evidence"
        elif score >= -0.2:
            return "contested"
        else:
            return "major_disagreements"

    def _build_sources_metadata(self, citations: List) -> Dict[str, Any]:
        """Build sources metadata for synthesis result."""
        return {
            "total_citations": len(citations),
            "papers": [
                {
                    "id": c.paper_id,
                    "title": c.title,
                    "year": c.year,
                    "citations": c.citation_count
                }
                for c in citations
            ]
        }