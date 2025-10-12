"""
Semantic Search over Knowledge Base using pgvector
"""

import os
from typing import List, Dict
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv()

# Configuration
EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "openai")

# Database connection
DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', 'localhost'),
    'port': os.getenv('POSTGRES_PORT', '5433'),
    'database': os.getenv('POSTGRES_DB', 'dbank'),
    'user': os.getenv('POSTGRES_USER', 'dbank_user'),
    'password': os.getenv('POSTGRES_PASSWORD', 'dbank_pass_2025')
}

# Initialize embedding model
if EMBEDDING_PROVIDER == "openai":
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    EMBEDDING_MODEL = "text-embedding-3-small"
    
    def get_embedding(text: str) -> List[float]:
        response = client.embeddings.create(input=text, model=EMBEDDING_MODEL)
        return response.data[0].embedding
else:
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    def get_embedding(text: str) -> List[float]:
        return model.encode(text).tolist()

def search_knowledge_base(
    query: str, 
    top_k: int = 5,
    filter_category: str = None,
    min_similarity: float = 0.5  # CHANGED: Lowered from 0.7 to 0.5
) -> List[Dict]:
    """
    Semantic search over knowledge base
    
    Args:
        query: Search query
        top_k: Number of results to return
        filter_category: Optional category filter (product_guide, support_doc, reference_doc)
        min_similarity: Minimum similarity threshold (0-1)
    
    Returns:
        List of matching document chunks with metadata
    """
    # Get query embedding
    query_embedding = get_embedding(query)
    
    # Connect to database
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # Build query
    sql = """
        SELECT 
            doc_id,
            document_name,
            chunk_index,
            content,
            metadata,
            1 - (embedding <=> %s::vector) as similarity
        FROM vector_store.documents
        WHERE 1=1
    """
    
    params = [query_embedding]
    
    # Add category filter if specified
    if filter_category:
        sql += " AND metadata->>'category' = %s"
        params.append(filter_category)
    
    # Add similarity threshold
    sql += " AND 1 - (embedding <=> %s::vector) >= %s"
    params.extend([query_embedding, min_similarity])
    
    # Order by similarity and limit
    sql += " ORDER BY similarity DESC LIMIT %s"
    params.append(top_k)
    
    # Execute query
    cur.execute(sql, params)
    results = cur.fetchall()
    
    # Close connection
    cur.close()
    conn.close()
    
    # Format results
    formatted_results = []
    for row in results:
        formatted_results.append({
            'doc_id': row['doc_id'],
            'title': row['document_name'],
            'content': row['content'],
            'chunk_index': row['chunk_index'],
            'similarity': float(row['similarity']),
            'category': row['metadata'].get('category'),
            'filename': row['metadata'].get('filename'),
            'is_critical': row['metadata'].get('is_critical', False)
        })
    
    return formatted_results

def search_and_display(query: str, top_k: int = 3, min_similarity: float = 0.5):
    """Search and display results nicely"""
    print(f"\n🔍 Searching for: \"{query}\"")
    print(f"   Threshold: {min_similarity:.2f} | Results: {top_k}")
    print("=" * 80)
    
    results = search_knowledge_base(query, top_k=top_k, min_similarity=min_similarity)
    
    if not results:
        print(f"\n❌ No results found with similarity ≥ {min_similarity}")
        print("\n💡 Suggestions:")
        print("   1. Try lowering the threshold (e.g., 0.3)")
        print("   2. Rephrase your query")
        print("   3. Run debug_search.py to see actual scores")
        return
    
    print(f"\n✅ Found {len(results)} results:\n")
    
    for i, result in enumerate(results, 1):
        similarity = result['similarity']
        
        # Add quality indicator
        if similarity >= 0.8:
            quality = "🟢 Excellent"
        elif similarity >= 0.7:
            quality = "🟢 Very Good"
        elif similarity >= 0.6:
            quality = "🟡 Good"
        elif similarity >= 0.5:
            quality = "🟡 Fair"
        else:
            quality = "🔴 Low"
        
        print(f"\n{'─' * 80}")
        print(f"📄 Result #{i} - {result['title']} (chunk {result['chunk_index']})")
        print(f"   {quality} Match: {similarity:.3f} | Category: {result['category']}")
        if result['is_critical']:
            print("   ⚠️  CRITICAL DOCUMENT")
        print(f"{'─' * 80}")
        
        # Show first 300 chars of content
        content = result['content']
        if len(content) > 300:
            content = content[:297] + "..."
        print(content)
    
    print("\n" + "=" * 80)

# =====================================================
# Example Queries
# =====================================================

def run_example_queries():
    """Run some example searches"""
    
    example_queries = [
        "How do I apply for a loan?",
        "Interest rate calculation problem",
        "v1.2 app crashes",
        "KYC verification requirements",
        "Digital Saving features",
        "Troubleshoot login issues"
    ]
    
    for query in example_queries:
        search_and_display(query, top_k=2)
        print("\n" + "🔹" * 40 + "\n")
        input("Press Enter for next query...")

if __name__ == "__main__":
    print("=" * 80)
    print("🔍 dBank Knowledge Base Semantic Search")
    print("=" * 80)
    
    # Interactive search
    while True:
        print("\nOptions:")
        print("1. Search knowledge base")
        print("2. Run example queries")
        print("3. Adjust search threshold")
        print("4. Exit")
        
        choice = input("\nEnter choice (1-4): ").strip()
        
        if choice == "1":
            query = input("\n🔍 Enter your search query: ").strip()
            if query:
                top_k = input("Number of results (default 5): ").strip() or "5"
                threshold = input("Similarity threshold 0.0-1.0 (default 0.5): ").strip() or "0.5"
                search_and_display(query, int(top_k), float(threshold))
        
        elif choice == "2":
            run_example_queries()
        
        elif choice == "3":
            print("\n📊 Similarity Threshold Guide:")
            print("   0.8-1.0: Very strict (only nearly identical matches)")
            print("   0.7-0.8: Strict (high quality matches)")
            print("   0.6-0.7: Balanced (good quality)")
            print("   0.5-0.6: Permissive (decent matches)")
            print("   0.3-0.5: Very permissive (may include loose matches)")
            print("   <0.3: Too loose (likely irrelevant)")
            print("\n💡 Recommended: Start with 0.5, adjust based on results")
        
        elif choice == "4":
            print("\n👋 Goodbye!")
            break
        
        else:
            print("Invalid choice!")