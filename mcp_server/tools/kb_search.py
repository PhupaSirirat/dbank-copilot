"""
Knowledge Base Search Tool - Semantic search wrapper for MCP
"""

import sys
import os
from pathlib import Path

# Add parent directory to path to import vector_search
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from vector_store.vector_search import search_knowledge_base
from typing import List, Dict, Optional

def search_knowledge_base_tool(
    query: str,
    top_k: int = 5,
    category: Optional[str] = None,
    min_similarity: float = 0.7
) -> List[Dict]:
    """
    Semantic search over knowledge base
    
    Args:
        query: Search query in natural language
        top_k: Number of results to return (1-20)
        category: Optional category filter (product_guide, support_doc, reference_doc)
        min_similarity: Minimum similarity score (0.0-1.0)
    
    Returns:
        List of matching document chunks with metadata
    """
    # Validate inputs
    if not query or not query.strip():
        raise ValueError("Query cannot be empty")
    
    if top_k < 1 or top_k > 20:
        raise ValueError("top_k must be between 1 and 20")
    
    if min_similarity < 0.0 or min_similarity > 1.0:
        raise ValueError("min_similarity must be between 0.0 and 1.0")
    
    if category and category not in ['product_guide', 'support_doc', 'reference_doc']:
        raise ValueError("category must be one of: product_guide, support_doc, reference_doc")
    
    try:
        # Call the vector search function
        results = search_knowledge_base(
            query=query,
            top_k=top_k,
            filter_category=category,
            min_similarity=min_similarity
        )
        
        # Format results for MCP response
        formatted_results = []
        for result in results:
            formatted_results.append({
                'title': result['title'],
                'content': result['content'],
                'similarity': round(result['similarity'], 3),
                'category': result['category'],
                'filename': result['filename'],
                'chunk_index': result['chunk_index'],
                'is_critical': result.get('is_critical', False)
            })
        
        return formatted_results
    
    except Exception as e:
        raise Exception(f"Knowledge base search failed: {str(e)}")

def get_document_categories() -> List[str]:
    """Get available document categories"""
    return ['product_guide', 'support_doc', 'reference_doc']

def get_critical_documents() -> List[Dict]:
    """Get all documents marked as critical (e.g., v1.2 issues)"""
    try:
        # Search for critical documents
        results = search_knowledge_base(
            query="critical issues bugs problems",
            top_k=20,
            min_similarity=0.5
        )
        
        # Filter for critical ones
        critical = [r for r in results if r.get('is_critical', False)]
        
        return critical
    except Exception as e:
        raise Exception(f"Failed to get critical documents: {str(e)}")

# =====================================================
# Example Searches
# =====================================================

def example_searches():
    """Example searches for testing"""
    
    examples = [
        {
            "name": "Loan application process",
            "query": "How do I apply for a loan?",
            "top_k": 3,
            "category": "product_guide"
        },
        {
            "name": "v1.2 issues",
            "query": "v1.2 app crashes and bugs",
            "top_k": 5,
            "category": "support_doc"
        },
        {
            "name": "KYC requirements",
            "query": "What documents needed for KYC verification?",
            "top_k": 3,
            "category": "reference_doc"
        },
        {
            "name": "Interest calculation problem",
            "query": "interest not calculating correctly",
            "top_k": 5
        },
        {
            "name": "Product comparison",
            "query": "difference between digital saving and digital lending",
            "top_k": 3
        }
    ]
    
    return examples

if __name__ == "__main__":
    # Test the tool
    print("=" * 60)
    print("🧪 Testing Knowledge Base Search Tool")
    print("=" * 60)
    
    # Test 1: Simple search
    print("\n1. Testing simple search...")
    try:
        results = search_knowledge_base_tool(
            query="How to apply for a loan?",
            top_k=2
        )
        print(f"✅ Found {len(results)} results")
        for i, r in enumerate(results, 1):
            print(f"\n   Result {i}:")
            print(f"   Title: {r['title']}")
            print(f"   Similarity: {r['similarity']}")
            print(f"   Category: {r['category']}")
            print(f"   Content preview: {r['content'][:100]}...")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: Category filter
    print("\n2. Testing category filter...")
    try:
        results = search_knowledge_base_tool(
            query="v1.2 bugs",
            top_k=3,
            category="support_doc"
        )
        print(f"✅ Found {len(results)} support documents")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 3: Critical documents
    print("\n3. Testing critical documents...")
    try:
        critical = get_critical_documents()
        print(f"✅ Found {len(critical)} critical documents")
        for doc in critical[:3]:
            print(f"   - {doc['title']}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "=" * 60)