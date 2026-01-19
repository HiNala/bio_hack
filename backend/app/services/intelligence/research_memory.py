"""
Research Memory Service

Manages persistent research context and session memory.
"""

import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.memory import (
    ResearchSession, SessionQuery, ResearchInsight,
    MemorySummary
)
from app.models.workspace import Workspace
from app.models.synthesis_result import SynthesisResult
from app.services.embedding.service import EmbeddingService

settings = get_settings()


@dataclass
class ResearchContext:
    """Context retrieved from research memory."""
    session_id: str
    context_text: str
    token_count: int
    sources: Dict[str, int]


@dataclass
class SessionTimeline:
    """Timeline of research session events."""
    session: ResearchSession
    events: List['TimelineEvent']
    total_queries: int
    total_insights: int


@dataclass
class TimelineEvent:
    """An event in the research timeline."""
    type: str  # 'query', 'insight'
    timestamp: datetime
    content: str
    metadata: Dict[str, any]


class ResearchMemoryService:
    """Manage persistent research context across sessions."""

    def __init__(
        self,
        embedding_service: EmbeddingService,
        db: AsyncSession
    ):
        self.embedder = embedding_service
        self.db = db

        # Initialize LLM client for summarization
        self.use_anthropic = bool(settings.anthropic_api_key)

        if self.use_anthropic:
            from anthropic import AsyncAnthropic
            self.anthropic_client = AsyncAnthropic(api_key=settings.anthropic_api_key)
            self.model = settings.synthesis_model
        else:
            from openai import AsyncOpenAI
            self.openai_client = AsyncOpenAI(api_key=settings.openai_api_key)
            self.model = settings.openai_chat_model

    async def get_or_create_session(
        self,
        workspace_id: str,
        query: str
    ) -> ResearchSession:
        """Find relevant existing session or create new one."""

        # Embed the query
        query_embedding = await self.embedder.embed_query(query)

        # Search for similar active sessions
        similar = await self._find_similar_sessions(
            workspace_id=workspace_id,
            embedding=query_embedding,
            threshold=0.75
        )

        if similar:
            # Update existing session
            session = similar[0]
            session.last_activity_at = datetime.utcnow()
            await self.db.commit()
            return session

        # Create new session
        topic = await self._extract_topic(query)

        session = ResearchSession(
            workspace_id=workspace_id,
            name=f"Research: {topic[:50]}",
            primary_topic=topic,
            status="active"
        )

        self.db.add(session)
        await self.db.commit()

        return session

    async def _extract_topic(self, query: str) -> str:
        """Extract primary topic from query using simple heuristics."""
        # Simplified topic extraction
        # In production, this could use LLM or NLP
        query_lower = query.lower()

        # Common research topics
        topics = {
            "fasting": ["fasting", "intermittent", "caloric restriction"],
            "metabolism": ["metabolism", "insulin", "glucose", "diabetes"],
            "exercise": ["exercise", "training", "cardio", "strength"],
            "nutrition": ["diet", "nutrition", "protein", "carbs"],
            "aging": ["aging", "longevity", "senescence"],
            "cancer": ["cancer", "tumor", "carcinogen"],
        }

        for topic, keywords in topics.items():
            if any(keyword in query_lower for keyword in keywords):
                return topic

        # Fallback: use first few words
        words = query.split()[:3]
        return " ".join(words)

    async def _find_similar_sessions(
        self,
        workspace_id: str,
        embedding: List[float],
        threshold: float = 0.75
    ) -> List[ResearchSession]:
        """Find sessions similar to the embedding."""

        # Get active sessions from the last 30 days
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)

        result = await self.db.execute(
            select(ResearchSession)
            .where(
                ResearchSession.workspace_id == workspace_id,
                ResearchSession.status == "active",
                ResearchSession.last_activity_at > thirty_days_ago
            )
        )

        sessions = list(result.scalars())

        # For now, return the most recently active session
        # In production, this would compare embeddings
        if sessions:
            return [max(sessions, key=lambda s: s.last_activity_at)]

        return []

    async def get_relevant_context(
        self,
        session_id: str,
        current_query: str,
        max_tokens: int = 2000
    ) -> ResearchContext:
        """Retrieve relevant context from memory for current query."""

        # Get session
        session = await self.db.get(ResearchSession, session_id)
        if not session:
            return ResearchContext(
                session_id=session_id,
                context_text="",
                token_count=0,
                sources={"insights": 0, "summaries": 0, "recent_queries": 0}
            )

        # Get memory summaries
        query_embedding = await self.embedder.embed_query(current_query)

        summaries_result = await self.db.execute(
            select(MemorySummary)
            .where(MemorySummary.session_id == session_id)
            .order_by(
                # Simplified: just order by recency for now
                desc(MemorySummary.created_at)
            )
            .limit(5)
        )

        # Get recent queries
        queries_result = await self.db.execute(
            select(SessionQuery)
            .where(SessionQuery.session_id == session_id)
            .order_by(desc(SessionQuery.created_at))
            .limit(10)
        )

        # Get key insights
        insights_result = await self.db.execute(
            select(ResearchInsight)
            .where(
                ResearchInsight.session_id == session_id,
                ResearchInsight.user_confirmed == True
            )
            .order_by(desc(ResearchInsight.discovered_at))
        )

        # Assemble context
        context_parts = []
        total_tokens = 0

        # Add key insights first
        for insight in insights_result.scalars():
            text = f"[Prior Finding] {insight.content}"
            tokens = self._count_tokens(text)
            if total_tokens + tokens <= max_tokens:
                context_parts.append(text)
                total_tokens += tokens

        # Add relevant summaries
        for summary in summaries_result.scalars():
            if total_tokens + summary.token_count <= max_tokens:
                context_parts.append(f"[Session Context] {summary.summary_text}")
                total_tokens += summary.token_count

        # Add recent query context
        for query in queries_result.scalars()[:3]:
            text = f"[Recent Query] Q: {query.query_text[:200]}"
            tokens = self._count_tokens(text)
            if total_tokens + tokens <= max_tokens:
                context_parts.append(text)
                total_tokens += tokens

        return ResearchContext(
            session_id=session_id,
            context_text="\n\n".join(context_parts),
            token_count=total_tokens,
            sources={
                "insights": len(list(insights_result.scalars())),
                "summaries": len(list(summaries_result.scalars())),
                "recent_queries": len(list(queries_result.scalars())[:3])
            }
        )

    def _count_tokens(self, text: str) -> int:
        """Rough token count (4 chars per token approximation)."""
        return len(text) // 4

    async def record_query(
        self,
        session_id: str,
        query: str,
        synthesis_id: str,
        claims_discovered: List[str],
        papers_used: List[str],
        context_used: str
    ) -> SessionQuery:
        """Record a query and its results to memory."""

        # Determine query type
        query_type = await self._classify_query_type(session_id, query)

        session_query = SessionQuery(
            session_id=session_id,
            query_text=query,
            query_type=query_type,
            synthesis_id=synthesis_id,
            claims_discovered=claims_discovered,
            papers_used=papers_used,
            prior_context_used=context_used
        )

        self.db.add(session_query)

        # Update session
        session = await self.db.get(ResearchSession, session_id)
        if session:
            session.last_activity_at = datetime.utcnow()

            # Add new claims and papers to session's key lists
            session.key_claims = list(set(
                (session.key_claims or []) + claims_discovered
            ))[:50]  # Keep top 50

            session.key_papers = list(set(
                (session.key_papers or []) + papers_used
            ))[:30]  # Keep top 30

        await self.db.commit()

        # Check if we need to create a new summary
        query_count = await self._get_query_count_since_last_summary(session_id)
        if query_count >= 5:
            await self._create_memory_summary(session_id)

        return session_query

    async def _classify_query_type(self, session_id: str, query: str) -> str:
        """Classify the type of query being asked."""
        # Simplified classification
        query_lower = query.lower()

        if any(word in query_lower for word in ["what", "how", "why", "explain"]):
            return "initial"
        elif any(word in query_lower for word in ["more", "further", "additionally", "also"]):
            return "followup"
        elif any(word in query_lower for word in ["refine", "narrow", "focus", "specifically"]):
            return "refinement"
        else:
            return "tangent"

    async def _get_query_count_since_last_summary(self, session_id: str) -> int:
        """Count queries since last memory summary."""
        # Get last summary time
        result = await self.db.execute(
            select(MemorySummary.created_at)
            .where(MemorySummary.session_id == session_id)
            .order_by(desc(MemorySummary.created_at))
            .limit(1)
        )

        last_summary_time = result.scalar()
        if not last_summary_time:
            # No summaries yet, count all queries
            result = await self.db.execute(
                select(SessionQuery.id)
                .where(SessionQuery.session_id == session_id)
            )
            return len(result.scalars())

        # Count queries since last summary
        result = await self.db.execute(
            select(SessionQuery.id)
            .where(
                SessionQuery.session_id == session_id,
                SessionQuery.created_at > last_summary_time
            )
        )

        return len(result.scalars())

    async def _create_memory_summary(self, session_id: str):
        """Compress recent queries into a memory summary."""

        # Get queries since last summary
        last_summary_result = await self.db.execute(
            select(MemorySummary.created_at)
            .where(MemorySummary.session_id == session_id)
            .order_by(desc(MemorySummary.created_at))
            .limit(1)
        )

        last_summary_time = last_summary_result.scalar()
        if last_summary_time is None:
            last_summary_time = datetime.min

        queries_result = await self.db.execute(
            select(SessionQuery)
            .where(
                SessionQuery.session_id == session_id,
                SessionQuery.created_at > last_summary_time
            )
            .order_by(SessionQuery.created_at)
        )

        queries = list(queries_result.scalars())

        if not queries:
            return

        # Generate summary using LLM
        query_texts = "\n".join([
            f"Q{i+1}: {q.query_text}"
            for i, q in enumerate(queries)
        ])

        prompt = """Summarize this research session into key learnings.
Focus on:
1. Main questions explored
2. Key findings discovered
3. Important claims established
4. Gaps or contradictions identified

Be concise but preserve important details. Output as a narrative summary."""

        try:
            if self.use_anthropic:
                content = await self._generate_with_anthropic(prompt, query_texts)
            else:
                content = await self._generate_with_openai(prompt, query_texts)

            summary_text = content
        except Exception:
            # Fallback summary
            summary_text = f"Session covering {len(queries)} queries about research topics."

        summary_embedding = await self.embedder.embed_query(summary_text)

        summary = MemorySummary(
            session_id=session_id,
            summary_text=summary_text,
            summary_embedding=summary_embedding,
            query_ids=[str(q.id) for q in queries],
            time_range_start=queries[0].created_at,
            time_range_end=queries[-1].created_at,
            token_count=self._count_tokens(summary_text),
            compression_ratio=len(query_texts) / len(summary_text)
        )

        self.db.add(summary)
        await self.db.commit()

    async def _generate_with_anthropic(self, prompt: str, query_texts: str) -> str:
        """Generate summary using Anthropic Claude."""
        user_message = f"{prompt}\n\nResearch queries:\n{query_texts}"

        response = await self.anthropic_client.messages.create(
            model=self.model,
            max_tokens=500,
            system="You are a research session summarizer.",
            messages=[{"role": "user", "content": user_message}],
        )
        return response.content[0].text

    async def _generate_with_openai(self, prompt: str, query_texts: str) -> str:
        """Generate summary using OpenAI GPT."""
        user_message = f"{prompt}\n\nResearch queries:\n{query_texts}"

        response = await self.openai_client.chat.completions.create(
            model=self.model,
            max_tokens=500,
            messages=[
                {"role": "system", "content": "You are a research session summarizer."},
                {"role": "user", "content": user_message}
            ],
        )
        return response.choices[0].message.content

    async def get_session_timeline(
        self,
        session_id: str
    ) -> SessionTimeline:
        """Get chronological timeline of research session."""

        session = await self.db.get(ResearchSession, session_id)
        if not session:
            return SessionTimeline(
                session=None,
                events=[],
                total_queries=0,
                total_insights=0
            )

        queries_result = await self.db.execute(
            select(SessionQuery)
            .where(SessionQuery.session_id == session_id)
            .order_by(SessionQuery.created_at)
        )

        insights_result = await self.db.execute(
            select(ResearchInsight)
            .where(ResearchInsight.session_id == session_id)
            .order_by(ResearchInsight.discovered_at)
        )

        # Merge into timeline
        events = []

        for query in queries_result.scalars():
            events.append(TimelineEvent(
                type="query",
                timestamp=query.created_at,
                content=query.query_text,
                metadata={"query_type": query.query_type}
            ))

        for insight in insights_result.scalars():
            events.append(TimelineEvent(
                type="insight",
                timestamp=insight.discovered_at,
                content=insight.content,
                metadata={"insight_type": insight.insight_type}
            ))

        events.sort(key=lambda e: e.timestamp)

        return SessionTimeline(
            session=session,
            events=events,
            total_queries=len([e for e in events if e.type == "query"]),
            total_insights=len([e for e in events if e.type == "insight"])
        )