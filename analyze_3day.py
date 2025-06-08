#!/usr/bin/env python3

import json

def analyze_3day_trips():
    with open('trip_duration_datasets/trip_duration_3_days.json', 'r') as f:
        data = json.load(f)
    
    print("3-Day Trip Analysis:")
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
        receipts_per_day = receipts / 3
        print(f"{i+1:2}: Miles={miles:6.1f}, Receipts=${receipts:7.2f}, Expected=${expected:7.2f}, Ratio={ratio:.3f}, ReceiptsPerDay=${receipts_per_day:.2f}")
    
    # Current 3-day logic analysis
    print("\nCurrent 3-day logic performance:")
    print("-" * 50)
    
    current_errors = []
    for i, case in enumerate(data, 1):
        miles = case['input']['miles_traveled']
        receipts = case['input']['total_receipts_amount']
        expected = case['expected_output']
        
        # Current 3-day logic from reimbursement.py
        receipts_per_day = receipts / 3
        
        if receipts < 50:
            daily_rate = 100.0
            mileage_rate = 0.70
            receipt_rate = -0.50
            bonus = -20
        elif receipts_per_day < 75:
            daily_rate = 90.0
            mileage_rate = 0.80
            receipt_rate = 0.95
            bonus = 0
        else:
            daily_rate = 95.0
            mileage_rate = 0.95
            receipt_rate = 1.25
            bonus = 50
        
        predicted = (3 * daily_rate) + (miles * mileage_rate) + (receipts * receipt_rate) + bonus
        error = abs(predicted - expected)
        current_errors.append((i, miles, receipts, expected, predicted, error))
        
        print(f"Case {i:2}: Miles={miles:6.1f}, Receipts=${receipts:7.2f}, Expected=${expected:7.2f}, Got=${predicted:7.2f}, Error=${error:7.2f}")
    
    current_avg_error = sum(x[5] for x in current_errors) / len(current_errors)
    print(f"\nCurrent average error: ${current_avg_error:.2f}")
    
    # Identify the worst over-estimations
    worst_cases = sorted(current_errors, key=lambda x: x[5], reverse=True)
    print(f"\nWorst over-estimations:")
    print("-" * 60)
    for i in range(min(3, len(worst_cases))):
        case_num, miles, receipts, expected, predicted, error = worst_cases[i]
        over_estimation = predicted - expected
        print(f"Case {case_num}: Miles={miles:.1f}, Receipts=${receipts:.2f}")
        print(f"  Expected=${expected:.2f}, Got=${predicted:.2f}, Over by=${over_estimation:.2f}")
        print(f"  Receipts per day: ${receipts/3:.2f}")
        print()
    
    # Test optimized formulas
    print("\nTesting optimized formulas:")
    print("-" * 40)
    
    best_error = float('inf')
    best_params = None
    
    # Test various coefficients - much lower rates since current is over-estimating
    for base in [0, 20, 40, 60, 80, 100]:
        for mile_coeff in [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]:
            for receipt_coeff in [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]:
                # Test different receipt thresholds for different logic
                for receipt_threshold in [500, 1000, 1500, 2000, 2500]:
                    # Test penalties for high values
                    for mile_penalty_threshold in [400, 600, 800, 1000]:
                        for mile_penalty in [0, 0.1, 0.2, 0.3]:
                            for receipt_penalty_threshold in [1000, 1500, 2000]:
                                for receipt_penalty in [0, 0.1, 0.2, 0.3]:
                                    
                                    total_error = 0
                                    for case in data:
                                        miles = case['input']['miles_traveled']
                                        receipts = case['input']['total_receipts_amount']
                                        expected = case['expected_output']
                                        
                                        # Base formula
                                        predicted = base + (miles * mile_coeff) + (receipts * receipt_coeff)
                                        
                                        # Apply logic based on receipt threshold
                                        if receipts < receipt_threshold:
                                            predicted *= 1.1  # Small bonus for lower receipts
                                        
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
                                            'receipt_threshold': receipt_threshold,
                                            'mile_penalty_threshold': mile_penalty_threshold,
                                            'mile_penalty': mile_penalty,
                                            'receipt_penalty_threshold': receipt_penalty_threshold,
                                            'receipt_penalty': receipt_penalty,
                                        }
    
    print(f"Best optimized formula (Avg Error: ${best_error:.2f}):")
    print(f"  Base: {best_params['base']}")
    print(f"  Mile coefficient: {best_params['mile_coeff']}")
    print(f"  Receipt coefficient: {best_params['receipt_coeff']}")
    print(f"  Receipt threshold for bonus: {best_params['receipt_threshold']}")
    print(f"  Mile penalty threshold: {best_params['mile_penalty_threshold']}")
    print(f"  Mile penalty: {best_params['mile_penalty']}")
    print(f"  Receipt penalty threshold: {best_params['receipt_penalty_threshold']}")
    print(f"  Receipt penalty: {best_params['receipt_penalty']}")
    
    improvement = current_avg_error - best_error
    improvement_pct = (improvement / current_avg_error * 100) if current_avg_error > 0 else 0
    print(f"\nImprovement: ${improvement:.2f} ({improvement_pct:.1f}%)")
    
    print("\nTesting optimized formula on each case:")
    print("-" * 80)
    for i, case in enumerate(data, 1):
        miles = case['input']['miles_traveled']
        receipts = case['input']['total_receipts_amount']
        expected = case['expected_output']
        
        # Apply optimized formula
        predicted = best_params['base'] + (miles * best_params['mile_coeff']) + (receipts * best_params['receipt_coeff'])
        
        # Apply logic based on receipt threshold
        if receipts < best_params['receipt_threshold']:
            predicted *= 1.1
        
        # Apply penalties
        if miles > best_params['mile_penalty_threshold']:
            predicted *= (1 - best_params['mile_penalty'])
        
        if receipts > best_params['receipt_penalty_threshold']:
            predicted *= (1 - best_params['receipt_penalty'])
        
        error = abs(predicted - expected)
        
        print(f"Case {i:2}: Miles={miles:6.1f}, Receipts=${receipts:7.2f}, Expected=${expected:7.2f}, Predicted=${predicted:7.2f}, Error=${error:6.2f}")

if __name__ == "__main__":
    analyze_3day_trips() 