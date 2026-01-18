"""
Paper Deduplicator

Intelligent deduplication of papers from multiple sources using
DOI matching and fuzzy title matching.
"""

import re
from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass, field
from collections import defaultdict

from rapidfuzz import fuzz

from app.services.literature.models import UnifiedPaper


@dataclass
class DeduplicationResult:
    """Result of paper deduplication."""
    papers: List[UnifiedPaper]
    original_count: int
    unique_count: int
    duplicates_removed: int
    merge_log: List[Dict] = field(default_factory=list)


class PaperDeduplicator:
    """
    Remove duplicate papers from multi-source results.
    
    Uses multi-stage matching:
    1. Exact DOI match (highest confidence)
    2. Fuzzy title match + year + first author (medium confidence)
    3. Merge records to keep most complete data
    """
    
    # Thresholds
    TITLE_MATCH_THRESHOLD = 92  # 92% similarity required
    
    def __init__(self):
        self._seen_dois: Set[str] = set()
        self._title_index: Dict[str, List[UnifiedPaper]] = defaultdict(list)
    
    def deduplicate(self, papers: List[UnifiedPaper]) -> DeduplicationResult:
        """
        Deduplicate papers, keeping the most complete record.
        
        Args:
            papers: List of papers to deduplicate
            
        Returns:
            DeduplicationResult with unique papers and statistics
        """
        if not papers:
            return DeduplicationResult(
                papers=[],
                original_count=0,
                unique_count=0,
                duplicates_removed=0,
            )
        
        original_count = len(papers)
        
        # Build indexes
        doi_index: Dict[str, List[UnifiedPaper]] = defaultdict(list)
        title_index: Dict[str, List[UnifiedPaper]] = defaultdict(list)
        
        for paper in papers:
            # Index by DOI
            if paper.doi:
                normalized_doi = self._normalize_doi(paper.doi)
                if normalized_doi:
                    doi_index[normalized_doi].append(paper)
            
            # Index by year + normalized title prefix
            if paper.year and paper.title:
                title_normalized = self._normalize_title(paper.title)
                if title_normalized:
                    key = f"{paper.year}:{title_normalized[:50]}"
                    title_index[key].append(paper)
        
        # Track processed papers
        processed_ids: Set[str] = set()
        unique_papers: List[UnifiedPaper] = []
        merge_log: List[Dict] = []
        
        for paper in papers:
            # Create a unique identifier for this paper instance
            paper_id = f"{paper.source}:{paper.external_id}"
            
            if paper_id in processed_ids:
                continue
            
            # Find potential duplicates
            duplicates = self._find_duplicates(paper, doi_index, title_index)
            
            # Filter out already processed duplicates
            duplicates = [
                d for d in duplicates
                if f"{d.source}:{d.external_id}" not in processed_ids
                and f"{d.source}:{d.external_id}" != paper_id
            ]
            
            if duplicates:
                # Merge all records
                merged = self._merge_papers([paper] + duplicates)
                unique_papers.append(merged)
                
                # Mark all as processed
                processed_ids.add(paper_id)
                for dup in duplicates:
                    dup_id = f"{dup.source}:{dup.external_id}"
                    processed_ids.add(dup_id)
                
                # Log merge
                merge_log.append({
                    "kept_source": merged.source,
                    "kept_id": merged.external_id,
                    "merged_count": len(duplicates),
                    "merged_sources": [d.source for d in duplicates],
                    "reason": "doi_match" if paper.doi else "title_match",
                })
            else:
                unique_papers.append(paper)
                processed_ids.add(paper_id)
        
        duplicates_removed = original_count - len(unique_papers)
        
        return DeduplicationResult(
            papers=unique_papers,
            original_count=original_count,
            unique_count=len(unique_papers),
            duplicates_removed=duplicates_removed,
            merge_log=merge_log,
        )
    
    def _find_duplicates(
        self,
        paper: UnifiedPaper,
        doi_index: Dict[str, List[UnifiedPaper]],
        title_index: Dict[str, List[UnifiedPaper]],
    ) -> List[UnifiedPaper]:
        """Find papers that are duplicates of the given paper."""
        duplicates: List[UnifiedPaper] = []
        paper_id = f"{paper.source}:{paper.external_id}"
        
        # Stage 1: DOI match (highest confidence)
        if paper.doi:
            normalized_doi = self._normalize_doi(paper.doi)
            if normalized_doi and normalized_doi in doi_index:
                for candidate in doi_index[normalized_doi]:
                    candidate_id = f"{candidate.source}:{candidate.external_id}"
                    if candidate_id != paper_id:
                        duplicates.append(candidate)
        
        # Stage 2: Title + year match (if no DOI matches)
        if not duplicates and paper.year and paper.title:
            title_normalized = self._normalize_title(paper.title)
            if title_normalized:
                key = f"{paper.year}:{title_normalized[:50]}"
                
                for candidate in title_index.get(key, []):
                    candidate_id = f"{candidate.source}:{candidate.external_id}"
                    if candidate_id != paper_id and candidate not in duplicates:
                        # Fuzzy match on full title
                        candidate_title = self._normalize_title(candidate.title)
                        similarity = fuzz.ratio(title_normalized, candidate_title)
                        
                        if similarity >= self.TITLE_MATCH_THRESHOLD:
                            # Additional check: first author should match
                            if self._authors_match(paper, candidate):
                                duplicates.append(candidate)
        
        return duplicates
    
    def _authors_match(self, p1: UnifiedPaper, p2: UnifiedPaper) -> bool:
        """Check if first authors are likely the same person."""
        if not p1.authors or not p2.authors:
            return True  # Can't verify, assume match
        
        name1 = p1.authors[0].name.lower()
        name2 = p2.authors[0].name.lower()
        
        # Extract last names
        last1 = self._get_last_name(name1)
        last2 = self._get_last_name(name2)
        
        if not last1 or not last2:
            return True  # Can't extract, assume match
        
        # Exact last name match or high similarity
        if last1 == last2:
            return True
        
        return fuzz.ratio(last1, last2) >= 85
    
    def _get_last_name(self, name: str) -> str:
        """Extract last name from full name."""
        if not name:
            return ""
        
        # Handle "Last, First" format
        if "," in name:
            return name.split(",")[0].strip()
        
        # Handle "First Last" format
        parts = name.split()
        if parts:
            return parts[-1].strip()
        
        return name.strip()
    
    def _merge_papers(self, papers: List[UnifiedPaper]) -> UnifiedPaper:
        """
        Merge multiple duplicate papers into single best record.
        
        Scoring factors:
        - Has DOI (+10)
        - Abstract length
        - Author count
        - Citation count
        - Has PDF URL (+1)
        """
        if len(papers) == 1:
            return papers[0]
        
        # Score each paper
        scored = []
        for p in papers:
            score = 0
            score += 10 if p.doi else 0
            score += min(len(p.abstract or "") / 100, 5)
            score += min(len(p.authors), 3)
            score += min(p.citation_count / 100, 2)
            score += 1 if p.pdf_url else 0
            scored.append((score, p))
        
        # Sort by score descending
        scored.sort(key=lambda x: x[0], reverse=True)
        
        # Start with best record
        best = scored[0][1]
        
        # Enhance with data from other records
        for _, other in scored[1:]:
            # Fill in missing DOI
            if not best.doi and other.doi:
                best = best.model_copy(update={"doi": other.doi})
            
            # Fill in missing PDF URL
            if not best.pdf_url and other.pdf_url:
                best = best.model_copy(update={"pdf_url": other.pdf_url})
            
            # Use longer abstract
            if (other.abstract and 
                (not best.abstract or len(other.abstract) > len(best.abstract))):
                best = best.model_copy(update={"abstract": other.abstract})
            
            # Merge topics (unique)
            if other.topics:
                existing = set(best.topics)
                new_topics = [t for t in other.topics if t not in existing]
                if new_topics:
                    best = best.model_copy(update={
                        "topics": best.topics + new_topics
                    })
            
            # Merge fields of study (unique)
            if other.fields_of_study:
                existing = set(best.fields_of_study)
                new_fields = [f for f in other.fields_of_study if f not in existing]
                if new_fields:
                    best = best.model_copy(update={
                        "fields_of_study": best.fields_of_study + new_fields
                    })
            
            # Use higher citation count
            if other.citation_count > best.citation_count:
                best = best.model_copy(update={
                    "citation_count": other.citation_count
                })
        
        return best
    
    def _normalize_doi(self, doi: str) -> Optional[str]:
        """Normalize DOI for comparison."""
        if not doi:
            return None
        
        doi = doi.lower().strip()
        
        # Remove prefixes
        prefixes = [
            "https://doi.org/",
            "http://doi.org/",
            "doi:",
        ]
        for prefix in prefixes:
            if doi.startswith(prefix):
                doi = doi[len(prefix):]
        
        return doi if doi else None
    
    def _normalize_title(self, title: str) -> str:
        """
        Normalize title for fuzzy matching.
        
        - Lowercase
        - Remove punctuation
        - Normalize whitespace
        """
        if not title:
            return ""
        
        # Lowercase
        title = title.lower()
        
        # Remove punctuation
        title = re.sub(r"[^\w\s]", " ", title)
        
        # Normalize whitespace
        title = " ".join(title.split())
        
        return title
