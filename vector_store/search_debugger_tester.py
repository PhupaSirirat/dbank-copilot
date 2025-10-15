"""
Advanced Vector Search Debugger & Testing Suite
Comprehensive testing and analysis for vector search quality
"""

import os
import json
import time
import statistics
from datetime import datetime
from collections import defaultdict, Counter
from typing import List, Dict, Tuple, Optional
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor
from colorama import init, Fore, Back, Style

# Initialize colorama for cross-platform color support
init(autoreset=True)

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

# =====================================================
# Core Search Functions
# =====================================================

def search_vectors(
    query: str, 
    top_k: int = 20,
    min_similarity: Optional[float] = None,
    category_filter: Optional[str] = None
) -> Tuple[List[Dict], float, float]:
    """
    Execute vector search and return results with timing
    Returns: (results, embedding_time, search_time)
    """
    # Time embedding generation
    embed_start = time.time()
    query_embedding = get_embedding(query)
    embed_time = time.time() - embed_start
    
    # Time database search
    search_start = time.time()
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # Build SQL with optional filters
    sql = """
        SELECT 
            doc_id,
            document_name,
            document_type,
            chunk_index,
            content,
            metadata,
            1 - (embedding <=> %s::vector) as similarity
        FROM vector_store.documents
        WHERE 1=1
    """
    params = [query_embedding]
    
    if category_filter:
        sql += " AND metadata->>'category' = %s"
        params.append(category_filter)
    
    if min_similarity:
        sql += " AND (1 - (embedding <=> %s::vector)) >= %s"
        params.extend([query_embedding, min_similarity])
    
    sql += " ORDER BY similarity DESC LIMIT %s"
    params.append(top_k)
    
    cur.execute(sql, params)
    results = cur.fetchall()
    search_time = time.time() - search_start
    
    cur.close()
    conn.close()
    
    # Parse metadata
    for r in results:
        r['metadata'] = json.loads(r['metadata']) if isinstance(r['metadata'], str) else r['metadata']
        r['similarity'] = float(r['similarity'])
    
    return results, embed_time, search_time

def get_database_stats() -> Dict:
    """Get overall database statistics"""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    stats = {}
    
    # Total documents and chunks
    cur.execute("SELECT COUNT(*) as total FROM vector_store.documents")
    stats['total_chunks'] = int(cur.fetchone()['total'])
    
    cur.execute("SELECT COUNT(DISTINCT document_name) as total FROM vector_store.documents")
    stats['total_documents'] = int(cur.fetchone()['total'])
    
    # Category breakdown
    cur.execute("""
        SELECT 
            metadata->>'category' as category,
            COUNT(*) as count
        FROM vector_store.documents
        GROUP BY metadata->>'category'
        ORDER BY count DESC
    """)
    categories_raw = cur.fetchall()
    stats['categories'] = {row['category']: int(row['count']) for row in categories_raw}
    
    # Chunking method
    cur.execute("""
        SELECT 
            metadata->>'chunking_method' as method,
            COUNT(*) as count
        FROM vector_store.documents
        GROUP BY metadata->>'chunking_method'
    """)
    chunking_raw = cur.fetchall()
    stats['chunking_methods'] = {row['method']: int(row['count']) for row in chunking_raw}
    
    # Token statistics
    cur.execute("""
        SELECT 
            AVG((metadata->>'chunk_tokens')::int) as avg_tokens,
            MIN((metadata->>'chunk_tokens')::int) as min_tokens,
            MAX((metadata->>'chunk_tokens')::int) as max_tokens
        FROM vector_store.documents
        WHERE metadata->>'chunk_tokens' IS NOT NULL
    """)
    token_stats = cur.fetchone()
    if token_stats and token_stats['avg_tokens'] is not None:
        stats['token_stats'] = {
            'avg_tokens': float(token_stats['avg_tokens']),
            'min_tokens': int(token_stats['min_tokens']),
            'max_tokens': int(token_stats['max_tokens'])
        }
    
    cur.close()
    conn.close()
    
    return stats

# =====================================================
# Analysis Functions
# =====================================================

def analyze_similarity_distribution(results: List[Dict]) -> Dict:
    """Analyze similarity score distribution"""
    if not results:
        return {}
    
    similarities = [r['similarity'] for r in results]
    
    return {
        'mean': statistics.mean(similarities),
        'median': statistics.median(similarities),
        'stdev': statistics.stdev(similarities) if len(similarities) > 1 else 0,
        'min': min(similarities),
        'max': max(similarities),
        'high_quality': sum(1 for s in similarities if s >= 0.7),
        'medium_quality': sum(1 for s in similarities if 0.5 <= s < 0.7),
        'low_quality': sum(1 for s in similarities if s < 0.5)
    }

def analyze_category_distribution(results: List[Dict]) -> Dict:
    """Analyze which categories appear in results"""
    categories = [r['metadata'].get('category', 'unknown') for r in results]
    return dict(Counter(categories))

def analyze_chunk_quality(results: List[Dict]) -> Dict:
    """Analyze chunk characteristics"""
    chunk_tokens = [r['metadata'].get('chunk_tokens', 0) for r in results if r['metadata'].get('chunk_tokens')]
    chunk_titles = [r['metadata'].get('chunk_title', 'N/A') for r in results]
    
    return {
        'avg_chunk_size': statistics.mean(chunk_tokens) if chunk_tokens else 0,
        'unique_documents': len(set(r['document_name'] for r in results)),
        'has_titles': sum(1 for t in chunk_titles if t != 'N/A'),
        'chunking_methods': list(set(r['metadata'].get('chunking_method', 'unknown') for r in results))
    }

def create_histogram(values: List[float], bins: int = 10, width: int = 50) -> str:
    """Create ASCII histogram"""
    if not values:
        return "No data"
    
    min_val, max_val = min(values), max(values)
    range_val = max_val - min_val or 1
    
    # Create bins
    bin_counts = [0] * bins
    for val in values:
        bin_idx = min(int((val - min_val) / range_val * bins), bins - 1)
        bin_counts[bin_idx] += 1
    
    # Normalize to width
    max_count = max(bin_counts) or 1
    
    # Build histogram
    lines = []
    for i, count in enumerate(bin_counts):
        bin_start = min_val + (i * range_val / bins)
        bin_end = min_val + ((i + 1) * range_val / bins)
        bar_width = int((count / max_count) * width)
        bar = "█" * bar_width
        lines.append(f"  {bin_start:.2f}-{bin_end:.2f} | {bar} ({count})")
    
    return "\n".join(lines)

# =====================================================
# Display Functions
# =====================================================

def print_header(text: str, char: str = "="):
    """Print formatted header"""
    width = 100
    print(f"\n{Fore.CYAN}{char * width}")
    print(f"{text.center(width)}")
    print(f"{char * width}{Style.RESET_ALL}\n")

def print_subheader(text: str):
    """Print formatted subheader"""
    print(f"\n{Fore.YELLOW}{'─' * 100}")
    print(f"{Fore.YELLOW}{text}")
    print(f"{'─' * 100}{Style.RESET_ALL}\n")

def format_similarity(similarity: float) -> str:
    """Color-code similarity score"""
    if similarity >= 0.8:
        return f"{Fore.GREEN}★★★★★ {similarity:.4f} (EXCELLENT){Style.RESET_ALL}"
    elif similarity >= 0.7:
        return f"{Fore.GREEN}★★★★☆ {similarity:.4f} (GOOD){Style.RESET_ALL}"
    elif similarity >= 0.6:
        return f"{Fore.YELLOW}★★★☆☆ {similarity:.4f} (DECENT){Style.RESET_ALL}"
    elif similarity >= 0.5:
        return f"{Fore.YELLOW}★★☆☆☆ {similarity:.4f} (OKAY){Style.RESET_ALL}"
    else:
        return f"{Fore.RED}★☆☆☆☆ {similarity:.4f} (POOR){Style.RESET_ALL}"

def display_result(result: Dict, index: int, show_full_content: bool = False):
    """Display a single search result"""
    metadata = result['metadata']
    
    # Header with similarity
    print(f"{Fore.CYAN}╔══ Result #{index} {format_similarity(result['similarity'])}")
    
    # Document info
    print(f"{Fore.CYAN}║{Style.RESET_ALL} 📄 Document: {Fore.WHITE}{result['document_name']}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}║{Style.RESET_ALL} 📑 Chunk: {result['chunk_index']}")
    
    if metadata.get('chunk_title'):
        print(f"{Fore.CYAN}║{Style.RESET_ALL} 🏷️  Title: {Fore.MAGENTA}{metadata['chunk_title']}{Style.RESET_ALL}")
    
    print(f"{Fore.CYAN}║{Style.RESET_ALL} 📁 Category: {metadata.get('category', 'N/A')}")
    
    if metadata.get('chunk_tokens'):
        print(f"{Fore.CYAN}║{Style.RESET_ALL} 📊 Tokens: {metadata['chunk_tokens']}")
    
    if metadata.get('chunking_method'):
        print(f"{Fore.CYAN}║{Style.RESET_ALL} 🧠 Method: {metadata['chunking_method']}")
    
    if metadata.get('is_critical') == True or metadata.get('is_critical') == 'true':
        print(f"{Fore.CYAN}║{Style.RESET_ALL} ⚠️  {Fore.RED}CRITICAL DOCUMENT{Style.RESET_ALL}")
    
    # Content preview or full
    print(f"{Fore.CYAN}║")
    if show_full_content:
        print(f"{Fore.CYAN}║{Style.RESET_ALL} 💬 Content:")
        for line in result['content'].split('\n'):
            print(f"{Fore.CYAN}║{Style.RESET_ALL}    {line}")
    else:
        preview = result['content'][:300].replace('\n', ' ')
        print(f"{Fore.CYAN}║{Style.RESET_ALL} 💬 Preview: {preview}...")
    
    print(f"{Fore.CYAN}╚{'═' * 98}{Style.RESET_ALL}\n")

# =====================================================
# Testing Functions
# =====================================================

def comprehensive_search(query: str, top_k: int = 10, show_full: bool = False):
    """Full search analysis with all features"""
    print_header(f"🔍 COMPREHENSIVE SEARCH ANALYSIS", "=")
    print(f"Query: {Fore.WHITE}\"{query}\"{Style.RESET_ALL}")
    print(f"Top-K: {top_k}")
    print(f"Provider: {Fore.CYAN}{EMBEDDING_PROVIDER.upper()}{Style.RESET_ALL}")
    
    # Execute search
    print(f"\n⏳ Executing search...")
    results, embed_time, search_time = search_vectors(query, top_k)
    
    if not results:
        print(f"\n{Fore.RED}❌ No results found!{Style.RESET_ALL}")
        return
    
    # Timing info
    print_subheader("⏱️  PERFORMANCE METRICS")
    print(f"  Embedding Generation: {Fore.GREEN}{embed_time*1000:.2f}ms{Style.RESET_ALL}")
    print(f"  Database Search:      {Fore.GREEN}{search_time*1000:.2f}ms{Style.RESET_ALL}")
    print(f"  Total Time:           {Fore.GREEN}{(embed_time + search_time)*1000:.2f}ms{Style.RESET_ALL}")
    
    # Similarity analysis
    print_subheader("📊 SIMILARITY ANALYSIS")
    sim_stats = analyze_similarity_distribution(results)
    
    print(f"  Mean Similarity:   {format_similarity(sim_stats['mean'])}")
    print(f"  Median Similarity: {format_similarity(sim_stats['median'])}")
    print(f"  Std Deviation:     {sim_stats['stdev']:.4f}")
    print(f"  Range:             {sim_stats['min']:.4f} - {sim_stats['max']:.4f}")
    print()
    print(f"  {Fore.GREEN}★★★★★ Excellent (≥0.7): {sim_stats['high_quality']} results{Style.RESET_ALL}")
    print(f"  {Fore.YELLOW}★★★☆☆ Decent (0.5-0.7):  {sim_stats['medium_quality']} results{Style.RESET_ALL}")
    print(f"  {Fore.RED}★☆☆☆☆ Poor (<0.5):       {sim_stats['low_quality']} results{Style.RESET_ALL}")
    
    # Histogram
    print(f"\n  Similarity Distribution:")
    print(create_histogram([r['similarity'] for r in results], bins=10))
    
    # Category analysis
    print_subheader("📁 CATEGORY DISTRIBUTION")
    cat_dist = analyze_category_distribution(results)
    for category, count in sorted(cat_dist.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / len(results)) * 100
        bar = "█" * int(percentage / 2)
        print(f"  {category:<20} {bar} {count} ({percentage:.1f}%)")
    
    # Chunk analysis
    print_subheader("📦 CHUNK QUALITY ANALYSIS")
    chunk_stats = analyze_chunk_quality(results)
    print(f"  Average Chunk Size:  {chunk_stats['avg_chunk_size']:.0f} tokens")
    print(f"  Unique Documents:    {chunk_stats['unique_documents']}")
    print(f"  Chunks with Titles:  {chunk_stats['has_titles']}/{len(results)}")
    print(f"  Chunking Methods:    {', '.join(chunk_stats['chunking_methods'])}")
    
    # Display results
    print_subheader("📋 SEARCH RESULTS")
    for i, result in enumerate(results, 1):
        display_result(result, i, show_full_content=show_full)
    
    # Recommendations
    print_subheader("💡 RECOMMENDATIONS")
    if sim_stats['high_quality'] >= 3:
        print(f"  {Fore.GREEN}✓ Great results! Current threshold (0.7) works well.{Style.RESET_ALL}")
    elif sim_stats['medium_quality'] >= 3:
        print(f"  {Fore.YELLOW}⚠ Consider lowering threshold to 0.5 for more results.{Style.RESET_ALL}")
    else:
        print(f"  {Fore.RED}⚠ Low similarity scores. Try:{Style.RESET_ALL}")
        print(f"    • Rephrase query with different keywords")
        print(f"    • Lower threshold to 0.3")
        print(f"    • Check if relevant documents are in database")

def batch_test(queries: List[str], top_k: int = 5):
    """Test multiple queries and compare"""
    print_header("🧪 BATCH QUERY TESTING", "=")
    
    all_results = {}
    
    for query in queries:
        print(f"\n{Fore.CYAN}Testing:{Style.RESET_ALL} \"{query}\"")
        results, embed_time, search_time = search_vectors(query, top_k)
        
        if results:
            sim_stats = analyze_similarity_distribution(results)
            print(f"  ⏱️  {(embed_time + search_time)*1000:.1f}ms")
            print(f"  📊 Mean: {sim_stats['mean']:.3f} | Top: {results[0]['similarity']:.3f}")
            print(f"  📄 {len(results)} results from {analyze_chunk_quality(results)['unique_documents']} docs")
            
            all_results[query] = {
                'results': results,
                'stats': sim_stats,
                'time': embed_time + search_time
            }
        else:
            print(f"  {Fore.RED}❌ No results{Style.RESET_ALL}")
    
    # Comparative analysis
    print_subheader("📊 COMPARATIVE ANALYSIS")
    
    if all_results:
        mean_sims = [data['stats']['mean'] for data in all_results.values()]
        times = [data['time'] for data in all_results.values()]
        
        print(f"  Average Similarity:  {statistics.mean(mean_sims):.3f}")
        print(f"  Average Search Time: {statistics.mean(times)*1000:.1f}ms")
        print(f"  Best Query:          \"{max(all_results.items(), key=lambda x: x[1]['stats']['mean'])[0]}\"")
        print(f"  Fastest Query:       \"{min(all_results.items(), key=lambda x: x[1]['time'])[0]}\"")

def compare_queries(query1: str, query2: str, top_k: int = 5):
    """Compare two queries side by side"""
    print_header("⚖️  QUERY COMPARISON", "=")
    
    print(f"{Fore.CYAN}Query 1:{Style.RESET_ALL} \"{query1}\"")
    print(f"{Fore.MAGENTA}Query 2:{Style.RESET_ALL} \"{query2}\"")
    
    results1, time1_e, time1_s = search_vectors(query1, top_k)
    results2, time2_e, time2_s = search_vectors(query2, top_k)
    
    stats1 = analyze_similarity_distribution(results1)
    stats2 = analyze_similarity_distribution(results2)
    
    print("\n" + "─" * 100)
    print(f"{'Metric':<30} {'Query 1':<30} {'Query 2':<30}")
    print("─" * 100)
    print(f"{'Results Found':<30} {len(results1):<30} {len(results2):<30}")
    print(f"{'Mean Similarity':<30} {stats1['mean']:.4f}{' ✓' if stats1['mean'] > stats2['mean'] else '':<30} {stats2['mean']:.4f}{' ✓' if stats2['mean'] > stats1['mean'] else '':<30}")
    print(f"{'Top Similarity':<30} {stats1['max']:.4f}{' ✓' if stats1['max'] > stats2['max'] else '':<30} {stats2['max']:.4f}{' ✓' if stats2['max'] > stats1['max'] else '':<30}")
    print(f"{'Search Time (ms)':<30} {(time1_e+time1_s)*1000:.2f}{' ✓' if (time1_e+time1_s) < (time2_e+time2_s) else '':<30} {(time2_e+time2_s)*1000:.2f}{' ✓' if (time2_e+time2_s) < (time1_e+time1_s) else '':<30}")
    
    # Document overlap
    docs1 = set(r['document_name'] for r in results1)
    docs2 = set(r['document_name'] for r in results2)
    overlap = len(docs1 & docs2)
    print(f"{'Document Overlap':<30} {overlap} documents appear in both")
    print("─" * 100)

def export_results(query: str, results: List[Dict], filename: Optional[str] = None):
    """Export search results to JSON file"""
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"search_results_{timestamp}.json"
    
    export_data = {
        'query': query,
        'timestamp': datetime.now().isoformat(),
        'provider': EMBEDDING_PROVIDER,
        'results_count': len(results),
        'results': [
            {
                'rank': i + 1,
                'similarity': r['similarity'],
                'document_name': r['document_name'],
                'chunk_index': r['chunk_index'],
                'content': r['content'],
                'metadata': r['metadata']
            }
            for i, r in enumerate(results)
        ]
    }
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n{Fore.GREEN}✓ Results exported to: {filename}{Style.RESET_ALL}")

def show_database_overview():
    """Display database statistics"""
    print_header("📊 DATABASE OVERVIEW", "=")
    
    stats = get_database_stats()
    
    if stats['total_chunks'] == 0:
        print(f"{Fore.RED}⚠️  Database is empty! No documents found.{Style.RESET_ALL}")
        print(f"\nRun the embedding script first:")
        print(f"  python embed_knowledge_base.py")
        return
    
    print(f"  Total Documents: {Fore.CYAN}{stats['total_documents']}{Style.RESET_ALL}")
    print(f"  Total Chunks:    {Fore.CYAN}{stats['total_chunks']}{Style.RESET_ALL}")
    
    if stats['total_documents'] > 0:
        print(f"  Avg Chunks/Doc:  {Fore.CYAN}{stats['total_chunks']/stats['total_documents']:.1f}{Style.RESET_ALL}")
    
    if stats.get('token_stats') and stats['token_stats'].get('avg_tokens'):
        print_subheader("📊 TOKEN STATISTICS")
        print(f"  Average: {stats['token_stats']['avg_tokens']:.0f} tokens")
        print(f"  Range:   {stats['token_stats']['min_tokens']:.0f} - {stats['token_stats']['max_tokens']:.0f} tokens")
    
    if stats.get('categories'):
        print_subheader("📁 CATEGORIES")
        for cat, count in sorted(stats['categories'].items(), key=lambda x: x[1], reverse=True):
            percentage = (count / stats['total_chunks']) * 100
            bar = "█" * int(percentage / 2)
            print(f"  {cat:<20} {bar} {count} ({percentage:.1f}%)")
    
    if stats.get('chunking_methods'):
        print_subheader("🧠 CHUNKING METHODS")
        for method, count in stats['chunking_methods'].items():
            percentage = (count / stats['total_chunks']) * 100
            print(f"  {method or 'unknown':<20} {count} ({percentage:.1f}%)")

# =====================================================
# Interactive CLI
# =====================================================

def main():
    """Main interactive CLI"""
    print_header("🔬 ADVANCED VECTOR SEARCH DEBUGGER", "█")
    print(f"Provider: {Fore.CYAN}{EMBEDDING_PROVIDER.upper()}{Style.RESET_ALL}")
    print(f"Database: {Fore.CYAN}{DB_CONFIG['database']}@{DB_CONFIG['host']}{Style.RESET_ALL}\n")
    
    # Show DB stats on startup
    try:
        show_database_overview()
    except Exception as e:
        print(f"{Fore.RED}⚠️  Could not load database stats: {e}{Style.RESET_ALL}\n")
    
    while True:
        print("\n" + "=" * 100)
        print(f"{Fore.YELLOW}MAIN MENU{Style.RESET_ALL}")
        print("=" * 100)
        print("1.  🔍 Comprehensive Search (detailed analysis)")
        print("2.  ⚡ Quick Search (fast results)")
        print("3.  🧪 Batch Test (multiple queries)")
        print("4.  ⚖️  Compare Two Queries")
        print("5.  📊 Database Overview")
        print("6.  🎯 Category-Filtered Search")
        print("7.  📁 Export Last Results")
        print("8.  🔧 Change Settings")
        print("9.  ❌ Exit")
        print("=" * 100)
        
        choice = input(f"\n{Fore.GREEN}Select option (1-9):{Style.RESET_ALL} ").strip()
        
        if choice == "1":
            query = input(f"\n{Fore.CYAN}Enter search query:{Style.RESET_ALL} ").strip()
            if query:
                top_k = input("Top-K results (default 10): ").strip() or "10"
                show_full = input("Show full content? (y/n, default n): ").strip().lower() == 'y'
                comprehensive_search(query, int(top_k), show_full)
                
                # Ask to export
                export = input("\nExport results? (y/n): ").strip().lower()
                if export == 'y':
                    results, _, _ = search_vectors(query, int(top_k))
                    export_results(query, results)
        
        elif choice == "2":
            query = input(f"\n{Fore.CYAN}Enter search query:{Style.RESET_ALL} ").strip()
            if query:
                results, embed_time, search_time = search_vectors(query, 5)
                print(f"\n⏱️  {(embed_time + search_time)*1000:.1f}ms | {len(results)} results")
                for i, r in enumerate(results, 1):
                    print(f"  {i}. {format_similarity(r['similarity'])} - {r['document_name']}")
        
        elif choice == "3":
            print("\nEnter queries (one per line, empty line to finish):")
            queries = []
            while True:
                q = input(f"  Query {len(queries)+1}: ").strip()
                if not q:
                    break
                queries.append(q)
            
            if queries:
                top_k = input("Top-K per query (default 5): ").strip() or "5"
                batch_test(queries, int(top_k))
        
        elif choice == "4":
            query1 = input(f"\n{Fore.CYAN}First query:{Style.RESET_ALL} ").strip()
            query2 = input(f"{Fore.MAGENTA}Second query:{Style.RESET_ALL} ").strip()
            if query1 and query2:
                top_k = input("Top-K per query (default 5): ").strip() or "5"
                compare_queries(query1, query2, int(top_k))
        
        elif choice == "5":
            show_database_overview()
        
        elif choice == "6":
            stats = get_database_stats()
            print("\nAvailable categories:")
            for i, cat in enumerate(stats['categories'].keys(), 1):
                print(f"  {i}. {cat}")
            
            cat_choice = input("\nSelect category number: ").strip()
            try:
                category = list(stats['categories'].keys())[int(cat_choice) - 1]
                query = input(f"Search query (in {category}): ").strip()
                if query:
                    results, _, _ = search_vectors(query, 10, category_filter=category)
                    print(f"\n{len(results)} results in '{category}':")
                    for i, r in enumerate(results, 1):
                        print(f"  {i}. {format_similarity(r['similarity'])} - {r['document_name']}")
            except (ValueError, IndexError):
                print(f"{Fore.RED}Invalid selection{Style.RESET_ALL}")
        
        elif choice == "7":
            query = input("Enter query for export: ").strip()
            if query:
                results, _, _ = search_vectors(query, 20)
                filename = input("Filename (default: auto-generated): ").strip() or None
                export_results(query, results, filename)
        
        elif choice == "8":
            print(f"\nCurrent settings:")
            print(f"  Provider: {EMBEDDING_PROVIDER}")
            print(f"  Database: {DB_CONFIG['database']}")
            print("\n(Settings are configured via .env file)")
        
        elif choice == "9":
            print(f"\n{Fore.GREEN}👋 Goodbye!{Style.RESET_ALL}\n")
            break
        
        else:
            print(f"{Fore.RED}Invalid option{Style.RESET_ALL}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Fore.YELLOW}Interrupted by user{Style.RESET_ALL}")
    except Exception as e:
        print(f"\n{Fore.RED}Error: {e}{Style.RESET_ALL}")
        import traceback
        traceback.print_exc()