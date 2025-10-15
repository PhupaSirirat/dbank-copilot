"""
Knowledge Base Search Tool - Enhanced version with debugging and fallback
"""

import sys
import os
from pathlib import Path
import logging

# Add parent directory to path to import vector_search
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from vector_store.vector_search import search_knowledge_base
from typing import List, Dict, Optional

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def search_knowledge_base_tool(
    query: str,
    top_k: int = 5,
    category: Optional[str] = None,
    min_similarity: float = 0.5,  # Lowered from 0.7 to 0.5
    enable_fallback: bool = True
) -> List[Dict]:
    """
    Semantic search over knowledge base with intelligent fallback
    
    Args:
        query: Search query in natural language
        top_k: Number of results to return (1-20)
        category: Optional category filter (product_guide, support_doc, reference_doc)
        min_similarity: Minimum similarity score (0.0-1.0), default 0.5
        enable_fallback: If True, retry with lower threshold if no results
    
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
    
    valid_categories = ['product_guide', 'support_doc', 'reference_doc', 'general']
    if category and category not in valid_categories:
        raise ValueError(f"category must be one of: {', '.join(valid_categories)}")
    
    try:
        logger.info(f"🔍 Searching: '{query}' | top_k={top_k} | category={category} | min_sim={min_similarity}")
        
        # Call the vector search function
        results = search_knowledge_base(
            query=query,
            top_k=top_k,
            filter_category=category,
            min_similarity=min_similarity
        )
        
        logger.info(f"✅ Initial search returned {len(results)} results")
        
        # Fallback strategy if no results
        if not results and enable_fallback:
            logger.warning(f"⚠️  No results with similarity >= {min_similarity}")
            
            # Try 1: Lower similarity threshold
            if min_similarity > 0.3:
                logger.info(f"🔄 Retrying with lower threshold (0.3)...")
                results = search_knowledge_base(
                    query=query,
                    top_k=top_k,
                    filter_category=category,
                    min_similarity=0.3
                )
                logger.info(f"   Found {len(results)} results with threshold 0.3")
            
            # Try 2: Remove category filter if still no results
            if not results and category:
                logger.info(f"🔄 Retrying without category filter...")
                results = search_knowledge_base(
                    query=query,
                    top_k=top_k,
                    filter_category=None,
                    min_similarity=0.3
                )
                logger.info(f"   Found {len(results)} results without category filter")
            
            # Try 3: Get ANY results (no similarity filter)
            if not results:
                logger.info(f"🔄 Final attempt: getting top results regardless of similarity...")
                results = search_knowledge_base(
                    query=query,
                    top_k=top_k,
                    filter_category=None,
                    min_similarity=0.0  # No filter
                )
                logger.info(f"   Found {len(results)} results (all similarities)")
        
        # Format results for MCP response
        formatted_results = []
        for result in results:
            formatted_results.append({
                'title': result.get('title', 'Untitled'),
                'content': result.get('content', ''),
                'similarity': round(result.get('similarity', 0.0), 3),
                'category': result.get('category', 'unknown'),
                'filename': result.get('filename', ''),
                'chunk_index': result.get('chunk_index', 0),
                'chunk_title': result.get('chunk_title', 'N/A'),
                'is_critical': result.get('is_critical', False),
                'source': result.get('filepath', '')
            })
        
        # Log final result count
        if formatted_results:
            logger.info(f"📊 Returning {len(formatted_results)} results (similarity range: {formatted_results[-1]['similarity']:.3f} - {formatted_results[0]['similarity']:.3f})")
        else:
            logger.warning(f"❌ No results found even after fallback attempts")
        
        return formatted_results
    
    except Exception as e:
        logger.error(f"❌ Knowledge base search failed: {str(e)}", exc_info=True)
        raise Exception(f"Knowledge base search failed: {str(e)}")

def check_database_status() -> Dict:
    """
    Check database connectivity and content
    Returns database statistics
    """
    try:
        import os
        from dotenv import load_dotenv
        import psycopg2
        from psycopg2.extras import RealDictCursor
        
        load_dotenv()
        
        DB_CONFIG = {
            'host': os.getenv('POSTGRES_HOST', 'localhost'),
            'port': os.getenv('POSTGRES_PORT', '5433'),
            'database': os.getenv('POSTGRES_DB', 'dbank'),
            'user': os.getenv('POSTGRES_USER', 'dbank_user'),
            'password': os.getenv('POSTGRES_PASSWORD', 'dbank_pass_2025')
        }
        
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get stats
        cur.execute("SELECT COUNT(*) as total FROM vector_store.documents")
        total_chunks = cur.fetchone()['total']
        
        cur.execute("SELECT COUNT(DISTINCT document_name) as total FROM vector_store.documents")
        total_docs = cur.fetchone()['total']
        
        cur.execute("""
            SELECT metadata->>'category' as category, COUNT(*) as count
            FROM vector_store.documents
            GROUP BY metadata->>'category'
        """)
        categories = {row['category']: row['count'] for row in cur.fetchall()}
        
        cur.close()
        conn.close()
        
        return {
            'status': 'connected',
            'total_documents': total_docs,
            'total_chunks': total_chunks,
            'categories': categories
        }
    
    except Exception as e:
        logger.error(f"Database check failed: {e}")
        return {
            'status': 'error',
            'error': str(e)
        }

def get_document_categories() -> List[str]:
    """Get available document categories"""
    return ['product_guide', 'support_doc', 'reference_doc', 'general']

def get_critical_documents(top_k: int = 20) -> List[Dict]:
    """Get all documents marked as critical (e.g., v1.2 issues)"""
    try:
        # Search for critical documents with low threshold
        results = search_knowledge_base(
            query="critical issues bugs problems version v1.2",
            top_k=top_k,
            min_similarity=0.3
        )
        
        # Filter for critical ones
        critical = [r for r in results if r.get('is_critical', False)]
        
        logger.info(f"Found {len(critical)} critical documents")
        return critical
    except Exception as e:
        logger.error(f"Failed to get critical documents: {e}")
        raise Exception(f"Failed to get critical documents: {str(e)}")

def search_with_context(
    query: str,
    top_k: int = 5,
    include_surrounding: bool = True
) -> List[Dict]:
    """
    Search with surrounding context (previous and next chunks)
    Useful for getting more complete information
    """
    try:
        # Get initial results
        results = search_knowledge_base_tool(query, top_k=top_k)
        
        if not results or not include_surrounding:
            return results
        
        # For each result, try to get adjacent chunks
        import os
        from dotenv import load_dotenv
        import psycopg2
        from psycopg2.extras import RealDictCursor
        
        load_dotenv()
        
        DB_CONFIG = {
            'host': os.getenv('POSTGRES_HOST', 'localhost'),
            'port': os.getenv('POSTGRES_PORT', '5433'),
            'database': os.getenv('POSTGRES_DB', 'dbank'),
            'user': os.getenv('POSTGRES_USER', 'dbank_user'),
            'password': os.getenv('POSTGRES_PASSWORD', 'dbank_pass_2025')
        }
        
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        enriched_results = []
        
        for result in results:
            doc_name = result['title']
            chunk_idx = result['chunk_index']
            
            # Get adjacent chunks
            cur.execute("""
                SELECT content, chunk_index
                FROM vector_store.documents
                WHERE document_name = %s 
                AND chunk_index IN (%s, %s, %s)
                ORDER BY chunk_index
            """, (doc_name, chunk_idx - 1, chunk_idx, chunk_idx + 1))
            
            adjacent = cur.fetchall()
            
            # Combine content
            full_content = "\n\n---\n\n".join([chunk['content'] for chunk in adjacent])
            
            result['full_context'] = full_content
            result['has_context'] = len(adjacent) > 1
            
            enriched_results.append(result)
        
        cur.close()
        conn.close()
        
        return enriched_results
    
    except Exception as e:
        logger.error(f"Context enrichment failed: {e}")
        # Return original results if context enrichment fails
        return results

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
        },
        {
            "name": "Account opening",
            "query": "how to open new account",
            "top_k": 3
        },
        {
            "name": "Transfer limits",
            "query": "daily transfer limit",
            "top_k": 3
        }
    ]
    
    return examples

if __name__ == "__main__":
    # Comprehensive testing
    print("=" * 80)
    print("🧪 TESTING KNOWLEDGE BASE SEARCH TOOL")
    print("=" * 80)
    
    # Test 0: Check database status
    print("\n0. Checking database status...")
    db_status = check_database_status()
    print(f"   Status: {db_status.get('status')}")
    if db_status.get('status') == 'connected':
        print(f"   Documents: {db_status.get('total_documents')}")
        print(f"   Chunks: {db_status.get('total_chunks')}")
        print(f"   Categories: {db_status.get('categories')}")
    else:
        print(f"   ⚠️  Error: {db_status.get('error')}")
        print("\n   💡 Make sure to run the embedding script first:")
        print("      python embed_knowledge_base.py")
        sys.exit(1)
    
    if db_status.get('total_chunks', 0) == 0:
        print("\n   ⚠️  Database is empty! Run embedding script first.")
        sys.exit(1)
    
    # Test 1: Simple search with logging
    print("\n1. Testing simple search...")
    try:
        results = search_knowledge_base_tool(
            query="How to apply for a loan?",
            top_k=3,
            min_similarity=0.5
        )
        print(f"✅ Found {len(results)} results")
        for i, r in enumerate(results, 1):
            print(f"\n   Result {i}:")
            print(f"   Title: {r['title']}")
            print(f"   Chunk: {r.get('chunk_title', 'N/A')}")
            print(f"   Similarity: {r['similarity']}")
            print(f"   Category: {r['category']}")
            print(f"   Preview: {r['content'][:150]}...")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: Category filter
    print("\n2. Testing category filter (product_guide)...")
    try:
        results = search_knowledge_base_tool(
            query="savings account features",
            top_k=3,
            category="product_guide",
            min_similarity=0.4
        )
        print(f"✅ Found {len(results)} product guide results")
        for r in results:
            print(f"   - {r['title']} (sim: {r['similarity']})")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 3: Low similarity threshold
    print("\n3. Testing with low similarity threshold...")
    try:
        results = search_knowledge_base_tool(
            query="customer support contact information",
            top_k=3,
            min_similarity=0.3
        )
        print(f"✅ Found {len(results)} results")
        for r in results:
            print(f"   - {r['title']} (sim: {r['similarity']})")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 4: Fallback mechanism
    print("\n4. Testing fallback with difficult query...")
    try:
        results = search_knowledge_base_tool(
            query="xyz123 nonexistent topic",
            top_k=3,
            min_similarity=0.7,
            enable_fallback=True
        )
        print(f"✅ Fallback returned {len(results)} results")
        if results:
            print(f"   Best match: {results[0]['title']} (sim: {results[0]['similarity']})")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 5: Critical documents
    print("\n5. Testing critical documents retrieval...")
    try:
        critical = get_critical_documents(top_k=10)
        print(f"✅ Found {len(critical)} critical documents")
        for doc in critical[:3]:
            print(f"   - {doc['title']} (sim: {doc['similarity']})")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 6: Search with context
    print("\n6. Testing search with context...")
    try:
        results = search_with_context(
            query="interest calculation",
            top_k=2,
            include_surrounding=True
        )
        print(f"✅ Found {len(results)} results with context")
        for r in results:
            print(f"   - {r['title']}")
            print(f"     Has context: {r.get('has_context', False)}")
            if r.get('has_context'):
                print(f"     Context length: {len(r.get('full_context', ''))} chars")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "=" * 80)
    print("✅ All tests completed!")
    print("=" * 80)