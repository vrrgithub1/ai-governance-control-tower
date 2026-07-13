# raw_generator.py
import json
import random
import uuid
from datetime import datetime
from azure.identity import DefaultAzureCredential
from azure.storage.filedatalake import DataLakeServiceClient

def generate_mock_transactions(num_records=10):
    tx_types = ["DEPOSIT", "WITHDRAWAL", "TRANSFER", "PAYMENT"]
    statuses = ["COMPLETED", "PENDING", "FAILED"]
    
    records = []
    for _ in range(num_records):
        records.append({
            "transaction_id": str(uuid.uuid4()),
            "account_id": f"ACC-{random.randint(10000, 99999)}",
            "amount": round(random.uniform(5.0, 2500.0), 2),
            "transaction_type": random.choice(tx_types),
            "status": random.choice(statuses),
            # Old line: "timestamp": datetime.utcnow().isoformat() + "Z"
            # Replace with this clean, timezone-aware UTC format:
            "timestamp": datetime.now(datetime.timezone.utc).isoformat()
        })
    return records

def upload_to_adls():
    account_name = "saigctdatastor"
    file_system_name = "main"
    
    # Authenticate using Azure CLI credentials active in the session
    credential = DefaultAzureCredential()
    service_client = DataLakeServiceClient(
        account_url=f"https://{account_name}.dfs.core.windows.net", 
        credential=credential
    )
    
    # Structure a timestamped file name
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = f"raw/transactions/batch_{timestamp}.json"
    
    # Generate data
    data_records = generate_mock_transactions(15)
    # Convert array of dicts into line-delimited JSON format (JSON Lines)
    json_lines = "\n".join([json.dumps(r) for r in data_records])
    
    # Upload directly to the Azure Landing Zone
    file_system_client = service_client.get_file_system_client(file_system_name)
    file_client = file_system_client.get_file_client(file_path)
    
    print(f"📡 Generating and uploading {len(data_records)} mock transactions to ADLS Gen2...")
    file_client.upload_data(json_lines, overwrite=True)
    print(f"🚀 File written successfully to: {file_path}")

if __name__ == "__main__":
    upload_to_adls()
