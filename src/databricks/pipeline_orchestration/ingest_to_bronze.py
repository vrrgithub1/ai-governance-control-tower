# ingest_to_bronze.py
from pyspark.sql import SparkSession

spark = SparkSession.builder.getOrCreate()

# 1. Configuration matching our single-catalog mesh architecture
CATALOG = "adb_governance_control"
SCHEMA = "dev_banking_bronze"
TABLE = "transactions"

STORAGE_ACCOUNT = "saigctdatastor"
CONTAINER = "main"
LANDING_PATH = f"abfss://{CONTAINER}@{STORAGE_ACCOUNT}.dfs.core.windows.net/raw/transactions/"
CHECKPOINT_PATH = f"abfss://{CONTAINER}@{STORAGE_ACCOUNT}.dfs.core.windows.net/checkpoints/dev_bronze_transactions/"

print(f"🔄 Setting up Auto Loader stream from: {LANDING_PATH}")

# 2. Configure Auto Loader (cloudFiles) to stream JSON data incrementally
bronze_stream = (
    spark.readStream
    .format("cloudFiles")
    .option("cloudFiles.format", "json")
    # Schema inference automatically learns and evolves column types
    .option("cloudFiles.inferColumnTypes", "true")
    .load(LANDING_PATH)
)

# 3. Add system metadata attributes for audit tracing and data governance
from pyspark.sql.functions import current_timestamp, input_file_name

enriched_bronze_stream = (
    bronze_stream
    .withColumn("ingest_timestamp", current_timestamp())
    .withColumn("source_file", input_file_name())
)

# 4. Write the stream incrementally into our managed Delta table
query = (
    enriched_bronze_stream.writeStream
    .format("delta")
    .outputMode("append")
    .option("checkpointLocation", CHECKPOINT_PATH)
    # trigger once means it runs as a fast micro-batch and shuts down (saving money!)
    .trigger(availableNow=True) 
    .toTable(f"{CATALOG}.{SCHEMA}.{TABLE}")
)

query.awaitTermination()
print(f"🎉 Bronze ingestion completed successfully! Data loaded into {CATALOG}.{SCHEMA}.{TABLE}")
