#!/usr/bin/env python3

from reimbursement import calculate_reimbursement

# Test the worst cases from the evaluation
worst_cases = [
    (5, 516, 1878.49, 669.85),    # Case 711
    (4, 69, 2321.49, 322.00),     # Case 152  
    (1, 1166, 1423.69, 1412.13),  # Case 496
    (1, 993, 1143.58, 1328.85),   # Case 600
    (1, 1035, 1289.84, 1317.33),  # Case 890
]

print("Analysis of worst cases:")
print("=" * 60)

for days, miles, receipts, expected in worst_cases:
    actual = calculate_reimbursement(days, miles, receipts)
    error = abs(actual - expected)
    ratio = miles / receipts if receipts > 0 else 0
    
    print(f"{days}d trip: Miles={miles}, Receipts=${receipts:.2f}")
    print(f"  Expected=${expected:.2f}, Got=${actual:.2f}, Error=${error:.2f}")
    print(f"  Miles/Receipts ratio: {ratio:.3f}")
    
    if actual > expected:
        print(f"  OVER-estimated by ${actual - expected:.2f}")
    else:
        print(f"  UNDER-estimated by ${expected - actual:.2f}")
    print() 