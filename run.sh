#!/bin/bash

# This script runs the Python reimbursement calculation.
# It can accept input as three separate arguments or as a single JSON string.

# Check for correct number of arguments
if [ "$#" -ne 1 ] && [ "$#" -ne 3 ]; then
    echo "Error: Incorrect number of arguments" >&2
    echo "Usage: ./run.sh <trip_duration_days> <miles_traveled> <total_receipts_amount>" >&2
    echo "   or: ./run.sh '<json_input>'" >&2
    exit 1
fi

# Check if jq is available for parsing JSON
if ! command -v jq &> /dev/null; then
    echo "Error: jq is required but not installed." >&2
    exit 1
fi

# Handle input format
if [ "$#" -eq 1 ]; then
    # Input is a single JSON string
    json_input=$1
    trip_duration=$(echo "$json_input" | jq '.trip_duration_days')
    miles_traveled=$(echo "$json_input" | jq '.miles_traveled')
    total_receipts=$(echo "$json_input" | jq '.total_receipts_amount')
else
    # Input is three separate arguments
    trip_duration=$1
    miles_traveled=$2
    total_receipts=$3
fi

# Validate that we have all required values
if [ -z "$trip_duration" ] || [ -z "$miles_traveled" ] || [ -z "$total_receipts" ]; then
    echo "Error: Failed to parse input values." >&2
    echo "  Duration: $trip_duration" >&2
    echo "  Miles: $miles_traveled" >&2
    echo "  Receipts: $total_receipts" >&2
    exit 1
fi

# Run the python script with the extracted values
python3 -c "import reimbursement; print(reimbursement.calculate_reimbursement($trip_duration, $miles_traveled, $total_receipts))" 