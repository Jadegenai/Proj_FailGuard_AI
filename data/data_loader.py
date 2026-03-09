import pandas as pd
import numpy as np
import random
import uuid
from datetime import datetime, timedelta

def generate_warranty_data(num_claims=1000):
    # --- 1. Generate 100 Unique Manufacturing Batches ---
    plants = ["Detroit-Main", "Berlin-East", "Shanghai-Giga", "Monterrey-Plant"]
    suppliers = ["PrecisionSteel", "ElectroCore", "PolymerX", "OpticFlow"]
    grades = ["A1", "A2", "B1", "B2"]
    
    batches = []
    for i in range(100):
        batch_id = f"BCH-{2026}{i:03d}"
        qc_score = round(random.uniform(0.1, 5.0), 2)
        
        batches.append({
            "BATCH_ID": batch_id,
            "PRODUCTION_DATE": datetime(2025, 1, 1) + timedelta(days=random.randint(0, 365)),
            "PLANT_LOCATION": random.choice(plants),
            "SUPPLIER_NAME": random.choice(suppliers),
            "QC_SENSITIVITY_SCORE": qc_score,
            "MATERIAL_GRADE": random.choice(grades),
            "OPERATOR_ID": f"OP-{random.randint(100, 999)}"
        })
    
    df_batches = pd.DataFrame(batches)

    # --- 2. Generate 1000 Field Failure & Warranty Claims ---
    failure_types = ["Mechanical", "Electrical", "Structural", "Sensor", "Software"]
    claims = []
    
    for i in range(num_claims):
        # Select a random batch
        batch = random.choice(batches)
        
        # LOGIC: Higher QC scores (>4.0) increase risk of expensive/early failures
        is_risky = batch["QC_SENSITIVITY_SCORE"] > 3.8
        
        days_in_field = random.randint(10, 180) if is_risky else random.randint(30, 720)
        repair_cost = round(random.uniform(800, 5000) * (2.5 if is_risky else 1.0), 2)
        sentiment = round(random.uniform(-1.0, -0.4) if is_risky else random.uniform(-0.3, 0.8), 2)
        
        claims.append({
            "CLAIM_ID": f"CLM-{uuid.uuid4().hex[:8].upper()}",
            "BATCH_ID": batch["BATCH_ID"],
            "CLAIM_DATE": batch["PRODUCTION_DATE"] + timedelta(days=days_in_field),
            "FAILURE_TYPE": random.choice(failure_types),
            "REPAIR_COST": repair_cost,
            "CUSTOMER_SENTIMENT_SCORE": sentiment,
            "DAYS_IN_FIELD": days_in_field
        })
    
    df_claims = pd.DataFrame(claims)

    # --- 3. Generate 20 AI Risk Alerts for the Dashboard ---
    # We'll flag the highest risk batches based on our simulated logic
    risk_alerts = []
    high_risk_batches = df_batches[df_batches["QC_SENSITIVITY_SCORE"] > 4.2].head(20)
    
    for _, row in high_risk_batches.iterrows():
        prob = round(random.uniform(0.75, 0.98), 2)
        risk_alerts.append({
            "ALERT_ID": str(uuid.uuid4()),
            "BATCH_ID": row["BATCH_ID"],
            "PREDICTED_FAILURE_PROBABILITY": prob,
            "RISK_LEVEL": "CRITICAL" if prob > 0.9 else "HIGH",
            "DETECTION_TIMESTAMP": datetime.now(),
            "RECOMMENDED_ACTION": random.choice(["Immediate Recall", "Proactive Service Alert", "Design Audit Required"])
        })
    
    df_alerts = pd.DataFrame(risk_alerts)
    
    return df_batches, df_claims, df_alerts

if __name__ == "__main__":
    df_batches, df_claims, df_alerts = generate_warranty_data()
    
    # Save to CSV for bulk loading into Snowflake
    df_batches.to_csv("MANUFACTURING_DATA.csv", index=False)
    df_claims.to_csv("FIELD_CLAIMS.csv", index=False)
    df_alerts.to_csv("RISK_ALERTS.csv", index=False)
    
    print("✅ 1000 sample records generated for all 3 tables.")
    print("Files ready: MANUFACTURING_DATA.csv, FIELD_CLAIMS.csv, RISK_ALERTS.csv")