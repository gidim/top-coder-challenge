#!/usr/bin/env python3

import json
import numpy as np
from scipy.optimize import minimize
from scipy.optimize import differential_evolution
import time

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

def parameterized_reimbursement(days, miles, receipts, params):
    """
    Parameterized version of our reimbursement calculation
    params is a dict containing all the parameters we want to optimize
    """
    
    if days == 1:
        return calculate_1_day_parameterized(miles, receipts, params)
    elif days == 2:
        return calculate_2_day_parameterized(miles, receipts, params)
    elif days == 3:
        return calculate_3_day_parameterized(miles, receipts, params)
    elif 4 <= days <= 6:
        return calculate_4_6_day_parameterized(days, miles, receipts, params)
    elif days >= 7:
        return calculate_7_plus_day_parameterized(days, miles, receipts, params)
    else:
        return 0.0

def calculate_1_day_parameterized(miles, receipts, params):
    """1-day trip calculation with parameters"""
    # Base rates
    mile_rate = params['day1_mile_rate']
    receipt_rate = params['day1_receipt_rate']
    
    # Base calculation
    reimbursement = (miles * mile_rate) + (receipts * receipt_rate)
    
    # High miles penalty
    if miles > params['day1_high_miles_threshold']:
        reimbursement *= params['day1_high_miles_penalty']
    
    # High receipts penalty
    if receipts > params['day1_high_receipts_threshold']:
        reimbursement *= params['day1_high_receipts_penalty']
    
    # Miles-to-receipts ratio penalty
    miles_receipts_ratio = miles / receipts if receipts > 0 else 0
    if miles_receipts_ratio > params['day1_ratio_threshold']:
        reimbursement *= params['day1_ratio_penalty']
    
    return max(0, reimbursement)

def calculate_2_day_parameterized(miles, receipts, params):
    """2-day trip calculation with parameters"""
    base = params['day2_base']
    mile_rate = params['day2_mile_rate']
    receipt_rate = params['day2_receipt_rate']
    
    reimbursement = base + (miles * mile_rate) + (receipts * receipt_rate)
    
    # Low miles bonus
    if miles < params['day2_low_miles_threshold']:
        reimbursement *= params['day2_low_miles_bonus']
    
    # High miles penalty
    if miles > params['day2_high_miles_threshold']:
        reimbursement *= params['day2_high_miles_penalty']
    
    return max(0, reimbursement)

def calculate_3_day_parameterized(miles, receipts, params):
    """3-day trip calculation with parameters"""
    base = params['day3_base']
    mile_rate = params['day3_mile_rate']
    receipt_rate = params['day3_receipt_rate']
    
    reimbursement = base + (miles * mile_rate) + (receipts * receipt_rate)
    
    # Low receipts bonus
    if receipts < params['day3_low_receipts_threshold']:
        reimbursement *= params['day3_low_receipts_bonus']
    
    # High miles penalty
    if miles > params['day3_high_miles_threshold']:
        reimbursement *= params['day3_high_miles_penalty']
    
    # High receipts penalty
    if receipts > params['day3_high_receipts_threshold']:
        reimbursement *= params['day3_high_receipts_penalty']
    
    return max(0, reimbursement)

def calculate_4_6_day_parameterized(days, miles, receipts, params):
    """4-6 day trip calculation with parameters"""
    daily_rate = params['day46_daily_rate']
    mile_rate = params['day46_mile_rate']
    receipt_rate = params['day46_receipt_rate']
    
    reimbursement = (days * daily_rate) + (miles * mile_rate) + (receipts * receipt_rate)
    
    # Low miles bonus
    if miles < params['day46_low_miles_threshold']:
        reimbursement *= params['day46_low_miles_bonus']
    
    # High miles penalty
    if miles > params['day46_high_miles_threshold']:
        reimbursement *= params['day46_high_miles_penalty']
    
    # High receipts penalty
    if receipts > params['day46_high_receipts_threshold']:
        reimbursement *= params['day46_high_receipts_penalty']
    
    return max(0, reimbursement)

def calculate_7_plus_day_parameterized(days, miles, receipts, params):
    """7+ day trip calculation with parameters"""
    daily_rate = params['day7_daily_rate']
    mile_rate = params['day7_mile_rate']
    receipt_rate = params['day7_receipt_rate']
    bonus = params['day7_bonus']
    
    # Miles-to-receipts ratio for "hustle" bonus
    miles_receipts_ratio = miles / receipts if receipts > 0 else 0
    
    # Apply hustle bonus
    if miles_receipts_ratio > params['day7_hustle_ratio_threshold']:
        mile_rate *= params['day7_hustle_mile_bonus']
        bonus += params['day7_hustle_bonus_amount']
    
    # Daily spending penalty
    daily_spending = receipts / days
    if daily_spending > params['day7_high_daily_spending_threshold']:
        receipt_rate *= params['day7_high_daily_spending_penalty']
        if days >= 8:  # Vacation penalty
            receipt_rate *= params['day7_vacation_penalty']
    
    # High values penalties
    if miles > params['day7_high_miles_threshold']:
        mile_rate *= params['day7_high_miles_penalty']
    if receipts > params['day7_high_receipts_threshold']:
        receipt_rate *= params['day7_high_receipts_penalty']
    
    reimbursement = (days * daily_rate) + (miles * mile_rate) + (receipts * receipt_rate) + bonus
    
    # Apply caps
    if days >= 10:
        cap = params['day7_cap_10plus']
    elif days >= 7:
        cap = params['day7_cap_7to9'] + (days * params['day7_cap_per_day'])
    else:
        cap = params['day7_cap_default']
    
    if reimbursement > cap:
        reimbursement = cap
    
    return max(0, reimbursement)

def get_initial_parameters():
    """Get initial parameter values (our current manually tuned values)"""
    return {
        # 1-day parameters
        'day1_mile_rate': 0.5,
        'day1_receipt_rate': 0.6,
        'day1_high_miles_threshold': 400,
        'day1_high_miles_penalty': 0.9,
        'day1_high_receipts_threshold': 1000,
        'day1_high_receipts_penalty': 0.9,
        'day1_ratio_threshold': 0.8,
        'day1_ratio_penalty': 0.4,
        
        # 2-day parameters
        'day2_base': 40,
        'day2_mile_rate': 0.8,
        'day2_receipt_rate': 0.6,
        'day2_low_miles_threshold': 75,
        'day2_low_miles_bonus': 1.1,
        'day2_high_miles_threshold': 300,
        'day2_high_miles_penalty': 0.8,
        
        # 3-day parameters
        'day3_base': 100,
        'day3_mile_rate': 0.6,
        'day3_receipt_rate': 0.8,
        'day3_low_receipts_threshold': 500,
        'day3_low_receipts_bonus': 1.1,
        'day3_high_miles_threshold': 800,
        'day3_high_miles_penalty': 0.8,
        'day3_high_receipts_threshold': 1500,
        'day3_high_receipts_penalty': 0.7,
        
        # 4-6 day parameters
        'day46_daily_rate': 50,
        'day46_mile_rate': 0.6,
        'day46_receipt_rate': 0.6,
        'day46_low_miles_threshold': 600,
        'day46_low_miles_bonus': 1.1,
        'day46_high_miles_threshold': 1000,
        'day46_high_miles_penalty': 0.9,
        'day46_high_receipts_threshold': 2000,
        'day46_high_receipts_penalty': 0.8,
        
        # 7+ day parameters
        'day7_daily_rate': 50,
        'day7_mile_rate': 0.55,
        'day7_receipt_rate': 0.65,
        'day7_bonus': 50,
        'day7_hustle_ratio_threshold': 0.8,
        'day7_hustle_mile_bonus': 1.05,
        'day7_hustle_bonus_amount': 25,
        'day7_high_daily_spending_threshold': 120,
        'day7_high_daily_spending_penalty': 0.9,
        'day7_vacation_penalty': 0.9,
        'day7_high_miles_threshold': 800,
        'day7_high_miles_penalty': 0.8,
        'day7_high_receipts_threshold': 1500,
        'day7_high_receipts_penalty': 0.75,
        'day7_cap_10plus': 2000,
        'day7_cap_7to9': 1800,
        'day7_cap_per_day': 25,
        'day7_cap_default': 1500,
    }

def get_parameter_bounds():
    """Get bounds for each parameter for optimization"""
    bounds = []
    param_names = []
    
    # 1-day bounds
    bounds.extend([
        (0.1, 2.0),   # day1_mile_rate
        (0.1, 2.0),   # day1_receipt_rate
        (100, 800),   # day1_high_miles_threshold
        (0.5, 1.0),   # day1_high_miles_penalty
        (500, 2000),  # day1_high_receipts_threshold
        (0.5, 1.0),   # day1_high_receipts_penalty
        (0.3, 1.5),   # day1_ratio_threshold
        (0.1, 0.8),   # day1_ratio_penalty
    ])
    param_names.extend(['day1_mile_rate', 'day1_receipt_rate', 'day1_high_miles_threshold',
                       'day1_high_miles_penalty', 'day1_high_receipts_threshold', 
                       'day1_high_receipts_penalty', 'day1_ratio_threshold', 'day1_ratio_penalty'])
    
    # 2-day bounds
    bounds.extend([
        (0, 100),     # day2_base
        (0.1, 1.5),   # day2_mile_rate
        (0.1, 1.5),   # day2_receipt_rate
        (25, 150),    # day2_low_miles_threshold
        (1.0, 1.3),   # day2_low_miles_bonus
        (100, 500),   # day2_high_miles_threshold
        (0.5, 1.0),   # day2_high_miles_penalty
    ])
    param_names.extend(['day2_base', 'day2_mile_rate', 'day2_receipt_rate',
                       'day2_low_miles_threshold', 'day2_low_miles_bonus',
                       'day2_high_miles_threshold', 'day2_high_miles_penalty'])
    
    # 3-day bounds
    bounds.extend([
        (0, 200),     # day3_base
        (0.1, 1.2),   # day3_mile_rate
        (0.1, 1.2),   # day3_receipt_rate
        (200, 800),   # day3_low_receipts_threshold
        (1.0, 1.3),   # day3_low_receipts_bonus
        (400, 1200),  # day3_high_miles_threshold
        (0.5, 1.0),   # day3_high_miles_penalty
        (800, 2500),  # day3_high_receipts_threshold
        (0.4, 1.0),   # day3_high_receipts_penalty
    ])
    param_names.extend(['day3_base', 'day3_mile_rate', 'day3_receipt_rate',
                       'day3_low_receipts_threshold', 'day3_low_receipts_bonus',
                       'day3_high_miles_threshold', 'day3_high_miles_penalty',
                       'day3_high_receipts_threshold', 'day3_high_receipts_penalty'])
    
    # 4-6 day bounds
    bounds.extend([
        (20, 80),     # day46_daily_rate
        (0.1, 1.0),   # day46_mile_rate
        (0.1, 1.0),   # day46_receipt_rate
        (300, 800),   # day46_low_miles_threshold
        (1.0, 1.3),   # day46_low_miles_bonus
        (600, 1500),  # day46_high_miles_threshold
        (0.5, 1.0),   # day46_high_miles_penalty
        (1000, 3000), # day46_high_receipts_threshold
        (0.4, 1.0),   # day46_high_receipts_penalty
    ])
    param_names.extend(['day46_daily_rate', 'day46_mile_rate', 'day46_receipt_rate',
                       'day46_low_miles_threshold', 'day46_low_miles_bonus',
                       'day46_high_miles_threshold', 'day46_high_miles_penalty',
                       'day46_high_receipts_threshold', 'day46_high_receipts_penalty'])
    
    # 7+ day bounds
    bounds.extend([
        (20, 80),     # day7_daily_rate
        (0.1, 1.0),   # day7_mile_rate
        (0.1, 1.0),   # day7_receipt_rate
        (0, 100),     # day7_bonus
        (0.3, 1.5),   # day7_hustle_ratio_threshold
        (1.0, 1.2),   # day7_hustle_mile_bonus
        (0, 100),     # day7_hustle_bonus_amount
        (80, 200),    # day7_high_daily_spending_threshold
        (0.5, 1.0),   # day7_high_daily_spending_penalty
        (0.5, 1.0),   # day7_vacation_penalty
        (400, 1200),  # day7_high_miles_threshold
        (0.5, 1.0),   # day7_high_miles_penalty
        (800, 2500),  # day7_high_receipts_threshold
        (0.4, 1.0),   # day7_high_receipts_penalty
        (1500, 2500), # day7_cap_10plus
        (1200, 2200), # day7_cap_7to9
        (10, 50),     # day7_cap_per_day
        (1000, 2000), # day7_cap_default
    ])
    param_names.extend(['day7_daily_rate', 'day7_mile_rate', 'day7_receipt_rate', 'day7_bonus',
                       'day7_hustle_ratio_threshold', 'day7_hustle_mile_bonus', 'day7_hustle_bonus_amount',
                       'day7_high_daily_spending_threshold', 'day7_high_daily_spending_penalty',
                       'day7_vacation_penalty', 'day7_high_miles_threshold', 'day7_high_miles_penalty',
                       'day7_high_receipts_threshold', 'day7_high_receipts_penalty',
                       'day7_cap_10plus', 'day7_cap_7to9', 'day7_cap_per_day', 'day7_cap_default'])
    
    return bounds, param_names

def objective_function(param_values, cases, param_names):
    """Objective function to minimize (average absolute error)"""
    # Convert parameter array to dictionary
    params = dict(zip(param_names, param_values))
    
    total_error = 0
    for case in cases:
        predicted = parameterized_reimbursement(case['days'], case['miles'], case['receipts'], params)
        error = abs(predicted - case['expected'])
        total_error += error
    
    avg_error = total_error / len(cases)
    return avg_error

def optimize_parameters():
    """Main optimization function"""
    print("Loading data...")
    cases = load_data()
    print(f"Loaded {len(cases)} cases")
    
    print("Setting up optimization...")
    initial_params = get_initial_parameters()
    bounds, param_names = get_parameter_bounds()
    
    # Convert initial params to array
    initial_values = [initial_params[name] for name in param_names]
    
    # Calculate baseline performance
    baseline_error = objective_function(initial_values, cases, param_names)
    print(f"Baseline average error: ${baseline_error:.2f}")
    
    print(f"Optimizing {len(param_names)} parameters...")
    print("This may take several minutes...")
    
    start_time = time.time()
    
    # Use differential evolution for global optimization
    result = differential_evolution(
        objective_function,
        bounds,
        args=(cases, param_names),
        maxiter=300,
        popsize=15,
        seed=42,
        disp=True,
        workers=1
    )
    
    end_time = time.time()
    
    print(f"\nOptimization completed in {end_time - start_time:.1f} seconds")
    print(f"Optimized average error: ${result.fun:.2f}")
    print(f"Improvement: ${baseline_error - result.fun:.2f} ({(baseline_error - result.fun) / baseline_error * 100:.1f}%)")
    
    # Create optimized parameters dictionary
    optimized_params = dict(zip(param_names, result.x))
    
    # Show significant parameter changes
    print(f"\nSignificant parameter changes:")
    print("-" * 50)
    for name in param_names:
        old_val = initial_params[name]
        new_val = optimized_params[name]
        change_pct = abs(new_val - old_val) / old_val * 100
        if change_pct > 10:  # Show changes > 10%
            print(f"{name}: {old_val:.3f} → {new_val:.3f} ({change_pct:.1f}% change)")
    
    # Test on worst cases
    print(f"\nTesting on previous worst cases:")
    print("-" * 40)
    worst_case_data = [
        (5, 516, 1878.49, 669.85, "Case 711"),
        (4, 69, 2321.49, 322.00, "Case 152"),
        (1, 1166, 1423.69, 1412.13, "Case 496"),
        (1, 993, 1143.58, 1328.85, "Case 600"),
        (1, 1035, 1289.84, 1317.33, "Case 890"),
    ]
    
    for days, miles, receipts, expected, case_id in worst_case_data:
        old_pred = parameterized_reimbursement(days, miles, receipts, initial_params)
        new_pred = parameterized_reimbursement(days, miles, receipts, optimized_params)
        old_error = abs(old_pred - expected)
        new_error = abs(new_pred - expected)
        improvement = old_error - new_error
        
        print(f"{case_id}: Expected=${expected:.2f}")
        print(f"  Old: ${old_pred:.2f} (error ${old_error:.2f})")
        print(f"  New: ${new_pred:.2f} (error ${new_error:.2f})")
        print(f"  Improvement: ${improvement:.2f}")
        print()
    
    return optimized_params, baseline_error, result.fun

if __name__ == "__main__":
    optimized_params, baseline_error, optimized_error = optimize_parameters() 