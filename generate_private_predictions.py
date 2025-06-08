#!/usr/bin/env python3

import json
import pandas as pd
import pickle
from xgboost_solution import create_features

def generate_private_predictions():
    """Generate predictions for all private cases and save to private_results.txt"""
    
    print("Loading XGBoost model...")
    with open('xgboost_model.pkl', 'rb') as f:
        model_data = pickle.load(f)
    
    model = model_data['model']
    feature_names = model_data['feature_names']
    
    print("Loading private cases...")
    with open('private_cases.json', 'r') as f:
        data = json.load(f)
    
    print(f"Processing {len(data)} private cases...")
    
    # Prepare all inputs for batch prediction
    input_rows = []
    
    for case in data:
        days = case['trip_duration_days']
        miles = case['miles_traveled']
        receipts = case['total_receipts_amount']
        
        input_rows.append({
            'trip_duration_days': days,
            'miles_traveled': miles,
            'total_receipts_amount': receipts
        })
    
    # Create DataFrame for batch prediction
    input_df = pd.DataFrame(input_rows)
    
    print(f"Creating features for {len(input_df)} cases...")
    features = create_features(input_df)
    
    # Ensure feature order matches training
    features = features.reindex(columns=feature_names, fill_value=0)
    
    print("Generating batch predictions...")
    predictions = model.predict(features)
    
    # Save results to private_results.txt (one per line)
    print("Saving results to private_results.txt...")
    with open('private_results.txt', 'w') as f:
        for prediction in predictions:
            f.write(f"{round(float(prediction), 2)}\n")
    
    print(f"✅ Generated {len(predictions)} predictions")
    print("Saved to 'private_results.txt'")
    
    # Show some sample predictions
    print(f"\nFirst 10 predictions:")
    for i in range(min(10, len(predictions))):
        days = data[i]['trip_duration_days']
        miles = data[i]['miles_traveled']
        receipts = data[i]['total_receipts_amount']
        pred = round(float(predictions[i]), 2)
        print(f"  Case {i+1}: {days}d, {miles}mi, ${receipts} -> ${pred}")

if __name__ == "__main__":
    generate_private_predictions() 