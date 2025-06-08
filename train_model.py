import json
import numpy as np
from scipy.optimize import minimize
from typing import List, Dict, Tuple

def load_training_data(filename: str) -> Tuple[List[Dict], List[float]]:
    with open(filename, 'r') as f:
        data = json.load(f)
    
    X = []  # Input features
    y = []  # Expected outputs
    
    for case in data:
        X.append({
            'trip_duration_days': case['input']['trip_duration_days'],
            'miles_traveled': case['input']['miles_traveled'],
            'total_receipts_amount': case['input']['total_receipts_amount']
        })
        y.append(case['expected_output'])
    
    return X, y

def calculate_reimbursement(params: np.ndarray, case: Dict) -> float:
    # Unpack parameters
    [
        base_per_diem_short,    # 0: Base per diem for trips <= 3 days
        base_per_diem_medium,   # 1: Base per diem for trips 4-7 days
        base_per_diem_long,     # 2: Base per diem for trips > 7 days
        five_day_bonus,         # 3: Bonus multiplier for 5-day trips
        
        mileage_rate_1,        # 4: Rate for first 100 miles
        mileage_rate_2,        # 5: Rate for miles 101-300
        mileage_rate_3,        # 6: Rate for miles 301-600
        mileage_rate_4,        # 7: Rate for miles > 600
        
        receipt_rate_1,        # 8: Rate for first $100
        receipt_rate_2,        # 9: Rate for $101-500
        receipt_rate_3,        # 10: Rate for $501-1000
        receipt_rate_4,        # 11: Rate for > $1000
        
        efficiency_bonus_short, # 12: Bonus for high miles/day on short trips
        efficiency_bonus_long,  # 13: Bonus for high miles/day on long trips
        
        duration_factor,       # 14: Receipt bonus factor per day
        
        high_mileage_penalty,  # 15: Penalty for high mileage
        high_receipt_penalty,  # 16: Penalty for high receipts
        
        cap_base,             # 17: Base cap amount
        cap_per_day,          # 18: Additional cap per day
        cap_reduction         # 19: Cap reduction for high values
    ] = params
    
    trip_duration_days = case['trip_duration_days']
    miles_traveled = case['miles_traveled']
    total_receipts_amount = case['total_receipts_amount']
    
    # Calculate per diem
    if trip_duration_days <= 3:
        base_per_diem = base_per_diem_short
    elif trip_duration_days <= 7:
        base_per_diem = base_per_diem_medium
    else:
        base_per_diem = base_per_diem_long
    
    per_diem = base_per_diem * trip_duration_days
    
    # 5-day bonus
    if trip_duration_days == 5:
        per_diem *= (1.0 + five_day_bonus)
    
    # Calculate mileage reimbursement
    mileage_reimbursement = 0.0
    miles_remaining = miles_traveled
    
    if miles_remaining > 0:
        miles_tier_1 = min(miles_remaining, 100)
        mileage_reimbursement += miles_tier_1 * mileage_rate_1
        miles_remaining -= miles_tier_1
    
    if miles_remaining > 0:
        miles_tier_2 = min(miles_remaining, 200)
        mileage_reimbursement += miles_tier_2 * mileage_rate_2
        miles_remaining -= miles_tier_2
    
    if miles_remaining > 0:
        miles_tier_3 = min(miles_remaining, 300)
        mileage_reimbursement += miles_tier_3 * mileage_rate_3
        miles_remaining -= miles_tier_3
    
    if miles_remaining > 0:
        mileage_reimbursement += miles_remaining * mileage_rate_4
    
    # Efficiency bonus
    miles_per_day = miles_traveled / trip_duration_days
    if trip_duration_days <= 3 and miles_per_day > 200:
        mileage_reimbursement *= (1.0 + efficiency_bonus_short)
    elif trip_duration_days > 3 and miles_per_day > 150:
        mileage_reimbursement *= (1.0 + efficiency_bonus_long)
    
    # Calculate receipt reimbursement
    receipt_reimbursement = 0.0
    receipts_remaining = total_receipts_amount
    
    if receipts_remaining > 0:
        receipts_tier_1 = min(receipts_remaining, 100)
        receipt_reimbursement += receipts_tier_1 * receipt_rate_1
        receipts_remaining -= receipts_tier_1
    
    if receipts_remaining > 0:
        receipts_tier_2 = min(receipts_remaining, 400)
        receipt_reimbursement += receipts_tier_2 * receipt_rate_2
        receipts_remaining -= receipts_tier_2
    
    if receipts_remaining > 0:
        receipts_tier_3 = min(receipts_remaining, 500)
        receipt_reimbursement += receipts_tier_3 * receipt_rate_3
        receipts_remaining -= receipts_tier_3
    
    if receipts_remaining > 0:
        receipt_reimbursement += receipts_remaining * receipt_rate_4
    
    # Duration factor for receipts
    if trip_duration_days > 3:
        receipt_reimbursement *= (1.0 + (trip_duration_days * duration_factor))
    
    # Penalties for high values
    if miles_traveled > 800:
        mileage_reimbursement *= (1.0 - high_mileage_penalty)
    if total_receipts_amount > 1500:
        receipt_reimbursement *= (1.0 - high_receipt_penalty)
    
    # Calculate total
    total = per_diem + mileage_reimbursement + receipt_reimbursement
    
    # Apply caps
    max_reimbursement = cap_base + (trip_duration_days * cap_per_day)
    if miles_traveled > 800 or total_receipts_amount > 1500:
        max_reimbursement *= (1.0 - cap_reduction)
    
    total = min(total, max_reimbursement)
    
    # Round to 2 decimal places
    return round(total, 2)

def loss_function(params: np.ndarray, cases: List[Dict], targets: List[float]) -> float:
    total_loss = 0.0
    for case, target in zip(cases, targets):
        predicted = calculate_reimbursement(params, case)
        error = abs(predicted - target)
        total_loss += error
    return total_loss / len(cases)

def main():
    # Load training data
    print("Loading training data...")
    X_train, y_train = load_training_data('public_cases.json')
    
    # Initial parameter guesses
    initial_params = np.array([
        90.0,   # base_per_diem_short
        80.0,   # base_per_diem_medium
        70.0,   # base_per_diem_long
        0.05,   # five_day_bonus
        
        0.55,   # mileage_rate_1
        0.45,   # mileage_rate_2
        0.35,   # mileage_rate_3
        0.25,   # mileage_rate_4
        
        0.7,    # receipt_rate_1
        0.6,    # receipt_rate_2
        0.4,    # receipt_rate_3
        0.2,    # receipt_rate_4
        
        0.1,    # efficiency_bonus_short
        0.05,   # efficiency_bonus_long
        
        0.02,   # duration_factor
        
        0.2,    # high_mileage_penalty
        0.2,    # high_receipt_penalty
        
        1000.0, # cap_base
        100.0,  # cap_per_day
        0.2     # cap_reduction
    ])
    
    # Parameter bounds
    bounds = [
        (50.0, 150.0),  # base_per_diem_short
        (50.0, 150.0),  # base_per_diem_medium
        (50.0, 150.0),  # base_per_diem_long
        (0.0, 0.2),     # five_day_bonus
        
        (0.3, 0.8),     # mileage_rate_1
        (0.2, 0.7),     # mileage_rate_2
        (0.1, 0.6),     # mileage_rate_3
        (0.1, 0.5),     # mileage_rate_4
        
        (0.4, 1.0),     # receipt_rate_1
        (0.3, 0.9),     # receipt_rate_2
        (0.2, 0.8),     # receipt_rate_3
        (0.1, 0.7),     # receipt_rate_4
        
        (0.0, 0.3),     # efficiency_bonus_short
        (0.0, 0.2),     # efficiency_bonus_long
        
        (0.0, 0.1),     # duration_factor
        
        (0.0, 0.5),     # high_mileage_penalty
        (0.0, 0.5),     # high_receipt_penalty
        
        (500.0, 2000.0),  # cap_base
        (50.0, 200.0),    # cap_per_day
        (0.0, 0.5)        # cap_reduction
    ]
    
    print("Starting optimization...")
    result = minimize(
        loss_function,
        initial_params,
        args=(X_train, y_train),
        method='L-BFGS-B',
        bounds=bounds,
        options={'maxiter': 1000}
    )
    
    print("\nOptimization complete!")
    print(f"Final average error: ${result.fun:.2f}")
    
    # Generate the optimized reimbursement.py
    optimized_params = result.x
    with open('reimbursement.py', 'w') as f:
        f.write(f"""def calculate_reimbursement(trip_duration_days: int, miles_traveled: int, total_receipts_amount: float) -> float:
    # Optimized parameters
    BASE_PER_DIEM_SHORT = {optimized_params[0]:.4f}
    BASE_PER_DIEM_MEDIUM = {optimized_params[1]:.4f}
    BASE_PER_DIEM_LONG = {optimized_params[2]:.4f}
    FIVE_DAY_BONUS = {optimized_params[3]:.4f}
    
    MILEAGE_RATE_1 = {optimized_params[4]:.4f}
    MILEAGE_RATE_2 = {optimized_params[5]:.4f}
    MILEAGE_RATE_3 = {optimized_params[6]:.4f}
    MILEAGE_RATE_4 = {optimized_params[7]:.4f}
    
    RECEIPT_RATE_1 = {optimized_params[8]:.4f}
    RECEIPT_RATE_2 = {optimized_params[9]:.4f}
    RECEIPT_RATE_3 = {optimized_params[10]:.4f}
    RECEIPT_RATE_4 = {optimized_params[11]:.4f}
    
    EFFICIENCY_BONUS_SHORT = {optimized_params[12]:.4f}
    EFFICIENCY_BONUS_LONG = {optimized_params[13]:.4f}
    
    DURATION_FACTOR = {optimized_params[14]:.4f}
    
    HIGH_MILEAGE_PENALTY = {optimized_params[15]:.4f}
    HIGH_RECEIPT_PENALTY = {optimized_params[16]:.4f}
    
    CAP_BASE = {optimized_params[17]:.4f}
    CAP_PER_DAY = {optimized_params[18]:.4f}
    CAP_REDUCTION = {optimized_params[19]:.4f}
    
    # Calculate per diem
    if trip_duration_days <= 3:
        base_per_diem = BASE_PER_DIEM_SHORT
    elif trip_duration_days <= 7:
        base_per_diem = BASE_PER_DIEM_MEDIUM
    else:
        base_per_diem = BASE_PER_DIEM_LONG
    
    per_diem = base_per_diem * trip_duration_days
    
    # 5-day bonus
    if trip_duration_days == 5:
        per_diem *= (1.0 + FIVE_DAY_BONUS)
    
    # Calculate mileage reimbursement
    mileage_reimbursement = 0.0
    miles_remaining = miles_traveled
    
    if miles_remaining > 0:
        miles_tier_1 = min(miles_remaining, 100)
        mileage_reimbursement += miles_tier_1 * MILEAGE_RATE_1
        miles_remaining -= miles_tier_1
    
    if miles_remaining > 0:
        miles_tier_2 = min(miles_remaining, 200)
        mileage_reimbursement += miles_tier_2 * MILEAGE_RATE_2
        miles_remaining -= miles_tier_2
    
    if miles_remaining > 0:
        miles_tier_3 = min(miles_remaining, 300)
        mileage_reimbursement += miles_tier_3 * MILEAGE_RATE_3
        miles_remaining -= miles_tier_3
    
    if miles_remaining > 0:
        mileage_reimbursement += miles_remaining * MILEAGE_RATE_4
    
    # Efficiency bonus
    miles_per_day = miles_traveled / trip_duration_days
    if trip_duration_days <= 3 and miles_per_day > 200:
        mileage_reimbursement *= (1.0 + EFFICIENCY_BONUS_SHORT)
    elif trip_duration_days > 3 and miles_per_day > 150:
        mileage_reimbursement *= (1.0 + EFFICIENCY_BONUS_LONG)
    
    # Calculate receipt reimbursement
    receipt_reimbursement = 0.0
    receipts_remaining = total_receipts_amount
    
    if receipts_remaining > 0:
        receipts_tier_1 = min(receipts_remaining, 100)
        receipt_reimbursement += receipts_tier_1 * RECEIPT_RATE_1
        receipts_remaining -= receipts_tier_1
    
    if receipts_remaining > 0:
        receipts_tier_2 = min(receipts_remaining, 400)
        receipt_reimbursement += receipts_tier_2 * RECEIPT_RATE_2
        receipts_remaining -= receipts_tier_2
    
    if receipts_remaining > 0:
        receipts_tier_3 = min(receipts_remaining, 500)
        receipt_reimbursement += receipts_tier_3 * RECEIPT_RATE_3
        receipts_remaining -= receipts_tier_3
    
    if receipts_remaining > 0:
        receipt_reimbursement += receipts_remaining * RECEIPT_RATE_4
    
    # Duration factor for receipts
    if trip_duration_days > 3:
        receipt_reimbursement *= (1.0 + (trip_duration_days * DURATION_FACTOR))
    
    # Penalties for high values
    if miles_traveled > 800:
        mileage_reimbursement *= (1.0 - HIGH_MILEAGE_PENALTY)
    if total_receipts_amount > 1500:
        receipt_reimbursement *= (1.0 - HIGH_RECEIPT_PENALTY)
    
    # Calculate total
    total = per_diem + mileage_reimbursement + receipt_reimbursement
    
    # Apply caps
    max_reimbursement = CAP_BASE + (trip_duration_days * CAP_PER_DAY)
    if miles_traveled > 800 or total_receipts_amount > 1500:
        max_reimbursement *= (1.0 - CAP_REDUCTION)
    
    total = min(total, max_reimbursement)
    
    # Round to 2 decimal places
    return round(total, 2)
""")
    
    print("\nGenerated optimized reimbursement.py")
    print("Run eval.sh to test the optimized implementation")

if __name__ == "__main__":
    main() 