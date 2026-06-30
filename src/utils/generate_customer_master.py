import os
import csv
import random
from datetime import datetime, timedelta

def create_mock_customer_csv(records: int = 1000):
    os.makedirs("./data", exist_ok=True)
    file_path = "./data/customer_master.csv"
    
    first_names = ["James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda", "William", "Elizabeth", "David", "Barbara"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez", "Hernandez"]
    countries = ["US", "CA", "GB", "DE", "FR", "CH", "JP", "AU", "SG", "HK", "BR", "MX"]
    kyc_statuses = ["Approved", "Approved", "Approved", "Pending", "Rejected"] # heavily weighted to good data
    cust_types = ["Retail", "Retail", "Corporate", "SME"]
    risk_ratings = ["Low", "Low", "Medium", "High"]
    
    start_date = datetime(2020, 1, 1)
    
    with open(file_path, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        # Headers matching your required staging attributes
        writer.writerow(["Customer_ID", "Customer_Name", "Country_Code", "KYC_Status", "Customer_Type", "Onboarding_Date", "Risk_Rating", "Is_Active"])
        
        for i in range(1, records + 1):
            cust_id = f"CUST_{i:04d}"
            name = f"{random.choice(first_names)} {random.choice(last_names)}"
            country = random.choice(countries)
            
            # Inject a few clean bad data rows deliberately to test quarantine routing
            if i % 15 == 0:
                country = "XX"  # Invalid Country Code (Will fail validation)
            if i % 25 == 0:
                kyc_status = "" # Missing field (Will fail validation)
            else:
                kyc_status = random.choice(kyc_statuses)
                
            cust_type = random.choice(cust_types)
            onboard_date = (start_date + timedelta(days=random.randint(0, 2000))).strftime("%Y-%m-%d")
            risk = random.choice(risk_ratings)
            is_active = random.choice(["Y", "Y", "Y", "N"])
            
            writer.writerow([cust_id, name, country, kyc_status, cust_type, onboard_date, risk, is_active])
            
    print(f"✔ Successfully generated {records} mock customer profiles in '{file_path}'.")

if __name__ == "__main__":
    create_mock_customer_csv()