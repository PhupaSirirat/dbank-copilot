"""
Embed Knowledge Base Documents into pgvector
Supports both OpenAI and local sentence-transformers
"""

import os
import glob
import json
from pathlib import Path
from typing import List, Dict, Tuple
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import execute_batch
from tqdm import tqdm
import tiktoken

# Load environment variables
load_dotenv()

# Configuration
KNOWLEDGE_BASE_DIR = "knowledge_base\kb_files"
CHUNK_SIZE = 600  # tokens per chunk
CHUNK_OVERLAP = 50  # token overlap between chunks
EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "openai")  # or "local"

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
    EMBEDDING_DIM = 1536
else:
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer('all-MiniLM-L6-v2')
    EMBEDDING_DIM = 384

print(f"🚀 Using {EMBEDDING_PROVIDER} embeddings (dimension: {EMBEDDING_DIM})")

# =====================================================
# Document Processing Functions
# =====================================================

def read_markdown_file(filepath: str) -> str:
    """Read markdown file content"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()

def chunk_text(
    text: str,
    chunk_size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP,
) -> List[str]:
    """
    Fast token-based chunking (V1-style) with safety guards:
    - No heavy precompute
    - Prevent infinite loops (always forward progress)
    - Clamp overlap if it's too large for the current chunk
    - Choose cut points using character-length heuristics (unit-consistent)
    """
    encoding = tiktoken.get_encoding("cl100k_base")
    tokens = encoding.encode(text)
    n_tokens = len(tokens)

    chunks: List[str] = []
    start = 0

    # simple helpers for sentence-like break without regex
    def best_sentence_break(s: str) -> int:
        # check a few common patterns; pick the rightmost
        cand = [
            s.rfind(". "),
            s.rfind(".\n"),
            s.rfind("! "),
            s.rfind("!\n"),
            s.rfind("? "),
            s.rfind("?\n"),
        ]
        return max(cand)

    while start < n_tokens:
        end = min(start + chunk_size, n_tokens)
        chunk_tokens = tokens[start:end]
        chunk_str = encoding.decode(chunk_tokens)

        # try to cut nicely only if not the last chunk
        if end < n_tokens and chunk_str:
            half_char = len(chunk_str) * 0.5  # compare with chars (unit-consistent)
            cut_idx = -1

            # 1) paragraph break
            last_para = chunk_str.rfind("\n\n")
            if last_para != -1 and last_para >= half_char:
                cut_idx = last_para
            else:
                # 2) sentence break
                last_sent = best_sentence_break(chunk_str)
                if last_sent != -1 and last_sent >= half_char:
                    # include the punctuation if it exists
                    cut_idx = last_sent + 1

            if cut_idx != -1:
                # re-encode to align token boundary
                sub = chunk_str[:cut_idx]
                sub_tokens = encoding.encode(sub)
                end = start + len(sub_tokens)
                chunk_tokens = tokens[start:end]
                chunk_str = sub

        piece = chunk_str.strip()
        if piece:
            chunks.append(piece)

        # --- SAFETY: ensure forward progress & clamp overlap dynamically ---
        step = end - start  # tokens moved this round
        if step <= 0:
            # pathological case: force move 1 token
            start += 1
            continue

        eff_overlap = overlap
        # if overlap >= current step, clamp to 1/4 of current step (keeps speed & context)
        if eff_overlap >= step:
            eff_overlap = max(step // 4, 0)

        next_start = end - eff_overlap
        if next_start <= start:
            next_start = start + 1  # always move forward at least 1 token
        start = next_start

    return chunks

def extract_metadata(filepath: str, content: str) -> Dict:
    """Extract metadata from document"""
    path = Path(filepath)
    
    # Extract title from first # heading
    lines = content.split('\n')
    title = path.stem.replace('_', ' ').title()
    for line in lines:
        if line.startswith('# '):
            title = line.replace('# ', '').strip()
            break
    
    # Determine category
    parent_dir = path.parent.name
    category_map = {
        'products': 'product_guide',
        'support': 'support_doc',
        'reference': 'reference_doc'
    }
    category = category_map.get(parent_dir, 'general')
    
    # Check for critical flags
    is_critical = 'v1.2' in content.lower() or 'critical' in content.lower()
    
    return {
        'title': title,
        'category': category,
        'filename': path.name,
        'filepath': str(path),
        'is_critical': is_critical,
        'parent_dir': parent_dir
    }

def get_embedding_openai(text: str) -> List[float]:
    """Get embedding from OpenAI"""
    response = client.embeddings.create(
        input=text,
        model=EMBEDDING_MODEL
    )
    return response.data[0].embedding

def get_embedding_local(text: str) -> List[float]:
    """Get embedding from local model"""
    embedding = model.encode(text)
    return embedding.tolist()

def get_embedding(text: str) -> List[float]:
    """Get embedding based on provider"""
    if EMBEDDING_PROVIDER == "openai":
        return get_embedding_openai(text)
    else:
        return get_embedding_local(text)

# =====================================================
# Database Functions
# =====================================================

def ensure_vector_dimension(conn, dim: int):
    """Update vector dimension if needed"""
    with conn.cursor() as cur:
        # Check current dimension
        cur.execute("""
            SELECT atttypmod 
            FROM pg_attribute 
            WHERE attrelid = 'vector_store.documents'::regclass 
            AND attname = 'embedding'
        """)
        result = cur.fetchone()
        
        if result and result[0] != dim:
            print(f"⚠️  Updating vector dimension from {result[0]} to {dim}")
            cur.execute("""
                ALTER TABLE vector_store.documents 
                ALTER COLUMN embedding TYPE vector(%s)
            """, (dim,))
            conn.commit()

def clear_existing_documents(conn):
    """Clear existing documents"""
    with conn.cursor() as cur:
        cur.execute("DELETE FROM vector_store.documents")
        conn.commit()
    print("🗑️  Cleared existing documents")

def insert_embeddings(conn, embeddings_data: List[Tuple]):
    """Insert embeddings into database"""
    with conn.cursor() as cur:
        insert_query = """
            INSERT INTO vector_store.documents 
            (document_name, document_type, chunk_index, content, embedding, metadata)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        
        # Convert metadata dicts to JSON strings
        formatted_data = [
            (name, doc_type, idx, content, embedding, json.dumps(metadata))
            for name, doc_type, idx, content, embedding, metadata in embeddings_data
        ]
        
        execute_batch(cur, insert_query, formatted_data, page_size=100)
        conn.commit()

# =====================================================
# Main Processing
# =====================================================

def process_knowledge_base():
    """Main function to process and embed knowledge base"""
    print("\n" + "=" * 60)
    print("📚 Knowledge Base Embedding Process")
    print("=" * 60)
    
    # Connect to database
    conn = psycopg2.connect(**DB_CONFIG)
    print("✅ Connected to database")
    
    # Ensure correct vector dimension
    ensure_vector_dimension(conn, EMBEDDING_DIM)
    
    # Clear existing documents
    clear_existing_documents(conn)
    
    # Find all markdown files
    md_files = glob.glob(f"{KNOWLEDGE_BASE_DIR}/**/*.md", recursive=True)
    print(f"\n📄 Found {len(md_files)} markdown files")
    
    all_embeddings = []
    total_chunks = 0
    
    # Process each file
    # for filepath in tqdm(md_files, desc="Processing documents"):
    for filepath in md_files:
        print(f"\n🔍 Processing file: {filepath}")
        # Skip README
        if filepath.endswith('README.md'):
            continue
        
        try:
            # Read content
            content = read_markdown_file(filepath)
            
            # Extract metadata
            metadata = extract_metadata(filepath, content)
            
            # Chunk the document
            chunks = chunk_text(content)
        except Exception as e:
            print(f"   ⚠️  Error processing file {filepath}: {e}")
            continue
        
        print(f"\n📝 {metadata['title']}")
        print(f"   Chunks: {len(chunks)}")
        
        # Generate embeddings for each chunk
        for idx, chunk in tqdm(enumerate(chunks), desc="  Embedding chunks", total=len(chunks), leave=True):
            if len(chunk.strip()) < 50:  # Skip very short chunks
                continue
            
            try:
                # Get embedding
                embedding = get_embedding(chunk)
                
                # Prepare data
                chunk_metadata = {
                    **metadata,
                    'chunk_index': idx,
                    'chunk_size': len(chunk)
                }
                
                all_embeddings.append((
                    metadata['title'],
                    'markdown',
                    idx,
                    chunk,
                    embedding,
                    chunk_metadata
                ))
                
                total_chunks += 1
                
            except Exception as e:
                print(f"   ⚠️  Error embedding chunk {idx}: {e}")
                continue
    
    # Insert all embeddings
    print(f"\n💾 Inserting {total_chunks} chunks into database...")
    insert_embeddings(conn, all_embeddings)
    
    print(f"✅ Inserted {total_chunks} document chunks")
    
    # Create index for faster search
    print("\n🔨 Creating vector index...")
    with conn.cursor() as cur:
        # Drop existing index if any
        cur.execute("DROP INDEX IF EXISTS vector_store.documents_embedding_idx")
        
        # Create new index
        cur.execute("""
            CREATE INDEX documents_embedding_idx 
            ON vector_store.documents 
            USING ivfflat (embedding vector_cosine_ops)
            WITH (lists = 100)
        """)
        conn.commit()
    
    print("✅ Vector index created")
    
    # Summary
    with conn.cursor() as cur:
        cur.execute("""
            SELECT 
                metadata->>'category' as category,
                COUNT(*) as chunk_count,
                COUNT(DISTINCT document_name) as doc_count
            FROM vector_store.documents
            GROUP BY metadata->>'category'
        """)
        
        print("\n📊 Summary by Category:")
        for row in cur.fetchall():
            print(f"   {row[0]:<20} {row[2]} docs, {row[1]} chunks")
    
    conn.close()
    
    print("\n" + "=" * 60)
    print("✨ Knowledge Base Embedding Complete!")
    print("=" * 60)

if __name__ == "__main__":
    process_knowledge_base()