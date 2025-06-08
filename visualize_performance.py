#!/usr/bin/env python3

import json
import matplotlib.pyplot as plt
import numpy as np
from reimbursement import calculate_reimbursement
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score

def create_performance_visualization():
    # Load the public cases data
    with open('public_cases.json', 'r') as f:
        data = json.load(f)
    
    # Collect all predictions vs expected with trip duration
    predictions = []
    expected_values = []
    trip_durations = []
    errors = []
    case_info = []
    
    print("Generating predictions for all 1000 cases...")
    
    for i, case in enumerate(data):
        days = case['input']['trip_duration_days']
        miles = case['input']['miles_traveled']
        receipts = case['input']['total_receipts_amount']
        expected = case['expected_output']
        
        prediction = calculate_reimbursement(days, miles, receipts)
        error = abs(prediction - expected)
        
        predictions.append(prediction)
        expected_values.append(expected)
        trip_durations.append(days)
        errors.append(error)
        case_info.append({
            'case_id': i+1,
            'days': days,
            'miles': miles,
            'receipts': receipts,
            'expected': expected,
            'predicted': prediction,
            'error': error
        })
    
    # Convert to numpy arrays for easier manipulation
    predictions = np.array(predictions)
    expected_values = np.array(expected_values)
    trip_durations = np.array(trip_durations)
    errors = np.array(errors)
    
    # Create the visualization
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('Reimbursement System Performance Analysis', fontsize=16, fontweight='bold')
    
    # Plot 1: Prediction vs Expected with Trip Duration as Color
    scatter = ax1.scatter(expected_values, predictions, c=trip_durations, 
                         cmap='viridis', alpha=0.6, s=30)
    
    # Add perfect prediction line (diagonal)
    min_val = min(min(expected_values), min(predictions))
    max_val = max(max(expected_values), max(predictions))
    ax1.plot([min_val, max_val], [min_val, max_val], 'r--', linewidth=2, label='Perfect Prediction')
    
    # Add trend line
    reg = LinearRegression()
    reg.fit(expected_values.reshape(-1, 1), predictions)
    trend_line = reg.predict(np.array([min_val, max_val]).reshape(-1, 1))
    ax1.plot([min_val, max_val], trend_line, 'b-', linewidth=2, label='Trend Line')
    
    ax1.set_xlabel('Expected Reimbursement ($)')
    ax1.set_ylabel('Predicted Reimbursement ($)')
    ax1.set_title('Prediction vs Expected (colored by trip duration)')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Add colorbar for trip duration
    cbar = plt.colorbar(scatter, ax=ax1)
    cbar.set_label('Trip Duration (days)')
    
    # Calculate and display R² score
    r2 = r2_score(expected_values, predictions)
    ax1.text(0.05, 0.95, f'R² = {r2:.3f}', transform=ax1.transAxes, 
             bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    # Plot 2: Error distribution by trip duration
    unique_durations = np.unique(trip_durations)
    error_by_duration = [errors[trip_durations == d] for d in unique_durations]
    
    bp = ax2.boxplot(error_by_duration, labels=unique_durations, patch_artist=True)
    colors = plt.cm.viridis(np.linspace(0, 1, len(unique_durations)))
    for patch, color in zip(bp['boxes'], colors):
        patch.set_facecolor(color)
    
    ax2.set_xlabel('Trip Duration (days)')
    ax2.set_ylabel('Absolute Error ($)')
    ax2.set_title('Error Distribution by Trip Duration')
    ax2.grid(True, alpha=0.3)
    
    # Plot 3: Residuals plot (Error vs Expected)
    residuals = predictions - expected_values
    scatter2 = ax3.scatter(expected_values, residuals, c=trip_durations, 
                          cmap='viridis', alpha=0.6, s=30)
    ax3.axhline(y=0, color='r', linestyle='--', linewidth=2)
    ax3.set_xlabel('Expected Reimbursement ($)')
    ax3.set_ylabel('Residual (Predicted - Expected) ($)')
    ax3.set_title('Residuals vs Expected (colored by trip duration)')
    ax3.grid(True, alpha=0.3)
    
    # Plot 4: Error vs Trip Characteristics
    # Create a combined metric: miles + receipts
    combined_metric = []
    for case in case_info:
        combined_metric.append(case['miles'] + case['receipts'])
    
    scatter3 = ax4.scatter(combined_metric, errors, c=trip_durations, 
                          cmap='viridis', alpha=0.6, s=30)
    ax4.set_xlabel('Combined Metric (Miles + Receipts)')
    ax4.set_ylabel('Absolute Error ($)')
    ax4.set_title('Error vs Trip Complexity (colored by trip duration)')
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # Identify and highlight worst cases (top 1% errors)
    worst_threshold = np.percentile(errors, 99)
    worst_cases = [(case, err) for case, err in zip(case_info, errors) if err >= worst_threshold]
    
    print(f"\nIdentified {len(worst_cases)} worst cases (top 1% errors, threshold: ${worst_threshold:.2f})")
    print("\nWorst Cases Analysis:")
    print("=" * 80)
    
    # Highlight worst cases on the plots
    for case, error in worst_cases:
        # Mark on prediction vs expected plot
        ax1.scatter(case['expected'], case['predicted'], 
                   c='red', s=100, marker='x', linewidth=3)
        
        # Mark on residuals plot
        residual = case['predicted'] - case['expected']
        ax3.scatter(case['expected'], residual,
                   c='red', s=100, marker='x', linewidth=3)
    
    # Sort worst cases by error for reporting
    worst_cases.sort(key=lambda x: x[1], reverse=True)
    
    for i, (case, error) in enumerate(worst_cases[:10], 1):
        print(f"{i:2}. Case {case['case_id']}: {case['days']}d trip")
        print(f"    Miles: {case['miles']}, Receipts: ${case['receipts']:.2f}")
        print(f"    Expected: ${case['expected']:.2f}, Predicted: ${case['predicted']:.2f}")
        print(f"    Error: ${error:.2f}, Trip Duration: {case['days']} days")
        
        ratio = case['miles'] / case['receipts'] if case['receipts'] > 0 else 0
        daily_spending = case['receipts'] / case['days']
        print(f"    Miles/Receipts ratio: {ratio:.3f}, Daily spending: ${daily_spending:.2f}")
        print()
    
    # Performance statistics by trip duration
    print("\nPerformance by Trip Duration:")
    print("-" * 50)
    for duration in sorted(unique_durations):
        mask = trip_durations == duration
        duration_errors = errors[mask]
        duration_predictions = predictions[mask]
        duration_expected = expected_values[mask]
        
        avg_error = np.mean(duration_errors)
        median_error = np.median(duration_errors)
        max_error = np.max(duration_errors)
        count = len(duration_errors)
        r2_duration = r2_score(duration_expected, duration_predictions)
        
        print(f"{duration:2}d trips: {count:3} cases, Avg Error: ${avg_error:6.2f}, "
              f"Median: ${median_error:6.2f}, Max: ${max_error:7.2f}, R²: {r2_duration:.3f}")
    
    # Overall statistics
    avg_error = np.mean(errors)
    median_error = np.median(errors)
    std_error = np.std(errors)
    max_error = np.max(errors)
    
    print(f"\nOverall Performance:")
    print(f"Average Error: ${avg_error:.2f}")
    print(f"Median Error: ${median_error:.2f}")
    print(f"Std Dev Error: ${std_error:.2f}")
    print(f"Maximum Error: ${max_error:.2f}")
    print(f"R² Score: {r2:.3f}")
    
    # Save the plot
    plt.savefig('performance_analysis.png', dpi=300, bbox_inches='tight')
    print(f"\nVisualization saved as 'performance_analysis.png'")
    
    # Show the plot
    plt.show()
    
    return case_info, worst_cases

if __name__ == "__main__":
    case_info, worst_cases = create_performance_visualization() 