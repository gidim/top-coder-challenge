#!/usr/bin/env python3

import json
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import cross_val_score, KFold
from sklearn.metrics import mean_absolute_error, r2_score
import pickle
import sys

def create_features(df):
    """Create engineered features from the basic inputs"""
    # Basic features
    features = df.copy()
    
    # Derived features
    features['daily_rate'] = features['miles_traveled'] / features['trip_duration_days']
    features['daily_receipts'] = features['total_receipts_amount'] / features['trip_duration_days']
    features['miles_per_dollar'] = features['miles_traveled'] / (features['total_receipts_amount'] + 0.01)
    features['dollars_per_mile'] = features['total_receipts_amount'] / (features['miles_traveled'] + 0.01)
    
    # Trip duration categories
    features['is_1day'] = (features['trip_duration_days'] == 1).astype(int)
    features['is_2day'] = (features['trip_duration_days'] == 2).astype(int)
    features['is_3day'] = (features['trip_duration_days'] == 3).astype(int)
    features['is_4_6day'] = ((features['trip_duration_days'] >= 4) & (features['trip_duration_days'] <= 6)).astype(int)
    features['is_7plus_day'] = (features['trip_duration_days'] >= 7).astype(int)
    features['is_long_trip'] = (features['trip_duration_days'] >= 10).astype(int)
    
    # Spending patterns
    features['high_daily_spending'] = (features['daily_receipts'] > 100).astype(int)
    features['very_high_daily_spending'] = (features['daily_receipts'] > 200).astype(int)
    features['low_miles'] = (features['miles_traveled'] < 100).astype(int)
    features['high_miles'] = (features['miles_traveled'] > 500).astype(int)
    features['very_high_miles'] = (features['miles_traveled'] > 1000).astype(int)
    
    # Hustle theory features (from interviews)
    features['hustle_ratio'] = features['miles_traveled'] / (features['total_receipts_amount'] + 1)
    features['is_hustle_trip'] = (features['hustle_ratio'] > 0.8).astype(int)
    features['is_vacation_trip'] = (features['hustle_ratio'] < 0.1).astype(int)
    
    # Interaction features
    features['days_miles_interaction'] = features['trip_duration_days'] * features['miles_traveled']
    features['days_receipts_interaction'] = features['trip_duration_days'] * features['total_receipts_amount']
    features['miles_receipts_interaction'] = features['miles_traveled'] * features['total_receipts_amount']
    
    # Polynomial features for key variables
    features['days_squared'] = features['trip_duration_days'] ** 2
    features['miles_squared'] = features['miles_traveled'] ** 2
    features['receipts_squared'] = features['total_receipts_amount'] ** 2
    features['daily_receipts_squared'] = features['daily_receipts'] ** 2
    
    # Log features (handle zeros)
    features['log_miles'] = np.log1p(features['miles_traveled'])
    features['log_receipts'] = np.log1p(features['total_receipts_amount'])
    features['log_days'] = np.log1p(features['trip_duration_days'])
    
    # Binned features
    features['miles_bin'] = pd.cut(features['miles_traveled'], bins=10, labels=False)
    features['receipts_bin'] = pd.cut(features['total_receipts_amount'], bins=10, labels=False)
    features['days_bin'] = pd.cut(features['trip_duration_days'], bins=5, labels=False)
    
    return features

def load_and_prepare_data():
    """Load and prepare the training data"""
    with open('public_cases.json', 'r') as f:
        data = json.load(f)
    
    # Convert to DataFrame
    rows = []
    for case in data:
        row = {
            'trip_duration_days': case['input']['trip_duration_days'],
            'miles_traveled': case['input']['miles_traveled'],
            'total_receipts_amount': case['input']['total_receipts_amount'],
            'reimbursement': case['expected_output']
        }
        rows.append(row)
    
    df = pd.DataFrame(rows)
    
    # Create features
    X = create_features(df[['trip_duration_days', 'miles_traveled', 'total_receipts_amount']])
    y = df['reimbursement']
    
    return X, y, df

def train_xgboost_model(X, y):
    """Train an XGBoost model with hyperparameter optimization"""
    
    print(f"Training XGBoost model with {X.shape[1]} features on {X.shape[0]} samples...")
    
    # XGBoost parameters optimized for this problem
    params = {
        'objective': 'reg:squarederror',
        'eval_metric': 'mae',
        'max_depth': 8,
        'learning_rate': 0.05,
        'n_estimators': 500,
        'subsample': 0.8,
        'colsample_bytree': 0.8,
        'min_child_weight': 1,
        'reg_alpha': 0.1,
        'reg_lambda': 1.0,
        'random_state': 42
    }
    
    # Create model for cross-validation (without early stopping)
    cv_model = xgb.XGBRegressor(**params)
    
    # Cross-validation
    cv_scores = cross_val_score(cv_model, X, y, cv=5, scoring='neg_mean_absolute_error')
    cv_mae = -cv_scores.mean()
    cv_std = cv_scores.std()
    
    print(f"Cross-validation MAE: ${cv_mae:.2f} ± ${cv_std:.2f}")
    
    # Train final model (using CV results as they're already excellent)
    final_params = params.copy()
    final_params['n_estimators'] = 800  # Use a reasonable number without early stopping
    final_model = xgb.XGBRegressor(**final_params)
    
    # Fit the final model
    final_model.fit(X, y, verbose=False)
    
    # Feature importance
    feature_importance = pd.DataFrame({
        'feature': X.columns,
        'importance': final_model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    print("\nTop 10 Most Important Features:")
    print(feature_importance.head(10))
    
    return final_model, feature_importance

def evaluate_model(model, X, y):
    """Evaluate the model performance"""
    predictions = model.predict(X)
    
    mae = mean_absolute_error(y, predictions)
    r2 = r2_score(y, predictions)
    
    # Calculate errors
    errors = np.abs(predictions - y)
    exact_matches = np.sum(errors < 0.01)
    close_matches = np.sum(errors < 1.0)
    
    print(f"\nModel Performance:")
    print(f"Average Error (MAE): ${mae:.2f}")
    print(f"R² Score: {r2:.3f}")
    print(f"Exact matches (±$0.01): {exact_matches} ({exact_matches/len(y)*100:.1f}%)")
    print(f"Close matches (±$1.00): {close_matches} ({close_matches/len(y)*100:.1f}%)")
    print(f"Max error: ${np.max(errors):.2f}")
    
    # Calculate score like eval.sh
    score = mae * 100 + (len(y) - exact_matches) * 0.1
    print(f"Challenge Score: {score:.2f}")
    
    return predictions, mae, r2

def save_model(model, feature_names):
    """Save the trained model"""
    model_data = {
        'model': model,
        'feature_names': list(feature_names)
    }
    
    with open('xgboost_model.pkl', 'wb') as f:
        pickle.dump(model_data, f)
    print("\nModel saved as 'xgboost_model.pkl'")

def predict_single(days, miles, receipts, model_path='xgboost_model.pkl'):
    """Make a single prediction using the saved model"""
    with open(model_path, 'rb') as f:
        model_data = pickle.load(f)
    
    model = model_data['model']
    feature_names = model_data['feature_names']
    
    # Create single row DataFrame
    input_df = pd.DataFrame({
        'trip_duration_days': [days],
        'miles_traveled': [miles],
        'total_receipts_amount': [receipts]
    })
    
    # Create features
    features = create_features(input_df)
    
    # Ensure feature order matches training
    features = features.reindex(columns=feature_names, fill_value=0)
    
    # Predict
    prediction = model.predict(features)[0]
    return round(prediction, 2)

def analyze_worst_cases(model, X, y, df, top_n=10):
    """Analyze the worst prediction cases"""
    predictions = model.predict(X)
    errors = np.abs(predictions - y)
    
    # Get worst cases
    worst_indices = np.argsort(errors)[-top_n:][::-1]
    
    print(f"\nTop {top_n} Worst Cases:")
    print("=" * 80)
    
    for i, idx in enumerate(worst_indices):
        print(f"{i+1:2d}. Case {idx+1}:")
        print(f"    Input: {df.iloc[idx]['trip_duration_days']}d, {df.iloc[idx]['miles_traveled']}mi, ${df.iloc[idx]['total_receipts_amount']:.2f}")
        print(f"    Expected: ${y.iloc[idx]:.2f}, Predicted: ${predictions[idx]:.2f}")
        print(f"    Error: ${errors[idx]:.2f}")
        print()

if __name__ == "__main__":
    if len(sys.argv) == 4:
        # Prediction mode for run.sh
        days, miles, receipts = int(sys.argv[1]), int(sys.argv[2]), float(sys.argv[3])
        result = predict_single(days, miles, receipts)
        print(result)
    else:
        # Training mode
        print("🤖 XGBoost Reimbursement System Training")
        print("=" * 50)
        
        # Load and prepare data
        X, y, df = load_and_prepare_data()
        print(f"Loaded {len(df)} training cases")
        print(f"Created {X.shape[1]} features")
        
        # Train model
        model, feature_importance = train_xgboost_model(X, y)
        
        # Evaluate
        predictions, mae, r2 = evaluate_model(model, X, y)
        
        # Analyze worst cases
        analyze_worst_cases(model, X, y, df)
        
        # Save model
        save_model(model, X.columns)
        
        print(f"\n🎯 XGBoost model trained! Average error: ${mae:.2f}")
        print("Run './eval.sh' to test with the challenge evaluation script.") 