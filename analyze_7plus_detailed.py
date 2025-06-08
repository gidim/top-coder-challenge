#!/usr/bin/env python3

import json

def analyze_7plus_detailed():
    # Load data for 7+ day trips
    all_data = []
    
    for days in range(7, 15):  # 7 through 14 days
        try:
            with open(f'trip_duration_datasets/trip_duration_{days}_days.json', 'r') as f:
                data = json.load(f)
                for case in data:
                    case['trip_days'] = days
                    all_data.append(case)
        except FileNotFoundError:
            print(f"No data file found for {days}-day trips")
    
    print("Detailed 7+ Day Trip Analysis:")
    print("=" * 80)
    
    # Categorize cases by error patterns from current logic
    current_errors = []
    for case in all_data:
        days = case['trip_days']
        miles = case['input']['miles_traveled']
        receipts = case['input']['total_receipts_amount']
        expected = case['expected_output']
        
        # Current 7+ day logic
        daily_rate = 50.0
        mileage_rate = 0.55
        receipt_rate = 0.65
        bonus = 50
        
        if miles > 800:
            mileage_rate *= 0.80
        if receipts > 1500:
            receipt_rate *= 0.75
            
        reimbursement = (days * daily_rate) + (miles * mileage_rate) + (receipts * receipt_rate) + bonus

        if days >= 10:
            cap = 2000
        elif days >= 7:
            cap = 1800 + (days * 25)
        else:
            cap = 1500 + (days * 100)
        
        if reimbursement > cap:
            reimbursement = cap
        
        error = abs(reimbursement - expected)
        over_under = "OVER" if reimbursement > expected else "UNDER"
        current_errors.append((case, days, miles, receipts, expected, reimbursement, error, over_under))
    
    # Sort by error to find worst cases
    worst_cases = sorted(current_errors, key=lambda x: x[6], reverse=True)[:10]
    
    print("TOP 10 WORST CASES:")
    print("-" * 80)
    for i, (case, days, miles, receipts, expected, predicted, error, over_under) in enumerate(worst_cases, 1):
        ratio = miles / receipts if receipts > 0 else 0
        print(f"{i:2}. {days}d, Miles={miles:6.1f}, Receipts=${receipts:7.2f}, Ratio={ratio:.3f}")
        print(f"    Expected=${expected:7.2f}, Got=${predicted:7.2f}, Error=${error:7.2f} ({over_under})")
        
        # Calculate what the rates would need to be for exact match
        remaining = expected - 50 - (days * 50)  # Remove bonus and daily component
        if remaining > 0:
            ideal_mile_rate = remaining / (miles + receipts) if (miles + receipts) > 0 else 0
            ideal_receipt_rate = remaining / (miles + receipts) if (miles + receipts) > 0 else 0
            print(f"    Ideal combined rate: ${ideal_mile_rate:.4f} per mile+receipt")
        print()
    
    # Analyze low expected values (might need different logic)
    low_expected = [x for x in current_errors if x[4] < 1000]  # Expected < $1000
    print(f"LOW EXPECTED CASES (< $1000): {len(low_expected)} cases")
    print("-" * 50)
    for case, days, miles, receipts, expected, predicted, error, over_under in low_expected[:5]:
        ratio = miles / receipts if receipts > 0 else 0
        print(f"{days}d, Miles={miles:6.1f}, Receipts=${receipts:7.2f}, Ratio={ratio:.3f}")
        print(f"  Expected=${expected:7.2f}, Got=${predicted:7.2f}, Error=${error:7.2f}")
    
    # Analyze high expected values
    high_expected = [x for x in current_errors if x[4] > 1800]  # Expected > $1800
    print(f"\nHIGH EXPECTED CASES (> $1800): {len(high_expected)} cases")
    print("-" * 50)
    for case, days, miles, receipts, expected, predicted, error, over_under in high_expected[:5]:
        ratio = miles / receipts if receipts > 0 else 0
        print(f"{days}d, Miles={miles:6.1f}, Receipts=${receipts:7.2f}, Ratio={ratio:.3f}")
        print(f"  Expected=${expected:7.2f}, Got=${predicted:7.2f}, Error=${error:7.2f}")
    
    # Test focused optimization for different formula structures
    print(f"\nTESTING FOCUSED OPTIMIZATIONS:")
    print("-" * 50)
    
    # Test 1: Simple linear combination without caps/bonuses
    best_error_simple = float('inf')
    best_simple = None
    
    for daily in [10, 20, 30, 40, 50, 60, 70, 80]:
        for mile_rate in [0.3, 0.4, 0.5, 0.6, 0.7, 0.8]:
            for receipt_rate in [0.3, 0.4, 0.5, 0.6, 0.7, 0.8]:
                total_error = 0
                for case, days, miles, receipts, expected, _, _, _ in current_errors:
                    predicted = (days * daily) + (miles * mile_rate) + (receipts * receipt_rate)
                    error = abs(predicted - expected)
                    total_error += error
                
                avg_error = total_error / len(current_errors)
                if avg_error < best_error_simple:
                    best_error_simple = avg_error
                    best_simple = (daily, mile_rate, receipt_rate)
    
    print(f"Best simple formula: Daily=${best_simple[0]}, Mile=${best_simple[1]:.2f}, Receipt=${best_simple[2]:.2f}")
    print(f"Average error: ${best_error_simple:.2f}")
    
    # Test 2: With penalties for extreme values
    best_error_penalty = float('inf')
    best_penalty = None
    
    daily, mile_rate, receipt_rate = best_simple
    
    for mile_threshold in [600, 800, 1000]:
        for mile_penalty in [0.1, 0.2, 0.3]:
            for receipt_threshold in [1200, 1500, 2000]:
                for receipt_penalty in [0.1, 0.2, 0.3]:
                    total_error = 0
                    for case, days, miles, receipts, expected, _, _, _ in current_errors:
                        predicted = (days * daily) + (miles * mile_rate) + (receipts * receipt_rate)
                        
                        # Apply penalties
                        if miles > mile_threshold:
                            predicted *= (1 - mile_penalty)
                        if receipts > receipt_threshold:
                            predicted *= (1 - receipt_penalty)
                        
                        error = abs(predicted - expected)
                        total_error += error
                    
                    avg_error = total_error / len(current_errors)
                    if avg_error < best_error_penalty:
                        best_error_penalty = avg_error
                        best_penalty = (daily, mile_rate, receipt_rate, mile_threshold, mile_penalty, receipt_threshold, receipt_penalty)
    
    print(f"Best penalty formula: Daily=${best_penalty[0]}, Mile=${best_penalty[1]:.2f}, Receipt=${best_penalty[2]:.2f}")
    print(f"Mile penalty: {best_penalty[4]:.1%} for miles > {best_penalty[3]}")
    print(f"Receipt penalty: {best_penalty[6]:.1%} for receipts > {best_penalty[5]}")
    print(f"Average error: ${best_error_penalty:.2f}")
    
    # Test 3: Different approach for low vs high expected values
    low_cases = [x for x in current_errors if x[4] < 1200]
    high_cases = [x for x in current_errors if x[4] >= 1200]
    
    print(f"\nSEGMENTED APPROACH:")
    print(f"Low expected cases: {len(low_cases)}")
    print(f"High expected cases: {len(high_cases)}")
    
    # Optimize for low cases
    best_low_error = float('inf')
    best_low_params = None
    
    for base in [200, 300, 400, 500]:
        for mile_rate in [0.2, 0.3, 0.4, 0.5]:
            for receipt_rate in [0.2, 0.3, 0.4, 0.5]:
                total_error = 0
                for case, days, miles, receipts, expected, _, _, _ in low_cases:
                    predicted = base + (miles * mile_rate) + (receipts * receipt_rate)
                    error = abs(predicted - expected)
                    total_error += error
                
                if len(low_cases) > 0:
                    avg_error = total_error / len(low_cases)
                    if avg_error < best_low_error:
                        best_low_error = avg_error
                        best_low_params = (base, mile_rate, receipt_rate)
    
    print(f"Best for low expected: Base=${best_low_params[0]}, Mile=${best_low_params[1]:.2f}, Receipt=${best_low_params[2]:.2f}")
    print(f"Low cases average error: ${best_low_error:.2f}")
    
    # Test the best penalty formula on some sample cases
    print(f"\nTesting best penalty formula on worst cases:")
    print("-" * 60)
    daily, mile_rate, receipt_rate, mile_threshold, mile_penalty, receipt_threshold, receipt_penalty = best_penalty
    
    for i, (case, days, miles, receipts, expected, old_predicted, old_error, over_under) in enumerate(worst_cases[:10], 1):
        # Apply best penalty formula
        predicted = (days * daily) + (miles * mile_rate) + (receipts * receipt_rate)
        
        if miles > mile_threshold:
            predicted *= (1 - mile_penalty)
        if receipts > receipt_threshold:
            predicted *= (1 - receipt_penalty)
        
        new_error = abs(predicted - expected)
        improvement = old_error - new_error
        
        print(f"{i:2}. {days}d, Miles={miles:6.1f}, Receipts=${receipts:7.2f}")
        print(f"    Expected=${expected:7.2f}, Old=${old_predicted:7.2f}, New=${predicted:7.2f}")
        print(f"    Old Error=${old_error:6.2f}, New Error=${new_error:6.2f}, Improvement=${improvement:6.2f}")

if __name__ == "__main__":
    analyze_7plus_detailed() 