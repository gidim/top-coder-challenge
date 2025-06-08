#!/usr/bin/env python3

import json
from reimbursement import calculate_reimbursement

def load_data():
    """Load the public cases data"""
    with open('public_cases.json', 'r') as f:
        data = json.load(f)
    
    cases = []
    for case in data:
        cases.append({
            'days': case['input']['trip_duration_days'],
            'miles': case['input']['miles_traveled'],
            'receipts': case['input']['total_receipts_amount'],
            'expected': case['expected_output']
        })
    return cases

def test_accuracy():
    """Test the accuracy of our current implementation"""
    cases = load_data()
    
    total_error = 0
    exact_matches = 0
    close_matches = 0
    worst_cases = []
    
    for i, case in enumerate(cases):
        predicted = calculate_reimbursement(case['days'], case['miles'], case['receipts'])
        error = abs(predicted - case['expected'])
        total_error += error
        
        if error < 0.01:
            exact_matches += 1
        elif error < 1.0:
            close_matches += 1
            
        # Track worst cases
        worst_cases.append((i+1, case['days'], case['miles'], case['receipts'], 
                           case['expected'], predicted, error))
    
    # Sort by error (descending)
    worst_cases.sort(key=lambda x: x[6], reverse=True)
    
    avg_error = total_error / len(cases)
    score = avg_error * 100 + (len(cases) - exact_matches) * 0.1
    
    print(f"Current Implementation Results:")
    print(f"Total cases: {len(cases)}")
    print(f"Average error: ${avg_error:.2f}")
    print(f"Exact matches: {exact_matches}")
    print(f"Close matches: {close_matches}")
    print(f"Score: {score:.2f}")
    print()
    
    print("Top 10 worst cases:")
    print("-" * 100)
    print(f"{'Case':<5} {'Days':<4} {'Miles':<5} {'Receipts':<10} {'Expected':<10} {'Predicted':<10} {'Error':<8}")
    print("-" * 100)
    
    for case_data in worst_cases[:10]:
        case_num, days, miles, receipts, expected, predicted, error = case_data
        print(f"{case_num:<5} {days:<4} {miles:<5} ${receipts:<9.2f} ${expected:<9.2f} ${predicted:<9.2f} ${error:<7.2f}")

if __name__ == "__main__":
    test_accuracy() 