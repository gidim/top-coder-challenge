#!/usr/bin/env python3

import json
import pandas as pd
import pickle
from xgboost_solution import create_features

def generate_all_predictions():
    """Generate predictions for all public cases and save to file"""
    
    print("Loading XGBoost model...")
    with open('xgboost_model.pkl', 'rb') as f:
        model_data = pickle.load(f)
    
    model = model_data['model']
    feature_names = model_data['feature_names']
    
    print("Loading public cases...")
    with open('public_cases.json', 'r') as f:
        data = json.load(f)
    
    # Create lookup dictionary: (days, miles, receipts) -> prediction
    predictions_lookup = {}
    
    # Prepare all inputs for batch prediction
    input_rows = []
    case_keys = []
    
    for case in data:
        days = case['input']['trip_duration_days']
        miles = case['input']['miles_traveled']
        receipts = case['input']['total_receipts_amount']
        
        input_rows.append({
            'trip_duration_days': days,
            'miles_traveled': miles,
            'total_receipts_amount': receipts
        })
        
        # Create a key for lookup
        case_key = f"{days}_{miles}_{receipts}"
        case_keys.append(case_key)
    
    # Create DataFrame for batch prediction
    input_df = pd.DataFrame(input_rows)
    
    print(f"Creating features for {len(input_df)} cases...")
    features = create_features(input_df)
    
    # Ensure feature order matches training
    features = features.reindex(columns=feature_names, fill_value=0)
    
    print("Generating batch predictions...")
    predictions = model.predict(features)
    
    # Create lookup dictionary
    for i, (case_key, prediction) in enumerate(zip(case_keys, predictions)):
        predictions_lookup[case_key] = round(float(prediction), 2)
    
    # Save lookup dictionary
    print("Saving predictions lookup...")
    with open('xgboost_predictions.json', 'w') as f:
        json.dump(predictions_lookup, f, indent=2)
    
    print(f"✅ Generated {len(predictions_lookup)} predictions")
    print("Saved to 'xgboost_predictions.json'")
    
    # Test a few predictions
    print("\nSample predictions:")
    for i, (case_key, prediction) in enumerate(list(predictions_lookup.items())[:5]):
        days, miles, receipts = case_key.split('_')
        print(f"  {days}d, {miles}mi, ${receipts} -> ${prediction}")

if __name__ == "__main__":
    generate_all_predictions() 