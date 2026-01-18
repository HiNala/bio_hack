"""
Intelligent Text Chunker

Sentence-aware text chunking with recursive splitting, overlap handling,
and quality validation. Optimized for RAG retrieval of scientific literature.
"""

import re
from typing import Optional, List, Tuple
from dataclasses import dataclass, field
from functools import lru_cache

import tiktoken

from app.config import get_settings

settings = get_settings()


@dataclass
class ChunkResult:
    """Result of chunking a piece of text."""
    text: str
    chunk_index: int
    token_count: int
    char_count: int
    section: Optional[str] = None
    has_overlap: bool = False
    metadata: dict = field(default_factory=dict)


@dataclass
class ChunkValidation:
    """Validation result for a chunk."""
    is_valid: bool
    issues: List[str] = field(default_factory=list)


class TextChunker:
    """
    Intelligent text chunker for scientific literature.
    
    Features:
    - Token-based size limits using tiktoken
    - Sentence-aware splitting with abbreviation handling
    - Recursive splitting (paragraphs → sentences → words)
    - Overlap handling for context preservation
    - Section detection for abstracts vs body text
    - Quality validation for chunks
    
    Parameters are configurable via app settings.
    """
    
    # Common abbreviations to NOT split on
    ABBREVIATIONS = {
        "Dr", "Mr", "Mrs", "Ms", "Prof", "Jr", "Sr",
        "Fig", "Figs", "Eq", "Eqs", "Ref", "Refs",
        "et al", "i.e", "e.g", "vs", "cf", "etc",
        "approx", "ca", "no", "vol", "pp",
    }
    
    # Sentence ending patterns
    SENTENCE_ENDINGS = re.compile(
        r'(?<=[.!?])'        # After sentence-ending punctuation
        r'(?:\s*["\'])?'      # Optional closing quote
        r'\s+'                # Whitespace
        r'(?=[A-Z0-9\[\("])'  # Before capital letter, number, or opening bracket
    )
    
    # Paragraph separators
    PARAGRAPH_SEP = re.compile(r'\n\s*\n')
    
    # Section headers (common in academic abstracts)
    SECTION_PATTERNS = {
        'background': re.compile(r'^(?:background|introduction|context)[:.]?\s*', re.I),
        'methods': re.compile(r'^(?:methods?|methodology|approach|materials)[:.]?\s*', re.I),
        'results': re.compile(r'^(?:results?|findings|observations)[:.]?\s*', re.I),
        'conclusion': re.compile(r'^(?:conclusions?|summary|discussion)[:.]?\s*', re.I),
        'objective': re.compile(r'^(?:objectives?|aims?|purpose|goals?)[:.]?\s*', re.I),
    }
    
    # Quality thresholds
    MIN_TOKENS = 20
    MAX_TOKENS = 600
    MIN_UNIQUE_WORDS_RATIO = 0.3
    
    def __init__(
        self,
        target_tokens: int = None,
        overlap_tokens: int = None,
        min_chunk_tokens: int = 50,
    ):
        """
        Initialize the chunker.
        
        Args:
            target_tokens: Target chunk size in tokens (default from settings)
            overlap_tokens: Overlap between chunks in tokens (default from settings)
            min_chunk_tokens: Minimum chunk size to keep (avoid tiny chunks)
        """
        self.target_tokens = target_tokens or settings.chunk_size
        self.overlap_tokens = overlap_tokens or settings.chunk_overlap
        self.min_chunk_tokens = min_chunk_tokens
        
        # Initialize tiktoken encoder for token counting
        self._encoder = self._get_encoder()
        
        # Build abbreviation pattern
        self._abbrev_pattern = self._build_abbrev_pattern()
    
    @staticmethod
    @lru_cache(maxsize=1)
    def _get_encoder():
        """Get cached tiktoken encoder."""
        return tiktoken.get_encoding("cl100k_base")
    
    def _build_abbrev_pattern(self) -> re.Pattern:
        """Build regex pattern for detecting abbreviations."""
        escaped = [re.escape(abbr) for abbr in self.ABBREVIATIONS]
        pattern = r'\b(' + '|'.join(escaped) + r')\.\s*$'
        return re.compile(pattern, re.IGNORECASE)
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text using tiktoken."""
        if not text:
            return 0
        return len(self._encoder.encode(text))
    
    def chunk_text(
        self,
        text: str,
        section: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> List[ChunkResult]:
        """
        Chunk text into appropriately sized pieces.
        
        Uses recursive splitting strategy:
        1. If text fits in target size, return as single chunk
        2. Split by paragraphs first
        3. If paragraph too large, split by sentences
        4. If sentence too large, split by clauses/words
        5. Merge small chunks to reach target size
        6. Add overlap from previous chunk
        
        Args:
            text: Text to chunk
            section: Optional section label (e.g., 'abstract')
            metadata: Optional metadata to include with chunks
            
        Returns:
            List of ChunkResult objects
        """
        if not text or not text.strip():
            return []
        
        # Clean the text
        text = self._clean_text(text)
        
        # Count tokens
        token_count = self.count_tokens(text)
        
        # If text fits in target, return as single chunk
        if token_count <= self.target_tokens:
            return [ChunkResult(
                text=text,
                chunk_index=0,
                token_count=token_count,
                char_count=len(text),
                section=section or self._detect_section(text),
                has_overlap=False,
                metadata=metadata or {},
            )]
        
        # Recursive splitting
        raw_chunks = self._split_recursive(text)
        
        # Merge small chunks
        merged_chunks = self._merge_small_chunks(raw_chunks)
        
        # Add overlap
        final_chunks = self._add_overlap(merged_chunks)
        
        # Build results
        results = []
        for i, (chunk_text, has_overlap) in enumerate(final_chunks):
            detected_section = section or self._detect_section(chunk_text)
            chunk_metadata = metadata.copy() if metadata else {}
            chunk_metadata["chunk_position"] = f"{i+1}/{len(final_chunks)}"
            
            results.append(ChunkResult(
                text=chunk_text,
                chunk_index=i,
                token_count=self.count_tokens(chunk_text),
                char_count=len(chunk_text),
                section=detected_section,
                has_overlap=has_overlap,
                metadata=chunk_metadata,
            ))
        
        return results
    
    def chunk_paper(
        self,
        title: str,
        abstract: Optional[str],
        full_text: Optional[str] = None,
    ) -> List[ChunkResult]:
        """
        Chunk a complete paper (title + abstract + optional full text).
        
        Args:
            title: Paper title
            abstract: Paper abstract
            full_text: Optional full text (not yet implemented)
            
        Returns:
            List of ChunkResult objects
        """
        all_chunks = []
        chunk_offset = 0
        
        if abstract:
            # Prepend title to first chunk for context
            abstract_with_context = f"Title: {title}\n\nAbstract: {abstract}"
            abstract_chunks = self.chunk_text(
                abstract_with_context,
                section="abstract",
                metadata={"title": title},
            )
            
            for chunk in abstract_chunks:
                chunk.chunk_index = chunk_offset
                chunk_offset += 1
                all_chunks.append(chunk)
        
        return all_chunks
    
    def validate_chunk(self, chunk: ChunkResult) -> ChunkValidation:
        """
        Validate chunk quality.
        
        Checks:
        - Token count within bounds
        - Not too repetitive
        - Not garbage content
        """
        issues = []
        
        # Check length
        if chunk.token_count < self.MIN_TOKENS:
            issues.append(f"Too short: {chunk.token_count} tokens (min: {self.MIN_TOKENS})")
        
        if chunk.token_count > self.MAX_TOKENS:
            issues.append(f"Too long: {chunk.token_count} tokens (max: {self.MAX_TOKENS})")
        
        # Check for repetitive content
        words = chunk.text.lower().split()
        if words:
            unique_ratio = len(set(words)) / len(words)
            if unique_ratio < self.MIN_UNIQUE_WORDS_RATIO:
                issues.append(f"Too repetitive: {unique_ratio:.1%} unique words")
        
        # Check for garbage content
        if self._is_garbage(chunk.text):
            issues.append("Contains garbage/non-text content")
        
        return ChunkValidation(
            is_valid=len(issues) == 0,
            issues=issues,
        )
    
    def _is_garbage(self, text: str) -> bool:
        """Check if text appears to be garbage."""
        if not text:
            return True
        
        # Too many numbers (more than 50% digits)
        digits = sum(c.isdigit() for c in text)
        if digits / len(text) > 0.5:
            return True
        
        # Too many special characters
        special = sum(not c.isalnum() and not c.isspace() for c in text)
        if special / len(text) > 0.3:
            return True
        
        # Repeated patterns
        if re.search(r'(.{10,})\1{2,}', text):
            return True
        
        return False
    
    def _clean_text(self, text: str) -> str:
        """Clean text for chunking."""
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove control characters
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
        # Strip
        text = text.strip()
        return text
    
    def _split_recursive(self, text: str) -> List[str]:
        """
        Recursively split text into chunks.
        
        Strategy:
        1. Try splitting by paragraphs
        2. If any paragraph too large, split by sentences
        3. If any sentence too large, split by clauses/words
        """
        chunks = []
        
        # First, try splitting by paragraphs
        paragraphs = self.PARAGRAPH_SEP.split(text)
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            para_tokens = self.count_tokens(para)
            
            if para_tokens <= self.target_tokens:
                chunks.append(para)
            else:
                # Paragraph too large, split by sentences
                sentence_chunks = self._split_by_sentences(para)
                chunks.extend(sentence_chunks)
        
        return chunks
    
    def _split_by_sentences(self, text: str) -> List[str]:
        """
        Split text by sentences, handling abbreviations and edge cases.
        """
        # First, protect abbreviations
        protected_text = self._protect_abbreviations(text)
        
        # Split by sentence endings
        sentences = self.SENTENCE_ENDINGS.split(protected_text)
        
        chunks = []
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            # Restore abbreviations
            sentence = self._restore_abbreviations(sentence)
            
            sent_tokens = self.count_tokens(sentence)
            
            if sent_tokens <= self.target_tokens:
                chunks.append(sentence)
            else:
                # Sentence too large, split by clauses or words
                clause_chunks = self._split_long_sentence(sentence)
                chunks.extend(clause_chunks)
        
        return chunks
    
    def _protect_abbreviations(self, text: str) -> str:
        """Replace periods after abbreviations with placeholder."""
        for abbr in self.ABBREVIATIONS:
            pattern = rf'\b{re.escape(abbr)}\.'
            replacement = f'{abbr}[[PERIOD]]'
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        return text
    
    def _restore_abbreviations(self, text: str) -> str:
        """Restore periods after abbreviations."""
        return text.replace('[[PERIOD]]', '.')
    
    def _split_long_sentence(self, sentence: str) -> List[str]:
        """
        Split an overly long sentence into smaller pieces.
        Try clause boundaries first, then word boundaries.
        """
        # Try splitting on semicolons and colons
        parts = re.split(r'[;:]', sentence)
        if len(parts) > 1:
            result = []
            for part in parts:
                part = part.strip()
                if not part:
                    continue
                if self.count_tokens(part) <= self.target_tokens:
                    result.append(part)
                else:
                    result.extend(self._split_by_commas(part))
            return result
        
        return self._split_by_commas(sentence)
    
    def _split_by_commas(self, text: str) -> List[str]:
        """Split by commas (clause boundaries)."""
        parts = text.split(',')
        
        if len(parts) <= 2:
            return self._split_by_words(text)
        
        result = []
        current = []
        current_tokens = 0
        
        for part in parts:
            part = part.strip()
            if not part:
                continue
            
            part_tokens = self.count_tokens(part)
            
            if current_tokens + part_tokens <= self.target_tokens:
                current.append(part)
                current_tokens += part_tokens + 1  # +1 for comma
            else:
                if current:
                    result.append(', '.join(current))
                current = [part]
                current_tokens = part_tokens
        
        if current:
            result.append(', '.join(current))
        
        # If still too large, split by words
        final_result = []
        for chunk in result:
            if self.count_tokens(chunk) > self.target_tokens:
                final_result.extend(self._split_by_words(chunk))
            else:
                final_result.append(chunk)
        
        return final_result
    
    def _split_by_words(self, text: str) -> List[str]:
        """Split text by words when sentences are too long."""
        chunks = []
        words = text.split()
        current_chunk = []
        current_tokens = 0
        
        for word in words:
            word_tokens = self.count_tokens(word + ' ')
            
            if current_tokens + word_tokens > self.target_tokens:
                if current_chunk:
                    chunks.append(' '.join(current_chunk))
                current_chunk = [word]
                current_tokens = word_tokens
            else:
                current_chunk.append(word)
                current_tokens += word_tokens
        
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks
    
    def _merge_small_chunks(self, chunks: List[str]) -> List[str]:
        """Merge chunks that are too small."""
        if not chunks:
            return []
        
        merged = []
        current = chunks[0]
        current_tokens = self.count_tokens(current)
        
        for chunk in chunks[1:]:
            chunk_tokens = self.count_tokens(chunk)
            combined_tokens = self.count_tokens(current + ' ' + chunk)
            
            # Merge if combined size is under target and current is small
            if combined_tokens <= self.target_tokens:
                current = current + ' ' + chunk
                current_tokens = combined_tokens
            else:
                # Only keep current if it's big enough
                if current_tokens >= self.min_chunk_tokens:
                    merged.append(current)
                elif merged:
                    # Try to append to previous chunk
                    prev = merged[-1]
                    prev_combined = self.count_tokens(prev + ' ' + current)
                    if prev_combined <= self.target_tokens * 1.2:
                        merged[-1] = prev + ' ' + current
                    else:
                        merged.append(current)
                else:
                    merged.append(current)
                
                current = chunk
                current_tokens = chunk_tokens
        
        # Don't forget the last chunk
        if current_tokens >= self.min_chunk_tokens:
            merged.append(current)
        elif merged:
            prev = merged[-1]
            prev_combined = self.count_tokens(prev + ' ' + current)
            if prev_combined <= self.target_tokens * 1.2:
                merged[-1] = prev + ' ' + current
            else:
                merged.append(current)
        else:
            merged.append(current)
        
        return merged
    
    def _add_overlap(self, chunks: List[str]) -> List[Tuple[str, bool]]:
        """
        Add overlap from previous chunk to each chunk.
        
        Returns list of (chunk_text, has_overlap) tuples.
        """
        if not chunks:
            return []
        
        if len(chunks) == 1:
            return [(chunks[0], False)]
        
        result = [(chunks[0], False)]  # First chunk has no overlap
        
        for i in range(1, len(chunks)):
            prev_chunk = chunks[i - 1]
            current_chunk = chunks[i]
            
            # Get overlap text from end of previous chunk
            overlap_text = self._get_overlap_text(prev_chunk)
            
            if overlap_text:
                combined = overlap_text + ' ' + current_chunk
                result.append((combined, True))
            else:
                result.append((current_chunk, False))
        
        return result
    
    def _get_overlap_text(self, text: str) -> str:
        """Extract overlap text from end of a chunk."""
        if not text:
            return ''
        
        words = text.split()
        overlap_words = []
        token_count = 0
        
        for word in reversed(words):
            word_tokens = self.count_tokens(word + ' ')
            if token_count + word_tokens > self.overlap_tokens:
                break
            overlap_words.insert(0, word)
            token_count += word_tokens
        
        return ' '.join(overlap_words)
    
    def _detect_section(self, text: str) -> Optional[str]:
        """Detect section type from text content."""
        start = text[:100].lower()
        
        for section_name, pattern in self.SECTION_PATTERNS.items():
            if pattern.search(start):
                return section_name
        
        if 'abstract' in start or 'title:' in start:
            return 'abstract'
        
        return None
