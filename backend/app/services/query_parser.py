"""
Intelligent Query Parser Service

Extracts scientific concepts, temporal bounds, negations, and generates
multiple search query variations for comprehensive literature retrieval.
"""

import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ParsedQuery:
    """Structured representation of a parsed research query."""
    raw_query: str
    primary_concepts: List[str] = field(default_factory=list)
    secondary_concepts: List[str] = field(default_factory=list)
    excluded_concepts: List[str] = field(default_factory=list)
    year_from: Optional[int] = None
    year_to: Optional[int] = None
    fields: List[str] = field(default_factory=list)
    search_queries: List[str] = field(default_factory=list)
    complexity: str = "simple"
    intent: str = "explore"


class QueryParser:
    """
    Intelligent query parser for scientific research questions.
    
    Features:
    - Concept extraction using scientific vocabulary
    - Temporal bound detection (since 2020, recent, 2015-2020)
    - Negation/contrast detection (instead of, not, rather than)
    - Query expansion with synonyms and related terms
    - Intent classification (explore, compare, find_specific, survey)
    """
    
    # Stopwords to filter out
    STOPWORDS = {
        "i", "im", "i'm", "me", "my", "myself", "we", "our", "ours", "ourselves",
        "you", "your", "yours", "yourself", "yourselves", "he", "him", "his",
        "himself", "she", "her", "hers", "herself", "it", "its", "itself",
        "they", "them", "their", "theirs", "themselves", "what", "which", "who",
        "whom", "this", "that", "these", "those", "am", "is", "are", "was",
        "were", "be", "been", "being", "have", "has", "had", "having", "do",
        "does", "did", "doing", "a", "an", "the", "and", "but", "if", "or",
        "because", "as", "until", "while", "of", "at", "by", "for", "with",
        "about", "against", "between", "into", "through", "during", "before",
        "after", "above", "below", "to", "from", "up", "down", "in", "out",
        "on", "off", "over", "under", "again", "further", "then", "once",
        "here", "there", "when", "where", "why", "how", "all", "each", "few",
        "more", "most", "other", "some", "such", "no", "nor", "not", "only",
        "own", "same", "so", "than", "too", "very", "can", "will", "just",
        "should", "now", "thinking", "want", "would", "could", "might",
    }
    
    # Scientific term patterns for concept extraction
    SCIENTIFIC_PATTERNS = [
        # Physics
        r"quantum\s+\w+", r"double\s+slit", r"wave[\s-]particle", 
        r"superposition", r"entanglement", r"decoherence",
        r"superconductor\w*", r"superconductivity",
        # Chemistry/Biology
        r"CRISPR", r"gene\s+therapy", r"protein\s+\w+",
        r"enzyme\w*", r"DNA", r"RNA", r"molecular\s+\w+",
        # Computing
        r"machine\s+learning", r"deep\s+learning", r"neural\s+network\w*",
        r"artificial\s+intelligence", r"natural\s+language",
        # General scientific
        r"experiment\w*", r"hypothesis", r"theory", r"phenomenon",
        r"mechanism\w*", r"effect\w*", r"synthesis",
    ]
    
    # Synonym map for query expansion
    SYNONYMS = {
        "double slit": ["two slit", "Young's experiment", "double slit interference"],
        "quantum": ["quantum mechanics", "quantum physics", "quantum theory"],
        "molecule": ["molecular", "molecules"],
        "electron": ["electrons", "electronic"],
        "experiment": ["study", "investigation", "research"],
        "CRISPR": ["CRISPR-Cas9", "gene editing", "genome editing"],
        "machine learning": ["ML", "statistical learning"],
        "deep learning": ["neural network", "neural networks", "DNN"],
        "superconductor": ["superconducting", "superconductivity"],
        "intermittent fasting": ["IF", "time-restricted eating", "fasting"],
    }
    
    # Field/discipline keywords
    FIELD_KEYWORDS = {
        "Physics": ["quantum", "particle", "wave", "energy", "relativity", "superconductor"],
        "Biology": ["gene", "protein", "cell", "organism", "evolution", "CRISPR"],
        "Chemistry": ["molecule", "reaction", "synthesis", "compound", "chemical"],
        "Computer Science": ["algorithm", "neural", "machine learning", "artificial intelligence"],
        "Medicine": ["disease", "treatment", "therapy", "clinical", "patient"],
        "Neuroscience": ["brain", "neural", "cognition", "neuron", "consciousness"],
    }
    
    def parse(self, query: str) -> Dict[str, any]:
        """
        Parse a natural language query into structured components.
        
        Returns a dictionary for backwards compatibility, but internally
        creates a ParsedQuery dataclass.
        """
        # Preprocess
        cleaned = self._preprocess(query)
        
        # Extract components
        year_from, year_to = self._extract_temporal(cleaned)
        excluded = self._extract_excluded(cleaned)
        
        # Remove temporal and exclusion patterns for concept extraction
        concept_text = self._remove_patterns(cleaned)
        
        # Extract concepts
        primary, secondary = self._extract_concepts(concept_text)
        
        # Infer fields
        fields = self._infer_fields(primary + secondary)
        
        # Detect intent and complexity
        intent = self._detect_intent(cleaned)
        complexity = self._assess_complexity(cleaned, primary)
        
        # Generate search queries
        search_queries = self._generate_search_queries(
            primary, secondary, excluded, query
        )
        
        return {
            "raw_query": query,
            "primary_terms": primary,
            "expanded_terms": secondary,
            "excluded_terms": excluded,
            "search_queries": search_queries,
            "year_from": year_from,
            "year_to": year_to,
            "fields": fields,
            "intent": intent,
            "complexity": complexity,
        }
    
    def _preprocess(self, text: str) -> str:
        """Normalize and clean input text."""
        # Normalize whitespace
        text = " ".join(text.split())
        # Fix common contractions
        text = text.replace("'m", " am").replace("'re", " are")
        text = text.replace("'s", " is").replace("'ve", " have")
        return text
    
    def _extract_temporal(self, text: str) -> Tuple[Optional[int], Optional[int]]:
        """Extract temporal bounds from query."""
        text_lower = text.lower()
        year_from, year_to = None, None
        current_year = datetime.now().year
        
        # "since YYYY"
        match = re.search(r"since\s+(\d{4})", text_lower)
        if match:
            year_from = int(match.group(1))
        
        # "after YYYY"
        match = re.search(r"after\s+(\d{4})", text_lower)
        if match:
            year_from = int(match.group(1)) + 1
        
        # "before YYYY"
        match = re.search(r"before\s+(\d{4})", text_lower)
        if match:
            year_to = int(match.group(1)) - 1
        
        # "YYYY-YYYY" or "YYYY to YYYY"
        match = re.search(r"(\d{4})\s*[-–to]+\s*(\d{4})", text_lower)
        if match:
            year_from = int(match.group(1))
            year_to = int(match.group(2))
        
        # "in the YYYYs"
        match = re.search(r"in\s+the\s+(\d{4})s", text_lower)
        if match:
            decade = int(match.group(1))
            year_from = decade
            year_to = decade + 9
        
        # "recent" / "latest" / "new"
        if re.search(r"\b(recent|latest|new|current)\b", text_lower):
            year_from = current_year - 3
        
        # "last N years"
        match = re.search(r"last\s+(\d+)\s+years?", text_lower)
        if match:
            years = int(match.group(1))
            year_from = current_year - years
        
        # "post-YYYY"
        match = re.search(r"post[- ]?(\d{4})", text_lower)
        if match:
            year_from = int(match.group(1))
        
        return year_from, year_to
    
    def _extract_excluded(self, text: str) -> List[str]:
        """Extract concepts that should be excluded from search."""
        excluded = []
        text_lower = text.lower()
        
        # "instead of X"
        match = re.search(r"instead\s+of\s+(.+?)(?:\.|,|$|\s+(?:and|but|with))", text_lower)
        if match:
            excluded.append(match.group(1).strip())
        
        # "not X"
        match = re.search(r"\bnot\s+(.+?)(?:\.|,|$|\s+(?:and|but|with))", text_lower)
        if match:
            excluded.append(match.group(1).strip())
        
        # "rather than X"
        match = re.search(r"rather\s+than\s+(.+?)(?:\.|,|$|\s+(?:and|but|with))", text_lower)
        if match:
            excluded.append(match.group(1).strip())
        
        # "excluding X"
        match = re.search(r"excluding\s+(.+?)(?:\.|,|$|\s+(?:and|but|with))", text_lower)
        if match:
            excluded.append(match.group(1).strip())
        
        return excluded
    
    def _remove_patterns(self, text: str) -> str:
        """Remove temporal and exclusion patterns for cleaner concept extraction."""
        patterns = [
            r"since\s+\d{4}",
            r"after\s+\d{4}",
            r"before\s+\d{4}",
            r"\d{4}\s*[-–to]+\s*\d{4}",
            r"in\s+the\s+\d{4}s",
            r"\b(recent|latest|new|current)\b",
            r"last\s+\d+\s+years?",
            r"post[- ]?\d{4}",
            r"instead\s+of\s+.+?(?:\.|,|$)",
            r"\bnot\s+.+?(?:\.|,|$)",
            r"rather\s+than\s+.+?(?:\.|,|$)",
        ]
        
        result = text
        for pattern in patterns:
            result = re.sub(pattern, " ", result, flags=re.IGNORECASE)
        
        return " ".join(result.split())
    
    def _extract_concepts(self, text: str) -> Tuple[List[str], List[str]]:
        """Extract primary and secondary concepts from text."""
        text_lower = text.lower()
        primary = []
        secondary = []
        
        # Extract scientific patterns first (higher priority)
        for pattern in self.SCIENTIFIC_PATTERNS:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            for match in matches:
                clean_match = match.strip()
                if clean_match and clean_match not in primary:
                    primary.append(clean_match)
        
        # Extract noun phrases (simple approach)
        # Split into tokens
        tokens = re.findall(r"[a-zA-Z][a-zA-Z0-9-]*", text)
        tokens = [t.lower() for t in tokens if t.lower() not in self.STOPWORDS]
        
        # Build bigrams and trigrams
        for i in range(len(tokens)):
            # Single important terms
            if tokens[i] not in self.STOPWORDS and len(tokens[i]) > 2:
                if tokens[i] not in primary and tokens[i] not in secondary:
                    secondary.append(tokens[i])
            
            # Bigrams
            if i + 1 < len(tokens):
                bigram = f"{tokens[i]} {tokens[i+1]}"
                if bigram not in primary and bigram not in secondary:
                    # Check if it looks scientific
                    if self._is_scientific_term(bigram):
                        if bigram not in primary:
                            primary.append(bigram)
                    else:
                        secondary.append(bigram)
            
            # Trigrams
            if i + 2 < len(tokens):
                trigram = f"{tokens[i]} {tokens[i+1]} {tokens[i+2]}"
                if self._is_scientific_term(trigram):
                    if trigram not in primary:
                        primary.append(trigram)
        
        # Limit and prioritize
        primary = self._prioritize_concepts(primary)[:5]
        secondary = [c for c in secondary if c not in primary][:5]
        
        return primary, secondary
    
    def _is_scientific_term(self, term: str) -> bool:
        """Check if a term appears to be scientific."""
        term_lower = term.lower()
        
        # Check patterns
        for pattern in self.SCIENTIFIC_PATTERNS:
            if re.search(pattern, term_lower):
                return True
        
        # Check if contains scientific keywords
        scientific_keywords = [
            "quantum", "molecular", "experiment", "theory", "hypothesis",
            "mechanism", "effect", "synthesis", "reaction", "neural",
            "genetic", "protein", "cell", "particle", "wave",
        ]
        
        for keyword in scientific_keywords:
            if keyword in term_lower:
                return True
        
        return False
    
    def _prioritize_concepts(self, concepts: List[str]) -> List[str]:
        """Prioritize concepts by likely relevance."""
        scored = []
        for concept in concepts:
            score = 0
            # Longer concepts are usually more specific
            score += len(concept.split()) * 2
            # Scientific terms get bonus
            if self._is_scientific_term(concept):
                score += 5
            scored.append((concept, score))
        
        scored.sort(key=lambda x: x[1], reverse=True)
        return [c for c, _ in scored]
    
    def _infer_fields(self, concepts: List[str]) -> List[str]:
        """Infer academic fields from concepts."""
        fields = []
        concept_text = " ".join(concepts).lower()
        
        for field_name, keywords in self.FIELD_KEYWORDS.items():
            for keyword in keywords:
                if keyword in concept_text:
                    if field_name not in fields:
                        fields.append(field_name)
                    break
        
        return fields
    
    def _detect_intent(self, text: str) -> str:
        """Detect the intent of the query."""
        text_lower = text.lower()
        
        # Comparison intent
        if any(word in text_lower for word in ["compare", "versus", "vs", "difference", "between"]):
            return "compare"
        
        # Survey/overview intent
        if any(word in text_lower for word in ["overview", "survey", "review", "state of"]):
            return "survey"
        
        # Specific finding intent
        if any(word in text_lower for word in ["find", "locate", "specific", "particular"]):
            return "find_specific"
        
        # Question intent
        if text_lower.startswith(("what", "how", "why", "when", "where", "who")):
            return "explore"
        
        return "explore"
    
    def _assess_complexity(self, text: str, concepts: List[str]) -> str:
        """Assess query complexity."""
        # Compound query (multiple distinct topics)
        if len(concepts) >= 4:
            return "compound"
        
        # Comparative query
        if any(word in text.lower() for word in ["versus", "vs", "compare", "difference"]):
            return "comparative"
        
        return "simple"
    
    def _generate_search_queries(
        self,
        primary: List[str],
        secondary: List[str],
        excluded: List[str],
        raw_query: str,
    ) -> List[str]:
        """Generate multiple search query variations."""
        queries = []
        
        # Query 1: Primary concepts combined
        if primary:
            q1 = " ".join(primary[:2])
            queries.append(q1)
        
        # Query 2: Primary + secondary
        if primary and secondary:
            q2 = f"{primary[0]} {secondary[0]}"
            if q2 not in queries:
                queries.append(q2)
        
        # Query 3: Synonym expansion
        for concept in primary[:2]:
            synonyms = self._get_synonyms(concept)
            if synonyms:
                q3 = primary[0] if primary else ""
                q3 = q3.replace(concept, synonyms[0])
                if q3 and q3 not in queries:
                    queries.append(q3)
        
        # Query 4: Broader search (main concept only)
        if primary:
            q4 = primary[0]
            if q4 not in queries:
                queries.append(q4)
        
        # Query 5: Full primary phrase if multi-word
        if primary and len(primary) > 1:
            q5 = " ".join(primary[:3])
            if q5 not in queries:
                queries.append(q5)
        
        # Fallback: use cleaned raw query
        if not queries:
            cleaned = " ".join([
                w for w in raw_query.lower().split()
                if w not in self.STOPWORDS
            ])[:100]
            queries.append(cleaned)
        
        # Remove excluded terms from queries
        if excluded:
            filtered = []
            for q in queries:
                should_include = True
                for exc in excluded:
                    if exc.lower() in q.lower():
                        should_include = False
                        break
                if should_include:
                    filtered.append(q)
            queries = filtered if filtered else queries[:1]
        
        # Dedupe and limit
        seen = set()
        unique = []
        for q in queries:
            q_normalized = " ".join(sorted(q.lower().split()))
            if q_normalized not in seen and q.strip():
                seen.add(q_normalized)
                unique.append(q)
        
        return unique[:5]
    
    def _get_synonyms(self, term: str) -> List[str]:
        """Get synonyms for a term."""
        term_lower = term.lower()
        
        # Check exact match
        if term_lower in self.SYNONYMS:
            return self.SYNONYMS[term_lower]
        
        # Check partial match
        for key, synonyms in self.SYNONYMS.items():
            if key in term_lower or term_lower in key:
                return synonyms
        
        return []
