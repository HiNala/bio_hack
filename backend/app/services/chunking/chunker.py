"""
Text Chunker

Intelligent text chunking with recursive splitting and overlap handling.
Optimized for RAG retrieval of scientific literature.
"""

import re
from typing import Optional
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


class TextChunker:
    """
    Intelligent text chunker for scientific literature.
    
    Features:
    - Token-based size limits using tiktoken
    - Recursive splitting (paragraphs → sentences → words)
    - Overlap handling for context preservation
    - Section detection for abstracts vs body text
    
    Parameters are configurable via app settings.
    """
    
    # Sentence ending patterns
    SENTENCE_ENDINGS = re.compile(r'(?<=[.!?])\s+(?=[A-Z])')
    
    # Paragraph separators
    PARAGRAPH_SEP = re.compile(r'\n\s*\n')
    
    # Section headers (common in academic abstracts)
    SECTION_PATTERNS = {
        'background': re.compile(r'^(?:background|introduction|context)[:.]?\s*', re.I),
        'methods': re.compile(r'^(?:methods?|methodology|approach)[:.]?\s*', re.I),
        'results': re.compile(r'^(?:results?|findings)[:.]?\s*', re.I),
        'conclusion': re.compile(r'^(?:conclusions?|summary|discussion)[:.]?\s*', re.I),
        'objective': re.compile(r'^(?:objectives?|aims?|purpose)[:.]?\s*', re.I),
    }
    
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
        # Use cl100k_base which is used by text-embedding-3-small
        self._encoder = self._get_encoder()
    
    @staticmethod
    @lru_cache(maxsize=1)
    def _get_encoder():
        """Get cached tiktoken encoder."""
        return tiktoken.get_encoding("cl100k_base")
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text using tiktoken."""
        if not text:
            return 0
        return len(self._encoder.encode(text))
    
    def chunk_text(
        self,
        text: str,
        section: Optional[str] = None,
    ) -> list[ChunkResult]:
        """
        Chunk text into appropriately sized pieces.
        
        Uses recursive splitting strategy:
        1. If text fits in target size, return as single chunk
        2. Split by paragraphs first
        3. If paragraph too large, split by sentences
        4. If sentence too large, split by words
        5. Merge small chunks to reach target size
        6. Add overlap from previous chunk
        
        Args:
            text: Text to chunk
            section: Optional section label (e.g., 'abstract')
            
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
            results.append(ChunkResult(
                text=chunk_text,
                chunk_index=i,
                token_count=self.count_tokens(chunk_text),
                char_count=len(chunk_text),
                section=detected_section,
                has_overlap=has_overlap,
            ))
        
        return results
    
    def chunk_paper(
        self,
        title: str,
        abstract: Optional[str],
        full_text: Optional[str] = None,
    ) -> list[ChunkResult]:
        """
        Chunk a complete paper (title + abstract + optional full text).
        
        For now, we focus on abstracts since that's what we have from APIs.
        Full text support can be added later.
        
        Args:
            title: Paper title
            abstract: Paper abstract
            full_text: Optional full text (not yet implemented)
            
        Returns:
            List of ChunkResult objects
        """
        all_chunks = []
        chunk_offset = 0
        
        # Chunk abstract with title context
        if abstract:
            # Prepend title to first chunk for context
            abstract_with_context = f"Title: {title}\n\nAbstract: {abstract}"
            abstract_chunks = self.chunk_text(abstract_with_context, section="abstract")
            
            # Update indices
            for chunk in abstract_chunks:
                chunk.chunk_index = chunk_offset
                chunk_offset += 1
                all_chunks.append(chunk)
        
        # Future: chunk full text sections
        # if full_text:
        #     body_chunks = self.chunk_text(full_text, section="body")
        #     for chunk in body_chunks:
        #         chunk.chunk_index = chunk_offset
        #         chunk_offset += 1
        #         all_chunks.append(chunk)
        
        return all_chunks
    
    def _clean_text(self, text: str) -> str:
        """Clean text for chunking."""
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove control characters
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
        # Strip
        text = text.strip()
        return text
    
    def _split_recursive(self, text: str) -> list[str]:
        """
        Recursively split text into chunks.
        
        Strategy:
        1. Try splitting by paragraphs
        2. If any paragraph too large, split by sentences
        3. If any sentence too large, split by words
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
    
    def _split_by_sentences(self, text: str) -> list[str]:
        """Split text by sentences, handling oversized sentences."""
        chunks = []
        
        # Split by sentence endings
        sentences = self.SENTENCE_ENDINGS.split(text)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            sent_tokens = self.count_tokens(sentence)
            
            if sent_tokens <= self.target_tokens:
                chunks.append(sentence)
            else:
                # Sentence too large, split by words
                word_chunks = self._split_by_words(sentence)
                chunks.extend(word_chunks)
        
        return chunks
    
    def _split_by_words(self, text: str) -> list[str]:
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
    
    def _merge_small_chunks(self, chunks: list[str]) -> list[str]:
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
                    if prev_combined <= self.target_tokens * 1.2:  # Allow slight overflow
                        merged[-1] = prev + ' ' + current
                    else:
                        merged.append(current)  # Keep small chunk anyway
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
    
    def _add_overlap(self, chunks: list[str]) -> list[tuple[str, bool]]:
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
                # Prepend overlap to current chunk
                combined = overlap_text + ' ' + current_chunk
                result.append((combined, True))
            else:
                result.append((current_chunk, False))
        
        return result
    
    def _get_overlap_text(self, text: str) -> str:
        """Extract overlap text from end of a chunk."""
        if not text:
            return ''
        
        # Get last N tokens worth of text
        words = text.split()
        overlap_words = []
        token_count = 0
        
        # Work backwards through words
        for word in reversed(words):
            word_tokens = self.count_tokens(word + ' ')
            if token_count + word_tokens > self.overlap_tokens:
                break
            overlap_words.insert(0, word)
            token_count += word_tokens
        
        return ' '.join(overlap_words)
    
    def _detect_section(self, text: str) -> Optional[str]:
        """Detect section type from text content."""
        # Check first 100 chars for section headers
        start = text[:100].lower()
        
        for section_name, pattern in self.SECTION_PATTERNS.items():
            if pattern.search(start):
                return section_name
        
        # Default based on content keywords
        if 'abstract' in start or 'title:' in start:
            return 'abstract'
        
        return None
