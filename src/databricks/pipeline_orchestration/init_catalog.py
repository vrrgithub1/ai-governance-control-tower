# init_catalog.py
from pyspark.sql import SparkSession

# Initialize Spark Session
spark = SparkSession.builder.getOrCreate()

# 1. Define your target workspace catalog
TARGET_CATALOG = "adb_governance_control"

# 2. Define the new schema matrix structured by environment prefix
schemas_to_create = [
    # Development Environment Layers
    "dev_banking_bronze",
    "dev_banking_silver",
    "dev_banking_gold",
    
    # Production Environment Layers
    "prod_banking_bronze",
    "prod_banking_silver",
    "prod_banking_gold",
    
    # Governance & Control Layer
    "gov_control_tower"
]

print(f"🚀 Starting schema initialization under catalog: '{TARGET_CATALOG}'...")

# 3. Explicitly set the session context to your workspace catalog
spark.sql(f"USE CATALOG {TARGET_CATALOG};")

# 4. Loop through and provision the schemas safely
for schema_name in schemas_to_create:
    try:
        spark.sql(f"CREATE SCHEMA IF NOT EXISTS {schema_name};")
        print(f"✅ Schema '{TARGET_CATALOG}.{schema_name}' verified/created successfully.")
    except Exception as e:
        print(f"❌ Failed to create schema '{schema_name}'. Error: {str(e)}")

print("🎉 Data mesh schema reorganization complete!")
