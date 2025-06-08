#!/usr/bin/env python3

import json

def analyze_4_6_day_trips():
    # Load data for 4, 5, and 6-day trips
    all_data = []
    
    for days in [4, 5, 6]:
        with open(f'trip_duration_datasets/trip_duration_{days}_days.json', 'r') as f:
            data = json.load(f)
            for case in data:
                case['trip_days'] = days  # Add trip duration for analysis
                all_data.append(case)
    
    print("4-6 Day Trip Analysis:")
    print("=" * 90)
    print(f"{'Days':<5} {'Miles':<8} {'Receipts':<10} {'Expected':<10} {'$/Mile':<8} {'$/Receipt':<12} {'Miles/Receipts':<15}")
    print("-" * 90)
    
    for case in all_data:
        days = case['trip_days']
        miles = case['input']['miles_traveled']
        receipts = case['input']['total_receipts_amount']
        expected = case['expected_output']
        
        # Calculate per-mile, per-receipt rates, and ratios
        per_mile = expected / miles if miles > 0 else 0
        per_receipt = expected / receipts if receipts > 0 else 0
        miles_receipts_ratio = miles / receipts if receipts > 0 else 0
        
        print(f"{days:<5} {miles:<8.1f} ${receipts:<9.2f} ${expected:<9.2f} ${per_mile:<7.2f} ${per_receipt:<11.4f} {miles_receipts_ratio:<14.3f}")
    
    print("\nLooking for patterns...")
    
    # Sort by different criteria to find patterns
    print("\nSorted by expected output (lowest to highest):")
    print("-" * 70)
    sorted_by_expected = sorted(all_data, key=lambda x: x['expected_output'])
    for i, case in enumerate(sorted_by_expected):
        days = case['trip_days']
        miles = case['input']['miles_traveled']
        receipts = case['input']['total_receipts_amount']
        expected = case['expected_output']
        ratio = miles / receipts if receipts > 0 else 0
        print(f"{i+1:2}: {days}d, Miles={miles:6.1f}, Receipts=${receipts:7.2f}, Expected=${expected:7.2f}, Ratio={ratio:.3f}")
    
    # Analyze by trip duration
    print("\nAnalysis by trip duration:")
    print("-" * 50)
    by_days = {}
    for case in all_data:
        days = case['trip_days']
        if days not in by_days:
            by_days[days] = []
        by_days[days].append(case)
    
    for days in sorted(by_days.keys()):
        cases = by_days[days]
        avg_expected = sum(c['expected_output'] for c in cases) / len(cases)
        avg_miles = sum(c['input']['miles_traveled'] for c in cases) / len(cases)
        avg_receipts = sum(c['input']['total_receipts_amount'] for c in cases) / len(cases)
        print(f"{days}-day trips: {len(cases)} cases, Avg Expected=${avg_expected:.2f}, Avg Miles={avg_miles:.1f}, Avg Receipts=${avg_receipts:.2f}")
    
    # Current 4-6 day logic analysis
    print("\nCurrent 4-6 day logic performance:")
    print("-" * 60)
    
    current_errors = []
    for i, case in enumerate(all_data, 1):
        days = case['trip_days']
        miles = case['input']['miles_traveled']
        receipts = case['input']['total_receipts_amount']
        expected = case['expected_output']
        
        # Current 4-6 day logic from reimbursement.py
        daily_rate = 0
        
        if miles < 400:
            mileage_rate = 0.75
            receipt_rate = 0.90
            bonus = 175
        else:
            mileage_rate = 0.68
            receipt_rate = 0.82
            bonus = 160
        
        predicted = (days * daily_rate) + (miles * mileage_rate) + (receipts * receipt_rate) + bonus
        error = abs(predicted - expected)
        current_errors.append((i, days, miles, receipts, expected, predicted, error))
        
        print(f"Case {i:2}: {days}d, Miles={miles:6.1f}, Receipts=${receipts:7.2f}, Expected=${expected:7.2f}, Got=${predicted:7.2f}, Error=${error:7.2f}")
    
    current_avg_error = sum(x[6] for x in current_errors) / len(current_errors)
    print(f"\nCurrent average error: ${current_avg_error:.2f}")
    
    # Identify the worst over-estimations
    worst_cases = sorted(current_errors, key=lambda x: x[6], reverse=True)
    print(f"\nWorst over-estimations:")
    print("-" * 70)
    for i in range(min(5, len(worst_cases))):
        case_num, days, miles, receipts, expected, predicted, error = worst_cases[i]
        over_estimation = predicted - expected
        print(f"Case {case_num}: {days}d, Miles={miles:.1f}, Receipts=${receipts:.2f}")
        print(f"  Expected=${expected:.2f}, Got=${predicted:.2f}, Over by=${over_estimation:.2f}")
        print()
    
    # Test optimized formulas
    print("\nTesting optimized formulas:")
    print("-" * 40)
    
    best_error = float('inf')
    best_params = None
    
    # Test various coefficients - lower rates since current is over-estimating
    for base in [0, 20, 40, 60, 80, 100, 120]:
        for mile_coeff in [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7]:
            for receipt_coeff in [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7]:
                for daily_rate in [0, 10, 20, 30, 40, 50]:  # Test daily rates
                    # Test different mile thresholds for different logic
                    for mile_threshold in [300, 400, 500, 600]:
                        # Test penalties for high values
                        for mile_penalty_threshold in [600, 800, 1000]:
                            for mile_penalty in [0, 0.1, 0.2, 0.3]:
                                for receipt_penalty_threshold in [1000, 1500, 2000, 2500]:
                                    for receipt_penalty in [0, 0.1, 0.2, 0.3]:
                                        
                                        total_error = 0
                                        for case in all_data:
                                            days = case['trip_days']
                                            miles = case['input']['miles_traveled']
                                            receipts = case['input']['total_receipts_amount']
                                            expected = case['expected_output']
                                            
                                            # Base formula
                                            predicted = base + (days * daily_rate) + (miles * mile_coeff) + (receipts * receipt_coeff)
                                            
                                            # Apply logic based on mile threshold
                                            if miles < mile_threshold:
                                                predicted *= 1.1  # Small bonus for lower miles
                                            
                                            # Apply penalties for high values
                                            if miles > mile_penalty_threshold:
                                                predicted *= (1 - mile_penalty)
                                            
                                            if receipts > receipt_penalty_threshold:
                                                predicted *= (1 - receipt_penalty)
                                            
                                            error = abs(predicted - expected)
                                            total_error += error
                                        
                                        avg_error = total_error / len(all_data)
                                        
                                        if avg_error < best_error:
                                            best_error = avg_error
                                            best_params = {
                                                'base': base,
                                                'daily_rate': daily_rate,
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
    print(f"  Daily rate: {best_params['daily_rate']}")
    print(f"  Mile coefficient: {best_params['mile_coeff']}")
    print(f"  Receipt coefficient: {best_params['receipt_coeff']}")
    print(f"  Mile threshold for bonus: {best_params['mile_threshold']}")
    print(f"  Mile penalty threshold: {best_params['mile_penalty_threshold']}")
    print(f"  Mile penalty: {best_params['mile_penalty']}")
    print(f"  Receipt penalty threshold: {best_params['receipt_penalty_threshold']}")
    print(f"  Receipt penalty: {best_params['receipt_penalty']}")
    
    improvement = current_avg_error - best_error
    improvement_pct = (improvement / current_avg_error * 100) if current_avg_error > 0 else 0
    print(f"\nImprovement: ${improvement:.2f} ({improvement_pct:.1f}%)")
    
    print("\nTesting optimized formula on each case:")
    print("-" * 90)
    for i, case in enumerate(all_data, 1):
        days = case['trip_days']
        miles = case['input']['miles_traveled']
        receipts = case['input']['total_receipts_amount']
        expected = case['expected_output']
        
        # Apply optimized formula
        predicted = best_params['base'] + (days * best_params['daily_rate']) + (miles * best_params['mile_coeff']) + (receipts * best_params['receipt_coeff'])
        
        # Apply logic based on mile threshold
        if miles < best_params['mile_threshold']:
            predicted *= 1.1
        
        # Apply penalties
        if miles > best_params['mile_penalty_threshold']:
            predicted *= (1 - best_params['mile_penalty'])
        
        if receipts > best_params['receipt_penalty_threshold']:
            predicted *= (1 - best_params['receipt_penalty'])
        
        error = abs(predicted - expected)
        
        print(f"Case {i:2}: {days}d, Miles={miles:6.1f}, Receipts=${receipts:7.2f}, Expected=${expected:7.2f}, Predicted=${predicted:7.2f}, Error=${error:6.2f}")

if __name__ == "__main__":
    analyze_4_6_day_trips() 