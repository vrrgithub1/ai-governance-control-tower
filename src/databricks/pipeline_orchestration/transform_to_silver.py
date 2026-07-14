# transform_to_silver.py
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, to_timestamp, upper

spark = SparkSession.builder.getOrCreate()

# 1. Configuration matching our single-catalog mesh architecture
CATALOG = "adb_governance_control"
SOURCE_SCHEMA = "dev_banking_bronze"
TARGET_SCHEMA = "dev_banking_silver"
TABLE = "transactions"

STORAGE_ACCOUNT = "saigctdatastor"
CONTAINER = "main"

# Explicit storage paths matching our secure Unity Catalog external location setup
TABLE_LOCATION = f"abfss://{CONTAINER}@{STORAGE_ACCOUNT}.dfs.core.windows.net/unity/dev_banking_silver/transactions/"
CHECKPOINT_PATH = f"abfss://{CONTAINER}@{STORAGE_ACCOUNT}.dfs.core.windows.net/checkpoints/dev_silver_transactions/"

print(f"🔄 Reading incremental stream from Bronze table: {CATALOG}.{SOURCE_SCHEMA}.{TABLE}")

# 2. Read as a stream directly from our managed Bronze Delta table
bronze_stream = spark.readStream.table(f"{CATALOG}.{SOURCE_SCHEMA}.{TABLE}")

# 3. Transform data types & enforce enterprise analytics schema standards
# This explicit column-level manipulation triggers Unity Catalog's detailed column lineage mapping!
silver_transformed_stream = (
    bronze_stream
    .withColumn("transaction_id", col("transaction_id"))
    .withColumn("account_id", col("account_id"))
    # Cast raw string timestamp to a structured Spark SQL Timestamp Type
    .withColumn("transaction_timestamp", to_timestamp(col("timestamp")))
    # Safely cast financial amounts to doubles for calculations
    .withColumn("amount", col("amount").cast("double"))
    # Clean up classification strings by standardizing them to UPPERCASE
    .withColumn("transaction_type", upper(col("transaction_type")))
    .withColumn("status", upper(col("status")))
    # Carry forward audit tracking fields unchanged
    .withColumn("ingest_timestamp", col("ingest_timestamp"))
    .withColumn("source_file", col("source_file"))
    # Drop the uncleaned string column to optimize storage
    .drop("timestamp")
)

print(f"✍️ Streaming cleansed rows out to Silver target path: {TABLE_LOCATION}")

# 4. Write out incrementally into the Silver schema table
query = (
    silver_transformed_stream.writeStream
    .format("delta")
    .outputMode("append")
    .option("checkpointLocation", CHECKPOINT_PATH)
    .option("path", TABLE_LOCATION)
    .trigger(availableNow=True)
    .toTable(f"{CATALOG}.{TARGET_SCHEMA}.{TABLE}")
)

query.awaitTermination()
print(f"🎉 Silver transformation completed successfully! Data loaded into {CATALOG}.{TARGET_SCHEMA}.{TABLE}")
