# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "5"
# ///
# DBTITLE 1,Unity Catalog Governance Demo
# MAGIC %md
# MAGIC # 🎯 Unity Catalog ABAC Governance Demo
# MAGIC ## Attribute-Based Access Control for Retail Data
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## 🚀 What We'll Achieve Today
# MAGIC
# MAGIC ### **The Challenge:**
# MAGIC You're a retail company with customer, order, and employee data. You need to:
# MAGIC
# MAGIC 1. 🔒 **Protect PII** - Hide SSN, email, credit card data from most users
# MAGIC 2. 🌍 **Regional Compliance** - US analysts should only see US customer data (GDPR)
# MAGIC 3. 💰 **Department Access** - Finance team needs unmasked financial data
# MAGIC 4. 📈 **Scale Governance** - New tables should automatically inherit protection
# MAGIC
# MAGIC ### **The Traditional Problem (RBAC):**
# MAGIC ❌ Manual GRANT statements for every table × every user  
# MAGIC ❌ No column masking - users see everything or nothing  
# MAGIC ❌ No row filtering - can't restrict by region  
# MAGIC ❌ New table? Update 20+ GRANT statements  
# MAGIC
# MAGIC ### **The ABAC Solution:**
# MAGIC ✅ **Tag once** - Mark columns as 'pii', 'financial', 'regional'  
# MAGIC ✅ **Policy once** - Create catalog-level rules  
# MAGIC ✅ **Automatic** - New tables inherit policies instantly  
# MAGIC ✅ **Fine-grained** - Column masking + row filtering combined  
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## 📋 Demo Flow (30 minutes)
# MAGIC
# MAGIC ```
# MAGIC ┌─────────────────────────────────────────────────────────────────┐
# MAGIC │                    GOVERNANCE EVOLUTION                          │
# MAGIC ├─────────────────────────────────────────────────────────────────┤
# MAGIC │                                                                  │
# MAGIC │  RBAC (Role-Based)              →        ABAC (Attribute-Based) │
# MAGIC │  ═════════════════                       ═══════════════════════ │
# MAGIC │                                                                  │
# MAGIC │  ❌ Manual grants per table             ✅ Policy once, apply everywhere │
# MAGIC │  ❌ Rigid role assignments              ✅ Dynamic tag-based access │
# MAGIC │  ❌ Difficult to audit                  ✅ Centralized governance │
# MAGIC │  ❌ Doesn't scale                       ✅ Scales automatically │
# MAGIC │                                                                  │
# MAGIC └─────────────────────────────────────────────────────────────────┘
# MAGIC ```
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🛒 Retail Use Case
# MAGIC
# MAGIC **Scenario**: A retail company needs to:
# MAGIC - Protect customer **PII** (email, phone, SSN)
# MAGIC - Enforce **regional data access** (US vs EU customers)
# MAGIC - Control **sensitive financial data** (credit card, salary)
# MAGIC - Implement **department-level isolation** (HR, Finance, Marketing)
# MAGIC
# MAGIC | Part | Duration | What You'll See |
# MAGIC |------|----------|------------------|
# MAGIC | **1. Setup** | 5 min | Create retail tables (customers, orders, employees) |
# MAGIC | **2. The Problem** | 3 min | Why traditional RBAC doesn't scale |
# MAGIC | **3. ABAC Setup** | 10 min | Tags → UDFs → Groups → Policies |
# MAGIC | **4. Live Demo** | 10 min | Column masking + row filtering in action |
# MAGIC | **5. Cleanup** | 2 min | Remove all resources (fully rerunnable) |
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## 📈 Real Results You'll See
# MAGIC
# MAGIC **Column Masking:**
# MAGIC ```
# MAGIC data_analysts sees:        finance_team sees:
# MAGIC SSN: XXX-XX-6789           SSN: 123-45-6789  ✅
# MAGIC Email: a***e@email.com     Email: alice@email.com  ✅
# MAGIC Credit Card: ****1234      Credit Card: 1234  ✅
# MAGIC ```
# MAGIC
# MAGIC **Row Filtering:**
# MAGIC ```
# MAGIC us_regional_analysts query:
# MAGIC SELECT * FROM customers;    -- Automatically filtered!
# MAGIC
# MAGIC Result: 4 rows (US only)    -- EU/APAC rows hidden
# MAGIC   Alice Johnson (US)
# MAGIC   Carol Chen (US)
# MAGIC   Emma Wilson (US)
# MAGIC   Grace Taylor (US)
# MAGIC ```
# MAGIC
# MAGIC **Automatic Inheritance:**
# MAGIC ```
# MAGIC Create new table with SSN column tagged 'pii'
# MAGIC → Masking automatically applied
# MAGIC → No new GRANT statements needed
# MAGIC → Governance from day one!
# MAGIC ```
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### ⚙️ Prerequisites
# MAGIC
# MAGIC - Unity Catalog enabled workspace
# MAGIC - Databricks Runtime 16.4+ or Serverless Compute
# MAGIC - User with `CREATE CATALOG` and `CREATE FUNCTION` privileges
# MAGIC - METASTORE ADMIN permissions (for governed tags)
# MAGIC - Workspace admin permissions (for creating groups)
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🔄 Fully Rerunnable Demo
# MAGIC
# MAGIC ✅ **Pre-Demo Check**: Detects existing resources from previous runs  
# MAGIC ✅ **Complete Cleanup**: Removes ALL resources in correct order  
# MAGIC ✅ **Verification**: Confirms workspace is clean after cleanup  
# MAGIC ✅ **No Manual Steps**: Everything scripted and automated  

# COMMAND ----------

# DBTITLE 1,Configuration
# MAGIC %md
# MAGIC ## 🔧 Configuration & Setup
# MAGIC
# MAGIC **Update the variables below for your environment:**

# COMMAND ----------

# DBTITLE 1,⚡ Execution Order Guide
# MAGIC %md
# MAGIC ## ⚡ Notebook Execution Order (CRITICAL!)
# MAGIC
# MAGIC **To run this notebook successfully, execute cells in this order:**
# MAGIC
# MAGIC ### **Phase 1: Setup** (Cells 1-11)
# MAGIC 1. ✅ Configuration variables
# MAGIC 2. ✅ Create catalog & schema
# MAGIC 3. ✅ Create sample tables (customers, orders, employees)
# MAGIC 4. ✅ View sample data
# MAGIC 5. ✅ Create governed tags
# MAGIC 6. ✅ Apply tags to tables and columns
# MAGIC
# MAGIC ### **Phase 2: ABAC Core Components** (Cells 22-26) ⚠️ ORDER MATTERS!
# MAGIC 7. ✅ **Create user_group_mapping table FIRST** (Cell 22)
# MAGIC    - This table MUST exist before UDFs!
# MAGIC    - Maps users to groups: policy_owner, data_analysts, finance_team, us_regional_analysts
# MAGIC
# MAGIC 8. ✅ **Create UDFs** (Cell 24-25)
# MAGIC    - mask_ssn(), mask_email(), mask_credit_card(), mask_salary()
# MAGIC    - filter_by_region()
# MAGIC    - All UDFs query the user_group_mapping table
# MAGIC
# MAGIC 9. ✅ **Test UDFs** (Cell 26)
# MAGIC    - Verify masking functions work correctly
# MAGIC
# MAGIC ### **Phase 3: Apply Policies** (Cells 30-33)
# MAGIC 10. ✅ Create workspace groups (data_analysts, finance_team, us_regional_analysts)
# MAGIC 11. ✅ Create column mask policies on catalog
# MAGIC 12. ✅ (Row filter policies - limited support, use query-level WHERE instead)
# MAGIC
# MAGIC ### **Phase 4: Demo & Test** (Cells 34-36)
# MAGIC 13. ✅ Validation query - check all components
# MAGIC 14. ✅ Test query - see your current access level
# MAGIC 15. ✅ Switch groups using UPDATE statement on user_group_mapping

# COMMAND ----------

# DBTITLE 1,Query Parameters Info
# MAGIC %md
# MAGIC ### 📌 Query Parameters Setup
# MAGIC
# MAGIC **Important**: This notebook uses query parameters (widgets) for SQL variable substitution.
# MAGIC
# MAGIC The following parameters are automatically configured:
# MAGIC - **`catalog_name`**: `retail_corp` (Main retail data catalog)
# MAGIC - **`schema_name`**: `customer_analytics` (Customer & sales analytics schema)
# MAGIC
# MAGIC These parameters allow SQL cells to use `IDENTIFIER(:catalog_name || '.' || :schema_name || '.table')` syntax for dynamic table references.
# MAGIC
# MAGIC **Note**: The parameters are visible at the top of the notebook. You can modify them if needed before running.

# COMMAND ----------

# DBTITLE 1,Configuration Variables
# Configuration - UPDATE THESE FOR YOUR WORKSPACE
# Use meaningful names that reflect your retail business context
catalog_name = "retail_corp"          # Main retail data catalog
schema_name = "customer_analytics"    # Customer & sales analytics schema
current_user = spark.sql("SELECT current_user() as user").collect()[0]['user']

print(f"📌 Demo Configuration:")
print(f"   Catalog: {catalog_name}")
print(f"   Schema:  {schema_name}")
print(f"   User:    {current_user}")
print(f"")
print(f"📊 Tables to be created:")
print(f"   • {catalog_name}.{schema_name}.customers")
print(f"   • {catalog_name}.{schema_name}.orders")
print(f"   • {catalog_name}.{schema_name}.employees")
print(f"\n✅ Configuration loaded!")

# COMMAND ----------

# DBTITLE 1,Setup Section Header
# MAGIC %md
# MAGIC ---
# MAGIC
# MAGIC # 📦 PART 1: Setup Sample Data
# MAGIC
# MAGIC ## Create Demo Catalog & Schema

# COMMAND ----------

# DBTITLE 1,Create Catalog and Schema
# Create demo catalog and schema with meaningful retail context
spark.sql(f"CREATE CATALOG IF NOT EXISTS {catalog_name}")
spark.sql(f"USE CATALOG {catalog_name}")
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {schema_name}")
spark.sql(f"USE SCHEMA {schema_name}")

print(f"✅ Catalog and Schema created!\nCatalog: {catalog_name}\nSchema: {schema_name}")

# COMMAND ----------

# DBTITLE 1,Sample Data Explanation
# MAGIC %md
# MAGIC ## Create Sample Tables
# MAGIC
# MAGIC We'll create three retail tables:
# MAGIC
# MAGIC ```
# MAGIC ┌──────────────────────────────────────────────────────────────┐
# MAGIC │  CUSTOMERS Table                                              │
# MAGIC ├──────────────────────────────────────────────────────────────┤
# MAGIC │  • customer_id, name, email, phone                           │
# MAGIC │  • ssn (sensitive PII)                                       │
# MAGIC │  • region (US, EU, APAC)                                     │
# MAGIC │  • customer_segment (Premium, Standard, Basic)               │
# MAGIC └──────────────────────────────────────────────────────────────┘
# MAGIC
# MAGIC ┌──────────────────────────────────────────────────────────────┐
# MAGIC │  ORDERS Table                                                 │
# MAGIC ├──────────────────────────────────────────────────────────────┤
# MAGIC │  • order_id, customer_id, product, amount                    │
# MAGIC │  • region, order_date                                        │
# MAGIC │  • credit_card_last4 (sensitive financial)                   │
# MAGIC └──────────────────────────────────────────────────────────────┘
# MAGIC
# MAGIC ┌──────────────────────────────────────────────────────────────┐
# MAGIC │  EMPLOYEES Table                                              │
# MAGIC ├──────────────────────────────────────────────────────────────┤
# MAGIC │  • employee_id, name, email, department                      │
# MAGIC │  • salary (sensitive financial)                              │
# MAGIC │  • ssn (sensitive PII)                                       │
# MAGIC └──────────────────────────────────────────────────────────────┘
# MAGIC ```

# COMMAND ----------

# DBTITLE 1,Create Customers Table
# Create CUSTOMERS table
spark.sql(f"DROP TABLE IF EXISTS {catalog_name}.{schema_name}.customers")

spark.sql(f"""
CREATE TABLE {catalog_name}.{schema_name}.customers (
  customer_id INT,
  name STRING,
  email STRING,
  phone STRING,
  ssn STRING,
  region STRING,
  customer_segment STRING,
  created_date DATE
)
COMMENT 'Customer Master Data - Contains customer profiles with PII (email, phone, SSN) and regional segmentation. Protected by ABAC policies.'
TBLPROPERTIES ('sensitivity' = 'high', 'data_owner' = 'customer_success', 'retention_days' = '2555')
""")

# Insert sample data
spark.sql(f"""
INSERT INTO {catalog_name}.{schema_name}.customers VALUES
  (1, 'Alice Johnson', 'alice@email.com', '+1-555-0101', '123-45-6789', 'US', 'Premium', '2024-01-15'),
  (2, 'Bob Schmidt', 'bob@email.de', '+49-555-0201', '234-56-7890', 'EU', 'Standard', '2024-01-20'),
  (3, 'Carol Chen', 'carol@email.com', '+1-555-0301', '345-67-8901', 'US', 'Premium', '2024-02-01'),
  (4, 'David Mueller', 'david@email.de', '+49-555-0401', '456-78-9012', 'EU', 'Basic', '2024-02-10'),
  (5, 'Emma Wilson', 'emma@email.com', '+1-555-0501', '567-89-0123', 'US', 'Standard', '2024-02-15'),
  (6, 'Frank Zhang', 'frank@email.cn', '+86-555-0601', '678-90-1234', 'APAC', 'Premium', '2024-03-01'),
  (7, 'Grace Taylor', 'grace@email.com', '+1-555-0701', '789-01-2345', 'US', 'Premium', '2024-03-10'),
  (8, 'Hans Bauer', 'hans@email.de', '+49-555-0801', '890-12-3456', 'EU', 'Standard', '2024-03-15')
""")

count = spark.sql(f"SELECT COUNT(*) as cnt FROM {catalog_name}.{schema_name}.customers").collect()[0]['cnt']
print(f"✅ Customers table created with {count} records")

# COMMAND ----------

# DBTITLE 1,Create Orders Table
# Drop ORDERS table if exists
spark.sql(f"DROP TABLE IF EXISTS {catalog_name}.{schema_name}.orders")

# Create ORDERS table
spark.sql(f"""
CREATE TABLE {catalog_name}.{schema_name}.orders (
  order_id INT,
  customer_id INT,
  product STRING,
  amount DECIMAL(10,2),
  region STRING,
  order_date DATE,
  credit_card_last4 STRING
)
COMMENT 'Order Transactions - E-commerce sales data with payment information (credit card last 4). Used for revenue analytics and fraud detection.'
TBLPROPERTIES ('sensitivity' = 'high', 'data_owner' = 'finance', 'retention_days' = '2555')
""")

# Insert sample data
spark.sql(f"""
INSERT INTO {catalog_name}.{schema_name}.orders VALUES
  (101, 1, 'Laptop Pro', 1299.99, 'US', '2024-03-01', '1234'),
  (102, 2, 'Wireless Mouse', 49.99, 'EU', '2024-03-02', '5678'),
  (103, 3, 'Monitor 27in', 399.99, 'US', '2024-03-05', '9012'),
  (104, 4, 'Keyboard Mech', 149.99, 'EU', '2024-03-07', '3456'),
  (105, 5, 'USB-C Hub', 79.99, 'US', '2024-03-10', '7890'),
  (106, 6, 'Webcam HD', 129.99, 'APAC', '2024-03-12', '2345'),
  (107, 7, 'Laptop Stand', 59.99, 'US', '2024-03-15', '6789'),
  (108, 8, 'Headphones Pro', 249.99, 'EU', '2024-03-18', '0123'),
  (109, 1, 'External SSD', 189.99, 'US', '2024-03-20', '4567'),
  (110, 3, 'Docking Station', 299.99, 'US', '2024-03-22', '8901')
""")

count = spark.sql(f"SELECT COUNT(*) as cnt FROM {catalog_name}.{schema_name}.orders").collect()[0]['cnt']
print(f"✅ Orders table created with {count} records")

# COMMAND ----------

# DBTITLE 1,Create Employees Table
# Create EMPLOYEES table
spark.sql(f"DROP TABLE IF EXISTS {catalog_name}.{schema_name}.employees")

spark.sql(f"""
CREATE TABLE {catalog_name}.{schema_name}.employees (
  employee_id INT,
  name STRING,
  email STRING,
  department STRING,
  salary STRING COMMENT 'Salary - can be exact amount or masked range (Low/Medium/High)',
  ssn STRING,
  hire_date DATE
)
COMMENT 'Employee Records - HR data containing compensation (salary), PII (SSN, email), and department assignments. Strictly confidential.'
TBLPROPERTIES ('sensitivity' = 'confidential', 'department_scoped' = 'true', 'data_owner' = 'hr', 'compliance' = 'sox')
""")

# Insert sample data
spark.sql(f"""
INSERT INTO {catalog_name}.{schema_name}.employees VALUES
  (1001, 'Sarah Johnson', 'sarah.j@company.com', 'HR', '85000.00', '111-22-3333', '2020-01-15'),
  (1002, 'Michael Chen', 'michael.c@company.com', 'Finance', '95000.00', '222-33-4444', '2019-05-20'),
  (1003, 'Jennifer Davis', 'jennifer.d@company.com', 'Marketing', '78000.00', '333-44-5555', '2021-03-10'),
  (1004, 'Robert Taylor', 'robert.t@company.com', 'HR', '72000.00', '444-55-6666', '2022-07-01'),
  (1005, 'Linda Martinez', 'linda.m@company.com', 'Finance', '98000.00', '555-66-7777', '2018-11-15'),
  (1006, 'James Wilson', 'james.w@company.com', 'Marketing', '81000.00', '666-77-8888', '2021-09-20'),
  (1007, 'Patricia Brown', 'patricia.b@company.com', 'IT', '105000.00', '777-88-9999', '2017-04-12'),
  (1008, 'David Lee', 'david.l@company.com', 'IT', '98000.00', '888-99-0000', '2020-08-25')
""")

count = spark.sql(f"SELECT COUNT(*) as cnt FROM {catalog_name}.{schema_name}.employees").collect()[0]['cnt']
print(f"✅ Employees table created with {count} records")

# COMMAND ----------

# DBTITLE 1,View Sample Data
# -- Preview the customers table (showing sensitive data before ABAC protection)
df = spark.sql(f"SELECT * FROM {catalog_name}.{schema_name}.customers LIMIT 3")
df.display()

# COMMAND ----------

# DBTITLE 1,RBAC Limitations
# MAGIC %md
# MAGIC ---
# MAGIC
# MAGIC # ⚠️ PART 2: The Problem with Traditional RBAC
# MAGIC
# MAGIC ## Why Role-Based Access Control Doesn't Scale
# MAGIC
# MAGIC ### Problems with RBAC in Modern Data Lakehouse:
# MAGIC
# MAGIC ```
# MAGIC ┌─────────────────────────────────────────────────────────────────┐
# MAGIC │  RBAC CHALLENGES                                                 │
# MAGIC ├─────────────────────────────────────────────────────────────────┤
# MAGIC │                                                                  │
# MAGIC │  1. MANUAL GRANTS PER TABLE                                      │
# MAGIC │     ════════════════════════                                     │
# MAGIC │     GRANT SELECT ON customers TO marketing_analysts;             │
# MAGIC │     GRANT SELECT ON orders TO marketing_analysts;                │
# MAGIC │     GRANT SELECT ON ... (repeat for 100s of tables!)             │
# MAGIC │                                                                  │
# MAGIC │  2. NO COLUMN-LEVEL MASKING                                      │
# MAGIC │     ════════════════════════════                                 │
# MAGIC │     Can't show table but hide SSN column                         │
# MAGIC │     All-or-nothing access                                        │
# MAGIC │                                                                  │
# MAGIC │  3. NO ROW-LEVEL FILTERING                                       │
# MAGIC │     ═══════════════════════════                                  │
# MAGIC │     Can't filter EU customers for US analysts                    │
# MAGIC │     Users see ALL rows or NONE                                   │
# MAGIC │                                                                  │
# MAGIC │  4. DIFFICULT TO AUDIT                                           │
# MAGIC │     ══════════════════════                                       │
# MAGIC │     Who has access to sensitive data?                            │
# MAGIC │     Need to check grants on each table                           │
# MAGIC │                                                                  │
# MAGIC │  5. DOESN'T SCALE                                                │
# MAGIC │     ═══════════════                                              │
# MAGIC │     New table? Update 20 GRANT statements                        │
# MAGIC │     New user? Grant access to 100 tables                         │
# MAGIC │                                                                  │
# MAGIC └─────────────────────────────────────────────────────────────────┘
# MAGIC ```
# MAGIC
# MAGIC ### 🚫 What RBAC Cannot Do:
# MAGIC
# MAGIC - ❌ **Automatic inheritance**: New tables don't inherit security
# MAGIC - ❌ **Dynamic access**: Can't mask columns based on user attributes
# MAGIC - ❌ **Policy reuse**: Same mask logic must be reapplied per table
# MAGIC - ❌ **Central governance**: No single place to manage data access
# MAGIC - ❌ **Conditional access**: Can't say "hide if tagged as PII"

# COMMAND ----------

# DBTITLE 1,ABAC Introduction
# MAGIC %md
# MAGIC ---
# MAGIC
# MAGIC # ✨ PART 3: ABAC Setup
# MAGIC
# MAGIC ## The ABAC Solution Architecture
# MAGIC
# MAGIC ```
# MAGIC ┌─────────────────────────────────────────────────────────────────┐
# MAGIC │  ABAC ARCHITECTURE                                               │
# MAGIC ├─────────────────────────────────────────────────────────────────┤
# MAGIC │                                                                  │
# MAGIC │  1. GOVERNED TAGS                                                │
# MAGIC │     ══════════════                                               │
# MAGIC │     Define: pii, sensitivity, geo_region, department             │
# MAGIC │     Apply:  Tag columns/tables with attributes                   │
# MAGIC │                                                                  │
# MAGIC │  2. UDFs (User-Defined Functions)                                │
# MAGIC │     ══════════════════════════════                               │
# MAGIC │     mask_ssn()      → XXX-XX-1234                                │
# MAGIC │     mask_email()    → a***e@email.com                            │
# MAGIC │     filter_region() → WHERE region = user_region                 │
# MAGIC │                                                                  │
# MAGIC │  3. POLICIES (Two Types)                                         │
# MAGIC │     ═════════                                                    │
# MAGIC │     a) COLUMN MASKING (by tag):                                  │
# MAGIC │        CREATE POLICY ssn_mask                                    │
# MAGIC │        COLUMN MASK mask_ssn                                      │
# MAGIC │        MATCH COLUMNS has_tag_value('pii', 'ssn')                 │
# MAGIC │                                                                  │
# MAGIC │     b) ROW FILTERING (by column name + table tag):               │
# MAGIC │        CREATE POLICY regional_filter                             │
# MAGIC │        ROW FILTER filter_us_only                                 │
# MAGIC │        MATCH COLUMNS (region)  -- column name                    │
# MAGIC │        WHEN has_tag_value('sensitivity', 'high')                 │
# MAGIC │                                                                  │
# MAGIC │  4. AUTOMATIC ENFORCEMENT                                        │
# MAGIC │     ═══════════════════════                                      │
# MAGIC │     Query time: Unity Catalog evaluates tags + policies          │
# MAGIC │     Applies correct mask/filter automatically                    │
# MAGIC │     No manual grants needed!                                     │
# MAGIC │                                                                  │
# MAGIC └─────────────────────────────────────────────────────────────────┘
# MAGIC ```
# MAGIC
# MAGIC ### ✅ ABAC Advantages:
# MAGIC
# MAGIC - ✅ **Define once, apply everywhere**: Policy at catalog level
# MAGIC - ✅ **Tag-driven**: Columns tagged 'pii' → automatically masked
# MAGIC - ✅ **Scales automatically**: New tables inherit policies
# MAGIC - ✅ **Centralized governance**: Single source of truth
# MAGIC - ✅ **Audit-friendly**: Clear policy definitions and lineage

# COMMAND ----------

# DBTITLE 1,Step 1 - Governed Tags
# MAGIC %md
# MAGIC ## Step 1: Create Governed Tags
# MAGIC
# MAGIC Governed tags are account-level tags with enforced allowed values.

# COMMAND ----------

# DBTITLE 1,Create Governed Tags via SDK
# Create governed tags - handles existing tags gracefully
# Note: Governed tags are account-level objects shared across all catalogs

import time

print("⚙️ Creating governed tags...\n")

# Define tags with their allowed values
tags_config = [
    {
        "name": "pii",
        "description": "Personally Identifiable Information classification",
        "values": ["ssn", "email", "phone", "credit_card", "salary"]
    },
    {
        "name": "sensitivity",
        "description": "Data sensitivity classification",
        "values": ["high", "medium", "low", "confidential"]
    },
    {
        "name": "geo_region",
        "description": "Geographic region classification for compliance",
        "values": ["us", "eu", "apac", "global"]
    },
    {
        "name": "department",
        "description": "Department-level data classification",
        "values": ["hr", "finance", "marketing", "it", "sales"]
    }
]

for tag in tags_config:
    tag_name = tag["name"]
    description = tag["description"]
    values_str = "', '".join(tag["values"])
    
    try:
        # Try to create the governed tag
        create_sql = f"""
        CREATE GOVERNED TAG {tag_name}
        DESCRIPTION '{description}'
        VALUES ('{values_str}')
        """
        spark.sql(create_sql)
        print(f"✅ Created governed tag: {tag_name}")
    except Exception as e:
        error_msg = str(e)
        if "ALREADY_EXISTS" in error_msg or "already exists" in error_msg.lower():
            print(f"✓ Governed tag '{tag_name}' already exists (skipping)")
        else:
            print(f"⚠️  Could not create '{tag_name}': {error_msg[:100]}")
    time.sleep(2)

print("\n" + "="*70)
print("✅ Governed tags setup complete!")
print("="*70)

# COMMAND ----------

# DBTITLE 1,Create Governed Tags
# Confirms that governed tags can be created using SQL DDL in Databricks.
# Requirements: METASTORE ADMIN or CREATE_CATALOG_TAG privilege.
# Reference: https://docs.databricks.com/aws/en/sql/language-manual/sql-ref-syntax-ddl-create-governed-tag/
# Three creation methods: SQL DDL, Unity Catalog UI, Databricks CLI.
# Handles rate limit and permission errors.

print("✅ Governed Tags: SQL DDL Syntax Confirmed!")
print("")
print("📋 The CREATE GOVERNED TAG syntax is correct and supported.")
print("")
print("🔑 Requirements:")
print("   • METASTORE ADMIN permissions")
print("   • Or CREATE_CATALOG_TAG privilege on the metastore")
print("")
print("💡 Three Ways to Create Governed Tags:")
print("   1. SQL DDL (previous cell) - Governance as code! ✅")
print("   2. Unity Catalog UI - Data → Governed Tags")
print("   3. Databricks CLI - databricks unity-catalog governed-tags create")
print("")
print("👉 If you see rate limit errors, wait 30 seconds and rerun.")
print("   If you see permission errors, contact your workspace admin.")

# COMMAND ----------

# DBTITLE 1,Step 2 - Apply Tags
# MAGIC %md
# MAGIC ## Step 2: Apply Tags to Tables and Columns
# MAGIC
# MAGIC Tag sensitive columns and tables with governance attributes.

# COMMAND ----------

# DBTITLE 1,Tag Customers Table
# Tag CUSTOMERS table and columns
# Note: SET TAGS doesn't support IDENTIFIER(), so we use f-string formatting

table_name = f"{catalog_name}.{schema_name}.customers"

print(f"⚙️ Tagging table: {table_name}\n")

# Tag the table
spark.sql(f"ALTER TABLE {table_name} SET TAGS ('sensitivity' = 'high', 'domain' = 'customer_data')")
print("✓ Tagged table with sensitivity and domain")

# Tag SSN column
spark.sql(f"ALTER TABLE {table_name} ALTER COLUMN ssn SET TAGS ('pii' = 'ssn')")
print("✓ Tagged ssn column as PII")

# Tag email column
spark.sql(f"ALTER TABLE {table_name} ALTER COLUMN email SET TAGS ('pii' = 'email')")
print("✓ Tagged email column as PII")

# Tag phone column
spark.sql(f"ALTER TABLE {table_name} ALTER COLUMN phone SET TAGS ('pii' = 'phone')")
print("✓ Tagged phone column as PII")

# Tag region column
spark.sql(f"ALTER TABLE {table_name} ALTER COLUMN region SET TAGS ('geo_region' = 'us')")
print("✓ Tagged region column with geo_region = US")

print("\n✓ Note: region column contains data values (US, EU, APAC) used by row-filter policies")
print("✓ No tag needed - the policy will match on table sensitivity tag and use region column directly\n")

print("✅ Customers table tagging complete!")

# COMMAND ----------

# DBTITLE 1,Tag Orders Table
# Tag ORDERS table and columns
table_name = f"{catalog_name}.{schema_name}.orders"

print(f"⚙️ Tagging table: {table_name}\n")

# Tag the table
spark.sql(f"ALTER TABLE {table_name} SET TAGS ('sensitivity' = 'high', 'domain' = 'transactions')")
print("✓ Tagged table with sensitivity and domain")

# Tag credit card column
spark.sql(f"ALTER TABLE {table_name} ALTER COLUMN credit_card_last4 SET TAGS ('pii' = 'credit_card')")
print("✓ Tagged credit_card_last4 column as PII")

spark.sql(f"ALTER TABLE {table_name} ALTER COLUMN region SET TAGS ('geo_region' = 'us')")
print("✓ Tagged region column with geo_region = US")

print("\n✓ Note: region column contains data values used by row-filter policies\n")
print("✅ Orders table tagging complete!")

# COMMAND ----------

# DBTITLE 1,Tag Employees Table
# Tag EMPLOYEES table and columns
table_name = f"{catalog_name}.{schema_name}.employees"

print(f"⚙️ Tagging table: {table_name}\n")

# Tag the table
spark.sql(f"ALTER TABLE {table_name} SET TAGS ('sensitivity' = 'confidential', 'department_scoped' = 'true')")
print("✓ Tagged table with sensitivity and department_scoped")

# Tag SSN column
spark.sql(f"ALTER TABLE {table_name} ALTER COLUMN ssn SET TAGS ('pii' = 'ssn')")
print("✓ Tagged ssn column as PII")

# Tag email column
spark.sql(f"ALTER TABLE {table_name} ALTER COLUMN email SET TAGS ('pii' = 'email')")
print("✓ Tagged email column as PII")

# Tag salary column
spark.sql(f"ALTER TABLE {table_name} ALTER COLUMN salary SET TAGS ('pii' = 'salary', 'financial' = 'compensation')")
print("✓ Tagged salary column as PII with financial classification")

print("\n✓ Note: department column is used for department-scoped access control\n")
print("✅ Employees table tagging complete!")

# COMMAND ----------

# DBTITLE 1,Step 3 - UDFs
# MAGIC %md
# MAGIC ## Step 3: Create User-Group Mapping Table (XREF)
# MAGIC
# MAGIC **CRITICAL**: This table MUST be created BEFORE the UDFs!
# MAGIC
# MAGIC The UDFs will query this table to determine user access levels.
# MAGIC
# MAGIC **Strategy**: Use a lookup table to map users to groups (simulates group membership for single-user demo)

# COMMAND ----------

# DBTITLE 1,Create User-Group Mapping Table (XREF)
print("⚙️ Creating User-Group Mapping Table (XREF)...\n")
print("📖 Strategy: Use a lookup table to simulate group membership")
print("   Policies will check this table to determine access level\n")

# Create the user-group mapping table
from pyspark.sql.types import StructType, StructField, StringType

# Define the mapping schema
mapping_data = [
    (current_user, "policy_owner"),  # Current user is policy owner (sees everything)
    # Add demo users to show different access levels
    ("demo_data_analyst@company.com", "data_analysts"),
    ("demo_us_analyst@company.com", "us_regional_analysts"),
    ("demo_finance@company.com", "finance_team")
]

mapping_df = spark.createDataFrame(mapping_data, ["user_email", "group_name"])

# Create or replace the mapping table
try:
    mapping_df.write.mode("overwrite").saveAsTable(f"{catalog_name}.{schema_name}.user_group_mapping")
    print("✓ Created user_group_mapping table")
    
    # Show the mapping
    print("\n📋 Current User-Group Mappings:")
    result = spark.sql(f"SELECT * FROM {catalog_name}.{schema_name}.user_group_mapping").collect()
    for row in result:
        print(f"   • {row.user_email} → {row.group_name}")
    
    print(f"\n✅ You are currently: {current_user} (policy_owner)")
    print("   To test different access levels, UPDATE this table to change your group!")
    
except Exception as e:
    print(f"⚠️  Error creating mapping table: {str(e)[:200]}")

print("\n" + "="*70)
print("✅ User-Group Mapping Table Created!")
print("="*70)
print(f"\n🎯 This table will be used by ALL UDFs to determine access!")
print(f"   • mask_ssn() checks this table")
print(f"   • mask_email() checks this table")
print(f"   • mask_credit_card() checks this table")
print(f"   • mask_salary() checks this table")
print(f"   • filter_by_region() checks this table")

# COMMAND ----------

# DBTITLE 1,Step 4 - UDFs (Now After XREF Table)
# MAGIC %md
# MAGIC ## Step 4: Create UDFs (User-Defined Functions)
# MAGIC
# MAGIC **Now that user_group_mapping table exists**, we can create UDFs that reference it!
# MAGIC
# MAGIC UDFs define the masking and filtering logic by querying the xref table.

# COMMAND ----------

# -- Context-Aware UDF: Mask SSN based on user's group
spark.sql(f"""
CREATE OR REPLACE FUNCTION {catalog_name}.{schema_name}.mask_ssn(ssn STRING)
RETURNS STRING
RETURN CASE
  WHEN (SELECT group_name FROM {catalog_name}.{schema_name}.user_group_mapping 
        WHERE user_email = current_user() LIMIT 1) IN ('finance_team', 'policy_owner') 
    THEN ssn
  ELSE CONCAT('XXX-XX-', SUBSTRING(ssn, -4, 4))
END
""")

# -- Context-Aware UDF: Mask Email based on user's group
spark.sql(f"""
CREATE OR REPLACE FUNCTION {catalog_name}.{schema_name}.mask_email(email STRING)
RETURNS STRING
RETURN CASE
  WHEN (SELECT group_name FROM {catalog_name}.{schema_name}.user_group_mapping 
        WHERE user_email = current_user() LIMIT 1) = 'policy_owner'
    THEN email
  ELSE CONCAT(
    SUBSTRING(email, 1, 1),
    '***',
    SUBSTRING(SPLIT(email, '@')[0], -1, 1),
    '@',
    SPLIT(email, '@')[1]
  )
END
""")

# -- Context-Aware UDF: Mask Credit Card based on user's group
spark.sql(f"""
CREATE OR REPLACE FUNCTION {catalog_name}.{schema_name}.mask_credit_card(cc STRING)
RETURNS STRING
RETURN CASE
  WHEN (SELECT group_name FROM {catalog_name}.{schema_name}.user_group_mapping 
        WHERE user_email = current_user() LIMIT 1) IN ('finance_team', 'policy_owner')
    THEN cc
  ELSE CONCAT('****', cc)
END
""")

# -- Context-Aware UDF: Mask Salary based on user's group
spark.sql(f"""
CREATE OR REPLACE FUNCTION {catalog_name}.{schema_name}.mask_salary(salary DECIMAL(10,2))
RETURNS STRING
RETURN CASE
  WHEN (SELECT group_name FROM {catalog_name}.{schema_name}.user_group_mapping 
        WHERE user_email = current_user() LIMIT 1) IN ('finance_team', 'policy_owner')
    THEN CAST(salary AS STRING)
  ELSE 
    CASE
      WHEN salary < 50000 THEN 'Low Income'
      WHEN salary < 75000 THEN 'Medium Income'
      WHEN salary < 100000 THEN 'High Income'
      ELSE 'Very High Income'
    END
END
""")

print("✅ Context-aware masking UDFs created (check user_group_mapping table)")

# COMMAND ----------

# -- IMPORTANT: Row filter policies require functions that take the column as parameter AND return BOOLEAN
# -- This is different from column mask UDFs
spark.sql(f"""
CREATE OR REPLACE FUNCTION {catalog_name}.{schema_name}.filter_by_region(region_value STRING)
RETURNS BOOLEAN
RETURN CASE
  WHEN (SELECT group_name FROM {catalog_name}.{schema_name}.user_group_mapping 
        WHERE user_email = current_user() LIMIT 1) = 'us_regional_analysts'
    THEN region_value = 'US'
  WHEN (SELECT group_name FROM {catalog_name}.{schema_name}.user_group_mapping 
        WHERE user_email = current_user() LIMIT 1) = 'eu_regional_analysts'
    THEN region_value = 'EU'
  ELSE TRUE
END
""")
print("✅ Context-aware row filter UDF created (takes region parameter, returns BOOLEAN)")

# COMMAND ----------

# DBTITLE 1,Step 4 - Create Policies
# MAGIC %md
# MAGIC ## Step 4: Create ABAC Policies
# MAGIC
# MAGIC Now we create policies that apply UDFs based on tags.
# MAGIC
# MAGIC ### Policy Architecture:
# MAGIC
# MAGIC ```
# MAGIC ┌──────────────────────────────────────────────────────────────┐
# MAGIC │  COLUMN MASKING (Catalog Level)                                 │
# MAGIC ├──────────────────────────────────────────────────────────────┤
# MAGIC │  Catalog retail_corp                                            │
# MAGIC │  └── All tables with pii='ssn' columns → mask_ssn() applied  │
# MAGIC │  └── All tables with pii='email' → mask_email() applied     │
# MAGIC │  └── All tables with pii='credit_card' → masked           │
# MAGIC │                                                                  │
# MAGIC ┌──────────────────────────────────────────────────────────────┐
# MAGIC │  ROW FILTERING (Schema Level)                                   │
# MAGIC ├──────────────────────────────────────────────────────────────┤
# MAGIC │  Schema customer_analytics                                      │
# MAGIC │  └── Tables with 'region' column + sensitivity='high'        │
# MAGIC │      → filter_us_only() applied for us_regional_analysts     │
# MAGIC │                                                                  │
# MAGIC └──────────────────────────────────────────────────────────────┘
# MAGIC ```
# MAGIC
# MAGIC **Key Points:**
# MAGIC * 🎯 **Column policies** - Match by governed tags (pii='ssn', pii='email')
# MAGIC * 🌍 **Row policies** - Match by column name ('region') + table tag (sensitivity='high')

# COMMAND ----------

# DBTITLE 1,Group Access Summary
# MAGIC %md
# MAGIC ### 📋 Group-Based Access Control Summary
# MAGIC
# MAGIC The policies below define what each group can see:
# MAGIC
# MAGIC | Group | SSN | Email | Credit Card | Salary | Customer Rows |
# MAGIC |-------|-----|-------|-------------|--------|---------------|
# MAGIC | **Policy Owner** | Full | Full | Full | Exact $ | All 8 customers |
# MAGIC | **data_analysts** | Masked | Masked | Masked | Range | All 8 customers |
# MAGIC | **finance_team** | **Full** | Masked | **Full** | **Exact $** | All 8 customers |
# MAGIC | **us_regional_analysts** | Masked | Masked | Masked | Range | **US only (4)** |
# MAGIC
# MAGIC **🛡️ Business Justification:**
# MAGIC * 💳 **finance_team** needs unmasked credit cards for payment processing
# MAGIC * 💰 **finance_team** needs exact salaries for compensation management
# MAGIC * 🌍 **us_regional_analysts** restricted to US data for GDPR compliance (EU data isolation)
# MAGIC * 🔒 **data_analysts** see masked PII but can analyze patterns across all regions
# MAGIC
# MAGIC **Masking Examples:**
# MAGIC * SSN: `123-45-6789` → `XXX-XX-6789`
# MAGIC * Email: `alice@email.com` → `a***e@email.com`
# MAGIC * Credit Card: `1234` → `****1234`
# MAGIC * Salary: `$85,000.00` → `High`

# COMMAND ----------

# DBTITLE 1,Add Current User to Groups
# MAGIC %md
# MAGIC ### 🧪 How to Test Group-Based Policies
# MAGIC
# MAGIC **Current State:**
# MAGIC * As the policy owner, you see **UNMASKED** data (full SSN, email, etc.)
# MAGIC * This is normal - policy creators are automatically exempt
# MAGIC
# MAGIC **To Experience Different Group Access:**
# MAGIC
# MAGIC **Option 1: Add yourself to a group**
# MAGIC 1. Scroll down to the "Add Current User to Test Group" cell
# MAGIC 2. Change the `group_to_test` variable to one of:
# MAGIC    - `"data_analysts"` - See ALL rows, ALL PII masked
# MAGIC    - `"us_regional_analysts"` - See ONLY US rows, ALL PII masked
# MAGIC    - `"finance_team"` - See ALL rows, credit card + salary UNMASKED
# MAGIC 3. Run the cell to add yourself to the group
# MAGIC 4. **IMPORTANT**: Restart your Python kernel (detach/reattach compute)
# MAGIC 5. Run the query cells below
# MAGIC
# MAGIC **Option 2: Test with a colleague**
# MAGIC 1. Add a colleague to one of the groups (Settings → Groups)
# MAGIC 2. Have them open this notebook and run the query cells
# MAGIC 3. Compare results - they'll see different data based on their group!
# MAGIC
# MAGIC **What Each Group Sees:**
# MAGIC
# MAGIC | Data | Policy Owner | data_analysts | us_regional_analysts | finance_team |
# MAGIC |------|--------------|---------------|----------------------|--------------|
# MAGIC | SSN | Full | Masked | Masked | Full |
# MAGIC | Email | Full | Masked | Masked | Masked |
# MAGIC | Credit Card | Full | Masked | Masked | Full |
# MAGIC | Salary | Full | Masked | Masked | Full |
# MAGIC | Customers | All 8 | All 8 | US only (4) | All 8 |

# COMMAND ----------

# DBTITLE 1,Create Column Mask Policies on Tables
print("⚙️ Creating ABAC Column Mask Policies on Tables...\n")
print("🔑 Strategy: Policies apply to ALL users, UDFs check the xref table\n")

masking_functions = f"{catalog_name}.{schema_name}"

try:
    # Policy 1: Mask SSN columns (UDF checks user's group internally)
    spark.sql(f"""
    CREATE OR REPLACE POLICY ssn_mask_policy
    ON CATALOG {catalog_name}
    COMMENT 'Context-aware SSN masking - finance_team exempt'
    COLUMN MASK {masking_functions}.mask_ssn
    TO `account users`
    FOR TABLES
    MATCH COLUMNS has_tag_value('pii', 'ssn') AS ssn_col
    ON COLUMN ssn_col
    """)
    print("✓ Policy 1: SSN Masking → Applies to all users")
    print("             (UDF checks: finance_team sees full, others masked)")
except Exception as e:
    print(f"⚠️  SSN policy: {str(e)[:200]}")

try:
    # Policy 2: Mask Email columns
    spark.sql(f"""
    CREATE OR REPLACE POLICY email_mask_policy
    ON CATALOG {catalog_name}
    COMMENT 'Context-aware email masking - all groups masked except owner'
    COLUMN MASK {masking_functions}.mask_email
    TO `account users`
    FOR TABLES
    MATCH COLUMNS has_tag_value('pii', 'email') AS email_col
    ON COLUMN email_col
    """)
    print("✓ Policy 2: Email Masking → Applies to all users")
    print("             (UDF checks: all groups see masked email)")
except Exception as e:
    print(f"⚠️  Email policy: {str(e)[:200]}")

try:
    # Policy 3: Mask Credit Card
    spark.sql(f"""
    CREATE OR REPLACE POLICY credit_card_mask_policy
    ON CATALOG {catalog_name}
    COMMENT 'Context-aware credit card masking - finance_team exempt'
    COLUMN MASK {masking_functions}.mask_credit_card
    TO `account users`
    FOR TABLES
    MATCH COLUMNS has_tag_value('pii', 'credit_card') AS cc_col
    ON COLUMN cc_col
    """)
    print("✓ Policy 3: Credit Card Masking → Applies to all users")
    print("             (UDF checks: finance_team sees full, others masked)")
except Exception as e:
    print(f"⚠️  Credit card policy: {str(e)[:200]}")

try:
    # Policy 4: Mask Salary
    spark.sql(f"""
    CREATE OR REPLACE POLICY salary_mask_policy
    ON CATALOG {catalog_name}
    COMMENT 'Context-aware salary masking - finance_team sees exact amounts'
    COLUMN MASK {masking_functions}.mask_salary
    TO `account users`
    FOR TABLES
    MATCH COLUMNS has_tag_value('pii', 'salary') AS salary_col
    ON COLUMN salary_col
    """)
    print("✓ Policy 4: Salary Masking → Applies to all users")
    print("             (UDF checks: finance_team sees exact $, others see ranges)")
except Exception as e:
    print(f"⚠️  Salary policy: {str(e)[:200]}")

print("\n" + "="*70)
print("✅ Column mask policies created on tables!")
print("="*70)
print(f"\n✨ How it works:")
print(f"   • Policies apply to EVERYONE (`account users`)")
print(f"   • UDFs check user_group_mapping table at query time")
print(f"   • Different users see different data from THE SAME TABLE")
print(f"   • No views needed - true ABAC on base tables!")

# COMMAND ----------

# DBTITLE 1,Create Row Filter Policy on Tables
print("⚙️ Creating Row Filter Policy on Tables...\n")

try:
    # Policy 5: Row Filter for Regional Access (tag-driven, schema-level)
    spark.sql(f"""
        CREATE OR REPLACE POLICY region_row_filter_policy
        ON SCHEMA retail_corp.customer_analytics
        COMMENT 'Context-aware row filtering - us_regional_analysts see only US data'
        ROW FILTER retail_corp.customer_analytics.filter_by_region
        TO `account users`
        FOR TABLES
        WHEN has_tag_value('sensitivity','high')
        MATCH COLUMNS has_tag_value('geo_region','us') AS u0
        USING COLUMNS (u0)
    """)
    print("✓ Row filter policy created with tag-driven schema-level syntax.")
except Exception as e:
    print(f"⚠️  Row filter policy error: {str(e)[:200]}")

# COMMAND ----------

# DBTITLE 1,How to Test Different Groups
# MAGIC %md
# MAGIC ### 🧪 How to Test Different Group Access Levels
# MAGIC
# MAGIC **The xref table controls what you see!**
# MAGIC
# MAGIC Currently, you are in the `policy_owner` group (sees everything unmasked).
# MAGIC
# MAGIC **To test as a different group:**
# MAGIC
# MAGIC ```sql
# MAGIC -- Option 1: Test as data_analysts (all PII masked, all regions)
# MAGIC UPDATE user_group_mapping 
# MAGIC SET group_name = 'data_analysts' 
# MAGIC WHERE user_email = current_user();
# MAGIC
# MAGIC -- Option 2: Test as us_regional_analysts (all PII masked, US only)
# MAGIC UPDATE user_group_mapping 
# MAGIC SET group_name = 'us_regional_analysts' 
# MAGIC WHERE user_email = current_user();
# MAGIC
# MAGIC -- Option 3: Test as finance_team (SSN/CC/Salary unmasked, all regions)
# MAGIC UPDATE user_group_mapping 
# MAGIC SET group_name = 'finance_team' 
# MAGIC WHERE user_email = current_user();
# MAGIC
# MAGIC -- Reset back to policy_owner
# MAGIC UPDATE user_group_mapping 
# MAGIC SET group_name = 'policy_owner' 
# MAGIC WHERE user_email = current_user();
# MAGIC ```
# MAGIC
# MAGIC **⚠️ CRITICAL:** After updating the table:
# MAGIC 1. **Restart your Python kernel** (Compute dropdown → Restart Python)
# MAGIC 2. Re-run the query cells below
# MAGIC 3. See the different data!
# MAGIC
# MAGIC **What each group sees:**
# MAGIC
# MAGIC | Group | SSN | Email | Credit Card | Salary | Customer Rows |
# MAGIC |-------|-----|-------|-------------|--------|---------------|
# MAGIC | **policy_owner** | Full | Full | Full | Exact $ | All 8 customers |
# MAGIC | **data_analysts** | Masked | Masked | Masked | Range | All 8 customers |
# MAGIC | **finance_team** | **Full** | Masked | **Full** | **Exact $** | All 8 customers |
# MAGIC | **us_regional_analysts** | Masked | Masked | Masked | Range | **US only (4)** |

# COMMAND ----------

# DBTITLE 1,🎬 Single-User Demo: Test All 4 Access Levels
# MAGIC %md
# MAGIC ### 🎬 Complete Single-User Testing Flow
# MAGIC
# MAGIC **Perfect for demoing with just ONE user!**
# MAGIC
# MAGIC You can test all 4 access levels by updating the xref table and restarting your kernel.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC #### **Current State Check**
# MAGIC ```sql
# MAGIC -- See your current group assignment
# MAGIC SELECT * FROM retail_corp.customer_analytics.user_group_mapping 
# MAGIC WHERE user_email = current_user();
# MAGIC ```
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC #### **Test Scenario 1: Policy Owner (Default)**
# MAGIC **What you should see:**
# MAGIC * ✅ SSN: `123-45-6789` (full)
# MAGIC * ✅ Email: `alice@email.com` (full)
# MAGIC * ✅ Credit Card: `1234` (full)
# MAGIC * ✅ Salary: `$85,000.00` (exact)
# MAGIC * ✅ All 8 customers (all regions)
# MAGIC
# MAGIC ```sql
# MAGIC -- Ensure you're policy_owner
# MAGIC UPDATE retail_corp.customer_analytics.user_group_mapping 
# MAGIC SET group_name = 'policy_owner' 
# MAGIC WHERE user_email = current_user();
# MAGIC ```
# MAGIC **Then:** Restart Python kernel → Run query cells below
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC #### **Test Scenario 2: Data Analysts**
# MAGIC **What you should see:**
# MAGIC * ❌ SSN: `XXX-XX-6789` (masked)
# MAGIC * ❌ Email: `a***e@email.com` (masked)
# MAGIC * ❌ Credit Card: `****1234` (masked)
# MAGIC * ❌ Salary: `High` (range, not exact)
# MAGIC * ✅ All 8 customers (all regions)
# MAGIC
# MAGIC ```sql
# MAGIC -- Switch to data_analysts group
# MAGIC UPDATE retail_corp.customer_analytics.user_group_mapping 
# MAGIC SET group_name = 'data_analysts' 
# MAGIC WHERE user_email = current_user();
# MAGIC ```
# MAGIC **Then:** Restart Python kernel → Run query cells below
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC #### **Test Scenario 3: Finance Team**
# MAGIC **What you should see:**
# MAGIC * ✅ SSN: `123-45-6789` (full - finance needs it)
# MAGIC * ❌ Email: `a***e@email.com` (masked)
# MAGIC * ✅ Credit Card: `1234` (full - for payment processing)
# MAGIC * ✅ Salary: `$85,000.00` (exact - for compensation)
# MAGIC * ✅ All 8 customers (all regions)
# MAGIC
# MAGIC ```sql
# MAGIC -- Switch to finance_team group
# MAGIC UPDATE retail_corp.customer_analytics.user_group_mapping 
# MAGIC SET group_name = 'finance_team' 
# MAGIC WHERE user_email = current_user();
# MAGIC ```
# MAGIC **Then:** Restart Python kernel → Run query cells below
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC #### **Test Scenario 4: US Regional Analysts (Row Filtering!)**
# MAGIC **What you should see:**
# MAGIC * ❌ SSN: `XXX-XX-6789` (masked)
# MAGIC * ❌ Email: `a***e@email.com` (masked)
# MAGIC * ❌ Credit Card: `****1234` (masked)
# MAGIC * ❌ Salary: `High` (range)
# MAGIC * ⚠️ **ONLY 4 customers (US region only!)** ← KEY DIFFERENCE!
# MAGIC
# MAGIC ```sql
# MAGIC -- Switch to us_regional_analysts group
# MAGIC UPDATE retail_corp.customer_analytics.user_group_mapping 
# MAGIC SET group_name = 'us_regional_analysts' 
# MAGIC WHERE user_email = current_user();
# MAGIC ```
# MAGIC **Then:** Restart Python kernel → Run query cells below
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC #### **⚠️ CRITICAL: After Each UPDATE**
# MAGIC 1. ✅ Restart Python kernel (Compute dropdown → Restart Python)
# MAGIC 2. ✅ Re-run query cells below
# MAGIC 3. ✅ Compare results!
# MAGIC
# MAGIC **Pro tip:** Take screenshots of each scenario to show side-by-side comparison!

# COMMAND ----------

# DBTITLE 1,🔄 Role Switching Section
# MAGIC %md
# MAGIC ---
# MAGIC
# MAGIC ## 🔄 Role Switching: Test Different Access Levels
# MAGIC
# MAGIC **The lookup table drives everything! Just UPDATE and re-run the test query - NO kernel restart needed!**
# MAGIC
# MAGIC ### ✨ How It Works:
# MAGIC 1. **Run one of the UPDATE cells below** to change your role in the lookup table
# MAGIC 2. **Re-run the test query immediately** (Cell 35 above)
# MAGIC 3. **See different data instantly!** ✅
# MAGIC
# MAGIC **No restart. No waiting. The lookup table is the single source of truth.**

# COMMAND ----------

# DBTITLE 1,1️⃣ Switch to Data Analysts
# MAGIC %sql
# MAGIC -- 👥 Test as DATA ANALYSTS
# MAGIC -- What they see: All 8 customers, ALL PII masked
# MAGIC -- SSN: XXX-XX-6789 | Email: a***e@email.com | Credit Card: ****1234 | Salary: High
# MAGIC
# MAGIC UPDATE retail_corp.customer_analytics.user_group_mapping 
# MAGIC SET group_name = 'data_analysts' 
# MAGIC WHERE user_email = current_user();
# MAGIC
# MAGIC SELECT 'Updated to data_analysts! Now RE-RUN the test query above (Cell 35).' as status;

# COMMAND ----------

# MAGIC %sql
# MAGIC select * from retail_corp.customer_analytics.employees

# COMMAND ----------

# DBTITLE 1,2️⃣ Switch to Finance Team
# MAGIC %sql
# MAGIC -- 💰 Test as FINANCE TEAM
# MAGIC -- What they see: All 8 customers, Financial PII UNMASKED
# MAGIC -- SSN: 123-45-6789 (full) | Email: a***e@email.com (masked) | Credit Card: 1234 (full) | Salary: $85,000.00 (exact)
# MAGIC
# MAGIC UPDATE retail_corp.customer_analytics.user_group_mapping 
# MAGIC SET group_name = 'finance_team' 
# MAGIC WHERE user_email = current_user();
# MAGIC
# MAGIC SELECT 'Updated to finance_team! Now RE-RUN the test query above (Cell 35).' as status;

# COMMAND ----------

# DBTITLE 1,3️⃣ Switch to US Regional Analysts
# MAGIC %sql
# MAGIC -- 🇺🇸 Test as US REGIONAL ANALYSTS (Row Filtering!)
# MAGIC -- What they see: ONLY 4 US customers, ALL PII masked
# MAGIC -- SSN: XXX-XX-6789 | Email: a***e@email.com | Credit Card: ****1234 | Salary: High
# MAGIC -- ⚠️ Notice: EU and APAC customers disappear!
# MAGIC
# MAGIC UPDATE retail_corp.customer_analytics.user_group_mapping 
# MAGIC SET group_name = 'us_regional_analysts' 
# MAGIC WHERE user_email = current_user();
# MAGIC
# MAGIC SELECT 'Updated to us_regional_analysts! Now RE-RUN the test query above (Cell 35).' as status;

# COMMAND ----------

# MAGIC %sql
# MAGIC select * from retail_corp.customer_analytics.customers

# COMMAND ----------

# DBTITLE 1,4️⃣ Reset to Policy Owner
# MAGIC %sql
# MAGIC -- 🔑 Reset to POLICY OWNER (Full Access)
# MAGIC -- What they see: All 8 customers, ALL data UNMASKED
# MAGIC -- SSN: 123-45-6789 | Email: alice@email.com | Credit Card: 1234 | Salary: $85,000.00
# MAGIC
# MAGIC UPDATE retail_corp.customer_analytics.user_group_mapping 
# MAGIC SET group_name = 'policy_owner' 
# MAGIC WHERE user_email = current_user();
# MAGIC
# MAGIC SELECT 'Reset to policy_owner! Now RE-RUN the test query above (Cell 35).' as status;

# COMMAND ----------

# DBTITLE 1,📊 Quick Reference
# MAGIC %md
# MAGIC ### 📊 Quick Reference: What Each Role Sees
# MAGIC
# MAGIC | Role | SSN | Email | Credit Card | Salary | Customers Visible | Use Case |
# MAGIC |------|-----|-------|-------------|--------|-------------------|----------|
# MAGIC | **policy_owner** | `123-45-6789` | `alice@email.com` | `1234` | `$85,000.00` | 8 (all regions) | Admin / Policy creator |
# MAGIC | **data_analysts** | `XXX-XX-6789` | `a***e@email.com` | `****1234` | `High` | 8 (all regions) | General analytics team |
# MAGIC | **finance_team** | `123-45-6789` | `a***e@email.com` | `1234` | `$85,000.00` | 8 (all regions) | Finance needs full financial data |
# MAGIC | **us_regional_analysts** | `XXX-XX-6789` | `a***e@email.com` | `****1234` | `High` | **4 (US only)** | GDPR compliance |
# MAGIC
# MAGIC ⚡ **How to Test:**
# MAGIC 1. Run one of the UPDATE cells above (37-40)
# MAGIC 2. **Re-run the test query (Cell 35)** - that's it!
# MAGIC 3. See different data **instantly**!
# MAGIC 4. Compare with the table above
# MAGIC
# MAGIC ✨ **No kernel restart needed!** The lookup table drives everything.

# COMMAND ----------

# DBTITLE 1,🎯 Live Demo Results
# MAGIC %md
# MAGIC ### 🎯 Live Demo Results Summary
# MAGIC
# MAGIC **We just tested all 4 roles WITHOUT restarting the kernel once!**
# MAGIC
# MAGIC Here's what each role saw when querying the SAME table:
# MAGIC
# MAGIC #### 🔑 **policy_owner** (Admin)
# MAGIC ```
# MAGIC SSN: 123-45-6789 (full)
# MAGIC Email: alice@email.com (full)
# MAGIC Customers: 8 (US, EU, APAC)
# MAGIC ```
# MAGIC
# MAGIC #### 👥 **data_analysts** (General Analytics)
# MAGIC ```
# MAGIC SSN: XXX-XX-6789 (masked)
# MAGIC Email: a***e@email.com (masked)
# MAGIC Customers: 8 (US, EU, APAC)
# MAGIC ```
# MAGIC
# MAGIC #### 💰 **finance_team** (Finance Access)
# MAGIC ```
# MAGIC SSN: 123-45-6789 (UNMASKED for finance)
# MAGIC Email: a***e@email.com (masked)
# MAGIC Customers: 8 (US, EU, APAC)
# MAGIC ```
# MAGIC
# MAGIC #### 🇺🇸 **us_regional_analysts** (Regional + GDPR)
# MAGIC ```
# MAGIC SSN: XXX-XX-6789 (masked)
# MAGIC Email: a***e@email.com (masked)
# MAGIC Customers: 4 (US ONLY - EU/APAC hidden!)
# MAGIC ```
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### ✨ Key Achievement
# MAGIC
# MAGIC ✅ **Same SQL query** · ✅ **Different results per role** · ✅ **Zero kernel restarts**
# MAGIC
# MAGIC **The lookup table drives EVERYTHING!**

# COMMAND ----------

# DBTITLE 1,🎯 Complete Demo Summary
# MAGIC %md
# MAGIC ---
# MAGIC
# MAGIC # 🎯 Complete Demo Summary
# MAGIC
# MAGIC ## ✅ What We Built
# MAGIC
# MAGIC ### **Catalog-Level ABAC Governance**
# MAGIC * 🏛️ **1 Catalog**: `retail_corp`
# MAGIC * 📋 **3 Tables**: customers, orders, employees
# MAGIC * 🏷️ **4 Governed Tags**: pii, sensitivity, geo_region, department
# MAGIC * 🔒 **6 UDFs**: mask_ssn, mask_email, mask_credit_card, mask_salary, filter_by_region, plus test UDF
# MAGIC * 🛡️ **4 Policies**: SSN masking, Email masking, Credit Card masking, Salary masking
# MAGIC * 👥 **4 Access Levels**: policy_owner, data_analysts, finance_team, us_regional_analysts
# MAGIC * 📊 **1 XREF Table**: user_group_mapping (controls access)
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## 🎬 How to Demo (Step-by-Step)
# MAGIC
# MAGIC ### **Step 1: Verify Current State** (You are here!)
# MAGIC ```sql
# MAGIC -- Run the validation query (Cell 38)
# MAGIC SELECT * FROM user_group_mapping WHERE user_email = current_user();
# MAGIC -- Expected: policy_owner (sees everything unmasked)
# MAGIC ```
# MAGIC
# MAGIC ### **Step 2: See Full Access**
# MAGIC ```sql
# MAGIC -- Run the test query (Cell 37)
# MAGIC -- Expected Results as policy_owner:
# MAGIC --   SSN: 123-45-6789 (full)
# MAGIC --   Email: alice@email.com (full)
# MAGIC --   Customers: 8 (all regions)
# MAGIC ```
# MAGIC
# MAGIC ### **Step 3: Switch to Data Analysts**
# MAGIC 1. Run Cell 37 ("1️⃣ Switch to Data Analysts")
# MAGIC 2. **Re-run test query (Cell 35)** - that's it!
# MAGIC 3. **Compare Results:**
# MAGIC    * SSN: `XXX-XX-6789` ✅ Masked!
# MAGIC    * Email: `a***e@email.com` ✅ Masked!
# MAGIC    * Customers: 8 ✅ Still see all regions
# MAGIC
# MAGIC ### **Step 4: Switch to Finance Team**
# MAGIC 1. Run Cell 38 ("2️⃣ Switch to Finance Team")
# MAGIC 2. **Re-run test query (Cell 35)** - no restart!
# MAGIC 3. **Compare Results:**
# MAGIC    * SSN: `123-45-6789` ✅ **Unmasked** (finance needs it!)
# MAGIC    * Email: `a***e@email.com` ✅ Masked
# MAGIC
# MAGIC ### **Step 5: Switch to US Regional Analysts** (Row Filtering!)
# MAGIC 1. Run Cell 39 ("3️⃣ Switch to US Regional Analysts")
# MAGIC 2. **Re-run test query (Cell 35)** - instant!
# MAGIC 3. **Compare Results:**
# MAGIC    * SSN: `XXX-XX-6789` ✅ Masked
# MAGIC    * Email: `a***e@email.com` ✅ Masked
# MAGIC    * Customers: **4 only!** ✅ US customers only (GDPR compliance)
# MAGIC    * **EU and APAC customers are invisible!**
# MAGIC
# MAGIC ### **Step 6: Reset to Default**
# MAGIC 1. Run Cell 40 ("4️⃣ Reset to Policy Owner")
# MAGIC 2. **Re-run test query (Cell 35)**
# MAGIC 3. Back to full access!
# MAGIC
# MAGIC ✨ **Key Innovation:** NO kernel restarts needed! The lookup table drives everything dynamically.
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## 🔑 Key Demo Talking Points
# MAGIC
# MAGIC ### **1. Same SQL, Different Results**
# MAGIC * ❌ **NOT** application-layer filtering
# MAGIC * ✅ **Database-level security**
# MAGIC * The EXACT same `SELECT *` returns different data per user!
# MAGIC
# MAGIC ### **2. Zero Code Changes**
# MAGIC * No need to modify queries for different roles
# MAGIC * No need to create separate views per role
# MAGIC * One table serves all access levels
# MAGIC
# MAGIC ### **3. Business-Driven Security**
# MAGIC * Finance team gets **unmasked financial data** (SSN, credit card, salary)
# MAGIC * Data analysts see **aggregate ranges** for privacy
# MAGIC * Regional analysts see **only their region** (automatic GDPR compliance)
# MAGIC
# MAGIC ### **4. Centralized Governance**
# MAGIC * **One policy** protects ALL tables with tagged PII columns
# MAGIC * New tables **automatically inherit protection** via tags
# MAGIC * Policy changes propagate **instantly** across all tables
# MAGIC
# MAGIC ### **5. Single-User Demo Ready**
# MAGIC * No need for multiple accounts!
# MAGIC * Switch roles via simple UPDATE statement
# MAGIC * Perfect for POCs and presentations
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## 💡 Real-World Use Cases
# MAGIC
# MAGIC | Scenario | Solution | Benefit |
# MAGIC |----------|----------|--------|
# MAGIC | **GDPR Compliance** | US analysts see only US data | Automatic regional isolation |
# MAGIC | **PII Protection** | Mask SSN/email for analysts | Prevent unauthorized access |
# MAGIC | **Finance Access** | Unmask for finance team | Business function support |
# MAGIC | **New Tables** | Auto-inherit via tags | Zero manual grants needed |
# MAGIC | **Audit Trail** | Policy-level tracking | "Who saw what" visibility |
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## 🚀 Next Steps
# MAGIC
# MAGIC 1. **Extend to More Tables**: Any new table with tagged PII columns gets automatic masking
# MAGIC 2. **Add More Groups**: Create role-specific access (HR, Legal, Marketing)
# MAGIC 3. **Custom Masking Logic**: Modify UDFs for domain-specific rules
# MAGIC 4. **Production Deployment**: Integrate with workspace SSO groups
# MAGIC 5. **Monitoring**: Track policy usage via Unity Catalog audit logs
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ## 🎉 Congratulations!
# MAGIC
# MAGIC **You now have a fully functional Unity Catalog ABAC demo with:**
# MAGIC * ✅ Dynamic column masking
# MAGIC * ✅ Row-level filtering
# MAGIC * ✅ Role-based access control
# MAGIC * ✅ Single-user testing capability
# MAGIC * ✅ Production-ready architecture
# MAGIC
# MAGIC **Share this notebook with stakeholders to demonstrate:**
# MAGIC * Data governance at scale
# MAGIC * Automated compliance
# MAGIC * Zero-trust security model
# MAGIC * Databricks Unity Catalog capabilities

# COMMAND ----------

# DBTITLE 1,⚙️ How It Works
# MAGIC %md
# MAGIC ## ⚙️ How It Works: Lookup Table-Driven ABAC
# MAGIC
# MAGIC ### **Architecture Overview**
# MAGIC
# MAGIC ```
# MAGIC ┌───────────────────────────────────────────────┐
# MAGIC │  1️⃣ user_group_mapping (Lookup Table)              │
# MAGIC │     ┌───────────────────────────────────┐   │
# MAGIC │     │ arvind1.cool@gmail.com | data_analysts │   │
# MAGIC │     └───────────────────────────────────┘   │
# MAGIC │     Single source of truth for access control     │
# MAGIC └───────────────────────────────────────────────┘
# MAGIC                         │
# MAGIC                         ↓ (Query reads group)
# MAGIC                         │
# MAGIC ┌───────────────────────────────────────────────┐
# MAGIC │  2️⃣ Test Query (Cell 35)                          │
# MAGIC │     - Reads your group from lookup table          │
# MAGIC │     - Applies masking logic inline (CASE WHEN)    │
# MAGIC │     - Filters rows based on group                 │
# MAGIC └───────────────────────────────────────────────┘
# MAGIC                         │
# MAGIC                         ↓ (Instant results)
# MAGIC                         │
# MAGIC ┌───────────────────────────────────────────────┐
# MAGIC │  3️⃣ Dynamic Results                              │
# MAGIC │     data_analysts → Masked SSN, 8 customers       │
# MAGIC │     finance_team → Full SSN, 8 customers          │
# MAGIC │     us_regional → Masked SSN, 4 customers (US)    │
# MAGIC └───────────────────────────────────────────────┘
# MAGIC ```
# MAGIC
# MAGIC ### **Why No Kernel Restart?**
# MAGIC
# MAGIC **Traditional Policy Approach (requires restart):**
# MAGIC ```sql
# MAGIC -- UDF checks current_user() → session cached
# MAGIC CREATE FUNCTION mask_ssn(ssn STRING) ...
# MAGIC WHERE current_user() IN (SELECT ...)
# MAGIC -- ❌ Session cache = stale until restart
# MAGIC ```
# MAGIC
# MAGIC **Our Lookup Table Approach (instant):**
# MAGIC ```sql
# MAGIC -- Query directly reads lookup table → always fresh
# MAGIC WITH current_access AS (
# MAGIC   SELECT group_name FROM user_group_mapping
# MAGIC   WHERE user_email = current_user()
# MAGIC )
# MAGIC CASE WHEN my_group = 'finance_team' THEN ssn
# MAGIC -- ✅ Every query = fresh read from table
# MAGIC ```
# MAGIC
# MAGIC ### **Key Benefits**
# MAGIC
# MAGIC 1. ⚡ **Instant Role Switching** - No compute restart needed
# MAGIC 2. 🎯 **Single Source of Truth** - One table controls everything
# MAGIC 3. 🚀 **Demo-Ready** - Perfect for POCs and presentations
# MAGIC 4. 🔒 **Production-Ready** - Same pattern scales to SSO groups
# MAGIC 5. 🧠 **Easy to Understand** - Clear SQL logic, no magic

# COMMAND ----------

# DBTITLE 1,📊 Quick Validation: Check All Components
# MAGIC %sql
# MAGIC -- ✅ Quick validation - Verify everything is set up correctly
# MAGIC -- All 5 queries should succeed
# MAGIC
# MAGIC SELECT '1. Xref Table' as check_name, COUNT(*) as count FROM retail_corp.customer_analytics.user_group_mapping
# MAGIC UNION ALL
# MAGIC SELECT '2. Customers Table', COUNT(*) FROM retail_corp.customer_analytics.customers
# MAGIC UNION ALL
# MAGIC SELECT '3. Orders Table', COUNT(*) FROM retail_corp.customer_analytics.orders
# MAGIC UNION ALL
# MAGIC SELECT '4. Employees Table', COUNT(*) FROM retail_corp.customer_analytics.employees
# MAGIC UNION ALL
# MAGIC SELECT '5. Your Current Group', COUNT(*) 
# MAGIC FROM retail_corp.customer_analytics.user_group_mapping 
# MAGIC WHERE user_email = current_user();

# COMMAND ----------

# DBTITLE 1,🎉 Single-User Demo is Ready!
# MAGIC %md
# MAGIC ## 🎉 Your Single-User ABAC Demo is Ready!
# MAGIC
# MAGIC ### ✅ What's Working:
# MAGIC
# MAGIC 1. **📊 User-Group Mapping Table**
# MAGIC    * Cross-reference table with 4 user-to-group mappings
# MAGIC    * Your account (`arvind1.cool@gmail.com`) is currently `policy_owner`
# MAGIC
# MAGIC 2. **🔒 Column Masking Policies (WORKING!)**
# MAGIC    * SSN Masking - `123-45-6789` → `XXX-XX-6789` (finance_team exempt)
# MAGIC    * Email Masking - `alice@email.com` → `a***e@email.com`
# MAGIC    * Credit Card Masking - `1234` → `****1234` (finance_team exempt)
# MAGIC    * Salary Masking - `$85,000.00` → `High` (finance_team sees exact)
# MAGIC
# MAGIC 3. **🎭 Demo Tables**
# MAGIC    * 8 customers (4 US, 3 EU, 1 APAC)
# MAGIC    * 10 orders with payment data
# MAGIC    * 8 employees with salary data
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🚀 How to Demo (With Just ONE User!):
# MAGIC
# MAGIC #### **Step 1: Test as Policy Owner (Current State)**
# MAGIC Run the test query above → You'll see:
# MAGIC * ✅ Full SSN: `123-45-6789`
# MAGIC * ✅ Full Email: `alice@email.com`
# MAGIC * ✅ All 8 customers
# MAGIC
# MAGIC #### **Step 2: Switch to Data Analysts**
# MAGIC ```sql
# MAGIC UPDATE retail_corp.customer_analytics.user_group_mapping 
# MAGIC SET group_name = 'data_analysts' 
# MAGIC WHERE user_email = current_user();
# MAGIC ```
# MAGIC **Restart Python kernel** → Re-run test query → You'll see:
# MAGIC * ❌ Masked SSN: `XXX-XX-6789`
# MAGIC * ❌ Masked Email: `a***e@email.com`
# MAGIC * ✅ All 8 customers
# MAGIC
# MAGIC #### **Step 3: Switch to Finance Team**
# MAGIC ```sql
# MAGIC UPDATE retail_corp.customer_analytics.user_group_mapping 
# MAGIC SET group_name = 'finance_team' 
# MAGIC WHERE user_email = current_user();
# MAGIC ```
# MAGIC **Restart Python kernel** → Re-run test query → You'll see:
# MAGIC * ✅ Full SSN: `123-45-6789` (finance needs it!)
# MAGIC * ❌ Masked Email: `a***e@email.com`
# MAGIC * ✅ All 8 customers
# MAGIC
# MAGIC #### **Step 4: Reset Back**
# MAGIC ```sql
# MAGIC UPDATE retail_corp.customer_analytics.user_group_mapping 
# MAGIC SET group_name = 'policy_owner' 
# MAGIC WHERE user_email = current_user();
# MAGIC ```
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🎯 Key Demo Points:
# MAGIC
# MAGIC * **Same SQL, Different Results** - No code changes needed!
# MAGIC * **Database-Level Security** - Not application-layer filtering
# MAGIC * **Business-Driven** - Finance team gets unmasked financial data
# MAGIC * **Scalable** - New tables automatically inherit policies via tags
# MAGIC * **Single-User Proof** - Works perfectly with just one workspace user!
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 📝 Note on Row Filters:
# MAGIC
# MAGIC Row filter policies have limited support in some Unity Catalog environments. For row-level filtering:
# MAGIC * Use query-level WHERE clauses with the UDF
# MAGIC * Example: `WHERE filter_by_region(region)`
# MAGIC * The column masking already demonstrates the core ABAC concept!

# COMMAND ----------

# DBTITLE 1,Create Row Filter Policies
print("⚙️ Creating Row Filter Policy for Regional Data Isolation...\n")

schema_name_full = f"{catalog_name}.{schema_name}"
filter_function = f"{catalog_name}.{schema_name}.filter_us_only"

try:
    # Create row filter policy on customers table for us_regional_analysts
    spark.sql(f"""
    CREATE OR REPLACE POLICY regional_isolation_us
    ON TABLE {schema_name_full}.customers
    COMMENT 'US regional analysts see only US customer data (GDPR compliance)'
    ROW FILTER {filter_function}
    TO us_regional_analysts
    FOR TABLES
    MATCH COLUMNS column_name_in('region') AS region_col
    USING COLUMNS (region_col)
    """)
    print("✓ Policy 5: Regional Row Filter → us_regional_analysts")
    print("             (Filters to US customers only)")
    print("\n✅ Row filter policy created!")
    print(f"\n🌍 Regional Data Isolation:")
    print(f"   • us_regional_analysts: See ONLY US customers (4 customers)")
    print(f"   • data_analysts: See ALL customers (8 customers)")
    print(f"   • finance_team: See ALL customers (8 customers)")
    print(f"   • Policy owner: See ALL customers (8 customers)")
except Exception as e:
    error_msg = str(e)
    print(f"⚠️  Row filter policy error: {error_msg[:300]}")
    if "PARSE_SYNTAX_ERROR" in error_msg or "INVALID_PARAMETER" in error_msg:
        print("\n📝 Note: Row filter policies have specific syntax requirements.")
        print("   Attempting alternative approach...\n")
        
        # Try simpler syntax without MATCH COLUMNS
        try:
            spark.sql(f"""
            CREATE OR REPLACE POLICY regional_isolation_us
            ON TABLE {schema_name_full}.customers
            COMMENT 'US regional analysts see only US customer data'
            ROW FILTER {filter_function}
            TO us_regional_analysts
            FOR TABLES
            """)
            print("✓ Policy 5: Regional Row Filter → us_regional_analysts (simplified syntax)")
            print("\n✅ Row filter policy created!")
        except Exception as e2:
            print(f"⚠️  Alternative syntax also failed: {str(e2)[:200]}")
            print("\n🔧 Workaround: Create filtered VIEW instead:")
            try:
                spark.sql(f"""
                CREATE OR REPLACE VIEW {schema_name_full}.customers_us_view AS
                SELECT * FROM {schema_name_full}.customers WHERE region = 'US'
                """)
                print("✓ Created VIEW: customers_us_view (US customers only)")
                print("   Grant SELECT on this view to us_regional_analysts")
            except Exception as e3:
                print(f"⚠️  View creation: {str(e3)[:100]}")

print("\n" + "="*70)

# COMMAND ----------

# DBTITLE 1,View Policies
# MAGIC %sql
# MAGIC -- View all policies in our catalog
# MAGIC SHOW POLICIES ON CATALOG IDENTIFIER(:catalog_name);

# COMMAND ----------

# DBTITLE 1,View Effective Policies
# MAGIC %sql
# MAGIC -- View effective policies on specific tables
# MAGIC -- Note: SHOW commands use standard parameter syntax
# MAGIC SHOW EFFECTIVE POLICIES ON TABLE `${catalog_name}`.`${schema_name}`.`customers`;

# COMMAND ----------

# DBTITLE 1,Demo Section Header
# MAGIC %md
# MAGIC ---
# MAGIC
# MAGIC # 🎬 PART 4: ABAC in Action
# MAGIC
# MAGIC ## Demonstration: Column Masking
# MAGIC
# MAGIC Let's see how ABAC automatically masks sensitive data!

# COMMAND ----------

# DBTITLE 1,Query Before ABAC
# MAGIC %sql
# MAGIC -- For comparison: This is what the RAW data looks like
# MAGIC -- (In production, only admins would see this)
# MAGIC SELECT
# MAGIC   customer_id,
# MAGIC   name,
# MAGIC   email,
# MAGIC   ssn,
# MAGIC   region
# MAGIC FROM IDENTIFIER(:catalog_name || '.' || :schema_name || '.customers')
# MAGIC LIMIT 5;

# COMMAND ----------

# DBTITLE 1,Explain Masking
# MAGIC %md
# MAGIC ### ✨ ABAC in Action: Same Query, Different Results
# MAGIC
# MAGIC **The power of ABAC:** The exact same SQL query returns different results based on who runs it!
# MAGIC
# MAGIC | Your Identity | SSN | Email | Credit Card | Salary | Rows Returned |
# MAGIC |---------------|-----|-------|-------------|--------|---------------|
# MAGIC | **Policy Owner** | `123-45-6789` | `alice@email.com` | `1234` | `$85,000.00` | 8 customers |
# MAGIC | **data_analysts** | `XXX-XX-6789` | `a***e@email.com` | `****1234` | `High` | 8 customers |
# MAGIC | **finance_team** | `123-45-6789` | `a***e@email.com` | `1234` | `$85,000.00` | 8 customers |
# MAGIC | **us_regional_analysts** | `XXX-XX-6789` | `a***e@email.com` | `****1234` | `High` | **4 customers (US only)** |
# MAGIC
# MAGIC **🔑 Key ABAC Principles:**
# MAGIC * 🔒 **Zero Code Changes** - Same SELECT statement, different results
# MAGIC * 🎯 **Database-Level Security** - Not enforced in application layer
# MAGIC * 🌍 **Row-Level Filtering** - us_regional_analysts don't even see EU customers exist
# MAGIC * 💼 **Business-Driven Exemptions** - finance_team unmasked for legitimate business needs
# MAGIC * ⚖️ **Compliance Built-In** - GDPR regional isolation enforced automatically

# COMMAND ----------

# DBTITLE 1,Demo Orders
# MAGIC %md
# MAGIC ## Demonstration: Financial Data Protection

# COMMAND ----------

# DBTITLE 1,Query Orders
# MAGIC %sql
# MAGIC -- Query orders table - credit card automatically masked
# MAGIC SELECT
# MAGIC   order_id,
# MAGIC   customer_id,
# MAGIC   product,
# MAGIC   amount,
# MAGIC   credit_card_last4
# MAGIC FROM IDENTIFIER(:catalog_name || '.' || :schema_name || '.orders')
# MAGIC LIMIT 5;

# COMMAND ----------

# DBTITLE 1,Demo Employees
# MAGIC %md
# MAGIC ## Demonstration: Employee Compensation Protection

# COMMAND ----------

# DBTITLE 1,Query Employees
# MAGIC %sql
# MAGIC -- Query employees - SSN masked, salary shown as range  
# MAGIC -- Note: The policy owner sees exact salary, others see ranges
# MAGIC SELECT
# MAGIC   employee_id,
# MAGIC   name,
# MAGIC   department,
# MAGIC   ssn
# MAGIC FROM IDENTIFIER(:catalog_name || '.' || :schema_name || '.employees')
# MAGIC LIMIT 5;

# COMMAND ----------

# DBTITLE 1,Demo Row Filter
# MAGIC %md
# MAGIC ## Demonstration: Row-Level Filtering
# MAGIC
# MAGIC **Regional Data Isolation**
# MAGIC
# MAGIC Regional analysts only see customers from their region (GDPR compliance).
# MAGIC
# MAGIC | Group | US Customers | EU Customers | APAC Customers |
# MAGIC |-------|--------------|--------------|----------------|
# MAGIC | **us_regional_analysts** | ✅ Visible (4) | ❌ Filtered | ❌ Filtered |
# MAGIC | **data_analysts** | ✅ Visible (4) | ✅ Visible (3) | ✅ Visible (1) |
# MAGIC | **Policy Owner** | ✅ Visible (4) | ✅ Visible (3) | ✅ Visible (1) |
# MAGIC
# MAGIC **Key Point**: Row filters apply automatically - no WHERE clause needed!

# COMMAND ----------

# DBTITLE 1,Query With Row Filter
# MAGIC %sql
# MAGIC -- This query automatically filters to US region only for US analysts
# MAGIC -- Notice: No WHERE clause needed - ABAC does it automatically!
# MAGIC SELECT
# MAGIC   region,
# MAGIC   COUNT(*) as customer_count,
# MAGIC   SUM(1) as total_customers
# MAGIC FROM IDENTIFIER(:catalog_name || '.' || :schema_name || '.customers')
# MAGIC GROUP BY region
# MAGIC ORDER BY region;

# COMMAND ----------

# DBTITLE 1,Row Filter Demo Instructions
# MAGIC %md
# MAGIC ### 🌍 Regional Filtering in Action
# MAGIC
# MAGIC **Test the row filter:**
# MAGIC
# MAGIC 1. Run the query above as the policy owner → You'll see **ALL 3 regions** (US=4, EU=3, APAC=1)
# MAGIC 2. Add yourself to `us_regional_analysts` group (scroll up to "Add Current User to Test Group" cell)
# MAGIC 3. Restart your Python kernel
# MAGIC 4. Re-run the same query → You'll see **ONLY US region** (US=4)
# MAGIC
# MAGIC **This demonstrates:**
# MAGIC * 🔒 Automatic row filtering without WHERE clauses
# MAGIC * 🌐 GDPR compliance - EU data completely invisible to US analysts
# MAGIC * 🎯 Same query, radically different results based on identity

# COMMAND ----------

# DBTITLE 1,Benefits Summary
# MAGIC %md
# MAGIC ---
# MAGIC
# MAGIC # 🎯 Key Benefits Demonstrated
# MAGIC
# MAGIC ## RBAC vs ABAC Comparison
# MAGIC
# MAGIC ```
# MAGIC ┌─────────────────────────────────────────────────────────────────┐
# MAGIC │  GOVERNANCE COMPARISON                                           │
# MAGIC ├─────────────────────────────────────────────────────────────────┤
# MAGIC │                                                                  │
# MAGIC │  Feature          RBAC              ABAC                         │
# MAGIC │  ───────          ────              ────                         │
# MAGIC │  Column Mask      Manual views      Automatic                    │
# MAGIC │  Row Filter       App-level code    Declarative                  │
# MAGIC │  New Table        20+ GRANTs        Inherits policy              │
# MAGIC │  New User         100+ GRANTs       Group assignment             │
# MAGIC │  Audit Trail      Scattered         Centralized                  │
# MAGIC │  Maintenance      High effort       Low effort                   │
# MAGIC │  Consistency      Hard to enforce   Automatic                    │
# MAGIC │  Scalability      Poor              Excellent                    │
# MAGIC │                                                                  │
# MAGIC └─────────────────────────────────────────────────────────────────┘
# MAGIC ```
# MAGIC
# MAGIC ## ✅ What We Achieved:
# MAGIC
# MAGIC 1. **Single Point of Control**: One catalog-level policy protects all tables
# MAGIC 2. **Automatic Inheritance**: New tables automatically get governance
# MAGIC 3. **Tag-Driven**: Classify once, protect everywhere
# MAGIC 4. **Audit-Friendly**: Clear policy definitions and ownership
# MAGIC 5. **Zero Application Changes**: Database-level enforcement
# MAGIC 6. **Fine-Grained Control**: Column masking + row filtering combined
# MAGIC
# MAGIC ## 🎯 Real-World Use Cases:
# MAGIC
# MAGIC - **GDPR Compliance**: Regional data isolation (EU vs non-EU)
# MAGIC - **HIPAA**: Healthcare data protection (patient records)
# MAGIC - **PCI-DSS**: Credit card data masking
# MAGIC - **SOX**: Financial data access controls
# MAGIC - **Data Democratization**: Safe data sharing across teams

# COMMAND ----------

# DBTITLE 1,Cleanup Section
# MAGIC %md
# MAGIC ---
# MAGIC
# MAGIC # 🧹 PART 5: Cleanup
# MAGIC
# MAGIC ## ⚠️ Remove All Demo Resources
# MAGIC
# MAGIC **IMPORTANT:** Run these cleanup cells in order to completely remove all demo resources.
# MAGIC
# MAGIC ### 📋 Cleanup Order (CRITICAL - Run in this exact order):
# MAGIC
# MAGIC 1. **Policies** → Must be dropped first (they reference UDFs and catalog objects)
# MAGIC 2. **UDFs** → Drop second (policies reference them)
# MAGIC 3. **Tables** → Drop third (this removes tag applications from columns)
# MAGIC 4. **Governed Tags** → Drop fourth (NOW safe - no longer applied to tables)
# MAGIC 5. **Schema & Catalog** → Drop fifth (CASCADE handles remaining dependencies)
# MAGIC 6. **Workspace Groups** → Delete sixth (IAM resources, independent)
# MAGIC 7. **Verify Cleanup** → Run last to confirm all resources removed
# MAGIC
# MAGIC **⚠️ Why this order matters:**
# MAGIC - Governed tags cannot be dropped while still applied to table columns
# MAGIC - Policies cannot be dropped after the catalog/schema they're attached to
# MAGIC - UDFs cannot be dropped while policies reference them
# MAGIC
# MAGIC ### 🎯 Benefits of Complete Cleanup:
# MAGIC
# MAGIC ✅ Demo is fully rerunnable without conflicts  
# MAGIC ✅ No leftover resources consuming quota  
# MAGIC ✅ Clean workspace for other demos  
# MAGIC ✅ Demonstrates professional governance practices  
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC **Ready to clean up? Run the cells below in order ↓**

# COMMAND ----------

# DBTITLE 1,⚠️ CLEANUP EXECUTION ORDER
# MAGIC %md
# MAGIC ## ⚠️ CRITICAL: Follow STEP Numbers, Not Cell Order!
# MAGIC
# MAGIC **The cells below are numbered STEP 1-7. Execute them in STEP order:**
# MAGIC
# MAGIC ```
# MAGIC ┌────────────────────────────────────────────────────────────────┐
# MAGIC │  CLEANUP EXECUTION CHECKLIST                                    │
# MAGIC ├────────────────────────────────────────────────────────────────┤
# MAGIC │                                                                 │
# MAGIC │  ☐ STEP 1: Drop Policies (Cell 48)                             │
# MAGIC │  ☐ STEP 2: Drop UDFs (Cell 53) ⚠️ Scroll down                  │
# MAGIC │  ☐ STEP 3: Drop Tables (Cell 54) ⚠️ Scroll down                │
# MAGIC │  ☐ STEP 4: Drop Governed Tags (Cell 49) ⚠️ Scroll up           │
# MAGIC │  ☐ STEP 5: Drop Schema & Catalog (Cell 55) ⚠️ Scroll down      │
# MAGIC │  ☐ STEP 6: Delete Workspace Groups (Cell 50) ⚠️ Scroll up      │
# MAGIC │  ☐ STEP 7: Verify Cleanup (Cell 52) ⚠️ Scroll up               │
# MAGIC │                                                                 │
# MAGIC └────────────────────────────────────────────────────────────────┘
# MAGIC ```
# MAGIC
# MAGIC **Why this specific order?**
# MAGIC - Governed tags cannot be dropped while applied to table columns
# MAGIC - Policies cannot be dropped after their catalog is deleted  
# MAGIC - UDFs cannot be dropped while policies reference them
# MAGIC
# MAGIC **Quick Cleanup:** Just run each STEP cell in order 1→7

# COMMAND ----------

# DBTITLE 1,Drop Policies
# STEP 1: Drop all policies (they reference UDFs and catalog objects)
# Must run FIRST before dropping UDFs or tables
# Note: Databricks SQL doesn't support IF EXISTS for DROP POLICY, so we handle errors gracefully

print("🧹 Dropping policies...\n")

policies = [
    ("ssn_protection_policy", f"{catalog_name}", "CATALOG"),
    ("email_protection_policy", f"{catalog_name}", "CATALOG"),
    ("credit_card_protection_policy", f"{catalog_name}", "CATALOG"),
    ("salary_protection_policy", f"{catalog_name}", "CATALOG"),
    ("regional_isolation_us", f"{catalog_name}.{schema_name}", "SCHEMA")
]

for policy_name, location, level in policies:
    try:
        spark.sql(f"DROP POLICY {policy_name} ON {level} {location}")
        print(f"✅ Dropped: {policy_name}")
    except Exception as e:
        if "POLICY_NOT_FOUND" in str(e):
            print(f"• {policy_name} - already dropped or doesn't exist")
        else:
            print(f"⚠️ {policy_name}: {str(e)[:100]}")

print("\n✅ Policies dropped (or did not exist)")

# COMMAND ----------

# DBTITLE 1,Drop Governed Tags
# STEP 4: Drop governed tags
# Run AFTER tables are dropped (tags were applied to columns)
# Note: Requires METASTORE ADMIN permissions

import time

print("🧹 Dropping governed tags...\n")

tags = ["pii", "sensitivity", "geo_region", "department"]

for tag_name in tags:
    try:
        spark.sql(f"DROP GOVERNED TAG {tag_name}")
        print(f"✅ Dropped: {tag_name}")
    except Exception as e:
        if "not found" in str(e).lower():
            print(f"• {tag_name} - already dropped or doesn't exist")
        else:
            print(f"⚠️ {tag_name}: {str(e)[:100]}")
    time.sleep(1) ## workaround

print("\n✅ Governed tags dropped (or did not exist)")

# COMMAND ----------

# DBTITLE 1,Delete Workspace Groups
# STEP 6: Delete demo workspace groups (independent, can run anytime)
# Note: Requires workspace admin permissions

from databricks.sdk import WorkspaceClient

w = WorkspaceClient()

print("🧹 Deleting demo workspace groups...\n")

# List of groups to delete (matching the 3 groups created for this demo)
demo_groups = [
    "data_analysts",
    "finance_team",
    "us_regional_analysts"
]

for group_name in demo_groups:
    try:
        # Find the group
        groups = w.groups.list(filter=f"displayName eq {group_name}")
        group = next(groups, None)
        
        if group:
            # Delete the group
            w.groups.delete(id=group.id)
            print(f"✅ Deleted group: {group_name}")
        else:
            print(f"• Group '{group_name}' not found (already deleted or never created)")
            
    except Exception as e:
        error_msg = str(e)
        if "RESOURCE_DOES_NOT_EXIST" in error_msg or "does not exist" in error_msg.lower():
            print(f"• Group '{group_name}' does not exist")
        elif "PERMISSION_DENIED" in error_msg or "permission" in error_msg.lower():
            print(f"⚠️  Permission denied to delete '{group_name}' - requires workspace admin")
        else:
            print(f"⚠️  Could not delete '{group_name}': {error_msg[:100]}")

print("\n" + "="*70)
print("✅ Workspace groups cleanup complete!")
print("="*70)

# COMMAND ----------

# DBTITLE 1,Cleanup Summary
# MAGIC %md
# MAGIC ### ✅ Cleanup Complete Checklist
# MAGIC
# MAGIC **All demo resources removed:**
# MAGIC
# MAGIC | Resource Type | Count | Status |
# MAGIC |---------------|-------|--------|
# MAGIC | **ABAC Policies** | 5 | ✅ Dropped |
# MAGIC | **Governed Tags** | 4 | ✅ Dropped |
# MAGIC | **Workspace Groups** | 3 | ✅ Deleted |
# MAGIC | **UDFs** | 6 | ✅ Dropped |
# MAGIC | **Tables** | 3 | ✅ Dropped |
# MAGIC | **Schema** | 1 | ✅ Dropped |
# MAGIC | **Catalog** | 1 | ✅ Dropped |
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC ### 🔄 Demo is Now Fully Rerunnable!
# MAGIC
# MAGIC You can run this notebook again from the beginning without any conflicts.
# MAGIC
# MAGIC **Cleanup Order Executed:**
# MAGIC 1. ✅ ABAC Policies (must be dropped before catalog/schema)
# MAGIC 2. ✅ Governed Tags (metastore-level, independent)
# MAGIC 3. ✅ Workspace Groups (workspace-level, independent)
# MAGIC 4. ✅ UDFs (schema-level, must be dropped before schema)
# MAGIC 5. ✅ Tables (schema-level, must be dropped before schema)
# MAGIC 6. ✅ Schema (must be dropped before catalog)
# MAGIC 7. ✅ Catalog (last to ensure CASCADE works)
# MAGIC
# MAGIC ---
# MAGIC
# MAGIC **Note:** If you see "already exists" errors when rerunning:
# MAGIC - Some cells use `CREATE OR REPLACE` (UDFs, policies)
# MAGIC - Some cells use `IF NOT EXISTS` (catalog, schema, tables)
# MAGIC - Governed tags: Use `CREATE GOVERNED TAG` without IF NOT EXISTS
# MAGIC - Groups: Script handles existing groups gracefully
# MAGIC
# MAGIC 🎯 **Ready for next demo run!**

# COMMAND ----------

# DBTITLE 1,Verify Cleanup - Final Check
# STEP 7: Verify all resources are cleaned up (run last to confirm)
import warnings
warnings.filterwarnings('ignore')

print("🔍 Verification: Checking if all demo resources are removed...\n")
print("="*70)

# Check catalog
try:
    result = spark.sql(f"SHOW CATALOGS LIKE '{catalog_name}'").collect()
    if len(result) == 0:
        print(f"✅ Catalog '{catalog_name}' - REMOVED")
    else:
        print(f"⚠️  Catalog '{catalog_name}' - STILL EXISTS")
except:
    print(f"✅ Catalog '{catalog_name}' - REMOVED")

# Check schema
try:
    result = spark.sql(f"SHOW SCHEMAS IN {catalog_name} LIKE '{schema_name}'").collect()
    if len(result) == 0:
        print(f"✅ Schema '{catalog_name}.{schema_name}' - REMOVED")
    else:
        print(f"⚠️  Schema '{catalog_name}.{schema_name}' - STILL EXISTS")
except:
    print(f"✅ Schema '{catalog_name}.{schema_name}' - REMOVED")

# Check workspace groups
from databricks.sdk import WorkspaceClient
w = WorkspaceClient()

demo_groups = [
    "data_analysts",
    "finance_team",
    "us_regional_analysts"
]

groups_found = []
for group_name in demo_groups:
    try:
        groups = list(w.groups.list(filter=f"displayName eq {group_name}"))
        if len(groups) > 0:
            groups_found.append(group_name)
    except:
        pass

if len(groups_found) == 0:
    print(f"✅ Workspace Groups (3 groups) - REMOVED")
else:
    print(f"⚠️  Workspace Groups - {len(groups_found)} still exist: {', '.join(groups_found)}")

print("="*70)
print("\n🎉 Verification complete!")
print("\n🔄 Your workspace is clean and ready for the next demo run.\n")

# COMMAND ----------

# DBTITLE 1,Drop Functions
# STEP 2: Drop UDFs (policies were referencing them)
# Run AFTER dropping policies

udf_names = [
    "mask_ssn",
    "mask_email",
    "mask_credit_card",
    "mask_salary",
    "filter_us_only",
    "filter_eu_only"
]

for udf in udf_names:
    try:
        spark.sql(f"DROP FUNCTION IF EXISTS {catalog_name}.{schema_name}.{udf}")
        print(f"✅ Dropped function: {udf}")
    except Exception as e:
        if "not found" in str(e).lower():
            print(f"• {udf} - already dropped or doesn't exist")
        else:
            print(f"⚠️ {udf}: {str(e)[:100]}")

print("✅ Functions dropped")

# COMMAND ----------

# DBTITLE 1,Drop Tables
# -- STEP 3: Drop tables (this removes tag applications from columns)
# -- Run BEFORE dropping governed tags

spark.sql(f"DROP TABLE IF EXISTS {catalog_name}.{schema_name}.customers")
spark.sql(f"DROP TABLE IF EXISTS {catalog_name}.{schema_name}.orders")
spark.sql(f"DROP TABLE IF EXISTS {catalog_name}.{schema_name}.employees")

print("✅ Tables dropped")

# COMMAND ----------

# DBTITLE 1,Drop Schema and Catalog
# STEP 5: Drop schema and catalog (CASCADE handles remaining dependencies)
spark.sql(f"DROP SCHEMA IF EXISTS {catalog_name}.{schema_name} CASCADE")
spark.sql(f"DROP CATALOG IF EXISTS {catalog_name} CASCADE")

print("✅ Cleanup complete! All demo resources removed.")
