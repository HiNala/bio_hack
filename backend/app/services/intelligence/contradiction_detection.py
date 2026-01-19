"""
Contradiction Detection Service

Detects and classifies contradictions between scientific claims and evidence.
"""

import json
from typing import List, Dict, Optional
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.claim import Claim, ClaimEvidence, Contradiction
from app.models.paper import Paper

settings = get_settings()


@dataclass
class ConsensusReport:
    """Report on consensus and contradictions for a topic."""
    topic: str
    consensus: List['ConsensusItem']
    contested: List['ContestedItem']
    conditional: List['ConditionalItem']
    overall_consensus_score: float


@dataclass
class ConsensusItem:
    """A claim with strong consensus."""
    claim: Claim
    score: float
    evidence_count: int
    key_papers: List[str]


@dataclass
class ContestedItem:
    """A claim with active contradictions."""
    claim: Claim
    contradictions: List[Contradiction]
    severity: float


@dataclass
class ConditionalItem:
    """A claim with conditional evidence."""
    claim: Claim
    conditions: List[str]


@dataclass
class ClaimEvidenceMap:
    """Full evidence map for a claim."""
    claim: Claim
    supporting: List['EvidenceItem']
    opposing: List['EvidenceItem']
    conditional: List['EvidenceItem']
    consensus_score: float
    evidence_strength: float


@dataclass
class EvidenceItem:
    """Evidence from a paper supporting/opposing a claim."""
    paper_id: str
    paper_title: str
    paper_year: Optional[int]
    citation_count: int
    quote: str
    conditions: List[str]
    confidence: float


class ContradictionDetectionService:
    """Detect and classify contradictions between papers."""

    CONTRADICTION_ANALYSIS_PROMPT = """You are analyzing potential contradictions between scientific findings.

Given two pieces of evidence about the same claim, determine:

1. Is this a genuine contradiction, or can both be true?
2. What type of disagreement is this?
3. How severe is the disagreement?
4. How might this be resolved?

## Disagreement Types

- METHODOLOGICAL: Different experimental approaches yield different results
- POPULATION: Results vary based on study population characteristics
- TEMPORAL: Results may have changed over time (new discoveries, replication failures)
- DEFINITIONAL: Authors define key terms differently
- STATISTICAL: Same data interpreted differently
- SCOPE: Claims apply to different scopes/contexts

## Output Format

```json
{
  "is_contradiction": true,
  "contradiction_type": "methodological",
  "severity": 0.7,
  "explanation": "Study A used RCT while Study B was observational...",
  "resolution_suggestion": "A meta-analysis controlling for methodology might resolve...",
  "notes": "Both studies have limitations that should be considered"
}
```
"""

    def __init__(self, db: AsyncSession):
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

    async def detect_contradictions(
        self,
        claim_id: str
    ) -> List[Contradiction]:
        """Detect all contradictions for a claim."""

        try:
            # Get all evidence for claim
            evidence = await self._get_claim_evidence(claim_id)

            if len(evidence) < 2:
                return []  # Need at least 2 pieces of evidence to have a contradiction

            # Separate by stance
            supporting = [e for e in evidence if e.stance == "supports"]
            opposing = [e for e in evidence if e.stance == "opposes"]

            contradictions = []

            # Compare supporting vs opposing pairs
            for sup in supporting:
                for opp in opposing:
                    try:
                        contradiction = await self._analyze_pair(claim_id, sup, opp)
                        if contradiction and contradiction.is_contradiction:
                            contradictions.append(contradiction)
                    except Exception as e:
                        import logging
                        logger = logging.getLogger(__name__)
                        logger.warning(f"Failed to analyze contradiction pair for claim {claim_id}: {str(e)}")
                        continue

            # Also check for conditional conflicts (limit to avoid excessive computation)
            conditional = [e for e in evidence if e.stance == "conditional"]
            if len(conditional) > 1:
                for i, cond_a in enumerate(conditional[:5]):  # Limit to first 5
                    for cond_b in conditional[i+1:i+6]:  # Compare with next 5
                        try:
                            if self._conditions_conflict(cond_a.conditions, cond_b.conditions):
                                contradiction = await self._analyze_pair(claim_id, cond_a, cond_b)
                                if contradiction:
                                    contradictions.append(contradiction)
                        except Exception as e:
                            import logging
                            logger = logging.getLogger(__name__)
                            logger.warning(f"Failed to analyze conditional conflict for claim {claim_id}: {str(e)}")
                            continue

            return contradictions

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to detect contradictions for claim {claim_id}: {str(e)}")
            return []

    async def _analyze_pair(
        self,
        claim_id: str,
        evidence_a: ClaimEvidence,
        evidence_b: ClaimEvidence
    ) -> Optional[Contradiction]:
        """Analyze a pair of evidence for contradiction."""

        # Get paper details
        paper_a = await self.db.get(Paper, evidence_a.paper_id)
        paper_b = await self.db.get(Paper, evidence_b.paper_id)
        claim = await self.db.get(Claim, claim_id)

        prompt = f"""
Claim: {claim.canonical_text}

Evidence A ({paper_a.title}, {paper_a.publication_year}):
Stance: {evidence_a.stance}
Quote: "{evidence_a.relevant_quote}"
Conditions: {evidence_a.conditions}

Evidence B ({paper_b.title}, {paper_b.publication_year}):
Stance: {evidence_b.stance}
Quote: "{evidence_b.relevant_quote}"
Conditions: {evidence_b.conditions}

Analyze whether these represent a genuine scientific contradiction.
"""

        try:
            if self.use_anthropic:
                content = await self._generate_with_anthropic(prompt)
            else:
                content = await self._generate_with_openai(prompt)

            data = json.loads(content)

            if not data.get("is_contradiction"):
                return None

            contradiction = Contradiction(
                claim_id=claim_id,
                contradiction_type=data["contradiction_type"],
                severity=data["severity"],
                evidence_a_id=evidence_a.id,
                evidence_b_id=evidence_b.id,
                explanation=data["explanation"],
                resolution_suggestion=data.get("resolution_suggestion"),
                paper_a_id=evidence_a.paper_id,
                paper_b_id=evidence_b.paper_id
            )

            self.db.add(contradiction)
            await self.db.commit()

            return contradiction
        except Exception:
            return None

    async def _generate_with_anthropic(self, user_message: str) -> str:
        """Generate analysis using Anthropic Claude."""
        response = await self.anthropic_client.messages.create(
            model=self.model,
            max_tokens=1000,
            system=self.CONTRADICTION_ANALYSIS_PROMPT,
            messages=[{"role": "user", "content": user_message}],
        )
        return response.content[0].text

    async def _generate_with_openai(self, user_message: str) -> str:
        """Generate analysis using OpenAI GPT."""
        response = await self.openai_client.chat.completions.create(
            model=self.model,
            max_tokens=1000,
            messages=[
                {"role": "system", "content": self.CONTRADICTION_ANALYSIS_PROMPT},
                {"role": "user", "content": user_message}
            ],
        )
        return response.choices[0].message.content

    async def _get_claim_evidence(self, claim_id: str) -> List[ClaimEvidence]:
        """Get all evidence for a claim."""
        result = await self.db.execute(
            select(ClaimEvidence)
            .where(ClaimEvidence.claim_id == claim_id)
        )
        return list(result.scalars())

    def _conditions_conflict(self, conditions_a: List[str], conditions_b: List[str]) -> bool:
        """Check if two sets of conditions represent genuine conflicts."""
        # Simple check: if conditions are mutually exclusive
        # This is a simplified implementation
        if not conditions_a or not conditions_b:
            return False

        # Check for explicit contradictions
        for cond_a in conditions_a:
            for cond_b in conditions_b:
                if self._are_conditions_contradictory(cond_a, cond_b):
                    return True

        return False

    def _are_conditions_contradictory(self, cond_a: str, cond_b: str) -> bool:
        """Check if two conditions are contradictory."""
        # Very simplified - in practice this would use NLP
        contradictory_pairs = [
            ("healthy", "diabetic"),
            ("overweight", "normal weight"),
            ("young", "elderly"),
            ("male", "female"),
        ]

        cond_a_lower = cond_a.lower()
        cond_b_lower = cond_b.lower()

        for pair in contradictory_pairs:
            if (pair[0] in cond_a_lower and pair[1] in cond_b_lower) or \
               (pair[1] in cond_a_lower and pair[0] in cond_b_lower):
                return True

        return False

    async def get_claim_evidence_map(
        self,
        claim_id: str
    ) -> ClaimEvidenceMap:
        """Get full evidence map for a claim."""

        claim = await self.db.get(Claim, claim_id)

        # Get all evidence with paper details
        result = await self.db.execute(
            select(ClaimEvidence, Paper)
            .join(Paper, ClaimEvidence.paper_id == Paper.id)
            .where(ClaimEvidence.claim_id == claim_id)
            .order_by(Paper.citation_count.desc())
        )

        supporting = []
        opposing = []
        conditional = []

        for ev, paper in result:
            evidence_item = EvidenceItem(
                paper_id=str(paper.id),
                paper_title=paper.title,
                paper_year=paper.year,
                citation_count=paper.citation_count,
                quote=ev.relevant_quote or "",
                conditions=ev.conditions,
                confidence=ev.confidence
            )

            if ev.stance == "supports":
                supporting.append(evidence_item)
            elif ev.stance == "opposes":
                opposing.append(evidence_item)
            else:
                conditional.append(evidence_item)

        consensus_score = self._calculate_consensus(supporting, opposing, conditional)
        evidence_strength = self._calculate_strength(supporting, opposing, conditional)

        return ClaimEvidenceMap(
            claim=claim,
            supporting=supporting,
            opposing=opposing,
            conditional=conditional,
            consensus_score=consensus_score,
            evidence_strength=evidence_strength
        )

    def _calculate_consensus(
        self,
        supporting: List[EvidenceItem],
        opposing: List[EvidenceItem],
        conditional: List[EvidenceItem]
    ) -> float:
        """Calculate consensus score: -1 (contested) to 1 (full consensus)."""

        total_supporting = len(supporting)
        total_opposing = len(opposing)
        total_conditional = len(conditional)

        if total_supporting + total_opposing + total_conditional == 0:
            return 0.0

        # Weight evidence by citation count (simplified)
        supporting_weight = sum(e.citation_count for e in supporting) + total_supporting
        opposing_weight = sum(e.citation_count for e in opposing) + total_opposing
        conditional_weight = sum(e.citation_count for e in conditional) + total_conditional

        numerator = supporting_weight - opposing_weight
        denominator = supporting_weight + opposing_weight + conditional_weight

        if denominator == 0:
            return 0.0

        return max(-1.0, min(1.0, numerator / denominator))

    def _calculate_strength(
        self,
        supporting: List[EvidenceItem],
        opposing: List[EvidenceItem],
        conditional: List[EvidenceItem]
    ) -> float:
        """Calculate evidence strength: 0-1 based on quality and quantity."""

        all_evidence = supporting + opposing + conditional
        if not all_evidence:
            return 0.0

        # Simplified: average of citation counts, normalized
        avg_citations = sum(e.citation_count for e in all_evidence) / len(all_evidence)

        # Normalize to 0-1 scale (assuming 100 citations is "very strong")
        strength = min(1.0, avg_citations / 100.0)

        # Factor in number of papers
        paper_factor = min(1.0, len(all_evidence) / 10.0)  # 10+ papers = max strength

        return (strength + paper_factor) / 2.0

    async def get_consensus_report(
        self,
        topic: str,
        workspace_id: Optional[str] = None
    ) -> ConsensusReport:
        """Generate a consensus report for a topic."""

        # Find relevant claims
        claims = await self._find_claims_for_topic(topic)

        consensus_areas = []
        contested_areas = []
        conditional_areas = []

        for claim in claims:
            evidence_map = await self.get_claim_evidence_map(str(claim.id))
            contradictions = await self.detect_contradictions(str(claim.id))

            if evidence_map.consensus_score > 0.6 and not contradictions:
                consensus_areas.append(ConsensusItem(
                    claim=claim,
                    score=evidence_map.consensus_score,
                    evidence_count=len(evidence_map.supporting),
                    key_papers=[e.paper_id for e in evidence_map.supporting[:3]]
                ))
            elif contradictions:
                contested_areas.append(ContestedItem(
                    claim=claim,
                    contradictions=contradictions,
                    severity=max(c.severity for c in contradictions)
                ))
            else:
                conditional_areas.append(ConditionalItem(
                    claim=claim,
                    conditions=self._aggregate_conditions(evidence_map.conditional)
                ))

        overall_score = self._calculate_overall_consensus(claims)

        return ConsensusReport(
            topic=topic,
            consensus=sorted(consensus_areas, key=lambda x: -x.score),
            contested=sorted(contested_areas, key=lambda x: -x.severity),
            conditional=conditional_areas,
            overall_consensus_score=overall_score
        )

    async def _find_claims_for_topic(self, topic: str) -> List[Claim]:
        """Find claims related to a topic."""
        # Simplified: search by domain tags for now
        # In production, this would use semantic search
        topic_lower = topic.lower()

        result = await self.db.execute(
            select(Claim)
            .where(Claim.domain_tags.contains([topic_lower]))
            .limit(20)
        )

        return list(result.scalars())

    def _aggregate_conditions(self, conditional: List[EvidenceItem]) -> List[str]:
        """Aggregate conditions from conditional evidence."""
        all_conditions = []
        for evidence in conditional:
            all_conditions.extend(evidence.conditions)

        # Simple deduplication
        return list(set(all_conditions))

    def _calculate_overall_consensus(self, claims: List[Claim]) -> float:
        """Calculate overall consensus for a set of claims."""
        if not claims:
            return 0.0

        # Simple average of consensus scores
        scores = [getattr(c, 'consensus_score', 0) or 0 for c in claims]
        return sum(scores) / len(scores)