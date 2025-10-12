"""
PII Masking Utility - Protect sensitive data in query results
"""

import re
from typing import List, Dict, Any

# PII field patterns
PII_FIELDS = {
    'email': ['email', 'email_address', 'user_email'],
    'phone': ['phone', 'phone_number', 'mobile', 'telephone'],
    'national_id': ['national_id', 'ssn', 'id_number', 'citizen_id'],
    'name': ['full_name', 'customer_name', 'user_name'],
    'address': ['address', 'street_address', 'home_address'],
    'ip_address': ['ip_address', 'ip', 'ip_addr']
}

def mask_email(email: str) -> str:
    """
    Mask email address
    Example: john.doe@example.com -> jo***@example.com
    """
    if not email or '@' not in email:
        return email
    
    local, domain = email.split('@', 1)
    if len(local) <= 2:
        return f"{'*' * len(local)}@{domain}"
    
    return f"{local[:2]}***@{domain}"

def mask_phone(phone: str) -> str:
    """
    Mask phone number
    Example: +66-81-234-5678 -> +66****78
    """
    if not phone:
        return phone
    
    # Remove spaces and dashes for processing
    clean = re.sub(r'[\s\-()]', '', str(phone))
    
    if len(clean) <= 4:
        return '*' * len(clean)
    
    # Keep first 3 and last 2 digits
    return f"{clean[:3]}****{clean[-2:]}"

def mask_national_id(national_id: str) -> str:
    """
    Mask national ID
    Example: 1-2345-67890-12-3 -> 1-****-****
    """
    if not national_id:
        return national_id
    
    # Try to preserve format if it has dashes
    if '-' in str(national_id):
        parts = str(national_id).split('-')
        if len(parts) >= 2:
            return f"{parts[0]}-****-****"
    
    # Otherwise just show first 2 chars
    clean = str(national_id)
    if len(clean) <= 2:
        return '*' * len(clean)
    
    return f"{clean[:2]}****"

def mask_name(name: str) -> str:
    """
    Mask name
    Example: John Doe Smith -> John ***
    """
    if not name:
        return name
    
    parts = str(name).split()
    if len(parts) <= 1:
        return f"{name[:1]}***"
    
    # Keep first name, mask rest
    return f"{parts[0]} ***"

def mask_ip_address(ip: str) -> str:
    """
    Mask IP address
    Example: 192.168.1.100 -> 192.168.*.*
    """
    if not ip:
        return ip
    
    parts = str(ip).split('.')
    if len(parts) == 4:
        return f"{parts[0]}.{parts[1]}.*.*"
    
    return "***"

def mask_value(value: Any, field_type: str) -> Any:
    """
    Mask a value based on its field type
    
    Args:
        value: The value to mask
        field_type: Type of PII field
    
    Returns:
        Masked value
    """
    if value is None:
        return None
    
    value_str = str(value)
    
    if field_type == 'email':
        return mask_email(value_str)
    elif field_type == 'phone':
        return mask_phone(value_str)
    elif field_type == 'national_id':
        return mask_national_id(value_str)
    elif field_type == 'name':
        return mask_name(value_str)
    elif field_type == 'ip_address':
        return mask_ip_address(value_str)
    else:
        return value

def identify_pii_fields(column_name: str) -> str:
    """
    Identify if a column name contains PII
    
    Args:
        column_name: Column name to check
    
    Returns:
        PII type if identified, None otherwise
    """
    column_lower = column_name.lower()
    
    for pii_type, patterns in PII_FIELDS.items():
        for pattern in patterns:
            if pattern in column_lower:
                return pii_type
    
    return None

def mask_query_results(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Mask PII fields in query results
    
    Args:
        results: List of result rows (dicts)
    
    Returns:
        Results with PII fields masked
    """
    if not results:
        return results
    
    # Identify PII columns from first row
    pii_columns = {}
    for column in results[0].keys():
        pii_type = identify_pii_fields(column)
        if pii_type:
            pii_columns[column] = pii_type
    
    # Mask values in all rows
    masked_results = []
    for row in results:
        masked_row = row.copy()
        for column, pii_type in pii_columns.items():
            if column in masked_row:
                masked_row[column] = mask_value(masked_row[column], pii_type)
        masked_results.append(masked_row)
    
    return masked_results

# =====================================================
# Testing
# =====================================================

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 Testing PII Masking")
    print("=" * 60)
    
    # Test data
    test_data = [
        {
            'customer_id': 1,
            'full_name': 'John Doe Smith',
            'email': 'john.doe@example.com',
            'phone': '+66-81-234-5678',
            'national_id': '1-2345-67890-12-3',
            'balance': 10000.00
        },
        {
            'customer_id': 2,
            'full_name': 'Jane Smith',
            'email': 'jane@test.com',
            'phone': '0812345678',
            'national_id': '9876543210',
            'balance': 5000.00
        }
    ]
    
    print("\nOriginal data:")
    for row in test_data:
        print(f"  {row}")
    
    print("\nMasked data:")
    masked = mask_query_results(test_data)
    for row in masked:
        print(f"  {row}")
    
    print("\n" + "=" * 60)
    print("✅ PII fields successfully masked!")
    print("=" * 60)