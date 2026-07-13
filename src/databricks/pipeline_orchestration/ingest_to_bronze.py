# ingest_to_bronze.py
from pyspark.sql import SparkSession
from pyspark.sql.functions import current_timestamp, input_file_name

spark = SparkSession.builder.getOrCreate()

# 1. Configuration matching our single-catalog mesh architecture
CATALOG = "adb_governance_control"
SCHEMA = "dev_banking_bronze"
TABLE = "transactions"

STORAGE_ACCOUNT = "saigctdatastor"
CONTAINER = "main"

# Explicit paths pointing directly to your validated external location setup
LANDING_PATH = f"abfss://{CONTAINER}@{STORAGE_ACCOUNT}.dfs.core.windows.net/raw/transactions/"
TABLE_LOCATION = f"abfss://{CONTAINER}@{STORAGE_ACCOUNT}.dfs.core.windows.net/unity/dev_banking_bronze/transactions/"
CHECKPOINT_PATH = f"abfss://{CONTAINER}@{STORAGE_ACCOUNT}.dfs.core.windows.net/checkpoints/dev_bronze_transactions/"

print(f"🔄 Setting up Auto Loader stream from landing zone: {LANDING_PATH}")

# 2. Configure Auto Loader (cloudFiles) to stream JSON data incrementally
bronze_stream = (
    spark.readStream
    .format("cloudFiles")
    .option("cloudFiles.format", "json")
    .option("cloudFiles.inferColumnTypes", "true")
    .load(LANDING_PATH)
)

# 3. Add system metadata attributes for audit tracing and data governance
enriched_bronze_stream = (
    bronze_stream
    .withColumn("ingest_timestamp", current_timestamp())
    .withColumn("source_file", input_file_name())
)

print(f"✍️ Streaming data out to targeted storage table path: {TABLE_LOCATION}")

# 4. Write the stream explicitly specifying the external location target path
query = (
    enriched_bronze_stream.writeStream
    .format("delta")
    .outputMode("append")
    .option("checkpointLocation", CHECKPOINT_PATH)
    # The crucial fix: forcing it to create an external table at our location path
    .option("path", TABLE_LOCATION)
    .trigger(availableNow=True) 
    .toTable(f"{CATALOG}.{SCHEMA}.{TABLE}")
)

query.awaitTermination()
print(f"🎉 Bronze ingestion completed successfully! Data loaded into {CATALOG}.{SCHEMA}.{TABLE}")
