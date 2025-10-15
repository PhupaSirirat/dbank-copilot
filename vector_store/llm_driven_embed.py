"""
Embed Knowledge Base Documents into pgvector with LLM-Driven Chunking
Uses OpenAI GPT for intelligent semantic chunking
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
KNOWLEDGE_BASE_DIR = "knowledge_base/kb_files"
TARGET_CHUNK_SIZE = 800  # target tokens per chunk
MAX_CHUNK_SIZE = 1200  # maximum tokens per chunk
EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "openai")
CHUNKING_METHOD = os.getenv("CHUNKING_METHOD", "llm")  # "llm" or "simple"

# Database connection
DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', 'localhost'),
    'port': os.getenv('POSTGRES_PORT', '5433'),
    'database': os.getenv('POSTGRES_DB', 'dbank'),
    'user': os.getenv('POSTGRES_USER', 'dbank_user'),
    'password': os.getenv('POSTGRES_PASSWORD', 'dbank_pass_2025')
}

# Initialize OpenAI client
from openai import OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Initialize embedding model
if EMBEDDING_PROVIDER == "openai":
    EMBEDDING_MODEL = "text-embedding-3-small"
    EMBEDDING_DIM = 1536
else:
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer('all-MiniLM-L6-v2')
    EMBEDDING_DIM = 384

print(f"🚀 Using {EMBEDDING_PROVIDER} embeddings (dimension: {EMBEDDING_DIM})")
print(f"🧠 Using {CHUNKING_METHOD} chunking method")

# =====================================================
# LLM-Driven Chunking Functions
# =====================================================

def count_tokens(text: str) -> int:
    """Count tokens in text"""
    encoding = tiktoken.get_encoding("cl100k_base")
    return len(encoding.encode(text))

def chunk_text_llm(text: str, target_size: int = TARGET_CHUNK_SIZE) -> List[Dict]:
    """
    Use LLM to intelligently chunk text based on semantic boundaries
    Returns list of dicts with 'content', 'title', and 'token_count'
    """
    total_tokens = count_tokens(text)
    
    # If document is small enough, return as single chunk
    if total_tokens <= MAX_CHUNK_SIZE:
        return [{
            'content': text.strip(),
            'title': 'Full Document',
            'token_count': total_tokens
        }]
    
    # Estimate number of chunks needed
    estimated_chunks = max(2, (total_tokens // target_size) + 1)
    
    # Prepare prompt for LLM
    system_prompt = """You are an expert document chunking assistant. Your task is to split documents into semantically coherent chunks for a RAG system.

Rules:
1. Each chunk should be self-contained and meaningful
2. Keep related information together (e.g., a question with its answer)
3. Respect document structure (sections, subsections)
4. Target {target_size} tokens per chunk, but prioritize semantic coherence
5. Include relevant context/headers in each chunk when needed
6. Never split mid-sentence or mid-paragraph
7. For lists or steps, keep them together when possible

Output JSON format:
{{
  "chunks": [
    {{
      "title": "Brief descriptive title for this chunk",
      "content": "The actual chunk content with any necessary context"
    }}
  ]
}}""".format(target_size=target_size)

    user_prompt = f"""Split the following document into approximately {estimated_chunks} semantically coherent chunks.

Target: ~{target_size} tokens per chunk (but prioritize semantic boundaries over exact token counts)

Document:
---
{text}
---

Return ONLY valid JSON with no additional text."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Fast and cost-effective for chunking
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0,
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        chunks = result.get('chunks', [])
        
        # Add token counts and validate
        validated_chunks = []
        for chunk in chunks:
            content = chunk.get('content', '').strip()
            if len(content) < 50:  # Skip very short chunks
                continue
                
            token_count = count_tokens(content)
            validated_chunks.append({
                'content': content,
                'title': chunk.get('title', 'Untitled Section'),
                'token_count': token_count
            })
        
        # If chunking resulted in too few or no chunks, fall back to simple chunking
        if len(validated_chunks) == 0:
            print("   ⚠️  LLM chunking failed, falling back to simple chunking")
            return chunk_text_simple(text, target_size)
        
        return validated_chunks
        
    except Exception as e:
        print(f"   ⚠️  LLM chunking error: {e}, falling back to simple chunking")
        return chunk_text_simple(text, target_size)

def chunk_text_simple(text: str, chunk_size: int = TARGET_CHUNK_SIZE, overlap: int = 100) -> List[Dict]:
    """
    Simple token-based chunking as fallback
    Returns same format as LLM chunking for consistency
    """
    encoding = tiktoken.get_encoding("cl100k_base")
    tokens = encoding.encode(text)
    n_tokens = len(tokens)
    
    chunks = []
    start = 0
    chunk_num = 0
    
    while start < n_tokens:
        end = min(start + chunk_size, n_tokens)
        chunk_tokens = tokens[start:end]
        chunk_str = encoding.decode(chunk_tokens).strip()
        
        if chunk_str:
            chunks.append({
                'content': chunk_str,
                'title': f'Chunk {chunk_num + 1}',
                'token_count': len(chunk_tokens)
            })
            chunk_num += 1
        
        # Move forward with overlap
        step = end - start
        next_start = end - min(overlap, step // 2)
        start = max(next_start, start + 1)
    
    return chunks

def chunk_text(text: str) -> List[Dict]:
    """
    Main chunking function - chooses method based on configuration
    """
    if CHUNKING_METHOD == "llm":
        return chunk_text_llm(text, TARGET_CHUNK_SIZE)
    else:
        return chunk_text_simple(text, TARGET_CHUNK_SIZE)

# =====================================================
# Document Processing Functions
# =====================================================

def read_markdown_file(filepath: str) -> str:
    """Read markdown file content"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()

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
    total_tokens = 0
    
    # Process each file
    for filepath in md_files:
        print(f"\n🔍 Processing: {filepath}")
        
        # Skip README
        if filepath.endswith('README.md'):
            continue
        
        try:
            # Read content
            content = read_markdown_file(filepath)
            
            # Extract metadata
            metadata = extract_metadata(filepath, content)
            
            # Chunk the document (now returns dict with metadata)
            chunks = chunk_text(content)
            
        except Exception as e:
            print(f"   ⚠️  Error processing file: {e}")
            continue
        
        print(f"   📝 {metadata['title']}")
        print(f"   📊 Created {len(chunks)} semantic chunks")
        
        # Show chunk details
        for i, chunk_info in enumerate(chunks):
            print(f"      └─ Chunk {i+1}: '{chunk_info['title']}' ({chunk_info['token_count']} tokens)")
        
        # Generate embeddings for each chunk
        for idx, chunk_info in enumerate(tqdm(chunks, desc="  Embedding", leave=False)):
            try:
                # Get embedding
                embedding = get_embedding(chunk_info['content'])
                
                # Prepare enhanced metadata
                chunk_metadata = {
                    **metadata,
                    'chunk_index': idx,
                    'chunk_title': chunk_info['title'],
                    'chunk_tokens': chunk_info['token_count'],
                    'chunking_method': CHUNKING_METHOD
                }
                
                all_embeddings.append((
                    metadata['title'],
                    'markdown',
                    idx,
                    chunk_info['content'],
                    embedding,
                    chunk_metadata
                ))
                
                total_chunks += 1
                total_tokens += chunk_info['token_count']
                
            except Exception as e:
                print(f"   ⚠️  Error embedding chunk {idx}: {e}")
                continue
    
    # Insert all embeddings
    print(f"\n💾 Inserting {total_chunks} chunks into database...")
    insert_embeddings(conn, all_embeddings)
    
    avg_tokens = total_tokens / total_chunks if total_chunks > 0 else 0
    print(f"✅ Inserted {total_chunks} chunks (avg {avg_tokens:.0f} tokens/chunk)")
    
    # Create index for faster search
    print("\n🔨 Creating vector index...")
    with conn.cursor() as cur:
        cur.execute("DROP INDEX IF EXISTS vector_store.documents_embedding_idx")
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
                COUNT(DISTINCT document_name) as doc_count,
                AVG((metadata->>'chunk_tokens')::int) as avg_tokens
            FROM vector_store.documents
            GROUP BY metadata->>'category'
        """)
        
        print("\n📊 Summary by Category:")
        for row in cur.fetchall():
            print(f"   {row[0]:<20} {row[2]} docs, {row[1]} chunks (avg {row[3]:.0f} tokens)")
    
    conn.close()
    
    print("\n" + "=" * 60)
    print("✨ Knowledge Base Embedding Complete!")
    print("=" * 60)

if __name__ == "__main__":
    process_knowledge_base()