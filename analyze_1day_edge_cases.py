#!/usr/bin/env python3

import json

def analyze_edge_cases():
    with open('trip_duration_datasets/trip_duration_1_days.json', 'r') as f:
        data = json.load(f)
    
    print("1-Day Trip Edge Case Analysis:")
    print("=" * 80)
    
    # Sort cases by expected output to identify patterns
    sorted_cases = sorted(data, key=lambda x: x['expected_output'])
    
    print("Cases sorted by expected output (lowest to highest):")
    print("-" * 80)
    for i, case in enumerate(sorted_cases, 1):
        miles = case['input']['miles_traveled']
        receipts = case['input']['total_receipts_amount']
        expected = case['expected_output']
        
        # Calculate ratios
        miles_to_receipts_ratio = miles / receipts if receipts > 0 else 0
        receipts_to_miles_ratio = receipts / miles if miles > 0 else 0
        
        print(f"Case {i:2}: Miles={miles:6.1f}, Receipts=${receipts:7.2f}, Expected=${expected:7.2f}")
        print(f"         Miles/Receipts ratio: {miles_to_receipts_ratio:.3f}, Receipts/Miles ratio: {receipts_to_miles_ratio:.3f}")
        print()
    
    # Look for patterns in the lowest reimbursements
    print("Analysis of lowest reimbursements:")
    print("-" * 50)
    
    low_cases = sorted_cases[:3]  # Bottom 3 cases
    for case in low_cases:
        miles = case['input']['miles_traveled']
        receipts = case['input']['total_receipts_amount']
        expected = case['expected_output']
        
        print(f"Miles: {miles}, Receipts: ${receipts:.2f}, Expected: ${expected:.2f}")
        
        # Check if high miles + moderate receipts = penalty
        if miles > 400 and receipts < 1000:
            print("  -> Pattern: High miles + moderate receipts")
        
        # Check miles/receipts ratio
        ratio = miles / receipts if receipts > 0 else 0
        if ratio > 0.5:
            print(f"  -> High miles-to-receipts ratio: {ratio:.3f}")
        
        print()
    
    # Test alternative formulas for edge cases
    print("Testing edge case formulas:")
    print("-" * 40)
    
    # Test formulas with severe penalties for high miles + moderate receipts
    best_error = float('inf')
    best_params = None
    
    for base in [0, 10, 20, 30, 50]:
        for mile_coeff in [0.1, 0.2, 0.3, 0.4, 0.5, 0.6]:
            for receipt_coeff in [0.3, 0.4, 0.5, 0.6, 0.7, 0.8]:
                for severe_penalty_threshold in [0.5, 0.8, 1.0, 1.2]:  # miles/receipts ratio
                    for severe_penalty in [0.5, 0.6, 0.7, 0.8, 0.9]:  # Severe penalty
                        
                        total_error = 0
                        for case in data:
                            miles = case['input']['miles_traveled']
                            receipts = case['input']['total_receipts_amount']
                            expected = case['expected_output']
                            
                            # Base formula
                            predicted = base + (miles * mile_coeff) + (receipts * receipt_coeff)
                            
                            # Apply standard penalties
                            if miles > 400:
                                predicted *= 0.9
                            if receipts > 1000:
                                predicted *= 0.9
                            
                            # Apply severe penalty for high miles/receipts ratio
                            miles_receipts_ratio = miles / receipts if receipts > 0 else 0
                            if miles_receipts_ratio > severe_penalty_threshold:
                                predicted *= (1 - severe_penalty)
                            
                            error = abs(predicted - expected)
                            total_error += error
                        
                        avg_error = total_error / len(data)
                        
                        if avg_error < best_error:
                            best_error = avg_error
                            best_params = {
                                'base': base,
                                'mile_coeff': mile_coeff,
                                'receipt_coeff': receipt_coeff,
                                'severe_penalty_threshold': severe_penalty_threshold,
                                'severe_penalty': severe_penalty,
                            }
    
    print(f"Best edge case formula (Avg Error: ${best_error:.2f}):")
    print(f"  Base: {best_params['base']}")
    print(f"  Mile coefficient: {best_params['mile_coeff']}")
    print(f"  Receipt coefficient: {best_params['receipt_coeff']}")
    print(f"  Severe penalty threshold (miles/receipts ratio): {best_params['severe_penalty_threshold']}")
    print(f"  Severe penalty: {best_params['severe_penalty']}")
    
    print("\nTesting refined formula on each case:")
    print("-" * 80)
    for i, case in enumerate(data, 1):
        miles = case['input']['miles_traveled']
        receipts = case['input']['total_receipts_amount']
        expected = case['expected_output']
        
        # Apply best formula
        predicted = best_params['base'] + (miles * best_params['mile_coeff']) + (receipts * best_params['receipt_coeff'])
        
        # Apply standard penalties
        if miles > 400:
            predicted *= 0.9
        if receipts > 1000:
            predicted *= 0.9
        
        # Apply severe penalty for high miles/receipts ratio
        miles_receipts_ratio = miles / receipts if receipts > 0 else 0
        if miles_receipts_ratio > best_params['severe_penalty_threshold']:
            predicted *= (1 - best_params['severe_penalty'])
        
        error = abs(predicted - expected)
        
        print(f"Case {i:2}: Miles={miles:6.1f}, Receipts=${receipts:7.2f}, Expected=${expected:7.2f}, Predicted=${predicted:7.2f}, Error=${error:6.2f}")
        print(f"         Miles/Receipts ratio: {miles_receipts_ratio:.3f}")

if __name__ == "__main__":
    analyze_edge_cases() 