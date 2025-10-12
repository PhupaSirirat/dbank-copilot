# 🔄 dbt Transformations - Quick Start Guide

**Time Required: ~30 minutes**

## Important Notes Before Starting

⚠️ **Common Issues & Solutions:**

1. **TypeError at end of commands** - This is a harmless bug in dbt 1.7.7. Your commands still work! Look for success messages like "OK connection ok" or "Completed successfully" before the error.

2. **Port mismatch** - Your PostgreSQL might be on port 5433 (not 5432). Check with: `docker ps | grep dbank_postgres`

3. **marts schema doesn't exist yet** - This is normal! dbt creates the `marts` schema when you run `dbt run`. It's NOT in the initial database setup.

4. **Only see `public` schema in pgAdmin** - Refresh after running `dbt run`. Right-click Schemas → Refresh.

---

## Prerequisites

- ✅ Data layer completed (PostgreSQL with data loaded)
- ✅ Python virtual environment activated  
- ✅ dbt-core and dbt-postgres installed
- ✅ PostgreSQL running (check: `docker-compose ps`)

**Quick Environment Check:**
```bash
# Verify PostgreSQL is running
docker-compose ps
# Should show: dbank_postgres ... Up

# Check port
docker ps | grep dbank_postgres
# Note the port mapping (e.g., 5433:5432)

# Verify virtual environment
which python
# Should show: /path/to/.venv/bin/python
```

---

## Step 1: Create dbt Project Structure (2 min)

```bash
# From your dbank-copilot root directory
mkdir -p dbt_project/{models/{staging,marts},macros,analyses}
cd dbt_project
```

Your structure should be:
```
dbank-copilot/
├── dbt_project/          # ← New!
│   ├── models/
│   │   ├── staging/
│   │   └── marts/
│   ├── macros/
│   └── analyses/
├── data_layer/
└── ...
```

---

## Step 2: Create dbt Configuration Files (5 min)

### 1. Create `dbt_project.yml` in `dbt_project/`

Copy the `dbt_project.yml` artifact content to this file.

**Quick create:**
```bash
# Make sure you're in dbt_project/ directory
cat > dbt_project.yml << 'EOF'
name: 'dbank_analytics'
version: '1.0.0'
config-version: 2

profile: 'dbank'

model-paths: ["models"]
analysis-paths: ["analyses"]
macro-paths: ["macros"]

target-path: "target"
clean-targets:
  - "target"
  - "dbt_packages"

models:
  dbank_analytics:
    staging:
      +materialized: view
      +schema: staging
    marts:
      +materialized: table
      +schema: marts
EOF
```

### 2. Create `packages.yml` in `dbt_project/`

```bash
cat > packages.yml << 'EOF'
packages:
  - package: dbt-labs/dbt_utils
    version: 1.1.1
EOF
```

### 3. Set up dbt profile

**IMPORTANT: Check your database port first!**

```bash
# Check which port your PostgreSQL is running on
docker ps | grep dbank_postgres
# Look for something like: 0.0.0.0:5433->5432/tcp
```

**Location:** `~/.dbt/profiles.yml` (Mac/Linux) or `%USERPROFILE%\.dbt\profiles.yml` (Windows)

```bash
# Create directory
mkdir -p ~/.dbt

# Create profiles.yml with CORRECT PORT
cat > ~/.dbt/profiles.yml << 'EOF'
dbank:
  target: dev
  outputs:
    dev:
      type: postgres
      host: localhost
      port: 5433          # ← CHANGE THIS if your port is different!
      user: dbank_user
      password: dbank_pass_2025
      dbname: dbank
      schema: analytics
      threads: 4
EOF
```

**Verify the file:**
```bash
cat ~/.dbt/profiles.yml
```

---

## Step 3: Create Model Files (5 min)

Create these files with the artifact content. I'll show you two ways:

### Method A: Create Files Manually

Create these files and copy content from the artifacts I provided earlier:

**Required files:**
1. `models/staging/stg_tickets.sql` - Copy from artifact
2. `models/marts/mart_ticket_analytics.sql` - Copy from artifact  
3. `models/marts/mart_top_root_causes.sql` - Copy from artifact
4. `models/marts/mart_churned_customers.sql` - Copy from artifact
5. `models/sources.yml` - Copy from artifact
6. `models/schema.yml` - Copy from artifact
7. `macros/mask_pii.sql` - Copy from artifact

### Method B: Quick File Structure Check

Verify your files are in place:
```bash
# You should be in dbt_project/ directory
ls -la models/staging/
# Should show: stg_tickets.sql

ls -la models/marts/
# Should show: mart_ticket_analytics.sql, mart_top_root_causes.sql, mart_churned_customers.sql

ls -la models/
# Should show: sources.yml, schema.yml

ls -la macros/
# Should show: mask_pii.sql
```

**File tree should look like:**
```
dbt_project/
├── dbt_project.yml
├── packages.yml
├── models/
│   ├── staging/
│   │   └── stg_tickets.sql
│   ├── marts/
│   │   ├── mart_ticket_analytics.sql
│   │   ├── mart_top_root_causes.sql
│   │   └── mart_churned_customers.sql
│   ├── sources.yml
│   └── schema.yml
└── macros/
    └── mask_pii.sql
```

---

## Step 4: Install dbt Packages (2 min)

```bash
# Make sure you're in dbt_project/ directory
cd dbt_project

# Install packages
dbt deps
```

Expected output:
```
Installing dbt-labs/dbt_utils
  Installed from version 1.1.1
```

**Note:** You might see a `TypeError` at the very end about `MessageToJson` - this is a harmless bug in dbt 1.7.7 logging. The packages are still installed correctly if you see the "Installed from version" message.

**Verify installation:**
```bash
ls -la dbt_packages/
# Should show a dbt_utils folder
```

---

## Step 5: Test Database Connection (1 min)

```bash
dbt debug
```

**What to look for:**
```
✓ profiles.yml file [OK found and valid]
✓ dbt_project.yml file [OK found and valid]  
✓ Connection test: [OK connection ok]
✓ All checks passed!
```

(Ignore the TypeError at the end - it's harmless)

**If connection fails:**
- Check port in `~/.dbt/profiles.yml` matches your Docker port
- Verify PostgreSQL is running: `docker-compose ps`
- Test direct connection: `docker exec -it dbank_postgres psql -U dbank_user -d dbank -c "SELECT 1;"`

---

## Step 6: Run dbt Models (5 min)

### Run all models

```bash
dbt run
```

Expected output:
```
Running with dbt=1.7.7
Found 4 models, 28 tests, 0 snapshots...

Staging:
  CREATE VIEW staging.stg_tickets ........................... [OK in 0.12s]

Marts:
  CREATE TABLE marts.mart_ticket_analytics .................. [OK in 2.34s]
  CREATE TABLE marts.mart_top_root_causes ................... [OK in 1.87s]
  CREATE TABLE marts.mart_churned_customers ................. [OK in 2.15s]

Completed successfully in 6.48s
```

(Again, ignore any TypeError at the end)

**IMPORTANT:** dbt creates the `marts` schema automatically when you run models. If you refresh pgAdmin4 now, you should see:
- `analytics` schema (original data)
- `marts` schema (NEW - dbt models)
- `staging` schema (dbt staging views)

### Verify in database

**Option 1: Using psql**
```bash
docker exec -it dbank_postgres psql -U dbank_user -d dbank

# Check schemas
\dn

# Check marts tables
\dt marts.*

# Sample query
SELECT root_cause_name, total_tickets, pct_of_period 
FROM marts.mart_top_root_causes 
ORDER BY total_tickets DESC 
LIMIT 5;

# Exit
\q
```

**Option 2: Using pgAdmin4**
1. Right-click on **Schemas** → **Refresh**
2. You should now see **`marts`** and **`staging`** schemas
3. Expand `marts` → `Tables` to see your 3 mart tables

---

## Step 7: Run Data Quality Tests (2 min)

```bash
dbt test
```

Expected output:
```
Running with dbt=1.7.7
Found 4 models, 28 tests

Passed 26 tests in 8.32s

DONE. Pass=26 Error=0 Skip=0 Warn=2 Total=28
```

**If tests fail:**
- Review the error messages
- Check data quality in source tables
- Adjust tests if needed

---

## Step 8: Generate Documentation (2 min)

```bash
# Generate docs
dbt docs generate

# Serve docs (opens in browser)
dbt docs serve
```

This will open `http://localhost:8080` with:
- Model lineage graph
- Column-level documentation
- Test results
- Source freshness

---

## 🎯 Verification Checklist

Test that your marts answer the business requirements:

### Test 1: Top 5 Root Causes

```sql
SELECT 
    root_cause_name,
    category_name,
    total_tickets,
    pct_of_period,
    pct_open
FROM marts.mart_top_root_causes
WHERE created_year = 2024 
    AND created_month = (SELECT MAX(created_month) FROM marts.mart_top_root_causes WHERE created_year = 2024)
ORDER BY total_tickets DESC
LIMIT 5;
```

✅ Should show root causes with percentages and open ticket counts

### Test 2: v1.2 Spike Detection

```sql
SELECT 
    ticket_created_date,
    COUNT(*) as total_tickets,
    SUM(CASE WHEN app_version = 'v1.2' THEN 1 ELSE 0 END) as v12_tickets
FROM marts.mart_ticket_analytics
WHERE created_year = 2024 
    AND created_month >= 8
GROUP BY ticket_created_date
HAVING SUM(CASE WHEN app_version = 'v1.2' THEN 1 ELSE 0 END) > 0
ORDER BY ticket_created_date;
```

✅ Should show spike around August 15, 2024

### Test 3: Churned Customers

```sql
-- 30-day churn
SELECT COUNT(*), customer_segment
FROM marts.mart_churned_customers
WHERE is_churned_30d = true
GROUP BY customer_segment;

-- 90-day churn
SELECT COUNT(*), customer_segment
FROM marts.mart_churned_customers
WHERE is_churned_90d = true
GROUP BY customer_segment;
```

✅ Should show churned customer counts by segment

### Test 4: PII Masking

```sql
-- Test the masking macro
SELECT 
    customer_uuid,
    {{ mask_name('full_name') }} as name_masked,
    {{ mask_email('email') }} as email_masked
FROM analytics.dim_customers
LIMIT 3;
```

✅ Should show masked PII fields

---

## 🚀 Common dbt Commands

```bash
# Run all models
dbt run

# Run specific model
dbt run --select mart_ticket_analytics

# Run all marts
dbt run --select marts

# Run with full refresh
dbt run --full-refresh

# Run tests
dbt test

# Test specific model
dbt test --select mart_churned_customers

# Generate and serve docs
dbt docs generate && dbt docs serve

# Debug connection
dbt debug

# Compile without running
dbt compile

# See lineage for model
dbt docs generate
dbt docs serve
# Then click on model in UI
```

---

## 📊 What You Now Have

✅ **4 dbt models** answering all business requirements  
✅ **28 data quality tests** ensuring data integrity  
✅ **PII masking macros** for secure data access  
✅ **Auto-generated documentation** with lineage  
✅ **Pre-aggregated KPI tables** for fast queries  
✅ **Churn analysis** with risk scores  
✅ **v1.2 spike detection** built into models  

---

## 🐛 Troubleshooting

### "Compilation Error: sources not found"

```bash
# Make sure sources.yml is in models/ directory
ls models/sources.yml

# Check the schema name in sources.yml matches your database
grep "schema: analytics" models/sources.yml
```

### "Could not find profile named 'dbank'"

```bash
# Check profile exists
cat ~/.dbt/profiles.yml

# Verify dbt_project.yml has correct profile name
grep "profile:" dbt_project.yml  # Should show: profile: 'dbank'
```

### "Relation already exists"

```bash
# Drop and recreate
dbt run --full-refresh
```

### "password authentication failed"

Check your port and credentials:
```bash
# Verify port
docker ps | grep dbank_postgres

# Update ~/.dbt/profiles.yml with correct port
nano ~/.dbt/profiles.yml
```

### Tests Failing

```bash
# See detailed test results
dbt test --store-failures

# Query failures (if enabled)
docker exec -it dbank_postgres psql -U dbank_user -d dbank
SELECT * FROM analytics.test_results;
```

### Models Not Updating

```bash
# Clear cache and rerun
rm -rf target/
dbt clean
dbt run
```

### "TypeError: MessageToJson() got an unexpected keyword argument"

**This is HARMLESS!** It's a bug in dbt 1.7.7's logging system. Your commands still work correctly. Look for the actual success messages before the error:
- `Installing dbt-labs/dbt_utils` → Success
- `Connection test: [OK connection ok]` → Success  
- `Completed successfully` → Success

**To fix permanently:**
```bash
pip install protobuf==4.24.4
# Or upgrade dbt:
pip install --upgrade dbt-core==1.8.0 dbt-postgres==1.8.0
```

### "No such file or directory: dbt_project.yml"

```bash
# Make sure you're in the right directory
pwd  # Should show: /path/to/dbank-copilot/dbt_project

# If not:
cd dbt_project
```

### pgAdmin doesn't show `marts` schema

1. Make sure you ran `dbt run` successfully
2. In pgAdmin, right-click **Schemas** → **Refresh**
3. The `marts` schema is created by dbt, not by the initial schema SQL
4. Check if it exists:
```sql
SELECT schema_name FROM information_schema.schemata 
WHERE schema_name = 'marts';
```

---

## 🎯 Next Steps

You're now ready for:

1. ✅ Data Layer Complete
2. ✅ dbt Transformations Complete
3. 🔜 **Create Knowledge Base** (5-10 markdown docs about products, issues, policies)
4. 🔜 **Build Vector Store** (embed documents into pgvector)
5. 🔜 **Create MCP Server** (3 tools: sql.query, kb.search, kpi.top_root_causes)
6. 🔜 **Build FastAPI RAG** (/ask endpoint with LLM)
7. 🔜 **Create UI** (Simple chat interface)

---

## 📚 Additional Resources

- [dbt Documentation](https://docs.getdbt.com/)
- [dbt Best Practices](https://docs.getdbt.com/guides/best-practices)
- [dbt Learn](https://courses.getdbt.com/)
- [dbt Slack Community](https://www.getdbt.com/community/join-the-community/)

---

**Congratulations! Your analytics layer is ready!** 🎉