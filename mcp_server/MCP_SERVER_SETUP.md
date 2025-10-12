# 🔧 MCP Server Setup Guide

**Time Required:** ~30 minutes

---

## 🎯 What We Built

An MCP (Model Context Protocol) server with **3 production-ready tools**:

1. **`sql.query`** - Execute read-only SQL with PII masking
2. **`kb.search`** - Semantic search over knowledge base  
3. **`kpi.top_root_causes`** - Pre-aggregated KPIs

**Safety Features:**
- ✅ Read-only database access (no writes)
- ✅ PII auto-masking (emails, phones, IDs)
- ✅ SQL injection protection
- ✅ Tool call logging (audit trail)
- ✅ Error handling & validation

---

## 📁 File Structure

```
mcp_server/
├── server.py                  # Main FastAPI MCP server
├── tools/
│   ├── __init__.py
│   ├── sql_query.py           # SQL execution tool
│   ├── kb_search.py           # Knowledge base search
│   └── kpi_tools.py           # KPI aggregation
├── utils/
│   ├── __init__.py
│   ├── pii_masking.py         # PII protection
│   ├── sql_validator.py       # SQL safety checks
│   └── logger.py              # Audit logging
└── logs/                      # Tool call logs
```

---

## 🚀 Quick Start

### **Step 1: Create Files (5 min)**

```powershell
# Create directory structure
mkdir mcp_server\tools
mkdir mcp_server\utils
mkdir mcp_server\logs

# Create __init__.py files
New-Item mcp_server\tools\__init__.py
New-Item mcp_server\utils\__init__.py
New-Item mcp_server\__init__.py
```

Copy all 7 artifact files into the correct locations.

### **Step 2: Install Dependencies (already done)**

```powershell
pip install -r requirements.txt
```

### **Step 3: Start the Server**

```powershell
cd mcp_server
python server.py
```

**Expected output:**
```
============================================================
🚀 Starting dBank MCP Server
============================================================

📍 Server: http://localhost:8000
📚 Docs: http://localhost:8000/docs
🔧 Tools: 3

Available Tools:
  - sql.query
  - kb.search
  - kpi.top_root_causes

============================================================
```

---

## 🧪 Testing the Server

### **Test 1: Check Health**

```powershell
# Open browser to:
http://localhost:8000

# Should return:
{
  "service": "dBank MCP Server",
  "status": "operational",
  "version": "1.0.0"
}
```

### **Test 2: List Tools**

```powershell
# Browser or curl:
http://localhost:8000/tools/list

# Returns all 3 tools with descriptions
```

### **Test 3: Interactive API Docs**

```powershell
# Open browser to:
http://localhost:8000/docs

# Try the tools directly in the Swagger UI!
```

---

## 🔧 Testing Each Tool

### **Tool 1: sql.query**

**Test via PowerShell:**

```powershell
$body = @{
    tool = "sql.query"
    parameters = @{
        query = "SELECT COUNT(*) as total FROM analytics.dim_customers"
        mask_pii = $true
    }
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/tools/call" -Method Post -Body $body -ContentType "application/json"
```

**Test via API Docs:**
1. Go to http://localhost:8000/docs
2. Click on `POST /tools/call`
3. Click "Try it out"
4. Paste this JSON:
```json
{
  "tool": "sql.query",
  "parameters": {
    "query": "SELECT customer_uuid, email, phone FROM analytics.dim_customers LIMIT 3",
    "mask_pii": true
  },
  "user_id": "test_user"
}
```
5. Click "Execute"
6. See masked results!

**Test PII Masking:**
```json
{
  "tool": "sql.query",
  "parameters": {
    "query": "SELECT full_name, email, phone, national_id FROM analytics.dim_customers LIMIT 5",
    "mask_pii": true
  }
}
```

**Test Safety (should fail):**
```json
{
  "tool": "sql.query",
  "parameters": {
    "query": "DELETE FROM analytics.dim_customers"
  }
}
```
Should return error: "Only SELECT queries allowed"

---

### **Tool 2: kb.search**

```json
{
  "tool": "kb.search",
  "parameters": {
    "query": "How do I apply for a loan?",
    "top_k": 3,
    "category": "product_guide"
  }
}
```

**More tests:**
```json
{
  "tool": "kb.search",
  "parameters": {
    "query": "v1.2 app crashes",
    "top_k": 5,
    "min_similarity": 0.7
  }
}
```

---

### **Tool 3: kpi.top_root_causes**

```json
{
  "tool": "kpi.top_root_causes",
  "parameters": {
    "year": 2025,
    "month": 10,
    "top_n": 5
  }
}
```

**Get all months:**
```json
{
  "tool": "kpi.top_root_causes",
  "parameters": {
    "year": 2025,
    "top_n": 10
  }
}
```

---

## 📊 View Logs

**Get recent tool calls:**
```
http://localhost:8000/logs/recent?limit=20
```

**Check database logs:**
```powershell
docker exec -it dbank_postgres psql -U dbank_user -d dbank
```

```sql
SELECT 
    tool_name,
    user_id,
    execution_time_ms,
    status,
    created_at
FROM analytics.tool_call_logs
ORDER BY created_at DESC
LIMIT 10;
```

---

## 🧪 Unit Tests

Each tool file can be tested individually:

```powershell
# Test SQL query tool
cd mcp_server\tools
python sql_query.py

# Test KB search
python kb_search.py

# Test KPI tools
python kpi_tools.py

# Test PII masking
cd ..\utils
python pii_masking.py

# Test SQL validator
python sql_validator.py

# Test logger
python logger.py
```

---

## 🔒 Security Features Verified

### **1. Read-Only Protection**

```json
{
  "tool": "sql.query",
  "parameters": {
    "query": "UPDATE analytics.dim_customers SET email = 'hacked'"
  }
}
```
**Result:** ❌ Blocked - "Only SELECT queries allowed"

### **2. SQL Injection Protection**

```json
{
  "tool": "sql.query",
  "parameters": {
    "query": "SELECT * FROM users; DROP TABLE important;"
  }
}
```
**Result:** ❌ Blocked - "Multiple statements not allowed"

### **3. PII Masking**

Query with PII fields:
- `email: john.doe@example.com` → `jo***@example.com`
- `phone: +66-81-234-5678` → `+66****78`
- `national_id: 1-2345-67890` → `1-****-****`

### **4. Audit Logging**

Every tool call is logged with:
- Tool name
- Parameters
- User ID
- Execution time
- Success/error status
- Timestamp

---

## 📈 Expected Performance

| Tool | Avg Response Time | Notes |
|------|-------------------|-------|
| sql.query | 50-200ms | Depends on query complexity |
| kb.search | 100-300ms | Vector search + DB lookup |
| kpi.top_root_causes | 20-100ms | Pre-aggregated, very fast |

---

## 🐛 Troubleshooting

### **Server won't start**
```powershell
# Check if port 8000 is in use
netstat -ano | findstr :8000

# Kill process if needed
taskkill /PID <PID> /F

# Or use different port
$env:MCP_SERVER_PORT=8001
python server.py
```

### **"Module not found" errors**
```powershell
# Make sure you're in the right directory
cd mcp_server

# Check Python path
python -c "import sys; print(sys.path)"

# Add parent directory if needed
$env:PYTHONPATH="E:\Github Repo\dbank-copilot"
```

### **Database connection errors**
```powershell
# Check PostgreSQL is running
docker ps | findstr dbank

# Test connection
docker exec -it dbank_postgres psql -U dbank_user -d dbank -c "SELECT 1"
```

### **Vector search not working**
```powershell
# Make sure embeddings were generated
docker exec -it dbank_postgres psql -U dbank_user -d dbank

SELECT COUNT(*) FROM vector_store.documents;
# Should return ~87
```

---

## 🎯 Integration Testing

### **Full Workflow Test**

1. **Start server:** `python server.py`
2. **Search KB:** Find v1.2 issues
3. **Query SQL:** Get affected customers
4. **Get KPIs:** Top root causes for v1.2 period
5. **Check logs:** Verify all calls logged

**Test Script:**

```powershell
# 1. Search for v1.2 issues
$search = @{
    tool = "kb.search"
    parameters = @{
        query = "v1.2 bugs and crashes"
        top_k = 3
    }
} | ConvertTo-Json

$result1 = Invoke-RestMethod -Uri "http://localhost:8000/tools/call" -Method Post -Body $search -ContentType "application/json"
Write-Host "Found $($result1.result.Count) KB results"

# 2. Get v1.2 KPIs
$kpi = @{
    tool = "kpi.top_root_causes"
    parameters = @{
        year = 2024
        month = 8
        top_n = 5
    }
} | ConvertTo-Json

$result2 = Invoke-RestMethod -Uri "http://localhost:8000/tools/call" -Method Post -Body $kpi -ContentType "application/json"
Write-Host "Found $($result2.result.Count) root causes"

# 3. Check logs
$logs = Invoke-RestMethod -Uri "http://localhost:8000/logs/recent?limit=5"
Write-Host "Recent calls: $($logs.logs.Count)"
```

---

## ✅ Success Checklist

After setup, verify:

- [ ] Server starts without errors
- [ ] `/tools/list` returns 3 tools
- [ ] sql.query executes SELECT successfully
- [ ] sql.query blocks DELETE/UPDATE
- [ ] PII masking works (emails/phones masked)
- [ ] kb.search returns relevant results
- [ ] kpi.top_root_causes returns aggregated data
- [ ] Tool calls are logged to database
- [ ] API docs work at `/docs`
- [ ] All unit tests pass

---

## 📊 Production Readiness

Your MCP server is production-ready with:

✅ **Security:** Read-only DB, SQL injection protection, PII masking  
✅ **Reliability:** Error handling, validation, timeouts  
✅ **Observability:** Audit logs, execution times, success rates  
✅ **Performance:** Fast queries, efficient vector search  
✅ **Documentation:** OpenAPI/Swagger auto-docs  

---

## 🎯 Next Steps

1. ✅ Data Layer Complete
2. ✅ dbt Transformations Complete
3. ✅ Knowledge Base Complete
4. ✅ Vector Store Complete
5. ✅ **MCP Server Complete** ← You are here!
6. 🔜 **FastAPI RAG** - Connect LLM to MCP server
7. 🔜 UI - Chat interface

---

**Your MCP server is ready for the RAG system!** 🎉