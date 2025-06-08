#!/usr/bin/env python3

import json

def fine_tune_formula():
    with open('trip_duration_datasets/trip_duration_1_days.json', 'r') as f:
        data = json.load(f)
    
    print("Fine-tuning 1-Day Formula:")
    print("=" * 60)
    
    # Current formula results
    print("Current formula performance:")
    print("-" * 40)
    
    current_errors = []
    for i, case in enumerate(data, 1):
        miles = case['input']['miles_traveled']
        receipts = case['input']['total_receipts_amount']
        expected = case['expected_output']
        
        # Current formula
        predicted = (miles * 0.5) + (receipts * 0.6)
        
        if miles > 400:
            predicted *= 0.9
        if receipts > 1000:
            predicted *= 0.9
        
        miles_receipts_ratio = miles / receipts if receipts > 0 else 0
        if miles_receipts_ratio > 0.8:
            predicted *= 0.4
        
        error = abs(predicted - expected)
        current_errors.append((i, miles, receipts, expected, predicted, error, miles_receipts_ratio))
        
        print(f"Case {i:2}: Miles={miles:6.1f}, Receipts=${receipts:7.2f}, Expected=${expected:7.2f}, Got=${predicted:7.2f}, Error=${error:6.2f}, Ratio={miles_receipts_ratio:.3f}")
    
    # Sort by error to identify worst cases
    current_errors.sort(key=lambda x: x[5], reverse=True)
    
    print("\nWorst performing cases:")
    print("-" * 60)
    for i in range(min(3, len(current_errors))):
        case_num, miles, receipts, expected, predicted, error, ratio = current_errors[i]
        print(f"Case {case_num}: Miles={miles:.1f}, Receipts=${receipts:.2f}, Expected=${expected:.2f}, Got=${predicted:.2f}, Error=${error:.2f}")
        print(f"  Ratio: {ratio:.3f}, Penalty applied: {ratio > 0.8}")
        
        if ratio > 0.8:
            print(f"  -> Over-penalized? Ratio {ratio:.3f} > 0.8 threshold")
        elif ratio < 0.2:
            print(f"  -> Under-estimated? Low ratio {ratio:.3f}")
        print()
    
    # Test different penalty thresholds and severity
    print("Testing different penalty parameters:")
    print("-" * 50)
    
    best_error = float('inf')
    best_params = None
    
    # Test different ratio thresholds and penalties
    for ratio_threshold in [0.5, 0.6, 0.7, 0.8, 0.9, 1.0]:
        for penalty in [0.2, 0.3, 0.4, 0.5, 0.6, 0.7]:
            total_error = 0
            
            for case in data:
                miles = case['input']['miles_traveled']
                receipts = case['input']['total_receipts_amount']
                expected = case['expected_output']
                
                # Apply formula
                predicted = (miles * 0.5) + (receipts * 0.6)
                
                if miles > 400:
                    predicted *= 0.9
                if receipts > 1000:
                    predicted *= 0.9
                
                miles_receipts_ratio = miles / receipts if receipts > 0 else 0
                if miles_receipts_ratio > ratio_threshold:
                    predicted *= (1 - penalty)
                
                error = abs(predicted - expected)
                total_error += error
            
            avg_error = total_error / len(data)
            
            if avg_error < best_error:
                best_error = avg_error
                best_params = {
                    'ratio_threshold': ratio_threshold,
                    'penalty': penalty
                }
    
    print(f"Best parameters found (Avg Error: ${best_error:.2f}):")
    print(f"  Ratio threshold: {best_params['ratio_threshold']}")
    print(f"  Penalty: {best_params['penalty']}")
    
    print("\nTesting optimized formula:")
    print("-" * 60)
    for i, case in enumerate(data, 1):
        miles = case['input']['miles_traveled']
        receipts = case['input']['total_receipts_amount']
        expected = case['expected_output']
        
        # Apply optimized formula
        predicted = (miles * 0.5) + (receipts * 0.6)
        
        if miles > 400:
            predicted *= 0.9
        if receipts > 1000:
            predicted *= 0.9
        
        miles_receipts_ratio = miles / receipts if receipts > 0 else 0
        if miles_receipts_ratio > best_params['ratio_threshold']:
            predicted *= (1 - best_params['penalty'])
        
        error = abs(predicted - expected)
        
        print(f"Case {i:2}: Miles={miles:6.1f}, Receipts=${receipts:7.2f}, Expected=${expected:7.2f}, Got=${predicted:7.2f}, Error=${error:6.2f}")

if __name__ == "__main__":
    fine_tune_formula() 