# 🚀 dBank Data Layer - Quick Start Guide

**Total Time: ~30 minutes**

## Prerequisites

- Python 3.9+ installed
- Docker and Docker Compose installed
- Git installed
- Basic terminal/command line knowledge

---

## Step 1: Create Project Structure (2 min)

```bash
# Create main project directory
mkdir dbank-copilot
cd dbank-copilot

# Create subdirectories
mkdir -p data_layer/{sql,scripts,sample_data}
mkdir -p knowledge_base
mkdir -p mcp_server
mkdir -p fastapi_app
```

---

## Step 2: Set Up Files (5 min)

Create these files from the artifacts I provided:

### 1. In project root:
- `docker-compose.yml` (Database setup)
- `.env` (copy from `.env.example` and fill in values)
- `requirements.txt` (Python dependencies)

### 2. In `data_layer/sql/`:
- `01_create_schema.sql` (Database schema)

### 3. In `data_layer/scripts/`:
- `generate_sample_data.py` (Data generator)
- `load_data_to_postgres.py` (Data loader)
- `verify_data.py` (Verification script)

**Your structure should look like:**
```
dbank-copilot/
├── docker-compose.yml
├── .env
├── requirements.txt
├── data_layer/
│   ├── sql/
│   │   └── 01_create_schema.sql
│   ├── scripts/
│   │   ├── generate_sample_data.py
│   │   ├── load_data_to_postgres.py
│   │   └── verify_data.py
│   └── sample_data/        # Will be auto-created
├── knowledge_base/          # For later
├── mcp_server/              # For later
└── fastapi_app/             # For later
```

---

## Step 3: Start PostgreSQL Database (3 min)

```bash
# Start the database
docker-compose up -d

# Check it's running
docker-compose ps

# You should see:
# dbank_postgres   running   0.0.0.0:5433->5433/tcp
```

**Troubleshooting:**
- If port 5432 is already in use, change it in `docker-compose.yml` to `5433:5432`
- Update `.env` file with `DB_PORT=5433`

---

## Step 4: Create Database Schema (2 min)

```bash
# Method 1: Using docker exec (recommended)
docker exec -i dbank_postgres psql -U dbank_user -d dbank < data_layer/sql/01_create_schema.sql

# powershell
Get-Content data_layer/sql/01_create_schema.sql | docker exec -i dbank_postgres psql -U dbank_user -d dbank

# Method 2: Using psql directly (if installed locally)
psql -h localhost -U dbank_user -d dbank -f data_layer/sql/01_create_schema.sql
# Password: dbank_pass_2025
```

**Expected output:**
```
CREATE EXTENSION
CREATE SCHEMA
CREATE SCHEMA
CREATE SCHEMA
CREATE TABLE
CREATE TABLE
... (many more tables)
CREATE INDEX
COMMENT
```

---

## Step 5: Install Python Dependencies (3 min)

```bash
# Create virtual environment (recommended)
python3.11 -m venv .venv

# Activate it
# On Mac/Linux:
source .venv/bin/activate

# On Windows:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.venv\Scripts\activate

# Install packages
pip install -r requirements.txt
```

---

## Step 6: Generate Sample Data (2 min)

```bash
python data_layer/scripts/generate_sample_data.py
```

**Expected output:**
```
🏦 Generating dBank Sample Data...
============================================================

📦 Generating Products...
✅ Generated 8 products

👥 Generating 10000 Customers...
✅ Generated 10000 customers

🎫 Generating Ticket Categories and Root Causes...
✅ Generated 7 categories and 8 root causes

🎟️  Generating 15000 Tickets...
✅ Generated 15453 tickets
   📈 Tickets with v1.2: 2876

💰 Generating Customer Product Holdings...
✅ Generated 14567 product holdings

🔐 Generating Login Access Data...
✅ Generated 234567 login records

📅 Generating Time Dimension...
✅ Generated 1095 time dimension records

============================================================
✨ Data Generation Complete!
📁 All CSV files saved to: sample_data/
```

**Check the files:**
```bash
ls data_layer/sample_data
# You should see 8 CSV files
```

---

## Step 7: Load Data into PostgreSQL (5 min)

```bash
python data_layer/scripts/load_data_to_postgres.py
```

**Expected output:**
```
============================================================
🏦 dBank Data Loader
============================================================
✅ Connected to PostgreSQL database

📅 Loading Time Dimension...
✅ Loaded 1095 time dimension records

👥 Loading Customers...
✅ Loaded 10000 customers

📦 Loading Products...
✅ Loaded 8 products

... (more loading messages)

============================================================
✨ Data Loading Complete!
============================================================

📊 Database Summary:
   Customers                 10,000
   Products                       8
   Tickets                   15,453
   Logins                   234,567
   Product Holdings          14,567
```

---

## Step 8: Verify Everything Works (3 min)

```bash
# Still in data_layer/scripts directory
python verify_data.py
```

This will run several test queries to ensure:
- ✅ All tables have data
- ✅ Can query top root causes
- ✅ Can detect v1.2 spike
- ✅ Can find churned customers
- ✅ Data quality is good

---

## Step 9: Explore the Data (Optional)

### Connect using any PostgreSQL client:

**Connection details:**
- Host: `localhost`
- Port: `5432`
- Database: `dbank`
- User: `dbank_user`
- Password: `dbank_pass_2025`

### Try some queries:

```sql
-- See all schemas
\dn

-- See all tables
\dt analytics.*

-- Count tickets
SELECT COUNT(*) FROM analytics.fact_tickets;

-- Top products with issues
SELECT 
    p.product_name,
    COUNT(*) as issue_count
FROM analytics.fact_tickets t
JOIN analytics.dim_products p ON t.product_id = p.product_id
GROUP BY p.product_name
ORDER BY issue_count DESC;
```

---

## 🎉 Success!

You now have:
- ✅ PostgreSQL database running
- ✅ Star schema with dimensions and facts
- ✅ 10,000 customers
- ✅ 15,000+ tickets with v1.2 spike
- ✅ 234,000+ login records
- ✅ PII fields ready for masking
- ✅ Data ready for analysis

---

## Next Steps

### 1. **Set up dbt** (for transformations)
   - Create marts for common queries
   - Add data quality tests
   - Build aggregation tables

### 2. **Create Knowledge Base** (5-10 markdown files)
   - Product FAQs
   - Known issues
   - Release notes

### 3. **Build Vector Store** (embed documents)
   - Chunk documents
   - Generate embeddings
   - Store in pgvector

### 4. **Create MCP Server** (tools layer)
   - sql.query tool
   - kb.search tool
   - kpi.top_root_causes tool

### 5. **Build FastAPI RAG System**
   - /ask endpoint
   - LLM integration
   - Tool orchestration

---

## Troubleshooting

### Database won't start
```bash
# Check logs
docker-compose logs postgres

# Restart
docker-compose restart

# Full reset
docker-compose down -v
docker-compose up -d
```

### Can't connect to database
```bash
# Check if running
docker-compose ps

# Test connection
docker exec -it dbank_postgres psql -U dbank_user -d dbank -c "SELECT version();"
```

### Python errors
```bash
# Make sure virtual environment is activated
which python  # Should show path to venv

# Reinstall dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### Data loading fails
```bash
# Check if schema was created
docker exec -it dbank_postgres psql -U dbank_user -d dbank -c "\dt analytics.*"

# If tables don't exist, recreate schema
docker exec -i dbank_postgres psql -U dbank_user -d dbank < data_layer/sql/01_create_schema.sql
```

---

## Useful Commands

```bash
# Stop database
docker-compose stop

# Start database
docker-compose start

# View logs
docker-compose logs -f postgres

# Connect to database
docker exec -it dbank_postgres psql -U dbank_user -d dbank

# Backup database
docker exec dbank_postgres pg_dump -U dbank_user dbank > backup.sql

# Restore database
docker exec -i dbank_postgres psql -U dbank_user -d dbank < backup.sql

# Remove everything (careful!)
docker-compose down -v
```

---

## What We Built

### Database Architecture

```
analytics schema (main data warehouse)
├── Dimensions
│   ├── dim_customers (10K customers with PII)
│   ├── dim_products (8 products)
│   ├── dim_ticket_categories (7 categories)
│   ├── dim_root_causes (8 root causes)
│   └── dim_time (date dimension)
└── Facts
    ├── fact_tickets (15K+ support tickets)
    ├── fact_customer_products (product holdings)
    └── fact_logins (234K+ login events)

vector_store schema (for knowledge base)
└── documents (will store embeddings)

staging schema (raw data)
└── raw_* tables (for ETL)
```

### Key Features

✅ **Star Schema Design** - Optimized for analytics  
✅ **PII Fields** - Ready to be masked (email, phone, national_id)  
✅ **v1.2 Spike** - Simulated bug causing 50% more tickets  
✅ **Churn Data** - 15% of customers haven't logged in 30+ days  
✅ **Rich Dimensions** - Product categories, root causes, time dimension  
✅ **Indexes** - Optimized for query performance  
✅ **pgvector Ready** - Extension enabled for embeddings  

---

## Data Examples

### Sample Customer (with PII)
```sql
customer_uuid: 550e8400-e29b-41d4-a716-446655440000
full_name: สมชาย ใจดี (Somchai Jaidee)
email: somchai.j@example.com
phone: +66-81-234-5678
national_id: 1-2345-67890-12-3  ← Must be masked!
customer_segment: Premium
```

### Sample Ticket
```sql
ticket_number: TKT-001234
root_cause: App Version Bug (v1.2)
app_version: v1.2
created_date: 2024-08-20 (after v1.2 release)
status: Open
product: Digital Saving
```

### Sample Root Cause Analysis
```
Top 5 Root Causes (Last 30 Days):
1. App Version Bug (v1.2) - 32% (45% open)
2. Database Timeout - 18% (28% open)
3. API Gateway Error - 15% (22% open)
4. Third Party Gateway Down - 12% (50% open)
5. Network Connectivity - 10% (15% open)
```

---

## 📚 Additional Resources

- **PostgreSQL Docs**: https://www.postgresql.org/docs/
- **pgvector Guide**: https://github.com/pgvector/pgvector
- **Faker Library**: https://faker.readthedocs.io/
- **dbt Documentation**: https://docs.getdbt.com/

---

## Questions?

If you get stuck:
1. Check the troubleshooting section above
2. Review the logs: `docker-compose logs postgres`
3. Verify your `.env` file matches the database settings
4. Make sure all files are in the correct directories

---

**🎯 You're now ready to move to the next phase: dbt transformations!**
