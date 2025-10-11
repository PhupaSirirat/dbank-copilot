# 🏦 dBank Data Layer

Complete data foundation for the Deep Insights Copilot system.

## 📋 Overview

This data layer provides:
- **Star schema data warehouse** in PostgreSQL
- **10,000 customers** with realistic PII data
- **15,000+ support tickets** with simulated v1.2 spike
- **234,000+ login records** for churn analysis
- **8 products** across Savings, Lending, Investment, Insurance
- **pgvector support** for semantic search

---

## 🚀 Quick Setup

### Option 1: Automated Setup (Recommended)

**Mac/Linux:**
```bash
chmod +x setup.sh
./setup.sh
```

**Windows:**
```bash
setup.bat
```

### Option 2: Manual Setup

See [QUICKSTART.md](QUICKSTART.md) for detailed step-by-step instructions.

---

## 📊 Database Schema

### Analytics Schema (Main Warehouse)

#### Dimension Tables
- `dim_customers` - Customer master data with PII fields
- `dim_products` - Banking products (Savings, Lending, etc.)
- `dim_ticket_categories` - Support ticket categories
- `dim_root_causes` - Issue root causes
- `dim_time` - Date dimension for time-based analysis

#### Fact Tables
- `fact_tickets` - Support ticket transactions
- `fact_customer_products` - Product holdings
- `fact_logins` - Login access logs

### Vector Store Schema
- `documents` - Knowledge base with embeddings (pgvector)

### Staging Schema
- `raw_*` tables for ETL processes

---

## 🎯 Key Features

### 1. Realistic Data Simulation

**v1.2 App Release Spike:**
- Release date: August 15, 2024
- 50% increase in ticket volume
- 40% of tickets related to app bug
- Affects Digital Saving and Digital Lending products

**Customer Churn:**
- 15% of customers haven't logged in 30+ days
- Distributed across customer segments
- Ready for churn prediction models

**PII Fields (for masking):**
- `full_name` - Customer names
- `email` - Email addresses
- `phone` - Phone numbers
- `national_id` - National ID numbers

### 2. Query Performance

All tables have appropriate indexes:
```sql
-- Ticket analysis
CREATE INDEX idx_tickets_created_date ON fact_tickets(created_date);
CREATE INDEX idx_tickets_app_version ON fact_tickets(app_version);
CREATE INDEX idx_tickets_status ON fact_tickets(ticket_status);

-- Customer analysis
CREATE INDEX idx_logins_customer ON fact_logins(customer_id);
CREATE INDEX idx_logins_date ON fact_logins(login_date);
```

### 3. Data Quality

Built-in data integrity:
- Foreign key constraints
- Not-null constraints on critical fields
- Unique constraints on business keys
- Date validation rules

---

## 📈 Sample Queries

### Top 5 Root Causes (Requirement 1)

```sql
SELECT 
    rc.root_cause_name,
    tc.category_name,
    COUNT(*) as ticket_count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentage,
    SUM(CASE WHEN t.ticket_status = 'Open' THEN 1 ELSE 0 END) as open_tickets,
    ROUND(SUM(CASE WHEN t.ticket_status = 'Open' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as pct_open
FROM analytics.fact_tickets t
JOIN analytics.dim_root_causes rc ON t.root_cause_id = rc.root_cause_id
JOIN analytics.dim_ticket_categories tc ON t.category_id = tc.category_id
WHERE t.created_date >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY rc.root_cause_name, tc.category_name
ORDER BY ticket_count DESC
LIMIT 5;
```

### Detect v1.2 Spike (Requirement 2)

```sql
WITH daily_tickets AS (
    SELECT 
        created_date,
        app_version,
        COUNT(*) as ticket_count,
        AVG(COUNT(*)) OVER (
            ORDER BY created_date 
            ROWS BETWEEN 7 PRECEDING AND 1 PRECEDING
        ) as avg_tickets_7d
    FROM analytics.fact_tickets
    WHERE created_date >= '2024-08-01'
    GROUP BY created_date, app_version
)
SELECT 
    created_date,
    app_version,
    ticket_count,
    ROUND(avg_tickets_7d, 2) as baseline,
    CASE 
        WHEN ticket_count > avg_tickets_7d * 1.5 THEN 'ANOMALY'
        ELSE 'NORMAL'
    END as status,
    STRING_AGG(DISTINCT p.product_type, ', ') as affected_products
FROM daily_tickets dt
JOIN analytics.fact_tickets t ON dt.created_date = t.created_date 
    AND dt.app_version = t.app_version
JOIN analytics.dim_products p ON t.product_id = p.product_id
WHERE dt.app_version = 'v1.2'
GROUP BY dt.created_date, dt.app_version, dt.ticket_count, dt.avg_tickets_7d
ORDER BY dt.created_date;
```

### Churned Customers SQL (Requirement 3)

```sql
-- Customers who haven't logged in for 30 days
SELECT 
    c.customer_uuid,
    c.customer_segment,
    MAX(l.login_date) as last_login_date,
    CURRENT_DATE - MAX(l.login_date) as days_since_login,
    COUNT(DISTINCT cp.product_id) as active_products,
    SUM(cp.balance) as total_balance
FROM analytics.dim_customers c
LEFT JOIN analytics.fact_logins l ON c.customer_id = l.customer_id
LEFT JOIN analytics.fact_customer_products cp ON c.customer_id = cp.customer_id 
    AND cp.status = 'Active'
WHERE c.account_status = 'Active'
GROUP BY c.customer_uuid, c.customer_segment
HAVING MAX(l.login_date) < CURRENT_DATE - INTERVAL '30 days' 
    OR MAX(l.login_date) IS NULL
ORDER BY days_since_login DESC;

-- For 90 days churn
-- Change: INTERVAL '30 days' to INTERVAL '90 days'
```

---

## 🔧 Configuration

### Environment Variables (.env)

```bash
# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=dbank
DB_USER=dbank_user
DB_PASSWORD=dbank_pass_2025

# Application
APP_ENV=development
LOG_LEVEL=INFO
```

### Data Generation Parameters

Edit `generate_sample_data.py`:

```python
NUM_CUSTOMERS = 10000        # Scale up to 100K+
NUM_TICKETS_PER_MONTH = 5000 # Scale up to 50K
NUM_MONTHS = 3               # Historical months to generate
```

---

## 📁 File Structure

```
data_layer/
├── sql/
│   └── 01_create_schema.sql       # Database schema
├── scripts/
│   ├── generate_sample_data.py    # Data generator
│   ├── load_data_to_postgres.py   # Data loader
│   └── verify_data.py             # Verification tests
└── sample_data/                    # Generated CSV files
    ├── customers.csv
    ├── products.csv
    ├── tickets.csv
    ├── logins.csv
    ├── customer_products.csv
    ├── ticket_categories.csv
    ├── root_causes.csv
    └── time_dimension.csv
```

---

## 🧪 Testing & Verification

Run verification tests:
```bash
cd data_layer/scripts
python verify_data.py
```

Tests include:
- ✅ Table row counts
- ✅ Top root causes query
- ✅ v1.2 spike detection
- ✅ Churned customers
- ✅ Data quality checks
- ✅ PII field presence

---

## 🔒 Security Considerations

### PII Protection

**Fields requiring masking:**
- `dim_customers.full_name`
- `dim_customers.email`
- `dim_customers.phone`
- `dim_customers.national_id`

**Masking strategy (for tool outputs):**
```python
def mask_pii(value, field_type):
    if field_type == 'email':
        local, domain = value.split('@')
        return f"{local[:2]}***@{domain}"
    elif field_type == 'phone':
        return f"{value[:3]}****{value[-2:]}"
    elif field_type == 'national_id':
        return f"{value[:2]}-****-****"
    elif field_type == 'name':
        parts = value.split()
        return f"{parts[0]} ***"
```

### Database Access

- Read-only user for MCP tools
- No DROP/DELETE/TRUNCATE permissions
- Query timeout limits
- Connection pooling

---

## 📊 Data Statistics

After setup, you should have:

| Table | Approximate Rows |
|-------|-----------------|
| Customers | 10,000 |
| Products | 8 |
| Tickets | 15,000+ |
| Logins | 234,000+ |
| Product Holdings | 14,500+ |
| Time Dimension | 1,095 |

**Ticket Distribution:**
- Open: ~15%
- In Progress: ~10%
- Resolved: ~25%
- Closed: ~50%

**v1.2 Related:**
- ~19% of all tickets
- ~40% during spike period (Aug 15-30, 2024)

---

## 🚀 Performance Optimization

### Indexes Created
- All foreign keys
- Date fields (created_date, login_date)
- Status fields
- App version field
- Vector similarity index (ivfflat)

### Query Tips
```sql
-- Use EXPLAIN ANALYZE to check query plans
EXPLAIN ANALYZE
SELECT ...

-- Check index usage
SELECT schemaname, tablename, indexname
FROM pg_indexes
WHERE schemaname = 'analytics';

-- Monitor slow queries
SELECT query, calls, total_time, mean_time
FROM pg_stat_statements
ORDER BY total_time DESC
LIMIT 10;
```

---

## 🔄 Next Steps

1. **dbt Transformations**
   - Create mart tables for common queries
   - Add data quality tests
   - Build aggregation tables

2. **Knowledge Base**
   - Write 5-10 markdown files
   - Document known issues
   - Include v1.2 release notes

3. **Vector Store**
   - Implement document chunking
   - Generate embeddings
   - Populate vector_store.documents

4. **MCP Server**
   - Build sql.query tool
   - Build kb.search tool
   - Build kpi.top_root_causes tool

5. **FastAPI RAG**
   - Create /ask endpoint
   - Integrate LLM
   - Add tool orchestration

---

## ❓ Troubleshooting

### Common Issues

**Port 5432 already in use:**
```bash
# Change port in docker-compose.yml
ports:
  - "5433:5432"  # Use 5433 instead

# Update .env
DB_PORT=5433
```

**Database connection refused:**
```bash
# Check if container is running
docker-compose ps

# Check logs
docker-compose logs postgres

# Restart
docker-compose restart
```

**Data loading fails:**
```bash
# Drop and recreate schema
docker exec -it dbank_postgres psql -U dbank_user -d dbank
DROP SCHEMA analytics CASCADE;
DROP SCHEMA staging CASCADE;
DROP SCHEMA vector_store CASCADE;
\q

# Recreate
docker exec -i dbank_postgres psql -U dbank_user -d dbank < data_layer/sql/01_create_schema.sql
```

---

## 📚 Resources

- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [pgvector GitHub](https://github.com/pgvector/pgvector)
- [Star Schema Design](https://en.wikipedia.org/wiki/Star_schema)
- [Faker Documentation](https://faker.readthedocs.io/)

---

## 📝 License

Proprietary - ?

---

**Built with ❤️ for the dBank Deep Insights Copilot**