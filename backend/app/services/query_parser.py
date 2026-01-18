"""
Query Parser Service

Extracts key terms from natural language input.
"""

import re
from typing import List, Dict


class QueryParser:
    """Simple keyword and phrase extractor for research queries."""

    _stopwords = {
        "i", "im", "i'm", "thinking", "about", "doing", "the", "a", "an", "with",
        "instead", "of", "and", "or", "to", "for", "in", "on", "at", "by", "from",
        "my", "our", "we", "us", "you", "your", "is", "are", "was", "were",
        "be", "been", "being", "this", "that", "these", "those", "it",
    }

    def parse(self, query: str) -> Dict[str, List[str]]:
        text = query.lower().strip()

        # Extract excluded terms after "instead of"
        excluded_terms = []
        match = re.search(r"instead of ([a-z0-9\\s-]+)", text)
        if match:
            excluded_terms = [match.group(1).strip()]

        # Tokenize
        tokens = re.findall(r"[a-z0-9]+", text)
        tokens = [t for t in tokens if t not in self._stopwords]

        # Build simple phrases (bigrams/trigrams)
        phrases = []
        for i in range(len(tokens)):
            if i + 1 < len(tokens):
                phrases.append(f"{tokens[i]} {tokens[i+1]}")
            if i + 2 < len(tokens):
                phrases.append(f"{tokens[i]} {tokens[i+1]} {tokens[i+2]}")

        # Prioritize longer phrases, de-duplicate
        unique_phrases = []
        for phrase in sorted(set(phrases), key=len, reverse=True):
            if phrase not in unique_phrases:
                unique_phrases.append(phrase)

        primary_terms = unique_phrases[:3] if unique_phrases else tokens[:3]
        expanded_terms = unique_phrases[3:6] if len(unique_phrases) > 3 else tokens[3:6]

        # Build search queries
        search_queries = []
        if primary_terms:
            search_queries.append(" ".join(primary_terms[:2]))
        if expanded_terms:
            search_queries.append(" ".join(expanded_terms[:2]))
        if tokens:
            search_queries.append(" ".join(tokens[:4]))

        return {
            "primary_terms": primary_terms,
            "expanded_terms": expanded_terms,
            "excluded_terms": excluded_terms,
            "search_queries": list(dict.fromkeys([q for q in search_queries if q])),
        }
