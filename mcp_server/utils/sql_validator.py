"""
SQL Validator - Ensure only safe, read-only queries are executed
"""

import re
from typing import Optional

# Forbidden SQL keywords (write operations)
FORBIDDEN_KEYWORDS = [
    'DELETE', 'DROP', 'TRUNCATE', 'INSERT', 'UPDATE',
    'ALTER', 'CREATE', 'REPLACE', 'GRANT', 'REVOKE',
    'EXEC', 'EXECUTE', 'CALL', 'MERGE', 'RENAME'
]

# Dangerous patterns
DANGEROUS_PATTERNS = [
    r';.*DELETE',  # Chained DELETE
    r';.*DROP',    # Chained DROP
    r';.*INSERT',  # Chained INSERT
    r';.*UPDATE',  # Chained UPDATE
    r'--.*DROP',   # Comment with DROP
    r'/\*.*DROP.*\*/',  # Block comment with DROP
    r'xp_cmdshell', # SQL Server command execution
    r'INTO\s+OUTFILE',  # MySQL file write
    r'INTO\s+DUMPFILE', # MySQL file write
    r'LOAD_FILE',  # MySQL file read
    r'pg_read_file',  # PostgreSQL file read
    r'COPY.*FROM',  # PostgreSQL COPY
]

def is_read_only(query: str) -> bool:
    """
    Check if query is read-only (SELECT only)
    
    Args:
        query: SQL query string
    
    Returns:
        True if read-only, False otherwise
    """
    if not query:
        return False
    
    # Normalize query
    normalized = query.upper().strip()
    
    # Remove comments
    normalized = re.sub(r'--.*$', '', normalized, flags=re.MULTILINE)
    normalized = re.sub(r'/\*.*?\*/', '', normalized, flags=re.DOTALL)
    
    # Check for forbidden keywords
    for keyword in FORBIDDEN_KEYWORDS:
        # Use word boundaries to avoid false positives
        pattern = r'\b' + keyword + r'\b'
        if re.search(pattern, normalized):
            return False
    
    # Must start with SELECT or WITH (for CTEs)
    if not (normalized.startswith('SELECT') or normalized.startswith('WITH')):
        return False
    
    return True

def validate_sql_query(query: str) -> Optional[str]:
    """
    Validate SQL query for safety
    
    Args:
        query: SQL query string
    
    Returns:
        Error message if invalid, None if valid
    """
    if not query or not query.strip():
        return "Query cannot be empty"
    
    # Normalize for pattern matching
    normalized = query.upper()
    
    # Check for dangerous patterns
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, normalized, re.IGNORECASE):
            return f"Dangerous pattern detected: {pattern}"
    
    # Check for multiple statements (only one allowed)
    # Count semicolons (excluding those in strings)
    statements = re.split(r';(?=(?:[^\'"]|[\'"][^\'"]*[\'"])*$)', query)
    # Filter out empty statements
    statements = [s.strip() for s in statements if s.strip()]
    if len(statements) > 1:
        return "Multiple statements not allowed. Only single SELECT queries permitted."
    
    # Check for suspicious comment patterns
    if re.search(r'--.*(?:DROP|DELETE|INSERT)', query, re.IGNORECASE):
        return "Suspicious SQL comment detected"
    
    # Check for excessively long query (DoS protection)
    if len(query) > 50000:  # 50KB limit
        return "Query exceeds maximum length (50KB)"
    
    # Check for too many parentheses (complex injection attempts)
    open_parens = query.count('(')
    close_parens = query.count(')')
    if open_parens != close_parens:
        return "Unbalanced parentheses in query"
    if open_parens > 100:  # Arbitrary limit
        return "Query too complex (too many nested subqueries)"
    
    return None  # Valid

def sanitize_table_name(table_name: str) -> bool:
    """
    Validate table name is safe
    
    Args:
        table_name: Table name to validate
    
    Returns:
        True if valid, False otherwise
    """
    # Only allow alphanumeric, underscore, and dot (for schema.table)
    pattern = r'^[a-zA-Z0-9_\.]+$'
    return bool(re.match(pattern, table_name))

def extract_tables_from_query(query: str) -> list:
    """
    Extract table names from query (basic)
    
    Args:
        query: SQL query
    
    Returns:
        List of table names
    """
    # Simple pattern to find table names after FROM and JOIN
    pattern = r'(?:FROM|JOIN)\s+([a-zA-Z0-9_\.]+)'
    matches = re.findall(pattern, query, re.IGNORECASE)
    return matches

# =====================================================
# Testing
# =====================================================

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 Testing SQL Validator")
    print("=" * 60)
    
    test_queries = [
        # Valid queries
        ("SELECT * FROM customers", True, None),
        ("SELECT COUNT(*) FROM orders WHERE status = 'active'", True, None),
        ("WITH cte AS (SELECT id FROM users) SELECT * FROM cte", True, None),
        
        # Invalid queries
        ("DELETE FROM customers", False, "write operation"),
        ("SELECT * FROM users; DROP TABLE customers;", False, "multiple statements"),
        ("UPDATE users SET password = 'hacked'", False, "write operation"),
        ("SELECT * FROM users--DROP TABLE important", False, "suspicious comment"),
        ("INSERT INTO logs VALUES (1, 'test')", False, "write operation"),
        ("CREATE TABLE hackers (id INT)", False, "write operation"),
    ]
    
    print("\nTesting queries:\n")
    for query, should_be_valid, reason in test_queries:
        is_valid = is_read_only(query)
        validation_error = validate_sql_query(query)
        
        status = "✅" if (is_valid == should_be_valid) else "❌"
        
        print(f"{status} Query: {query[:60]}...")
        print(f"   Read-only: {is_valid}")
        print(f"   Validation: {validation_error or 'PASS'}")
        print()
    
    print("=" * 60)