# 🔄 dbt Transformations Layer

Data Build Tool (dbt) transformations for the dBank Deep Insights Copilot.

## 📋 Overview

This dbt project transforms raw data into analytics-ready models:

- **Staging models**: Clean and standardize raw data
- **Mart models**: Business-ready analytics tables
- **KPI models**: Pre-aggregated metrics for fast queries
- **Tests**: Data quality and integrity checks
- **Documentation**: Auto-generated data catalog

---

## 🚀 Quick Setup

### One-Command Setup

```bash
chmod +x setup_dbt.sh
./setup_dbt.sh
```

### Manual Setup

1. **Create project structure:**
```bash
cd dbt_project
```

2. **Copy model files:**
Place these files in the correct directories:
- `models/staging/stg_tickets.sql`
- `models/marts/mart_ticket_analytics.sql`
- `models/marts/mart_top_root_causes.sql`
- `models/marts/mart_churned_customers.sql`
- `models/sources.yml`
- `models/schema.yml`
- `macros/mask_pii.sql`

3. **Set up dbt profile:**
Copy the `profiles.yml` to `~/.dbt/profiles.yml`

4. **Install dependencies:**
```bash
dbt deps
```

5. **Test connection:**
```bash
dbt debug
```

6. **Run models:**
```bash
dbt run
```

---

## 📊 Models Overview

### Staging Layer

#### `stg_tickets`
- **Purpose**: Clean and standardize ticket data
- **Materialization**: View
- **Features**:
  - Lowercase status values
  - Derived fields (is_resolved, satisfaction_level)
  - Resolution speed categorization

### Marts Layer

#### `mart_ticket_analytics`
- **Purpose**: Comprehensive ticket analytics with all dimensions
- **Materialization**: Table
- **Key Features**:
  - All dimensions joined (customer, product, category, root cause)
  - Time dimension for easy date filtering
  - v1.2 spike identification
  - Satisfaction metrics
- **Powers**: General ticket analysis queries

#### `mart_top_root_causes`
- **Purpose**: Pre-aggregated root cause metrics
- **Materialization**: Table
- **Key Features**:
  - Aggregated by year/month/quarter
  - Percentage calculations
  - Open ticket tracking
  - v1.2 correlation
- **Powers**: `kpi.top_root_causes` MCP tool

#### `mart_churned_customers`
- **Purpose**: Customer churn analysis and prediction
- **Materialization**: Table
- **Key Features**:
  - 30-day and 90-day churn flags
  - Risk scores (0-100)
  - Risk levels (active → critical)
  - Customer lifetime value proxy
- **Powers**: Churn prediction and retention campaigns

---

## 🎯 Answering Business Requirements

### Requirement 1: Top 5 Root Causes

**Query the mart:**
```sql
SELECT 
    root_cause_name,
    category_name,
    total_tickets,
    pct_of_period,
    pct_open
FROM marts.mart_top_root_causes
WHERE created_year = 2024 
    AND created_month = 10
ORDER BY total_tickets DESC
LIMIT 5;
```

### Requirement 2: v1.2 Spike Detection

**Query the mart:**
```sql
SELECT 
    ticket_created_date,
    COUNT(*) as daily_tickets,
    SUM(CASE WHEN is_v12_related THEN 1 ELSE 0 END) as v12_tickets,
    STRING_AGG(DISTINCT product_type, ', ') as affected_products
FROM marts.mart_ticket_analytics
WHERE created_year = 2024 
    AND created_month >= 8
GROUP BY ticket_created_date
HAVING SUM(CASE WHEN is_v12_related THEN 1 ELSE 0 END) > 0
ORDER BY ticket_created_date;
```

### Requirement 3: Churned Customers SQL

**Query the mart:**
```sql
-- 30-day churn
SELECT 
    customer_uuid,
    customer_segment,
    days_since_login,
    total_products,
    total_balance,
    churn_risk_level
FROM marts.mart_churned_customers
WHERE is_churned_30d = true
ORDER BY estimated_clv DESC;

-- 90-day churn
SELECT 
    customer_uuid,
    customer_segment,
    days_since_login,
    total_products,
    total_balance,
    churn_risk_level
FROM marts.mart_churned_customers
WHERE is_churned_90d = true
ORDER BY estimated_clv DESC;
```

---

## 🧪 Data Quality Tests

### Source Tests
- Uniqueness on primary keys
- Not-null on critical fields
- Referential integrity (foreign keys)
- Accepted values for status fields

### Model Tests
- Unique ticket_id in all models
- Percentages between 0-100
- Risk scores match risk levels
- Data freshness (tickets within 1 day)

### Run Tests
```bash
# Run all tests
dbt test

# Run tests for specific model
dbt test --select mart_ticket_analytics

# Run tests for sources only
dbt test --select source:analytics
```

---

## 🔒 PII Masking

### Using the Macro

```sql
-- In your query
SELECT 
    customer_uuid,
    {{ mask_name('full_name') }} as full_name_masked,
    {{ mask_email('email') }} as email_masked,
    {{ mask_phone('phone') }} as phone_masked,
    {{ mask_national_id('national_id') }} as national_id_masked,
    customer_segment
FROM {{ source('analytics', 'dim_customers') }}
LIMIT 10;
```

### Masking Examples
- **Email**: `john.doe@example.com` → `jo***@example.com`
- **Phone**: `+66-81-234-5678` → `+66****78`
- **National ID**: `1-2345-67890-12-3` → `1-****-****`
- **Name**: `Somchai Jaidee` → `Somchai ***`

---

## 🛠️ Useful dbt Commands

### Running Models

```bash
# Run all models
dbt run

# Run specific model
dbt run --select mart_ticket_analytics

# Run all marts
dbt run --select marts

# Run with full refresh (drops and recreates tables)
dbt run --full-refresh

# Run specific tag
dbt run --select tag:kpi
```

### Testing

```bash
# Run all tests
dbt test

# Test specific model
dbt test --select mart_churned_customers

# Test sources
dbt test --select source:*
```

### Documentation

```bash
# Generate docs
dbt docs generate

# Serve docs (opens browser)
dbt docs serve
```

### Debugging

```bash
# Test connection
dbt debug

# Compile SQL without running
dbt compile

# See what would run
dbt run --select marts --dry-run
```

---

## 📁 Project Structure

```
dbt_project/
├── dbt_project.yml          # Project configuration
├── packages.yml             # dbt packages
├── models/
│   ├── staging/
│   │   └── stg_tickets.sql
│   ├── intermediate/        # For future complex logic
│   ├── marts/
│   │   ├── mart_ticket_analytics.sql
│   │   ├── mart_top_root_causes.sql
│   │   └── mart_churned_customers.sql
│   ├── kpis/               # For incremental KPI models
│   ├── sources.yml         # Source definitions
│   └── schema.yml          # Model documentation & tests
├── macros/
│   └── mask_pii.sql        # PII masking functions
├── tests/                  # Custom tests
├── analyses/               # Ad-hoc queries
├── seeds/                  # CSV reference data
└── snapshots/              # Slowly changing dimensions
```

---

## 🚀 Performance Tips

### Materialization Strategy

- **Views**: Staging models (fast, always fresh)
- **Tables**: Marts (slower build, fast queries)
- **Incremental**: Large fact tables (future optimization)

### Query Optimization

```sql
-- Use the marts instead of joining yourself
❌ BAD: SELECT ... FROM fact_tickets t 
        JOIN dim_customers c ...
        JOIN dim_products p ...

✅ GOOD: SELECT ... FROM marts.mart_ticket_analytics
```

### Indexes

dbt doesn't create indexes by default. Add them manually:
```sql
-- In migrations or post-hooks
CREATE INDEX idx_mart_tickets_date 
ON marts.mart_ticket_analytics(created_date);

CREATE INDEX idx_mart_churn_risk 
ON marts.mart_churned_customers(churn_risk_level);
```

---

## 📈 Model Lineage

```
Sources (analytics schema)
    ↓
stg_tickets (view)
    ↓
mart_ticket_analytics (table)
    ↓
mart_top_root_causes (table)

dim_customers + fact_logins + fact_customer_products
    ↓
mart_churned_customers (table)
```

View lineage graph:
```bash
dbt docs generate
dbt docs serve
# Click on any model to see its lineage
```

---

## 🔄 Incremental Models (Future)

For large datasets, convert to incremental:

```sql
-- models/kpis/kpi_daily_tickets.sql
{{
    config(
        materialized='incremental',
        unique_key='date'
    )
}}

SELECT ...
FROM {{ ref('mart_ticket_analytics') }}

{% if is_incremental() %}
WHERE created_date > (SELECT MAX(date) FROM {{ this }})
{% endif %}
```

---

## 🐛 Troubleshooting

### "Compilation Error"
```bash
# Check SQL syntax
dbt compile --select problematic_model

# Look at compiled SQL
cat target/compiled/dbank_analytics/models/...
```

### "Database Error"
```bash
# Test connection
dbt debug

# Check credentials in ~/.dbt/profiles.yml
```

### "Relation does not exist"
```bash
# Ensure source tables exist
dbt run --select source:analytics

# Full refresh
dbt run --full-refresh
```

### Tests Failing
```bash
# See which tests failed
dbt test --store-failures

# Query the failures
SELECT * FROM analytics.test_results;
```

---

## 📚 Resources

- [dbt Documentation](https://docs.getdbt.com/)
- [dbt Best Practices](https://docs.getdbt.com/guides/best-practices)
- [dbt Utils Package](https://github.com/dbt-labs/dbt-utils)
- [dbt Discourse](https://discourse.getdbt.com/)

---

## ✅ Checklist

After setup, verify:

- [ ] dbt debug passes
- [ ] All 4 models run successfully
- [ ] All tests pass
- [ ] Documentation generates
- [ ] Can query marts in SQL client
- [ ] PII masking macros work
- [ ] Marts answer the 3 business requirements

---

## 🎯 Next Steps

1. ✅ dbt transformations complete
2. 🔜 Create knowledge base documents (5-10 markdown files)
3. 🔜 Build vector store (embed documents)
4. 🔜 Implement MCP server with 3 tools
5. 🔜 Create FastAPI RAG system
6. 🔜 Build UI

---

**Ready for the retrieval layer!** 🎉