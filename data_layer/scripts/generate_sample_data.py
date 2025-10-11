"""
Sample Data Generator for dBank Virtual Bank
Generates realistic customer, ticket, login, and product data
"""

import pandas as pd
import numpy as np
from faker import Faker
from datetime import datetime, timedelta
import random
import os

# Initialize Faker with Thai locale
fake = Faker(['th_TH', 'en_US'])
Faker.seed(42)
np.random.seed(42)
random.seed(42)

# Configuration
NUM_CUSTOMERS = 10000  # Start small, can scale to 100k+
NUM_TICKETS_PER_MONTH = 5000  # ~50k in original, we'll do 5k for demo
NUM_MONTHS = 3
OUTPUT_DIR = 'data_layer/sample_data'

# Create output directory
os.makedirs(OUTPUT_DIR, exist_ok=True)

print("🏦 Generating dBank Sample Data...")
print("=" * 60)

# =====================================================
# 1. GENERATE PRODUCTS
# =====================================================
print("\n📦 Generating Products...")

products_data = [
    # Digital Savings
    {'product_code': 'DS001', 'product_name': 'dSave Plus', 'product_category': 'Savings', 
     'product_type': 'Digital Saving', 'launch_date': '2023-01-15'},
    {'product_code': 'DS002', 'product_name': 'dSave Premium', 'product_category': 'Savings', 
     'product_type': 'Digital Saving', 'launch_date': '2023-06-20'},
    
    # Digital Lending
    {'product_code': 'DL001', 'product_name': 'dLoan Quick', 'product_category': 'Lending', 
     'product_type': 'Digital Lending', 'launch_date': '2023-03-10'},
    {'product_code': 'DL002', 'product_name': 'dLoan Flexi', 'product_category': 'Lending', 
     'product_type': 'Digital Lending', 'launch_date': '2023-08-05'},
    
    # Investment
    {'product_code': 'DI001', 'product_name': 'dInvest Auto', 'product_category': 'Investment', 
     'product_type': 'Digital Investment', 'launch_date': '2023-02-28'},
    {'product_code': 'DI002', 'product_name': 'dInvest Pro', 'product_category': 'Investment', 
     'product_type': 'Digital Investment', 'launch_date': '2024-01-15'},
    
    # Insurance
    {'product_code': 'DIN001', 'product_name': 'dProtect Basic', 'product_category': 'Insurance', 
     'product_type': 'Digital Insurance', 'launch_date': '2023-05-10'},
    {'product_code': 'DIN002', 'product_name': 'dProtect Plus', 'product_category': 'Insurance', 
     'product_type': 'Digital Insurance', 'launch_date': '2023-11-20'},
]

df_products = pd.DataFrame(products_data)
df_products['is_active'] = True
df_products['description'] = df_products['product_name'] + ' - ' + df_products['product_type']
df_products.to_csv(f'{OUTPUT_DIR}/products.csv', index=False)
print(f"✅ Generated {len(df_products)} products")

# =====================================================
# 2. GENERATE CUSTOMERS
# =====================================================
print(f"\n👥 Generating {NUM_CUSTOMERS} Customers...")

customers = []
for i in range(NUM_CUSTOMERS):
    customer = {
        'customer_uuid': fake.uuid4(),
        'full_name': fake.name(),
        'email': fake.email(),
        'phone': fake.phone_number(),
        'national_id': fake.ssn(),
        'date_of_birth': fake.date_of_birth(minimum_age=18, maximum_age=80),
        'gender': random.choice(['Male', 'Female', 'Other']),
        'customer_segment': random.choices(
            ['Premium', 'Standard', 'Basic'], 
            weights=[0.1, 0.6, 0.3]
        )[0],
        'registration_date': fake.date_between(start_date='-3y', end_date='today'),
        'account_status': random.choices(
            ['Active', 'Suspended', 'Closed'], 
            weights=[0.85, 0.10, 0.05]
        )[0],
        'city': random.choice(['Bangkok', 'Chiang Mai', 'Phuket', 'Pattaya', 'Khon Kaen']),
        'country': 'Thailand'
    }
    customers.append(customer)

df_customers = pd.DataFrame(customers)
df_customers.to_csv(f'{OUTPUT_DIR}/customers.csv', index=False)
print(f"✅ Generated {len(df_customers)} customers")

# =====================================================
# 3. GENERATE TICKET CATEGORIES & ROOT CAUSES
# =====================================================
print("\n🎫 Generating Ticket Categories and Root Causes...")

categories_data = [
    {'category_code': 'LOGIN', 'category_name': 'Login Issues', 'parent_category': 'Authentication'},
    {'category_code': 'PAYMENT', 'category_name': 'Payment Failed', 'parent_category': 'Transaction'},
    {'category_code': 'APP_CRASH', 'category_name': 'App Crash', 'parent_category': 'Technical'},
    {'category_code': 'ACCOUNT', 'category_name': 'Account Access', 'parent_category': 'Authentication'},
    {'category_code': 'TRANSFER', 'category_name': 'Transfer Issues', 'parent_category': 'Transaction'},
    {'category_code': 'LOAN', 'category_name': 'Loan Application', 'parent_category': 'Product'},
    {'category_code': 'SAVING', 'category_name': 'Savings Account', 'parent_category': 'Product'},
]

df_categories = pd.DataFrame(categories_data)
df_categories.to_csv(f'{OUTPUT_DIR}/ticket_categories.csv', index=False)

root_causes_data = [
    {'root_cause_code': 'RC001', 'root_cause_name': 'App Version Bug (v1.2)', 'category': 'Technical', 'severity': 'Critical'},
    {'root_cause_code': 'RC002', 'root_cause_name': 'Database Timeout', 'category': 'Technical', 'severity': 'High'},
    {'root_cause_code': 'RC003', 'root_cause_name': 'User Error - Wrong Password', 'category': 'User', 'severity': 'Low'},
    {'root_cause_code': 'RC004', 'root_cause_name': 'API Gateway Error', 'category': 'Technical', 'severity': 'High'},
    {'root_cause_code': 'RC005', 'root_cause_name': 'KYC Document Expired', 'category': 'Compliance', 'severity': 'Medium'},
    {'root_cause_code': 'RC006', 'root_cause_name': 'Network Connectivity', 'category': 'Technical', 'severity': 'Medium'},
    {'root_cause_code': 'RC007', 'root_cause_name': 'Insufficient Balance', 'category': 'Business', 'severity': 'Low'},
    {'root_cause_code': 'RC008', 'root_cause_name': 'Third Party Payment Gateway Down', 'category': 'External', 'severity': 'Critical'},
]

df_root_causes = pd.DataFrame(root_causes_data)
df_root_causes.to_csv(f'{OUTPUT_DIR}/root_causes.csv', index=False)
print(f"✅ Generated {len(df_categories)} categories and {len(df_root_causes)} root causes")

# =====================================================
# 4. GENERATE TICKETS (with v1.2 spike)
# =====================================================
print(f"\n🎟️  Generating {NUM_TICKETS_PER_MONTH * NUM_MONTHS} Tickets...")

# App version v1.2 was released on 2024-08-15 and caused issues
V12_RELEASE_DATE = datetime(2024, 8, 15).date()
TODAY = datetime.now().date()
START_DATE = TODAY - timedelta(days=NUM_MONTHS * 30)

tickets = []
ticket_counter = 1000

for month in range(NUM_MONTHS):
    month_start = (START_DATE + timedelta(days=month * 30))
    month_end = month_start + timedelta(days=30)
    
    # Spike tickets after v1.2 release
    if V12_RELEASE_DATE <= month_start <= V12_RELEASE_DATE + timedelta(days=30):
        num_tickets = int(NUM_TICKETS_PER_MONTH * 1.5)  # 50% spike
        v12_weight = 0.4  # 40% of tickets related to v1.2
    else:
        num_tickets = NUM_TICKETS_PER_MONTH
        v12_weight = 0.05
    
    for _ in range(num_tickets):
        created_date = fake.date_between(start_date=month_start, end_date=month_end)
        
        # Determine app version
        if created_date >= V12_RELEASE_DATE:
            app_version = random.choices(['v1.1', 'v1.2'], weights=[1-v12_weight, v12_weight])[0]
        else:
            app_version = random.choice(['v1.0', 'v1.1'])
        
        # Select root cause (v1.2 more likely to be RC001)
        if app_version == 'v1.2':
            root_cause = random.choices(
                df_root_causes['root_cause_code'].tolist(),
                weights=[0.3, 0.1, 0.05, 0.15, 0.05, 0.1, 0.05, 0.2]
            )[0]
        else:
            root_cause = random.choice(df_root_causes['root_cause_code'].tolist())
        
        ticket = {
            'ticket_number': f'TKT-{ticket_counter:06d}',
            'customer_uuid': random.choice(df_customers['customer_uuid'].tolist()),
            'product_code': random.choice(df_products['product_code'].tolist()),
            'category_code': random.choice(df_categories['category_code'].tolist()),
            'root_cause_code': root_cause,
            'ticket_status': random.choices(
                ['Open', 'In Progress', 'Resolved', 'Closed'],
                weights=[0.15, 0.10, 0.25, 0.50]
            )[0],
            'priority': random.choices(
                ['Critical', 'High', 'Medium', 'Low'],
                weights=[0.05, 0.15, 0.50, 0.30]
            )[0],
            'subject': f'Issue with {random.choice(df_products["product_name"].tolist())}',
            'created_date': created_date,
            'channel': random.choice(['App', 'Web', 'Phone', 'Email']),
            'app_version': app_version,
        }
        
        # Add resolution date if closed
        if ticket['ticket_status'] in ['Resolved', 'Closed']:
            ticket['resolved_date'] = created_date + timedelta(hours=random.randint(1, 72))
            ticket['resolution_time_hours'] = random.uniform(0.5, 72)
            ticket['customer_satisfaction_score'] = random.randint(1, 5)
        else:
            ticket['resolved_date'] = None
            ticket['resolution_time_hours'] = None
            ticket['customer_satisfaction_score'] = None
        
        tickets.append(ticket)
        ticket_counter += 1

df_tickets = pd.DataFrame(tickets)
df_tickets.to_csv(f'{OUTPUT_DIR}/tickets.csv', index=False)
print(f"✅ Generated {len(df_tickets)} tickets")
print(f"   📈 Tickets with v1.2: {len(df_tickets[df_tickets['app_version'] == 'v1.2'])}")

# =====================================================
# 5. GENERATE CUSTOMER PRODUCT HOLDINGS
# =====================================================
print("\n💰 Generating Customer Product Holdings...")

holdings = []
for customer_uuid in df_customers['customer_uuid'].sample(int(NUM_CUSTOMERS * 0.7)):
    num_products = random.randint(1, 3)
    selected_products = df_products.sample(num_products)
    
    for _, product in selected_products.iterrows():
        holding = {
            'customer_uuid': customer_uuid,
            'product_code': product['product_code'],
            'activation_date': fake.date_between(start_date='-2y', end_date='today'),
            'status': random.choices(['Active', 'Inactive'], weights=[0.85, 0.15])[0],
            'balance': round(random.uniform(1000, 500000), 2) if product['product_category'] == 'Savings' else None,
            'credit_limit': round(random.uniform(10000, 300000), 2) if product['product_category'] == 'Lending' else None,
            'interest_rate': round(random.uniform(0.5, 5.0), 2),
        }
        holdings.append(holding)

df_holdings = pd.DataFrame(holdings)
df_holdings.to_csv(f'{OUTPUT_DIR}/customer_products.csv', index=False)
print(f"✅ Generated {len(df_holdings)} product holdings")

# =====================================================
# 6. GENERATE LOGIN ACCESS (for churn analysis)
# =====================================================
print("\n🔐 Generating Login Access Data...")

logins = []
for customer_uuid in df_customers['customer_uuid']:
    # Some customers are churned (no login in 30+ days)
    is_churned = random.random() < 0.15  # 15% churn rate
    
    if is_churned:
        last_login = fake.date_between(start_date='-90d', end_date='-31d')
    else:
        last_login = fake.date_between(start_date='-30d', end_date='today')
    
    # Generate login history
    num_logins = random.randint(5, 50)
    for _ in range(num_logins):
        login_date = fake.date_between(start_date=last_login - timedelta(days=60), end_date=last_login)
        login_timestamp = fake.date_time_between(start_date=login_date, end_date=login_date + timedelta(days=1))
        
        login = {
            'customer_uuid': customer_uuid,
            'login_date': login_date,
            'login_timestamp': login_timestamp,
            'session_duration_minutes': random.randint(1, 120),
            'device_type': random.choice(['Mobile', 'Desktop', 'Tablet']),
            'os_type': random.choice(['iOS', 'Android', 'Windows', 'Mac']),
            'app_version': random.choice(['v1.0', 'v1.1', 'v1.2']),
            'login_status': random.choices(['Success', 'Failed'], weights=[0.95, 0.05])[0],
        }
        logins.append(login)

df_logins = pd.DataFrame(logins)
df_logins.to_csv(f'{OUTPUT_DIR}/logins.csv', index=False)
print(f"✅ Generated {len(df_logins)} login records")

# =====================================================
# 7. GENERATE TIME DIMENSION
# =====================================================
print("\n📅 Generating Time Dimension...")

date_range = pd.date_range(start='2023-01-01', end=datetime.combine(TODAY, datetime.min.time()) + timedelta(days=30), freq='D')
time_dim = []

for date in date_range:
    time_dim.append({
        'date': date.date(),
        'year': date.year,
        'quarter': date.quarter,
        'month': date.month,
        'month_name': date.strftime('%B'),
        'week': date.isocalendar()[1],
        'day_of_month': date.day,
        'day_of_week': date.weekday(),
        'day_name': date.strftime('%A'),
        'is_weekend': date.weekday() >= 5,
        'is_holiday': False  # Can be enhanced with Thai holidays
    })

df_time = pd.DataFrame(time_dim)
df_time.to_csv(f'{OUTPUT_DIR}/time_dimension.csv', index=False)
print(f"✅ Generated {len(df_time)} time dimension records")

print("\n" + "=" * 60)
print("✨ Data Generation Complete!")
print(f"📁 All CSV files saved to: {OUTPUT_DIR}/")
print("\nGenerated files:")
print("  - customers.csv")
print("  - products.csv")
print("  - ticket_categories.csv")
print("  - root_causes.csv")
print("  - tickets.csv")
print("  - customer_products.csv")
print("  - logins.csv")
print("  - time_dimension.csv")
print("=" * 60)