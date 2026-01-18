"""
Test script for literature API integration.

Run with: python -m scripts.test_literature
"""

import asyncio
import sys
sys.path.insert(0, '.')

from app.services.literature import OpenAlexClient, SemanticScholarClient


async def test_openalex():
    """Test OpenAlex API client."""
    print("\n" + "="*60)
    print("Testing OpenAlex API")
    print("="*60)
    
    client = OpenAlexClient()
    
    try:
        result = await client.search(
            query="quantum mechanics interpretations",
            year_from=2010,
            per_page=5,
        )
        
        print(f"\nQuery: 'quantum mechanics interpretations'")
        print(f"Year filter: >= 2010")
        print(f"Total results: {result.total_results}")
        print(f"Papers returned: {len(result.papers)}")
        
        for i, paper in enumerate(result.papers[:3], 1):
            print(f"\n--- Paper {i} ---")
            print(f"Title: {paper.title[:80]}...")
            print(f"Year: {paper.year}")
            print(f"Authors: {', '.join(paper.get_author_names()[:3])}")
            print(f"Citations: {paper.citation_count}")
            print(f"DOI: {paper.doi}")
            print(f"Has abstract: {paper.has_abstract()}")
            if paper.abstract:
                print(f"Abstract preview: {paper.abstract[:150]}...")
        
        print("\n✅ OpenAlex test passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ OpenAlex test failed: {e}")
        return False


async def test_semantic_scholar():
    """Test Semantic Scholar API client."""
    print("\n" + "="*60)
    print("Testing Semantic Scholar API")
    print("="*60)
    
    client = SemanticScholarClient()
    
    try:
        result = await client.search(
            query="machine learning neural networks",
            year_from=2020,
            limit=5,
        )
        
        print(f"\nQuery: 'machine learning neural networks'")
        print(f"Year filter: >= 2020")
        print(f"Total results: {result.total_results}")
        print(f"Papers returned: {len(result.papers)}")
        
        for i, paper in enumerate(result.papers[:3], 1):
            print(f"\n--- Paper {i} ---")
            print(f"Title: {paper.title[:80]}...")
            print(f"Year: {paper.year}")
            print(f"Authors: {', '.join(paper.get_author_names()[:3])}")
            print(f"Citations: {paper.citation_count}")
            print(f"DOI: {paper.doi}")
            print(f"Fields: {', '.join(paper.fields_of_study[:3])}")
            print(f"Has abstract: {paper.has_abstract()}")
            if paper.abstract:
                print(f"Abstract preview: {paper.abstract[:150]}...")
        
        print("\n✅ Semantic Scholar test passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Semantic Scholar test failed: {e}")
        return False


async def main():
    """Run all tests."""
    print("\n" + "#"*60)
    print("# ScienceRAG Literature API Integration Tests")
    print("#"*60)
    
    results = await asyncio.gather(
        test_openalex(),
        test_semantic_scholar(),
    )
    
    print("\n" + "="*60)
    print("Summary")
    print("="*60)
    print(f"OpenAlex: {'✅ PASS' if results[0] else '❌ FAIL'}")
    print(f"Semantic Scholar: {'✅ PASS' if results[1] else '❌ FAIL'}")
    
    if all(results):
        print("\n🎉 All tests passed!")
    else:
        print("\n⚠️ Some tests failed.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
