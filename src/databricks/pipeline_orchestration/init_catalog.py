# src/databricks/pipeline_orchestration/init_catalog.py
# --- src/databricks/pipeline_orchestration/init_catalog.py ---
from pyspark.sql import SparkSession

spark = SparkSession.builder.getOrCreate()

# 1. Map directly to the companion storage account in your resource group
storage_account = "dbstoragevjgyobpzi5hwe" 
container = "main" # You can use any name; Databricks will auto-create the container path
storage_base = f"abfss://{container}@{storage_account}.dfs.core.windows.net"

print(f"🚀 Initializing AIGCT Data Architecture on storage: {storage_account}")

# 2. Deploy catalogs with an explicit target MANAGED LOCATION to bypass metastore limits
catalogs = {
    "aigct_dev": f"{storage_base}/unity/dev",
    "aigct_prod": f"{storage_base}/unity/prod",
    "aigct_governance": f"{storage_base}/unity/governance"
}

for catalog_name, storage_path in catalogs.items():
    # Use the MANAGED LOCATION clause to give the catalog a direct home
    spark.sql(f"CREATE CATALOG IF NOT EXISTS {catalog_name} MANAGED LOCATION '{storage_path}';")
    print(f"✅ Catalog '{catalog_name}' verified/created at {storage_path}.")
    
    # Generate our structural Medallion architecture schemas
    if "governance" not in catalog_name:
        for layer in ["banking_bronze", "banking_silver", "banking_gold"]:
            spark.sql(f"CREATE SCHEMA IF NOT EXISTS {catalog_name}.{layer};")
            print(f"  🧱 Schema {catalog_name}.{layer} verified/created.")

print("🏁 Data mesh setup completed successfully!")
