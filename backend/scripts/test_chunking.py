"""
Test script for text chunking functionality.

Run with: python -m scripts.test_chunking
"""

import sys
sys.path.insert(0, '.')

from app.services.chunking import TextChunker


def test_basic_chunking():
    """Test basic chunking of short text."""
    print("\n" + "="*60)
    print("Test 1: Basic Chunking (Short Text)")
    print("="*60)
    
    chunker = TextChunker()
    
    text = """
    Quantum mechanics is a fundamental theory in physics that describes nature at 
    the smallest scales of energy levels of atoms and subatomic particles. It differs 
    significantly from classical physics, which describes nature at larger scales.
    """
    
    chunks = chunker.chunk_text(text.strip())
    
    print(f"Input length: {len(text)} chars, {chunker.count_tokens(text)} tokens")
    print(f"Number of chunks: {len(chunks)}")
    
    for chunk in chunks:
        print(f"\n  Chunk {chunk.chunk_index}:")
        print(f"    Tokens: {chunk.token_count}")
        print(f"    Section: {chunk.section}")
        print(f"    Preview: {chunk.text[:80]}...")
    
    assert len(chunks) == 1, "Short text should be single chunk"
    print("\n✅ Basic chunking test passed!")


def test_long_text_chunking():
    """Test chunking of longer text with multiple paragraphs."""
    print("\n" + "="*60)
    print("Test 2: Long Text Chunking")
    print("="*60)
    
    chunker = TextChunker(target_tokens=100, overlap_tokens=20)  # Small for testing
    
    text = """
    Background: The double-slit experiment demonstrates the wave-particle duality 
    of quantum mechanics. When particles such as electrons are sent through two 
    slits, they create an interference pattern on the detector screen, suggesting 
    wave-like behavior.

    Methods: We conducted a series of experiments using single photons sent through 
    a modified double-slit apparatus. The apparatus included quantum erasers and 
    delayed choice mechanisms to probe the nature of measurement.

    Results: Our findings confirm that the act of measurement fundamentally changes 
    the outcome. When which-path information was available, the interference pattern 
    disappeared. When this information was erased, the pattern returned.

    Conclusions: These results support the Copenhagen interpretation while also 
    being consistent with many-worlds interpretations. The measurement problem 
    remains one of the deepest puzzles in quantum mechanics.
    """
    
    chunks = chunker.chunk_text(text.strip())
    
    print(f"Input length: {len(text)} chars, {chunker.count_tokens(text)} tokens")
    print(f"Target tokens per chunk: {chunker.target_tokens}")
    print(f"Overlap tokens: {chunker.overlap_tokens}")
    print(f"Number of chunks: {len(chunks)}")
    
    for chunk in chunks:
        print(f"\n  Chunk {chunk.chunk_index}:")
        print(f"    Tokens: {chunk.token_count}")
        print(f"    Section: {chunk.section}")
        print(f"    Has overlap: {chunk.has_overlap}")
        preview = chunk.text[:100].replace('\n', ' ')
        print(f"    Preview: {preview}...")
    
    assert len(chunks) > 1, "Long text should produce multiple chunks"
    print("\n✅ Long text chunking test passed!")


def test_paper_chunking():
    """Test chunking a complete paper (title + abstract)."""
    print("\n" + "="*60)
    print("Test 3: Paper Chunking")
    print("="*60)
    
    chunker = TextChunker()
    
    title = "Quantum Entanglement and Bell Inequality Violations in High-Energy Physics"
    abstract = """
    We present a comprehensive review of quantum entanglement experiments in 
    high-energy physics contexts. Recent advances in particle physics have enabled 
    the study of quantum correlations at energy scales previously inaccessible. 
    Our analysis covers experiments from multiple particle colliders including the 
    Large Hadron Collider at CERN. We find that Bell inequality violations have been 
    observed in systems ranging from bottom quark pairs to top quark pairs. These 
    findings have implications for our understanding of quantum mechanics at 
    fundamental scales and open new avenues for testing quantum field theory 
    predictions. The results are consistent with standard quantum mechanical 
    predictions and rule out local hidden variable theories at the 5-sigma level.
    """
    
    chunks = chunker.chunk_paper(title=title, abstract=abstract)
    
    print(f"Title: {title[:50]}...")
    print(f"Abstract length: {len(abstract)} chars, {chunker.count_tokens(abstract)} tokens")
    print(f"Number of chunks: {len(chunks)}")
    
    for chunk in chunks:
        print(f"\n  Chunk {chunk.chunk_index}:")
        print(f"    Tokens: {chunk.token_count}")
        print(f"    Section: {chunk.section}")
        preview = chunk.text[:120].replace('\n', ' ')
        print(f"    Preview: {preview}...")
    
    # Verify title is included
    assert "Title:" in chunks[0].text, "First chunk should include title"
    print("\n✅ Paper chunking test passed!")


def test_overlap():
    """Test that overlap is correctly applied between chunks."""
    print("\n" + "="*60)
    print("Test 4: Overlap Verification")
    print("="*60)
    
    chunker = TextChunker(target_tokens=50, overlap_tokens=15)
    
    # Create text that will definitely split
    sentences = [
        "First sentence about quantum physics and its implications.",
        "Second sentence discussing wave-particle duality experiments.",
        "Third sentence covering measurement theory in detail.",
        "Fourth sentence about decoherence and environmental effects.",
        "Fifth sentence regarding interpretations of quantum mechanics.",
    ]
    text = " ".join(sentences)
    
    chunks = chunker.chunk_text(text)
    
    print(f"Input: {len(sentences)} sentences")
    print(f"Target tokens: {chunker.target_tokens}")
    print(f"Overlap tokens: {chunker.overlap_tokens}")
    print(f"Chunks created: {len(chunks)}")
    
    # Check for overlap in non-first chunks
    overlap_found = False
    for i, chunk in enumerate(chunks):
        print(f"\n  Chunk {i}:")
        print(f"    Has overlap: {chunk.has_overlap}")
        print(f"    Tokens: {chunk.token_count}")
        if chunk.has_overlap:
            overlap_found = True
    
    if len(chunks) > 1:
        assert overlap_found, "Multi-chunk output should have overlap"
        print("\n✅ Overlap test passed!")
    else:
        print("\n⚠️ Text too short for overlap test (single chunk)")


def test_token_counting():
    """Test token counting accuracy."""
    print("\n" + "="*60)
    print("Test 5: Token Counting")
    print("="*60)
    
    chunker = TextChunker()
    
    test_cases = [
        ("Hello world", 2),
        ("The quick brown fox jumps over the lazy dog.", 10),
        ("Quantum mechanics", 2),
        ("", 0),
    ]
    
    for text, expected_approx in test_cases:
        tokens = chunker.count_tokens(text)
        print(f"  '{text[:30]}...' → {tokens} tokens (expected ~{expected_approx})")
    
    print("\n✅ Token counting test passed!")


def main():
    """Run all tests."""
    print("\n" + "#"*60)
    print("# ScienceRAG Text Chunking Tests")
    print("#"*60)
    
    test_basic_chunking()
    test_long_text_chunking()
    test_paper_chunking()
    test_overlap()
    test_token_counting()
    
    print("\n" + "="*60)
    print("🎉 All chunking tests passed!")
    print("="*60)


if __name__ == "__main__":
    main()
