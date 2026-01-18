"""
Query Parser

Uses LLM (Claude or OpenAI) to parse natural language queries into structured search parameters.
"""

import json
from typing import Optional

from app.config import get_settings
from app.schemas import ParsedQuery

settings = get_settings()


class QueryParser:
    """
    LLM-powered query parser.
    
    Converts natural language research questions into structured
    queries for literature APIs and semantic search.
    
    Supports both Anthropic Claude and OpenAI GPT.
    """
    
    SYSTEM_PROMPT = """You are a research query parser. Your job is to analyze natural language research questions and extract structured information for searching academic literature.

Given a research question, extract:
1. primary_terms: The main concepts to search for (3-5 terms)
2. expanded_terms: Related terms, synonyms, or alternative phrasings (3-5 terms)
3. year_from: Minimum publication year if mentioned (null if not specified)
4. year_to: Maximum publication year if mentioned (null if not specified)
5. fields: Academic disciplines relevant to the query (e.g., Physics, Biology, Computer Science)
6. query_type: One of "factual", "synthesis", "comparison", or "survey"
   - factual: Looking for specific facts or definitions
   - synthesis: Want to understand the overall state of knowledge
   - comparison: Comparing multiple approaches, theories, or methods
   - survey: Looking for a broad overview of a field or topic

Respond ONLY with valid JSON in this exact format:
{
  "primary_terms": ["term1", "term2", "term3"],
  "expanded_terms": ["related1", "related2"],
  "year_from": null,
  "year_to": null,
  "fields": ["Field1", "Field2"],
  "query_type": "synthesis"
}"""

    FEW_SHOT_EXAMPLES = [
        {
            "query": "What are the leading interpretations of quantum mechanics since 2010?",
            "response": {
                "primary_terms": ["quantum mechanics interpretations", "Copenhagen interpretation", "many-worlds interpretation"],
                "expanded_terms": ["quantum foundations", "measurement problem", "wave function collapse", "pilot wave theory"],
                "year_from": 2010,
                "year_to": None,
                "fields": ["Physics", "Philosophy of Science"],
                "query_type": "survey"
            }
        },
        {
            "query": "How does CRISPR compare to earlier gene editing techniques?",
            "response": {
                "primary_terms": ["CRISPR", "gene editing", "CRISPR-Cas9"],
                "expanded_terms": ["zinc finger nucleases", "TALENs", "genome editing", "genetic engineering"],
                "year_from": None,
                "year_to": None,
                "fields": ["Molecular Biology", "Genetics", "Biotechnology"],
                "query_type": "comparison"
            }
        }
    ]
    
    def __init__(self):
        """Initialize query parser with available LLM client."""
        self.use_anthropic = bool(settings.anthropic_api_key)
        
        if self.use_anthropic:
            from anthropic import AsyncAnthropic
            self.client = AsyncAnthropic(api_key=settings.anthropic_api_key)
            self.model = settings.synthesis_model
        elif settings.openai_api_key:
            from openai import AsyncOpenAI
            self.client = AsyncOpenAI(api_key=settings.openai_api_key)
            self.model = settings.openai_chat_model
        else:
            self.client = None
            self.model = None
    
    async def parse(self, query: str) -> dict:
        """
        Parse a natural language query into structured format.
        
        Args:
            query: Natural language research question
            
        Returns:
            Dictionary with extracted information
        """
        # If no LLM available, use fallback
        if not self.client:
            return self._fallback_parse(query)
        
        try:
            if self.use_anthropic:
                return await self._parse_with_anthropic(query)
            else:
                return await self._parse_with_openai(query)
        except Exception as e:
            print(f"LLM parsing failed: {e}, using fallback")
            return self._fallback_parse(query)
    
    async def _parse_with_anthropic(self, query: str) -> dict:
        """Parse using Anthropic Claude."""
        messages = []
        
        for example in self.FEW_SHOT_EXAMPLES:
            messages.append({
                "role": "user",
                "content": f"Parse this research query: {example['query']}"
            })
            messages.append({
                "role": "assistant",
                "content": json.dumps(example["response"])
            })
        
        messages.append({
            "role": "user",
            "content": f"Parse this research query: {query}"
        })
        
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=500,
            system=self.SYSTEM_PROMPT,
            messages=messages,
        )
        
        content = response.content[0].text.strip()
        return self._extract_json(content, query)
    
    async def _parse_with_openai(self, query: str) -> dict:
        """Parse using OpenAI GPT."""
        messages = [{"role": "system", "content": self.SYSTEM_PROMPT}]
        
        for example in self.FEW_SHOT_EXAMPLES:
            messages.append({
                "role": "user",
                "content": f"Parse this research query: {example['query']}"
            })
            messages.append({
                "role": "assistant",
                "content": json.dumps(example["response"])
            })
        
        messages.append({
            "role": "user",
            "content": f"Parse this research query: {query}"
        })
        
        response = await self.client.chat.completions.create(
            model=self.model,
            max_tokens=500,
            messages=messages,
        )
        
        content = response.choices[0].message.content.strip()
        return self._extract_json(content, query)
    
    def _extract_json(self, content: str, original_query: str) -> dict:
        """Extract and parse JSON from LLM response."""
        # Try to parse JSON directly
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError:
            # Try to extract JSON from markdown code block
            import re
            json_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', content)
            if json_match:
                parsed = json.loads(json_match.group(1).strip())
            else:
                # Last resort: find first { to last }
                start = content.find('{')
                end = content.rfind('}')
                if start != -1 and end != -1:
                    parsed = json.loads(content[start:end+1])
                else:
                    raise ValueError("No JSON found in response")
        
        return {
            "primary_terms": parsed.get("primary_terms", original_query.split()[:5]),
            "expanded_terms": parsed.get("expanded_terms", []),
            "year_from": parsed.get("year_from"),
            "year_to": parsed.get("year_to"),
            "fields": parsed.get("fields", []),
            "query_type": parsed.get("query_type", "synthesis"),
            "search_queries": parsed.get("primary_terms", [original_query]),
        }
    
    def _fallback_parse(self, query: str) -> dict:
        """
        Fallback parsing without LLM.
        
        Used when LLM API is unavailable or fails.
        """
        import re
        
        words = query.lower().split()
        stopwords = {"what", "where", "when", "which", "that", "this", "have", "been",
                     "with", "from", "they", "their", "about", "would", "could", "should",
                     "the", "and", "for", "are", "how", "does", "can", "will"}
        
        primary_terms = [w for w in words if len(w) > 3 and w not in stopwords][:5]
        
        # Year extraction
        year_from = None
        year_to = None
        
        since_match = re.search(r'(?:since|after|from)\s+(\d{4})', query.lower())
        if since_match:
            year_from = int(since_match.group(1))
        
        before_match = re.search(r'(?:before|until|to)\s+(\d{4})', query.lower())
        if before_match:
            year_to = int(before_match.group(1))
        
        # Query type detection
        query_type = "synthesis"
        if any(w in query.lower() for w in ["compare", "versus", "vs", "difference"]):
            query_type = "comparison"
        elif any(w in query.lower() for w in ["what is", "define", "explain"]):
            query_type = "factual"
        elif any(w in query.lower() for w in ["survey", "review", "overview"]):
            query_type = "survey"
        
        return {
            "primary_terms": primary_terms if primary_terms else query.split()[:3],
            "expanded_terms": [],
            "year_from": year_from,
            "year_to": year_to,
            "fields": [],
            "query_type": query_type,
            "search_queries": primary_terms if primary_terms else [query],
        }
