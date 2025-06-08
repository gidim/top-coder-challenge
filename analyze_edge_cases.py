#!/usr/bin/env python3

from reimbursement import calculate_reimbursement
import json

def analyze_edge_cases():
    print("Edge Case Analysis - Current Worst Performers")
    print("=" * 60)
    
    # Current worst cases from evaluation
    worst_cases = [
        (5, 516, 1878.49, 669.85, "Case 711"),    # 5-day, medium miles, very high receipts
        (4, 69, 2321.49, 322.00, "Case 152"),     # 4-day, very low miles, very high receipts
        (1, 1166, 1423.69, 1412.13, "Case 496"),  # 1-day, very high miles, high receipts
        (1, 993, 1143.58, 1328.85, "Case 600"),   # 1-day, high miles, high receipts
        (1, 1035, 1289.84, 1317.33, "Case 890"),  # 1-day, high miles, high receipts
    ]
    
    print("Detailed Analysis:")
    print("-" * 60)
    
    for days, miles, receipts, expected, case_id in worst_cases:
        actual = calculate_reimbursement(days, miles, receipts)
        error = abs(actual - expected)
        ratio = miles / receipts if receipts > 0 else 0
        daily_spending = receipts / days
        
        print(f"{case_id}: {days}d trip")
        print(f"  Miles: {miles}, Receipts: ${receipts:.2f}")
        print(f"  Expected: ${expected:.2f}, Got: ${actual:.2f}, Error: ${error:.2f}")
        print(f"  Miles/Receipts ratio: {ratio:.3f}")
        print(f"  Daily spending: ${daily_spending:.2f}")
        
        if actual > expected:
            print(f"  OVER-estimated by ${actual - expected:.2f}")
        else:
            print(f"  UNDER-estimated by ${expected - actual:.2f}")
        print()
    
    # Pattern analysis
    print("PATTERN ANALYSIS:")
    print("-" * 40)
    
    # Group by problem type
    over_estimated = [(days, miles, receipts, expected, case_id) for days, miles, receipts, expected, case_id in worst_cases 
                      if calculate_reimbursement(days, miles, receipts) > expected]
    under_estimated = [(days, miles, receipts, expected, case_id) for days, miles, receipts, expected, case_id in worst_cases 
                       if calculate_reimbursement(days, miles, receipts) <= expected]
    
    print(f"OVER-estimated cases: {len(over_estimated)}")
    for days, miles, receipts, expected, case_id in over_estimated:
        ratio = miles / receipts if receipts > 0 else 0
        daily_spending = receipts / days
        print(f"  {case_id}: {days}d, ratio={ratio:.3f}, daily=${daily_spending:.2f}")
    
    print(f"\nUNDER-estimated cases: {len(under_estimated)}")
    for days, miles, receipts, expected, case_id in under_estimated:
        ratio = miles / receipts if receipts > 0 else 0
        daily_spending = receipts / days
        print(f"  {case_id}: {days}d, ratio={ratio:.3f}, daily=${daily_spending:.2f}")
    
    # Identify specific patterns
    print(f"\nSPECIFIC PATTERNS:")
    print("-" * 30)
    
    # Pattern 1: Very high daily spending + low miles = over-estimation
    high_daily_low_miles = [case for case in worst_cases 
                           if case[2]/case[0] > 300 and case[1] < 200]  # >$300/day, <200 miles
    print(f"High daily spending + low miles: {len(high_daily_low_miles)} cases")
    for case in high_daily_low_miles:
        print(f"  {case[4]}: {case[0]}d, ${case[2]/case[0]:.0f}/day, {case[1]} miles")
    
    # Pattern 2: High miles + high receipts but low expected = under-estimation
    high_both_low_expected = [case for case in worst_cases 
                             if case[1] > 900 and case[2] > 1000 and case[3] > 1200]
    print(f"\nHigh miles + high receipts + high expected: {len(high_both_low_expected)} cases")
    for case in high_both_low_expected:
        print(f"  {case[4]}: {case[1]} miles, ${case[2]:.0f} receipts, expected ${case[3]:.0f}")
    
    # Test potential fixes
    print(f"\nPOTENTIAL TARGETED FIXES:")
    print("-" * 35)
    
    print("1. For OVER-estimated cases (high receipts, low miles):")
    print("   - These are getting 'vacation penalty' treatment already")
    print("   - Could increase penalties for daily spending > $350/day")
    
    print("\n2. For UNDER-estimated cases (high miles + high receipts + high expected):")
    print("   - These are special cases where both miles AND receipts should be rewarded")
    print("   - Current logic penalizes high miles-to-receipts ratio")
    print("   - Need exception for cases where BOTH are high AND expected is high")
    
    # Test a potential fix for under-estimated cases
    print(f"\nTESTING POTENTIAL FIX for under-estimated 1-day cases:")
    print("-" * 60)
    
    for days, miles, receipts, expected, case_id in under_estimated:
        if days == 1:  # Focus on 1-day cases
            # Current logic
            current = calculate_reimbursement(days, miles, receipts)
            
            # Test potential fix: Special case for high miles + high receipts + high expected
            if miles > 900 and receipts > 1000 and expected > 1200:
                # Use higher rates for these special cases
                test_result = round((miles * 0.62) + (receipts * 0.68), 2)
                improvement = abs(test_result - expected) - abs(current - expected)
                print(f"  {case_id}: Current=${current:.2f}, Test=${test_result:.2f}, Expected=${expected:.2f}")
                print(f"    Current error: ${abs(current - expected):.2f}")
                print(f"    Test error: ${abs(test_result - expected):.2f}")
                print(f"    Improvement: ${improvement:.2f}")
                print()

if __name__ == "__main__":
    analyze_edge_cases() 