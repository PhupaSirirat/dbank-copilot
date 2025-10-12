# 🔄 Vector Store Setup Guide

**Time Required:** ~45 minutes

---

## 🎯 What We're Building

A semantic search system that:
1. Reads markdown files from `knowledge_base/`
2. Splits them into chunks (~500 tokens each)
3. Generates vector embeddings (AI representation)
4. Stores in PostgreSQL with pgvector
5. Enables semantic search (find by meaning, not just keywords)

---

## 📦 Step 1: Install Dependencies (5 min)

```powershell
# Install new packages
pip install -r requirements.txt
```

**Packages added:**
- `langchain` - Document processing framework
- `openai` - OpenAI API (if using OpenAI embeddings)
- `sentence-transformers` - Local embeddings (if using local)
- `tiktoken` - Token counting for OpenAI
- `pypdf` - PDF support (future)
- `markdown` - Markdown processing

---

## 🔑 Step 2: Choose Embedding Provider

### **Option A: OpenAI (Recommended)**

**Pros:**
- Best quality semantic search
- Fast API calls
- 1536-dimensional embeddings

**Cons:**
- Requires API key
- Costs ~$0.02 per 1M tokens (very cheap!)

**Setup:**
1. Get API key from https://platform.openai.com/api-keys
2. Update `.env`:
   ```bash
   EMBEDDING_PROVIDER=openai
   OPENAI_API_KEY=sk-your-api-key-here
   ```

**Estimated Cost:**
- ~9 documents × 3,000 words each = ~27,000 words
- ~36,000 tokens
- Cost: **$0.0004** (less than a cent!)

### **Option B: Sentence-Transformers (Free)**

**Pros:**
- Completely free
- Runs locally
- No API key needed
- Good quality

**Cons:**
- Slower (processes on your machine)
- 384-dimensional embeddings (vs 1536)
- Requires ~500MB model download

**Setup:**
1. Update `.env`:
   ```bash
   EMBEDDING_PROVIDER=local
   ```

**First run will download model automatically** (~500MB, one-time)

---

## 🗄️ Step 3: Verify Database Schema (1 min)

Check that pgvector extension and table exist:

```powershell
docker exec -it dbank_postgres psql -U dbank_user -d dbank
```

```sql
-- Check extension
SELECT * FROM pg_extension WHERE extname = 'vector';

-- Check table
\d vector_store.documents

-- Should show:
-- embedding | vector(1536)

-- Exit
\q
```

If table doesn't exist, run:
```sql
CREATE TABLE IF NOT EXISTS vector_store.documents (
    doc_id SERIAL PRIMARY KEY,
    document_name VARCHAR(500),
    document_type VARCHAR(50),
    chunk_index INT,
    content TEXT,
    embedding vector(1536),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 📝 Step 4: Create Scripts (5 min)

Create folder structure:

```powershell
mkdir vector_store
cd vector_store
```

Create these files from the artifacts:
1. `embed_knowledge_base.py` - Document embedder
2. `vector_search.py` - Semantic search

**File locations:**
```
dbank-copilot/
├── vector_store/
│   ├── embed_knowledge_base.py
│   └── vector_search.py
├── knowledge_base/kb_files     # Your docs
└── .env                        # Config
```

---

## 🚀 Step 5: Generate Embeddings (10 min)

```powershell
# Run the embedder (project root)
python vector_store/embed_knowledge_base.py
```

**Expected output:**
```
============================================================
📚 Knowledge Base Embedding Process
============================================================
🚀 Using openai embeddings (dimension: 1536)
✅ Connected to database
🗑️  Cleared existing documents

📄 Found 9 markdown files

Processing documents: 100%
📝 Digital Saving Product Guide
   Chunks: 8

📝 Digital Lending Product Guide
   Chunks: 10

📝 v1.2 Release Notes
   Chunks: 5
   
...

💾 Inserting 87 chunks into database...
✅ Inserted 87 document chunks

🔨 Creating vector index...
✅ Vector index created

📊 Summary by Category:
   product_guide        3 docs, 25 chunks
   support_doc          3 docs, 42 chunks
   reference_doc        3 docs, 20 chunks

============================================================
✨ Knowledge Base Embedding Complete!
============================================================
```

**What just happened:**
- ✅ Read 9 markdown files
- ✅ Split into ~87 chunks
- ✅ Generated embeddings for each
- ✅ Stored in PostgreSQL
- ✅ Created search index

---

## 🔍 Step 6: Test Semantic Search (10 min)

```powershell
python vector_store/vector_search.py
```

**Try these searches:**

### **Query 1: "How do I apply for a loan?"**
Should return: Digital Lending Product Guide chunks

### **Query 2: "v1.2 app crashes"**
Should return: v1.2 Release Notes (marked as CRITICAL)

### **Query 3: "Interest calculation problem"**
Should return: Known issues from v1.2 notes

### **Query 4: "What are KYC requirements?"**
Should return: Customer Policies chunks

---

## 📊 Step 7: Verify in Database (5 min)

Check what was stored:

```powershell
docker exec -it dbank_postgres psql -U dbank_user -d dbank
```

```sql
-- Count documents
SELECT COUNT(*) FROM vector_store.documents;
-- Should show ~87

-- See documents by category
SELECT 
    metadata->>'category' as category,
    COUNT(*) as chunks,
    COUNT(DISTINCT document_name) as docs
FROM vector_store.documents
GROUP BY metadata->>'category';

-- Sample a document
SELECT 
    document_name,
    chunk_index,
    LEFT(content, 100) as preview,
    metadata->>'is_critical' as critical
FROM vector_store.documents
LIMIT 5;

-- Find v1.2 related docs
SELECT DISTINCT document_name
FROM vector_store.documents
WHERE content ILIKE '%v1.2%';
```

---

## 🧪 Step 8: Advanced Search Examples

### **Python API:**

```python
from vector_search import search_knowledge_base

# Basic search
results = search_knowledge_base("loan application process", top_k=3)

# Filter by category
results = search_knowledge_base(
    "product features",
    filter_category="product_guide",
    top_k=5
)

# Adjust similarity threshold
results = search_knowledge_base(
    "troubleshooting",
    min_similarity=0.8,  # Higher = more strict
    top_k=10
)
```

### **SQL Query:**

```sql
-- Direct vector search
WITH query_embedding AS (
    SELECT embedding 
    FROM vector_store.documents 
    WHERE document_name = 'Digital Saving Product Guide'
    LIMIT 1
)
SELECT 
    document_name,
    content,
    1 - (embedding <=> (SELECT embedding FROM query_embedding)) as similarity
FROM vector_store.documents
WHERE 1 - (embedding <=> (SELECT embedding FROM query_embedding)) > 0.7
ORDER BY similarity DESC
LIMIT 5;
```

---

## 🎯 What Makes Semantic Search Powerful

**Traditional Keyword Search:**
```
Query: "loan application"
Finds: Exact matches for "loan" AND "application"
Misses: "How to apply for credit", "borrowing process"
```

**Semantic Search:**
```
Query: "loan application"
Finds: 
  - "How to apply for a loan" ✓
  - "Credit application process" ✓
  - "Steps to borrow money" ✓
  - "Loan eligibility requirements" ✓
```

Understands MEANING, not just words!

---

## 🐛 Troubleshooting

### **Error: "No module named 'openai'"**
```powershell
pip install openai
```

### **Error: "Invalid API key"**
Check `.env` file:
```bash
OPENAI_API_KEY=sk-proj-...  # Must start with sk-
```

### **Error: "vector dimension mismatch"**
The script automatically fixes this, but if manual fix needed:
```sql
ALTER TABLE vector_store.documents 
ALTER COLUMN embedding TYPE vector(1536);
```

For local embeddings (384 dimensions):
```sql
ALTER TABLE vector_store.documents 
ALTER COLUMN embedding TYPE vector(384);
```

### **Slow embedding generation (local)**
Normal! Local processing is slower:
- OpenAI: ~10 seconds total
- Local: ~2-5 minutes total

### **No search results found**
Lower the similarity threshold:
```python
results = search_knowledge_base(query, min_similarity=0.5)  # Lower = more permissive
```

---

## 📈 Performance Metrics

**With OpenAI embeddings:**
- Embedding generation: ~10-20 seconds
- Search query: <100ms
- Accuracy: Excellent

**With local embeddings:**
- Embedding generation: ~2-5 minutes (first run)
- Search query: <100ms
- Accuracy: Good

**Database stats:**
```sql
SELECT 
    pg_size_pretty(pg_total_relation_size('vector_store.documents')) as table_size,
    COUNT(*) as total_chunks
FROM vector_store.documents;
```

---

## ✅ Success Checklist

After completing:

- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Embedding provider chosen (OpenAI or local)
- [ ] `.env` configured with API key (if OpenAI)
- [ ] Scripts created (`embed_knowledge_base.py`, `vector_search.py`)
- [ ] Embeddings generated successfully (~87 chunks)
- [ ] Vector index created
- [ ] Search returns relevant results
- [ ] Verified in PostgreSQL (`SELECT COUNT(*)...`)

---

## 🎯 Next Steps

After vector store is ready:

1. ✅ Data Layer Complete
2. ✅ dbt Transformations Complete
3. ✅ Knowledge Base Complete
4. ✅ Vector Store Complete
5. 🔜 **MCP Server** - Build 3 tools (sql.query, kb.search, kpi.top_root_causes)
6. 🔜 FastAPI RAG - Connect everything
7. 🔜 UI - Chat interface

---

## 💡 Tips

1. **Update documents?** Just run `embed_knowledge_base.py` again
2. **Add new docs?** Drop them in `knowledge_base/` and re-embed
3. **Cost tracking (OpenAI)?** Check usage at https://platform.openai.com/usage
4. **Want better search?** Adjust `CHUNK_SIZE` and `CHUNK_OVERLAP` in the script

---

**Your knowledge base is now searchable! 🎉**