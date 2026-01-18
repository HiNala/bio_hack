"""
RAG Service

Retrieval-Augmented Generation for synthesizing answers from scientific literature.
"""

import json
import re
from typing import Optional
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.services.search import SearchService, SearchResult
from app.services.intelligence.query_parser import QueryParser
from app.schemas import RAGResponse, Citation

settings = get_settings()


@dataclass
class ContextChunk:
    """Chunk with context for RAG."""
    index: int
    paper_id: str
    paper_title: str
    paper_authors: list[str]
    paper_year: Optional[int]
    text: str


class RAGService:
    """
    RAG service for answering research questions.
    
    Pipeline:
    1. Parse query to understand intent
    2. Search for relevant chunks
    3. Assemble context from top results
    4. Generate synthesized answer with citations
    
    Supports both Anthropic Claude and OpenAI GPT for synthesis.
    Falls back to OpenAI if Anthropic is not configured.
    """
    
    SYSTEM_PROMPT = """You are a research synthesis assistant. Your job is to answer research questions by synthesizing information from academic papers.

You will be given:
1. A research question
2. Excerpts from relevant academic papers (with citations)

Your response MUST follow this exact structure:

**Summary**
A 2-3 sentence direct answer to the question.

**Key Findings**
- Finding 1 [1]
- Finding 2 [2]
- Finding 3 [1][3]
(Use [N] citation format, referencing the source numbers provided)

**Consensus**
What do researchers generally agree on regarding this topic?

**Open Questions**
What remains uncertain or debated in this area?

IMPORTANT RULES:
1. ONLY cite sources from the provided excerpts
2. Use [N] format for citations (e.g., [1], [2])
3. Be specific and factual
4. Acknowledge uncertainty when present
5. If the excerpts don't contain enough information, say so"""

    def __init__(self, db: AsyncSession):
        """
        Initialize RAG service.
        
        Args:
            db: Database session
        """
        self.db = db
        self.search_service = SearchService(db)
        self.query_parser = QueryParser()
        
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
    
    async def answer(
        self,
        question: str,
        top_k: int = None,
        use_llm_parsing: bool = True,
    ) -> RAGResponse:
        """
        Answer a research question using RAG.
        
        Args:
            question: Research question
            top_k: Number of chunks to retrieve
            use_llm_parsing: Whether to use LLM for query parsing
            
        Returns:
            RAGResponse with synthesized answer and citations
        """
        top_k = top_k or settings.context_top_n
        
        # Step 1: Parse query (optional LLM enhancement)
        search_query = question
        if use_llm_parsing:
            try:
                parsed_query = await self.query_parser.parse(question)
                if parsed_query.get("primary_terms"):
                    search_query = " ".join(parsed_query["primary_terms"])
            except Exception:
                pass
        
        # Step 2: Search for relevant chunks
        search_results = await self.search_service.search(
            query=search_query,
            top_k=top_k * 2,  # Fetch extra to ensure diversity
            dedupe_papers=True,
        )
        
        if not search_results:
            return RAGResponse(
                query_id="",
                summary="No relevant papers found for this query. Try rephrasing or broadening your search.",
                key_findings=[],
                consensus=[],
                open_questions=["No papers available to analyze."],
                citations=[],
                papers_analyzed=0,
            )
        
        # Step 3: Build context
        context_chunks = self._build_context(search_results[:top_k])
        
        # Step 4: Generate answer
        answer = await self._generate_answer(question, context_chunks)
        
        # Step 5: Build citations
        citations = [
            Citation(
                index=chunk.index,
                paper_id=chunk.paper_id,
                title=chunk.paper_title,
                authors=chunk.paper_authors[:3],  # Limit authors
                year=chunk.paper_year,
            )
            for chunk in context_chunks
        ]
        
        return RAGResponse(
            query_id="",  # Will be set by caller
            summary=answer.get("summary", ""),
            key_findings=answer.get("key_findings", []),
            consensus=answer.get("consensus", []),
            open_questions=answer.get("open_questions", []),
            citations=citations,
            papers_analyzed=len(context_chunks),
        )
    
    def _build_context(self, results: list[SearchResult]) -> list[ContextChunk]:
        """
        Build context chunks from search results.
        
        Args:
            results: Search results
            
        Returns:
            List of context chunks with citations
        """
        chunks = []
        for i, result in enumerate(results):
            chunks.append(ContextChunk(
                index=i + 1,  # 1-indexed for citations
                paper_id=result.paper_id,
                paper_title=result.paper_title,
                paper_authors=result.paper_authors,
                paper_year=result.paper_year,
                text=result.chunk_text,
            ))
        return chunks
    
    async def _generate_answer(
        self,
        question: str,
        chunks: list[ContextChunk],
    ) -> dict:
        """
        Generate synthesized answer using LLM.
        
        Args:
            question: Research question
            chunks: Context chunks with citations
            
        Returns:
            Parsed answer with sections
        """
        # Format context
        context_text = self._format_context(chunks)
        
        # Build user message
        user_message = f"""Research Question: {question}

Relevant Paper Excerpts:
{context_text}

Please synthesize an answer based on these sources."""

        try:
            if self.use_anthropic:
                content = await self._generate_with_anthropic(user_message)
            else:
                content = await self._generate_with_openai(user_message)
            
            return self._parse_answer(content)
            
        except Exception as e:
            print(f"RAG generation failed: {e}")
            return {
                "summary": f"Error generating synthesis: {str(e)}",
                "key_findings": [],
                "consensus": [],
                "open_questions": [],
            }
    
    async def _generate_with_anthropic(self, user_message: str) -> str:
        """Generate answer using Anthropic Claude."""
        response = await self.anthropic_client.messages.create(
            model=self.model,
            max_tokens=2000,
            system=self.SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}],
        )
        return response.content[0].text
    
    async def _generate_with_openai(self, user_message: str) -> str:
        """Generate answer using OpenAI GPT."""
        response = await self.openai_client.chat.completions.create(
            model=self.model,
            max_tokens=2000,
            messages=[
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": user_message}
            ],
        )
        return response.choices[0].message.content
    
    def _format_context(self, chunks: list[ContextChunk]) -> str:
        """Format context chunks for the prompt."""
        formatted = []
        for chunk in chunks:
            authors_str = ", ".join(chunk.paper_authors[:3])
            if len(chunk.paper_authors) > 3:
                authors_str += " et al."
            
            year_str = f" ({chunk.paper_year})" if chunk.paper_year else ""
            
            formatted.append(f"""[{chunk.index}] {chunk.paper_title}
{authors_str}{year_str}

{chunk.text}
""")
        
        return "\n---\n".join(formatted)
    
    def _parse_answer(self, content: str) -> dict:
        """
        Parse LLM response into structured sections.
        
        Args:
            content: Raw response text
            
        Returns:
            Dictionary with summary, key_findings, consensus, open_questions
        """
        result = {
            "summary": "",
            "key_findings": [],
            "consensus": [],
            "open_questions": [],
        }
        
        # Split by sections
        sections = re.split(r'\*\*([^*]+)\*\*', content)
        
        current_section = None
        for part in sections:
            part = part.strip()
            
            # Check if this is a section header
            if part.lower() in ["summary", "key findings", "consensus", "open questions"]:
                current_section = part.lower().replace(" ", "_")
            elif current_section and part:
                if current_section == "summary":
                    result["summary"] = part
                elif current_section in ["key_findings", "consensus", "open_questions"]:
                    # Parse bullet points
                    lines = part.split("\n")
                    items = []
                    for line in lines:
                        line = line.strip()
                        if line.startswith("-") or line.startswith("•"):
                            items.append(line[1:].strip())
                        elif line and not line.startswith("*"):
                            items.append(line)
                    result[current_section] = items
        
        # Fallback: if parsing failed, use the whole content as summary
        if not result["summary"] and not result["key_findings"]:
            result["summary"] = content[:500] + "..." if len(content) > 500 else content
        
        return result
