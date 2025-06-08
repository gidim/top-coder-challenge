#!/usr/bin/env python3

import json

def analyze_2day_trips():
    with open('trip_duration_datasets/trip_duration_2_days.json', 'r') as f:
        data = json.load(f)
    
    print("2-Day Trip Analysis:")
    print("=" * 80)
    print(f"{'Miles':<8} {'Receipts':<10} {'Expected':<10} {'$/Mile':<8} {'$/Receipt':<12} {'Miles/Receipts':<15}")
    print("-" * 80)
    
    for case in data:
        miles = case['input']['miles_traveled']
        receipts = case['input']['total_receipts_amount']
        expected = case['expected_output']
        
        # Calculate per-mile, per-receipt rates, and ratios
        per_mile = expected / miles if miles > 0 else 0
        per_receipt = expected / receipts if receipts > 0 else 0
        miles_receipts_ratio = miles / receipts if receipts > 0 else 0
        
        print(f"{miles:<8.1f} ${receipts:<9.2f} ${expected:<9.2f} ${per_mile:<7.2f} ${per_receipt:<11.4f} {miles_receipts_ratio:<14.3f}")
    
    print("\nLooking for patterns...")
    
    # Sort by different criteria to find patterns
    print("\nSorted by expected output (lowest to highest):")
    print("-" * 60)
    sorted_by_expected = sorted(data, key=lambda x: x['expected_output'])
    for i, case in enumerate(sorted_by_expected):
        miles = case['input']['miles_traveled']
        receipts = case['input']['total_receipts_amount']
        expected = case['expected_output']
        ratio = miles / receipts if receipts > 0 else 0
        print(f"{i+1:2}: Miles={miles:6.1f}, Receipts=${receipts:7.2f}, Expected=${expected:7.2f}, Ratio={ratio:.3f}")
    
    # Current 2-day logic analysis
    print("\nCurrent 2-day logic performance:")
    print("-" * 50)
    
    current_errors = []
    for i, case in enumerate(data, 1):
        miles = case['input']['miles_traveled']
        receipts = case['input']['total_receipts_amount']
        expected = case['expected_output']
        
        # Current 2-day logic from reimbursement.py
        if miles < 100:
            daily_rate = 95.0
            mileage_rate = 0.80
            receipt_rate = 0.65
            bonus = 0
        else:
            daily_rate = 90.0
            mileage_rate = 0.75
            receipt_rate = 1.00
            bonus = -19.1
        
        predicted = (2 * daily_rate) + (miles * mileage_rate) + (receipts * receipt_rate) + bonus
        error = abs(predicted - expected)
        current_errors.append((i, miles, receipts, expected, predicted, error))
        
        print(f"Case {i:2}: Miles={miles:6.1f}, Receipts=${receipts:7.2f}, Expected=${expected:7.2f}, Got=${predicted:7.2f}, Error=${error:6.2f}")
    
    current_avg_error = sum(x[5] for x in current_errors) / len(current_errors)
    print(f"\nCurrent average error: ${current_avg_error:.2f}")
    
    # Test optimized formulas
    print("\nTesting optimized formulas:")
    print("-" * 40)
    
    best_error = float('inf')
    best_params = None
    
    # Test various coefficients and thresholds
    for base in [0, 20, 40, 60, 80, 100, 120, 150]:
        for mile_coeff in [0.2, 0.4, 0.6, 0.8, 1.0, 1.2, 1.4, 1.6]:
            for receipt_coeff in [0.2, 0.4, 0.6, 0.8, 1.0, 1.2, 1.4]:
                # Test different mile thresholds for different logic
                for mile_threshold in [50, 75, 100, 125, 150, 200]:
                    # Test penalties for high values
                    for mile_penalty_threshold in [200, 300, 400, 500]:
                        for mile_penalty in [0, 0.1, 0.2]:
                            for receipt_penalty_threshold in [500, 1000, 1500]:
                                for receipt_penalty in [0, 0.1, 0.2]:
                                    
                                    total_error = 0
                                    for case in data:
                                        miles = case['input']['miles_traveled']
                                        receipts = case['input']['total_receipts_amount']
                                        expected = case['expected_output']
                                        
                                        # Base formula
                                        predicted = base + (miles * mile_coeff) + (receipts * receipt_coeff)
                                        
                                        # Apply logic based on mile threshold
                                        if miles < mile_threshold:
                                            predicted *= 1.1  # Bonus for lower miles
                                        
                                        # Apply penalties for high values
                                        if miles > mile_penalty_threshold:
                                            predicted *= (1 - mile_penalty)
                                        
                                        if receipts > receipt_penalty_threshold:
                                            predicted *= (1 - receipt_penalty)
                                        
                                        error = abs(predicted - expected)
                                        total_error += error
                                    
                                    avg_error = total_error / len(data)
                                    
                                    if avg_error < best_error:
                                        best_error = avg_error
                                        best_params = {
                                            'base': base,
                                            'mile_coeff': mile_coeff,
                                            'receipt_coeff': receipt_coeff,
                                            'mile_threshold': mile_threshold,
                                            'mile_penalty_threshold': mile_penalty_threshold,
                                            'mile_penalty': mile_penalty,
                                            'receipt_penalty_threshold': receipt_penalty_threshold,
                                            'receipt_penalty': receipt_penalty,
                                        }
    
    print(f"Best optimized formula (Avg Error: ${best_error:.2f}):")
    print(f"  Base: {best_params['base']}")
    print(f"  Mile coefficient: {best_params['mile_coeff']}")
    print(f"  Receipt coefficient: {best_params['receipt_coeff']}")
    print(f"  Mile threshold for bonus: {best_params['mile_threshold']}")
    print(f"  Mile penalty threshold: {best_params['mile_penalty_threshold']}")
    print(f"  Mile penalty: {best_params['mile_penalty']}")
    print(f"  Receipt penalty threshold: {best_params['receipt_penalty_threshold']}")
    print(f"  Receipt penalty: {best_params['receipt_penalty']}")
    
    print(f"\nImprovement: ${current_avg_error - best_error:.2f} ({((current_avg_error - best_error) / current_avg_error * 100):.1f}%)")
    
    print("\nTesting optimized formula on each case:")
    print("-" * 80)
    for i, case in enumerate(data, 1):
        miles = case['input']['miles_traveled']
        receipts = case['input']['total_receipts_amount']
        expected = case['expected_output']
        
        # Apply optimized formula
        predicted = best_params['base'] + (miles * best_params['mile_coeff']) + (receipts * best_params['receipt_coeff'])
        
        # Apply logic based on mile threshold
        if miles < best_params['mile_threshold']:
            predicted *= 1.1
        
        # Apply penalties
        if miles > best_params['mile_penalty_threshold']:
            predicted *= (1 - best_params['mile_penalty'])
        
        if receipts > best_params['receipt_penalty_threshold']:
            predicted *= (1 - best_params['receipt_penalty'])
        
        error = abs(predicted - expected)
        
        print(f"Case {i:2}: Miles={miles:6.1f}, Receipts=${receipts:7.2f}, Expected=${expected:7.2f}, Predicted=${predicted:7.2f}, Error=${error:6.2f}")

if __name__ == "__main__":
    analyze_2day_trips() 