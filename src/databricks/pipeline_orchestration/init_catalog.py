# --- src/databricks/pipeline_orchestration/init_catalog.py ---
from pyspark.sql import SparkSession

spark = SparkSession.builder.getOrCreate()

# Explicitly target your new US-based infrastructure
storage_account = "saigctdatastor" 
container = "main" 
storage_base = f"abfss://{container}@{storage_account}.dfs.core.windows.net"

print(f"🚀 Initializing AIGCT Data Architecture on storage: {storage_account}")

catalogs = {
    "aigct_dev": f"{storage_base}/unity/dev",
    "aigct_prod": f"{storage_base}/unity/prod",
    "aigct_governance": f"{storage_base}/unity/governance"
}

for catalog_name, storage_path in catalogs.items():
    spark.sql(f"CREATE CATALOG IF NOT EXISTS {catalog_name} MANAGED LOCATION '{storage_path}';")
    print(f"✅ Catalog '{catalog_name}' verified/created at {storage_path}.")
    
    if "governance" not in catalog_name:
        for layer in ["banking_bronze", "banking_silver", "banking_gold"]:
            spark.sql(f"CREATE SCHEMA IF NOT EXISTS {catalog_name}.{layer};")
            print(f"  🧱 Schema {catalog_name}.{layer} verified/created.")

print("🏁 Data mesh setup completed successfully!")