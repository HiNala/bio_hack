"""
Claim Extraction Service

Extracts and manages scientific claims from papers using LLM analysis.
"""

import json
import uuid
from typing import List, Dict, Optional, Tuple
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.models.claim import Claim, ClaimEvidence
from app.models.chunk import Chunk
from app.models.paper import Paper
from app.services.embedding.service import EmbeddingService

settings = get_settings()


class ClaimExtractionService:
    """Extract and manage scientific claims from papers."""

    MAX_CLAIMS_PER_CHUNK = 10  # Limit to prevent excessive processing
    MIN_CLAIM_LENGTH = 10      # Minimum claim text length
    MAX_CLAIM_LENGTH = 1000    # Maximum claim text length

    CLAIM_EXTRACTION_PROMPT = """You are a scientific claim extraction system. Your task is to identify explicit claims made in scientific text.

## What is a Claim?

A claim is a statement that can be evaluated as true or false based on evidence. Claims include:
- **Findings**: "X causes Y", "Treatment A is more effective than B"
- **Methodological**: "This technique achieves 95% accuracy"
- **Definitions**: "We define X as..."
- **Hypotheses**: "We hypothesize that..."

## What is NOT a Claim?

- Background information without assertion
- Questions
- Future work suggestions
- Acknowledgments

## Extraction Rules

1. Extract claims as **complete, standalone statements**
2. Preserve quantitative data when present
3. Note hedging language (may, might, suggests, could)
4. Identify the claim type
5. Extract conditions under which the claim is made

## Output Format

For each claim found, output JSON:

```json
{
  "claims": [
    {
      "text": "The exact claim text from the source",
      "normalized": "Standardized version of the claim",
      "type": "finding|methodology|hypothesis|definition",
      "subject": "What the claim is about",
      "predicate": "The relationship or action",
      "object": "The outcome or target",
      "has_quantitative": true,
      "effect_direction": "positive|negative|neutral|mixed",
      "effect_magnitude": "20-30% improvement",
      "hedging_detected": false,
      "conditions": ["in healthy adults", "over 12 weeks"],
      "confidence": 0.9,
      "source_quote": "Relevant quote from text"
    }
  ]
}
```

Only extract claims that are explicitly stated. Do not infer claims not present in the text.
"""

    def __init__(
        self,
        embedding_service: EmbeddingService,
        db: AsyncSession
    ):
        self.embedder = embedding_service
        self.db = db

        # Initialize LLM client (prefer Anthropic, fallback to OpenAI)
        self.use_anthropic = bool(settings.anthropic_api_key)

        if self.use_anthropic:
            from anthropic import AsyncAnthropic
            self.anthropic_client = AsyncAnthropic(api_key=settings.anthropic_api_key)
            self.model = settings.synthesis_model
        else:
            from openai import AsyncOpenAI
            self.openai_client = AsyncOpenAI(api_key=settings.openai_api_key)
            self.model = settings.openai_chat_model

    async def extract_claims_from_paper(
        self,
        paper_id: str,
        chunks: List[Chunk]
    ) -> List[Claim]:
        """Extract all claims from a paper's chunks."""

        if not chunks:
            return []

        all_claims = []
        errors = []

        for chunk in chunks:
            try:
                # Extract claims from chunk
                extracted = await self._extract_from_chunk(chunk)

                for claim_data in extracted:
                    try:
                        # Check for similar existing claim
                        existing = await self._find_similar_claim(claim_data["normalized"])

                        if existing and existing.similarity > 0.92:
                            # Add as evidence to existing claim
                            await self._add_evidence(
                                claim_id=existing.claim_id,
                                chunk=chunk,
                                paper_id=paper_id,
                                claim_data=claim_data
                            )
                        else:
                            # Create new claim
                            claim = await self._create_claim(claim_data)
                            await self._add_evidence(
                                claim_id=claim.id,
                                chunk=chunk,
                                paper_id=paper_id,
                                claim_data=claim_data
                            )
                            all_claims.append(claim)
                    except Exception as e:
                        errors.append(f"Failed to process claim '{claim_data.get('text', 'unknown')[:50]}...': {str(e)}")
                        continue

            except Exception as e:
                errors.append(f"Failed to extract claims from chunk {chunk.chunk_index}: {str(e)}")
                continue

        # Update claim metrics
        try:
            await self._update_claim_metrics(paper_id)
        except Exception as e:
            errors.append(f"Failed to update claim metrics: {str(e)}")

        # Log errors if any occurred
        if errors:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Claim extraction completed with {len(errors)} errors for paper {paper_id}: {errors[:3]}")

        return all_claims

    async def _extract_from_chunk(self, chunk: Chunk) -> List[Dict]:
        """Use LLM to extract claims from a chunk."""

        # Validate input
        if not chunk.content or len(chunk.content.strip()) < 50:
            return []  # Skip chunks that are too short

        user_message = f"Extract claims from this scientific text:\n\n{chunk.content}"

        try:
            if self.use_anthropic:
                content = await self._generate_with_anthropic(user_message)
            else:
                content = await self._generate_with_openai(user_message)

            # Parse JSON response
            try:
                data = json.loads(content)
                claims = data.get("claims", [])

                # Validate and filter claims
                validated_claims = []
                for claim in claims[:self.MAX_CLAIMS_PER_CHUNK]:  # Limit number of claims
                    if self._validate_claim_data(claim):
                        validated_claims.append(claim)

                return validated_claims
            except json.JSONDecodeError:
                return []
        except Exception:
            return []

    def _validate_claim_data(self, claim_data: Dict) -> bool:
        """Validate claim data structure and content."""
        if not isinstance(claim_data, dict):
            return False

        # Check required fields
        required_fields = ["text", "normalized", "type"]
        if not all(field in claim_data for field in required_fields):
            return False

        # Validate text length
        text = claim_data.get("text", "")
        if not isinstance(text, str) or len(text.strip()) < self.MIN_CLAIM_LENGTH or len(text) > self.MAX_CLAIM_LENGTH:
            return False

        # Validate claim type
        valid_types = ["finding", "methodology", "hypothesis", "definition"]
        if claim_data.get("type") not in valid_types:
            return False

        # Validate normalized text
        normalized = claim_data.get("normalized", "")
        if not isinstance(normalized, str) or len(normalized.strip()) < self.MIN_CLAIM_LENGTH:
            return False

        return True

    async def _generate_with_anthropic(self, user_message: str) -> str:
        """Generate extraction using Anthropic Claude."""
        response = await self.anthropic_client.messages.create(
            model=self.model,
            max_tokens=2000,
            system=self.CLAIM_EXTRACTION_PROMPT,
            messages=[{"role": "user", "content": user_message}],
        )
        return response.content[0].text

    async def _generate_with_openai(self, user_message: str) -> str:
        """Generate extraction using OpenAI GPT."""
        response = await self.openai_client.chat.completions.create(
            model=self.model,
            max_tokens=2000,
            messages=[
                {"role": "system", "content": self.CLAIM_EXTRACTION_PROMPT},
                {"role": "user", "content": user_message}
            ],
        )
        return response.choices[0].message.content

    async def _find_similar_claim(
        self,
        normalized_text: str,
        threshold: float = 0.92
    ) -> Optional["SimilarClaim"]:
        """Find semantically similar existing claim."""

        # Embed the normalized text
        embedding = await self.embedder.embed_query(normalized_text)

        # Search for similar claims
        result = await self.db.execute(
            select(
                Claim,
                (1 - Claim.embedding.cosine_distance(embedding)).label("similarity")
            )
            .where(Claim.embedding.isnot(None))
            .order_by(Claim.embedding.cosine_distance(embedding))
            .limit(1)
        )

        row = result.first()
        if row and row.similarity >= threshold:
            return SimilarClaim(claim_id=row.Claim.id, similarity=row.similarity)

        return None

    async def _create_claim(self, claim_data: Dict) -> Claim:
        """Create a new claim record."""

        # Generate embedding
        embedding = await self.embedder.embed_query(claim_data["normalized"])

        claim = Claim(
            canonical_text=claim_data["text"],
            normalized_text=claim_data["normalized"],
            claim_type=claim_data["type"],
            subject=claim_data.get("subject"),
            predicate=claim_data.get("predicate"),
            object=claim_data.get("object"),
            has_quantitative_data=claim_data.get("has_quantitative", False),
            effect_direction=claim_data.get("effect_direction"),
            effect_magnitude=claim_data.get("effect_magnitude"),
            domain_tags=self._extract_domain_tags(claim_data),
            embedding=embedding
        )

        self.db.add(claim)
        await self.db.commit()

        return claim

    async def _add_evidence(
        self,
        claim_id: str,
        chunk: Chunk,
        paper_id: str,
        claim_data: Dict
    ):
        """Add evidence linking a claim to a source."""

        # Determine stance
        stance = self._determine_stance(claim_data)

        evidence = ClaimEvidence(
            claim_id=claim_id,
            chunk_id=chunk.id,
            paper_id=paper_id,
            stance=stance,
            confidence=claim_data.get("confidence", 0.8),
            relevant_quote=claim_data.get("source_quote"),
            conditions=claim_data.get("conditions", []),
            extraction_model="claude-3-sonnet"
        )

        self.db.add(evidence)
        await self.db.commit()

    def _determine_stance(self, claim_data: Dict) -> str:
        """Determine if evidence supports, opposes, or is conditional."""

        # Check for hedging
        if claim_data.get("hedging_detected"):
            return "conditional"

        # Check for conditions
        if claim_data.get("conditions"):
            return "conditional"

        # Default to supports (the claim exists in this paper)
        return "supports"

    def _extract_domain_tags(self, claim_data: Dict) -> List[str]:
        """Extract domain-relevant tags from claim data."""
        # Simple implementation - in practice this could use NLP
        tags = []

        text = claim_data.get("normalized", "").lower()

        # Common metabolic health terms
        metabolic_terms = ["metabolism", "insulin", "glucose", "fat", "obesity", "diabetes"]
        if any(term in text for term in metabolic_terms):
            tags.append("metabolism")

        # Fasting terms
        fasting_terms = ["fasting", "intermittent", "caloric restriction"]
        if any(term in text for term in fasting_terms):
            tags.append("fasting")

        # Exercise terms
        exercise_terms = ["exercise", "training", "resistance", "aerobic"]
        if any(term in text for term in exercise_terms):
            tags.append("exercise")

        return tags

    async def _update_claim_metrics(self, paper_id: str):
        """Update aggregated metrics for claims related to this paper."""
        # This would be implemented with database triggers in production
        # For now, we'll update manually
        pass

    async def get_or_extract_claims(
        self,
        chunks: List[Chunk],
        query: str
    ) -> List[Claim]:
        """Get existing claims or extract new ones from chunks."""

        # For now, extract from all chunks
        # In production, this would check for existing claims first
        claims = []

        for chunk in chunks:
            paper_id = str(chunk.paper_id)
            paper_claims = await self.extract_claims_from_paper(paper_id, [chunk])
            claims.extend(paper_claims)

        return claims


class SimilarClaim:
    """Helper class for similar claim results."""

    def __init__(self, claim_id: str, similarity: float):
        self.claim_id = claim_id
        self.similarity = similarity