import os
import csv
import random
from datetime import datetime, timedelta

def create_mock_trades_csv(records: int = 4000):
    os.makedirs("./data", exist_ok=True)
    file_path = "./data/trade_transactions.csv"
    
    products = ["Equity", "FX Spot", "Fixed Income", "Commodity Options", "Crypto ETF"]
    currencies = ["USD", "EUR", "GBP", "CAD", "JPY", "SGD", "HKD"]
    statuses = ["Settled", "Settled", "Pending", "Cancelled"]
    
    start_date = datetime(2026, 1, 1)
    
    with open(file_path, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["Trade_ID", "Trade_Date", "Customer_ID", "Counterparty_ID", "Product_Type", "Trade_Amount", "Currency", "Trade_Status"])
        
        for i in range(1, records + 1):
            trade_id = f"TRD_{i:05d}"
            t_date = (start_date + timedelta(days=random.randint(0, 180))).strftime("%Y-%m-%d")
            cust_id = f"CUST_{random.randint(1, 950):04d}"
            counterparty = f"CPTY_{random.randint(100, 150)}"
            prod_type = random.choice(products)
            amount = round(random.uniform(5000.00, 2500000.00), 2)
            currency = random.choice(currencies)
            status = random.choice(statuses)
            
            # Synthesize targeted data quality anomalies
            if i % 40 == 0:
                amount = -150.00    # Break DQ105 (Negative amount)
            if i % 60 == 0:
                currency = "ZWD"    # Break DQ106 (Unsupported currency)
            if i % 80 == 0:
                cust_id = ""       # Break DQ104 (Missing Customer ID)
                
            writer.writerow([trade_id, t_date, cust_id, counterparty, prod_type, amount, currency, status])
            
    print(f"✔ Successfully generated {records} mock trade entries in '{file_path}'.")

if __name__ == "__main__":
    create_mock_trades_csv()
