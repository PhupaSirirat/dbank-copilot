"""
Debug search to see actual similarity scores
"""

import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv()

EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "openai")

# Initialize embedding
if EMBEDDING_PROVIDER == "openai":
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    def get_embedding(text):
        response = client.embeddings.create(input=text, model="text-embedding-3-small")
        return response.data[0].embedding
else:
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    def get_embedding(text):
        return model.encode(text).tolist()

DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', 'localhost'),
    'port': os.getenv('POSTGRES_PORT', '5433'),
    'database': os.getenv('POSTGRES_DB', 'dbank'),
    'user': os.getenv('POSTGRES_USER', 'dbank_user'),
    'password': os.getenv('POSTGRES_PASSWORD', 'dbank_pass_2025')
}

def debug_search(query: str, top_k: int = 10):
    """
    Show top results WITHOUT similarity filtering
    This helps you see what similarity scores you're actually getting
    """
    print(f"\n{'='*80}")
    print(f"🔍 Debug Search: \"{query}\"")
    print(f"{'='*80}")
    
    # Get embedding
    print("\n⏳ Generating query embedding...")
    query_embedding = get_embedding(query)
    
    # Connect and search
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # Search WITHOUT minimum similarity filter
    sql = """
        SELECT 
            doc_id,
            document_name,
            chunk_index,
            LEFT(content, 200) as content_preview,
            metadata->>'category' as category,
            metadata->>'is_critical' as is_critical,
            1 - (embedding <=> %s::vector) as similarity
        FROM vector_store.documents
        ORDER BY similarity DESC
        LIMIT %s
    """
    
    cur.execute(sql, [query_embedding, top_k])
    results = cur.fetchall()
    
    cur.close()
    conn.close()
    
    if not results:
        print("\n❌ No documents in database!")
        return
    
    print(f"\n✅ Top {len(results)} results (showing ALL, no filtering):\n")
    
    # Group by similarity ranges
    high = [r for r in results if r['similarity'] >= 0.7]
    medium = [r for r in results if 0.5 <= r['similarity'] < 0.7]
    low = [r for r in results if r['similarity'] < 0.5]
    
    print(f"📊 Similarity Distribution:")
    print(f"   🟢 High (≥0.70):   {len(high)} results")
    print(f"   🟡 Medium (0.50-0.69): {len(medium)} results")
    print(f"   🔴 Low (<0.50):    {len(low)} results")
    print()
    
    # Show all results
    for i, result in enumerate(results, 1):
        similarity = float(result['similarity'])
        
        # Color code by similarity
        if similarity >= 0.7:
            icon = "🟢"
            rating = "GOOD"
        elif similarity >= 0.5:
            icon = "🟡"
            rating = "OK"
        else:
            icon = "🔴"
            rating = "LOW"
        
        critical = "⚠️ CRITICAL" if result['is_critical'] == 'true' else ""
        
        print(f"{icon} #{i} - Similarity: {similarity:.4f} ({rating}) {critical}")
        print(f"   📄 {result['document_name']} (chunk {result['chunk_index']})")
        print(f"   📁 Category: {result['category']}")
        print(f"   💬 Preview: {result['content_preview']}...")
        print()
    
    # Recommendation
    print("="*80)
    if high:
        print("✅ GOOD NEWS: High similarity results found!")
        print("   Your current threshold (0.7) should work fine.")
    elif medium:
        print("⚠️  MEDIUM RESULTS: Consider lowering threshold to 0.5")
        print("   Edit vector_search.py: min_similarity=0.5")
    else:
        print("⚠️  LOW SIMILARITY: Results exist but may not be relevant")
        print("   Try:")
        print("   1. Rephrase your query")
        print("   2. Lower threshold to 0.3")
        print("   3. Check if embeddings were generated correctly")

def test_multiple_queries():
    """Test multiple queries to see patterns"""
    test_queries = [
        "How do I apply for a loan?",
        "loan application process",
        "v1.2 app crashes",
        "app version 1.2 issues",
        "interest calculation problem",
        "digital saving account features",
        "KYC verification requirements",
        "login troubleshooting",
        "transfer money",
        "customer policies"
    ]
    
    print("\n" + "="*80)
    print("🧪 BATCH TEST: Multiple Queries")
    print("="*80)
    
    for query in test_queries:
        debug_search(query, top_k=3)
        print("\n" + "─"*80 + "\n")

if __name__ == "__main__":
    print("="*80)
    print("🐛 Vector Search Debugger")
    print("="*80)
    
    while True:
        print("\nOptions:")
        print("1. Debug specific query")
        print("2. Run batch test (10 queries)")
        print("3. Exit")
        
        choice = input("\nChoice (1-3): ").strip()
        
        if choice == "1":
            query = input("\n🔍 Enter search query: ").strip()
            if query:
                top_k = input("Show top N results (default 10): ").strip() or "10"
                debug_search(query, int(top_k))
        
        elif choice == "2":
            test_multiple_queries()
        
        elif choice == "3":
            break