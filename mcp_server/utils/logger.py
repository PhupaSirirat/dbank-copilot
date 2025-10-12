"""
Logger Utility - Audit logging for all tool calls
"""

import os
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

# Database connection
DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', 'localhost'),
    'port': os.getenv('POSTGRES_PORT', '5433'),
    'database': os.getenv('POSTGRES_DB', 'dbank'),
    'user': os.getenv('POSTGRES_USER', 'dbank_user'),
    'password': os.getenv('POSTGRES_PASSWORD', 'dbank_pass_2025')
}

# Also log to file as backup
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

def log_tool_call(
    tool_name: str,
    parameters: Dict[str, Any],
    user_id: str = "anonymous",
    session_id: Optional[str] = None,
    execution_time_ms: int = 0,
    status: str = "success",
    result_summary: Optional[str] = None,
    error_message: Optional[str] = None
):
    """
    Log a tool call to database and file
    
    Args:
        tool_name: Name of the tool called
        parameters: Parameters passed to the tool
        user_id: User who called the tool
        session_id: Session identifier
        execution_time_ms: Execution time in milliseconds
        status: 'success' or 'error'
        result_summary: Brief summary of results
        error_message: Error message if status is error
    """
    timestamp = datetime.now()
    
    # Prepare log entry
    log_entry = {
        'timestamp': timestamp.isoformat(),
        'tool_name': tool_name,
        'user_id': user_id,
        'session_id': session_id,
        'parameters': parameters,
        'execution_time_ms': execution_time_ms,
        'status': status,
        'result_summary': result_summary,
        'error_message': error_message
    }
    
    # Log to database
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        insert_query = """
            INSERT INTO analytics.tool_call_logs 
            (tool_name, parameters, user_id, execution_time_ms, status, error_message, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        
        cur.execute(insert_query, (
            tool_name,
            json.dumps(parameters),
            user_id,
            execution_time_ms,
            status,
            error_message,
            timestamp
        ))
        
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Warning: Failed to log to database: {e}")
    
    # Log to file as backup
    try:
        log_file = os.path.join(LOG_DIR, f"tool_calls_{timestamp.strftime('%Y%m%d')}.log")
        with open(log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
    except Exception as e:
        print(f"Warning: Failed to log to file: {e}")

def get_recent_logs(
    limit: int = 50,
    tool_name: Optional[str] = None,
    user_id: Optional[str] = None,
    status: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Get recent tool call logs
    
    Args:
        limit: Maximum number of logs to return
        tool_name: Filter by tool name
        user_id: Filter by user
        status: Filter by status (success/error)
    
    Returns:
        List of log entries
    """
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        query = """
            SELECT 
                log_id,
                tool_name,
                parameters,
                user_id,
                execution_time_ms,
                status,
                error_message,
                created_at
            FROM analytics.tool_call_logs
            WHERE 1=1
        """
        
        params = []
        
        if tool_name:
            query += " AND tool_name = %s"
            params.append(tool_name)
        
        if user_id:
            query += " AND user_id = %s"
            params.append(user_id)
        
        if status:
            query += " AND status = %s"
            params.append(status)
        
        query += " ORDER BY created_at DESC LIMIT %s"
        params.append(limit)
        
        cur.execute(query, params)
        results = cur.fetchall()
        
        # Format results
        logs = []
        for row in results:
            logs.append({
                'log_id': row['log_id'],
                'tool_name': row['tool_name'],
                'parameters': row['parameters'],
                'user_id': row['user_id'],
                'execution_time_ms': row['execution_time_ms'],
                'status': row['status'],
                'error_message': row['error_message'],
                'timestamp': row['created_at'].isoformat() if row['created_at'] else None
            })
        
        cur.close()
        conn.close()
        
        return logs
    
    except Exception as e:
        raise Exception(f"Failed to get logs: {str(e)}")

def get_tool_statistics(days: int = 7) -> Dict[str, Any]:
    """
    Get tool usage statistics
    
    Args:
        days: Number of days to look back
    
    Returns:
        Statistics dictionary
    """
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        query = """
            SELECT 
                tool_name,
                COUNT(*) as call_count,
                AVG(execution_time_ms) as avg_execution_time,
                SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success_count,
                SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END) as error_count
            FROM analytics.tool_call_logs
            WHERE created_at >= CURRENT_DATE - INTERVAL '%s days'
            GROUP BY tool_name
            ORDER BY call_count DESC
        """
        
        cur.execute(query, (days,))
        results = cur.fetchall()
        
        stats = {
            'period_days': days,
            'tools': []
        }
        
        for row in results:
            stats['tools'].append({
                'tool_name': row['tool_name'],
                'total_calls': int(row['call_count']),
                'success_rate': round(int(row['success_count']) / int(row['call_count']) * 100, 2) if row['call_count'] > 0 else 0,
                'avg_execution_ms': round(float(row['avg_execution_time']), 2) if row['avg_execution_time'] else 0,
                'error_count': int(row['error_count'])
            })
        
        cur.close()
        conn.close()
        
        return stats
    
    except Exception as e:
        raise Exception(f"Failed to get statistics: {str(e)}")

# =====================================================
# Testing
# =====================================================

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 Testing Logger")
    print("=" * 60)
    
    # Test 1: Log a successful call
    print("\n1. Logging successful tool call...")
    log_tool_call(
        tool_name="sql.query",
        parameters={"query": "SELECT COUNT(*) FROM customers"},
        user_id="test_user",
        session_id="test_session_123",
        execution_time_ms=45,
        status="success",
        result_summary="Returned 1 row"
    )
    print("✅ Logged successfully")
    
    # Test 2: Log an error
    print("\n2. Logging error...")
    log_tool_call(
        tool_name="kb.search",
        parameters={"query": "test"},
        user_id="test_user",
        execution_time_ms=10,
        status="error",
        error_message="Connection timeout"
    )
    print("✅ Error logged")
    
    # Test 3: Get recent logs
    print("\n3. Getting recent logs...")
    try:
        logs = get_recent_logs(limit=5)
        print(f"✅ Retrieved {len(logs)} log entries")
        for log in logs[:3]:
            print(f"   - {log['tool_name']}: {log['status']} ({log['execution_time_ms']}ms)")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 4: Get statistics
    print("\n4. Getting tool statistics...")
    try:
        stats = get_tool_statistics(days=7)
        print(f"✅ Statistics (last {stats['period_days']} days):")
        for tool in stats['tools']:
            print(f"   - {tool['tool_name']}: {tool['total_calls']} calls, {tool['success_rate']}% success")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "=" * 60)