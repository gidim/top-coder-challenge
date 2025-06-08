#!/usr/bin/env python3

import json

def analyze_1day_trips():
    with open('trip_duration_datasets/trip_duration_1_days.json', 'r') as f:
        data = json.load(f)
    
    print("1-Day Trip Analysis:")
    print("=" * 70)
    print(f"{'Miles':<8} {'Receipts':<10} {'Expected':<10} {'$/Mile':<8} {'$/Receipt':<12}")
    print("-" * 70)
    
    for case in data:
        miles = case['input']['miles_traveled']
        receipts = case['input']['total_receipts_amount']
        expected = case['expected_output']
        
        # Calculate per-mile and per-receipt rates
        per_mile = expected / miles if miles > 0 else 0
        per_receipt = expected / receipts if receipts > 0 else 0
        
        print(f"{miles:<8.1f} ${receipts:<9.2f} ${expected:<9.2f} ${per_mile:<7.2f} ${per_receipt:<11.4f}")
    
    print("\nLooking for patterns...")
    
    # Analyze cases with very low reimbursement per mile
    print("\nCases with unusually low $/mile (potential penalties):")
    for case in data:
        miles = case['input']['miles_traveled']
        receipts = case['input']['total_receipts_amount']
        expected = case['expected_output']
        per_mile = expected / miles if miles > 0 else 0
        
        if per_mile < 1.0:  # Less than $1 per mile
            print(f"  Miles: {miles}, Receipts: ${receipts:.2f}, Expected: ${expected:.2f}, $/Mile: ${per_mile:.2f}")
    
    print("\nTesting more sophisticated formulas...")
    
    best_error = float('inf')
    best_params = None
    
    # Test formulas with different receipt/mile ratio considerations
    for base in range(0, 101, 25):
        for mile_coeff in [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2]:
            for receipt_coeff in [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]:
                # Test penalties for high miles or high receipts
                for mile_penalty_threshold in [400, 500, 600, 1000]:
                    for mile_penalty in [0, 0.1, 0.2, 0.3, 0.4, 0.5]:
                        for receipt_penalty_threshold in [1000, 1500, 2000]:
                            for receipt_penalty in [0, 0.1, 0.2, 0.3, 0.4, 0.5]:
                                
                                total_error = 0
                                for case in data:
                                    miles = case['input']['miles_traveled']
                                    receipts = case['input']['total_receipts_amount']
                                    expected = case['expected_output']
                                    
                                    # Base formula
                                    predicted = base + (miles * mile_coeff) + (receipts * receipt_coeff)
                                    
                                    # Apply penalties
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
                                        'mile_penalty_threshold': mile_penalty_threshold,
                                        'mile_penalty': mile_penalty,
                                        'receipt_penalty_threshold': receipt_penalty_threshold,
                                        'receipt_penalty': receipt_penalty,
                                    }
    
    print(f"\nBest formula found (Avg Error: ${best_error:.2f}):")
    print(f"  Base: {best_params['base']}")
    print(f"  Mile coefficient: {best_params['mile_coeff']}")
    print(f"  Receipt coefficient: {best_params['receipt_coeff']}")
    print(f"  Mile penalty threshold: {best_params['mile_penalty_threshold']}")
    print(f"  Mile penalty: {best_params['mile_penalty']}")
    print(f"  Receipt penalty threshold: {best_params['receipt_penalty_threshold']}")
    print(f"  Receipt penalty: {best_params['receipt_penalty']}")
    
    print("\nTesting best formula on each case:")
    print("-" * 70)
    for i, case in enumerate(data, 1):
        miles = case['input']['miles_traveled']
        receipts = case['input']['total_receipts_amount']
        expected = case['expected_output']
        
        # Apply best formula
        predicted = best_params['base'] + (miles * best_params['mile_coeff']) + (receipts * best_params['receipt_coeff'])
        
        # Apply penalties
        if miles > best_params['mile_penalty_threshold']:
            predicted *= (1 - best_params['mile_penalty'])
        
        if receipts > best_params['receipt_penalty_threshold']:
            predicted *= (1 - best_params['receipt_penalty'])
        
        error = abs(predicted - expected)
        
        print(f"Case {i:2}: Miles={miles:6.1f}, Receipts=${receipts:7.2f}, Expected=${expected:7.2f}, Predicted=${predicted:7.2f}, Error=${error:6.2f}")

if __name__ == "__main__":
    analyze_1day_trips() 