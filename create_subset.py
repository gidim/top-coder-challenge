#!/usr/bin/env python3

import json
import random
import os

def create_subset_dataset():
    # Configuration
    SAMPLES_PER_DURATION = 10  # Make this variable to easily change sample size
    OUTPUT_FOLDER = 'trip_duration_datasets'
    
    # Create output folder if it doesn't exist
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    
    # Read the original public_cases.json
    with open('public_cases.json', 'r') as f:
        data = json.load(f)

    # Group cases by trip duration
    by_duration = {}
    for case in data:
        duration = case['input']['trip_duration_days']
        if duration not in by_duration:
            by_duration[duration] = []
        by_duration[duration].append(case)

    print(f'Original dataset distribution:')
    for duration in sorted(by_duration.keys()):
        print(f'  {duration} days: {len(by_duration[duration])} cases')

    # Create separate files for each trip duration
    total_cases = 0
    for duration in sorted(by_duration.keys()):
        cases = by_duration[duration]
        if len(cases) >= SAMPLES_PER_DURATION:
            # Randomly sample the specified number of cases
            subset_cases = random.sample(cases, SAMPLES_PER_DURATION)
        else:
            # If we have fewer than the target, take all of them
            subset_cases = cases
        
        # Save to individual file
        filename = f'trip_duration_{duration}_days.json'
        filepath = os.path.join(OUTPUT_FOLDER, filename)
        with open(filepath, 'w') as f:
            json.dump(subset_cases, f, indent=2)
        
        print(f'Created {filename}: {len(subset_cases)} cases')
        total_cases += len(subset_cases)

    print(f'\nTotal files created: {len(by_duration)}')
    print(f'Total cases across all files: {total_cases}')
    print(f'All datasets saved to: {OUTPUT_FOLDER}/')

if __name__ == "__main__":
    create_subset_dataset() 