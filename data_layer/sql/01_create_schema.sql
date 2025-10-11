-- =====================================================
-- dBank Data Warehouse Schema (Star Schema)
-- =====================================================

-- Enable pgvector extension for embeddings
CREATE EXTENSION IF NOT EXISTS vector;

-- Create schemas for different layers
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS analytics;
CREATE SCHEMA IF NOT EXISTS vector_store;

-- =====================================================
-- DIMENSION TABLES
-- =====================================================

-- Dimension: Customers
CREATE TABLE analytics.dim_customers (
    customer_id SERIAL PRIMARY KEY,
    customer_uuid VARCHAR(50) UNIQUE NOT NULL,
    -- PII fields (will be masked in outputs)
    full_name VARCHAR(200),
    email VARCHAR(200),
    phone VARCHAR(20),
    national_id VARCHAR(20),
    -- Non-PII fields
    date_of_birth DATE,
    gender VARCHAR(10),
    customer_segment VARCHAR(50), -- Premium, Standard, Basic
    registration_date DATE,
    account_status VARCHAR(20), -- Active, Suspended, Closed
    city VARCHAR(100),
    country VARCHAR(100) DEFAULT 'Thailand',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Dimension: Products
CREATE TABLE analytics.dim_products (
    product_id SERIAL PRIMARY KEY,
    product_code VARCHAR(50) UNIQUE NOT NULL,
    product_name VARCHAR(200) NOT NULL,
    product_category VARCHAR(100), -- Savings, Lending, Investment, Insurance
    product_type VARCHAR(100), -- Digital Saving, Digital Lending, etc.
    description TEXT,
    launch_date DATE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Dimension: Ticket Categories
CREATE TABLE analytics.dim_ticket_categories (
    category_id SERIAL PRIMARY KEY,
    category_code VARCHAR(50) UNIQUE NOT NULL,
    category_name VARCHAR(200) NOT NULL,
    parent_category VARCHAR(100),
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Dimension: Root Causes
CREATE TABLE analytics.dim_root_causes (
    root_cause_id SERIAL PRIMARY KEY,
    root_cause_code VARCHAR(50) UNIQUE NOT NULL,
    root_cause_name VARCHAR(200) NOT NULL,
    category VARCHAR(100),
    severity VARCHAR(20), -- Critical, High, Medium, Low
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Dimension: Time (Date dimension for easy date queries)
CREATE TABLE analytics.dim_time (
    date_id SERIAL PRIMARY KEY,
    date DATE UNIQUE NOT NULL,
    year INT,
    quarter INT,
    month INT,
    month_name VARCHAR(20),
    week INT,
    day_of_month INT,
    day_of_week INT,
    day_name VARCHAR(20),
    is_weekend BOOLEAN,
    is_holiday BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- FACT TABLES
-- =====================================================

-- Fact: Customer Tickets
CREATE TABLE analytics.fact_tickets (
    ticket_id SERIAL PRIMARY KEY,
    ticket_number VARCHAR(50) UNIQUE NOT NULL,
    customer_id INT REFERENCES analytics.dim_customers(customer_id),
    product_id INT REFERENCES analytics.dim_products(product_id),
    category_id INT REFERENCES analytics.dim_ticket_categories(category_id),
    root_cause_id INT REFERENCES analytics.dim_root_causes(root_cause_id),
    
    -- Ticket details
    ticket_status VARCHAR(50), -- Open, In Progress, Resolved, Closed
    priority VARCHAR(20), -- Critical, High, Medium, Low
    subject VARCHAR(500),
    description TEXT,
    
    -- Dates
    created_date DATE,
    resolved_date DATE,
    closed_date DATE,
    
    -- Metrics
    resolution_time_hours DECIMAL(10, 2),
    customer_satisfaction_score INT, -- 1-5 scale
    
    -- Metadata
    channel VARCHAR(50), -- App, Web, Phone, Email
    assigned_to VARCHAR(100),
    app_version VARCHAR(20), -- e.g., v1.2
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Fact: Customer Product Holdings
CREATE TABLE analytics.fact_customer_products (
    holding_id SERIAL PRIMARY KEY,
    customer_id INT REFERENCES analytics.dim_customers(customer_id),
    product_id INT REFERENCES analytics.dim_products(product_id),
    
    -- Product holding details
    activation_date DATE,
    deactivation_date DATE,
    status VARCHAR(50), -- Active, Inactive, Suspended
    
    -- Metrics (specific to product type)
    balance DECIMAL(15, 2),
    credit_limit DECIMAL(15, 2),
    interest_rate DECIMAL(5, 2),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(customer_id, product_id, activation_date)
);

-- Fact: Customer Login Access
CREATE TABLE analytics.fact_logins (
    login_id SERIAL PRIMARY KEY,
    customer_id INT REFERENCES analytics.dim_customers(customer_id),
    
    -- Login details
    login_date DATE,
    login_timestamp TIMESTAMP,
    logout_timestamp TIMESTAMP,
    session_duration_minutes INT,
    
    -- Technical details
    device_type VARCHAR(50), -- Mobile, Desktop, Tablet
    os_type VARCHAR(50), -- iOS, Android, Windows, Mac
    app_version VARCHAR(20),
    ip_address VARCHAR(50),
    login_status VARCHAR(20), -- Success, Failed
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- VECTOR STORE (for Knowledge Base)
-- =====================================================

CREATE TABLE vector_store.documents (
    doc_id SERIAL PRIMARY KEY,
    document_name VARCHAR(500),
    document_type VARCHAR(50), -- markdown, pdf
    chunk_index INT,
    content TEXT,
    embedding vector(1536), -- OpenAI embedding size
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index for vector similarity search
CREATE INDEX ON vector_store.documents USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- =====================================================
-- STAGING TABLES (Raw data ingestion)
-- =====================================================

CREATE TABLE staging.raw_customers (
    id SERIAL PRIMARY KEY,
    raw_data JSONB,
    loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE staging.raw_tickets (
    id SERIAL PRIMARY KEY,
    raw_data JSONB,
    loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE staging.raw_logins (
    id SERIAL PRIMARY KEY,
    raw_data JSONB,
    loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- AUDIT TABLE (Tool Call Logging)
-- =====================================================

CREATE TABLE analytics.tool_call_logs (
    log_id SERIAL PRIMARY KEY,
    tool_name VARCHAR(100),
    parameters JSONB,
    user_id VARCHAR(100),
    execution_time_ms INT,
    status VARCHAR(20), -- Success, Failed
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- INDEXES for Performance
-- =====================================================

-- Indexes on foreign keys
CREATE INDEX idx_tickets_customer ON analytics.fact_tickets(customer_id);
CREATE INDEX idx_tickets_product ON analytics.fact_tickets(product_id);
CREATE INDEX idx_tickets_category ON analytics.fact_tickets(category_id);
CREATE INDEX idx_tickets_root_cause ON analytics.fact_tickets(root_cause_id);
CREATE INDEX idx_tickets_created_date ON analytics.fact_tickets(created_date);
CREATE INDEX idx_tickets_status ON analytics.fact_tickets(ticket_status);
CREATE INDEX idx_tickets_app_version ON analytics.fact_tickets(app_version);

CREATE INDEX idx_logins_customer ON analytics.fact_logins(customer_id);
CREATE INDEX idx_logins_date ON analytics.fact_logins(login_date);

CREATE INDEX idx_cust_products_customer ON analytics.fact_customer_products(customer_id);
CREATE INDEX idx_cust_products_product ON analytics.fact_customer_products(product_id);

-- =====================================================
-- COMMENTS (Documentation)
-- =====================================================

COMMENT ON TABLE analytics.fact_tickets IS 'Support tickets with root causes and resolution metrics';
COMMENT ON TABLE analytics.fact_logins IS 'Customer login activity for churn analysis';
COMMENT ON TABLE analytics.fact_customer_products IS 'Products held by customers';
COMMENT ON COLUMN analytics.dim_customers.national_id IS 'PII - Must be masked in tool outputs';
COMMENT ON COLUMN analytics.dim_customers.email IS 'PII - Must be masked in tool outputs';
COMMENT ON COLUMN analytics.dim_customers.phone IS 'PII - Must be masked in tool outputs';