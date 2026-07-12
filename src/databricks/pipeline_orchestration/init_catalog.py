# src/databricks/pipeline_orchestration/init_catalog.py
from pyspark.sql import SparkSession

def initialize_governance_mesh():
    spark = SparkSession.builder.getOrCreate()
    
    # 1. Create the Environment Catalogs
    catalogs = ["aigct_governance", "aigct_dev", "aigct_prod"]
    for catalog in catalogs:
        spark.sql(f"CREATE CATALOG IF NOT EXISTS {catalog};")
        print(f"✅ Catalog '{catalog}' verified/created.")
    
    # 2. Establish Medallion Layers in Production
    schemas = ["banking_bronze", "banking_silver", "banking_gold"]
    for schema in schemas:
        spark.sql(f"CREATE SCHEMA IF NOT EXISTS aigct_prod.{schema};")
        print(f"🧱 Schema 'aigct_prod.{schema}' verified/created.")

if __name__ == "__main__":
    initialize_governance_mesh()
    