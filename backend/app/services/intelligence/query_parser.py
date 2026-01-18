"""
Query Parser

Uses Claude to parse natural language queries into structured search parameters.
"""

import json
from typing import Optional

from anthropic import AsyncAnthropic

from app.config import get_settings
from app.schemas import ParsedQuery

settings = get_settings()


class QueryParser:
    """
    LLM-powered query parser using Claude.
    
    Converts natural language research questions into structured
    queries for literature APIs and semantic search.
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
        },
        {
            "query": "What is the current consensus on dark matter candidates?",
            "response": {
                "primary_terms": ["dark matter", "dark matter candidates", "WIMPs"],
                "expanded_terms": ["axions", "primordial black holes", "sterile neutrinos", "cold dark matter"],
                "year_from": None,
                "year_to": None,
                "fields": ["Astrophysics", "Particle Physics", "Cosmology"],
                "query_type": "synthesis"
            }
        }
    ]
    
    def __init__(self):
        """Initialize query parser."""
        self.client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        self.model = settings.synthesis_model
    
    async def parse(self, query: str) -> ParsedQuery:
        """
        Parse a natural language query into structured format.
        
        Args:
            query: Natural language research question
            
        Returns:
            ParsedQuery with extracted information
        """
        # Build messages with few-shot examples
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
        
        # Add the actual query
        messages.append({
            "role": "user",
            "content": f"Parse this research query: {query}"
        })
        
        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=500,
                system=self.SYSTEM_PROMPT,
                messages=messages,
            )
            
            # Extract JSON from response
            content = response.content[0].text.strip()
            
            # Try to parse JSON
            parsed = json.loads(content)
            
            return ParsedQuery(
                primary_terms=parsed.get("primary_terms", query.split()[:5]),
                expanded_terms=parsed.get("expanded_terms", []),
                year_from=parsed.get("year_from"),
                year_to=parsed.get("year_to"),
                fields=parsed.get("fields", []),
                query_type=parsed.get("query_type", "synthesis"),
            )
            
        except Exception as e:
            # Fallback to basic parsing
            print(f"LLM parsing failed: {e}, using fallback")
            return self._fallback_parse(query)
    
    def _fallback_parse(self, query: str) -> ParsedQuery:
        """
        Fallback parsing without LLM.
        
        Used when Claude API is unavailable or fails.
        """
        import re
        
        words = query.lower().split()
        stopwords = {"what", "where", "when", "which", "that", "this", "have", "been",
                     "with", "from", "they", "their", "about", "would", "could", "should"}
        
        primary_terms = [w for w in words if len(w) > 4 and w not in stopwords][:5]
        
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
        
        return ParsedQuery(
            primary_terms=primary_terms if primary_terms else query.split()[:3],
            expanded_terms=[],
            year_from=year_from,
            year_to=year_to,
            fields=[],
            query_type=query_type,
        )
