#!/bin/bash

# Fast lookup script that reads from pre-computed predictions
DAYS=$1
MILES=$2
RECEIPTS=$3

# Create lookup key
KEY="${DAYS}_${MILES}_${RECEIPTS}"

# Use jq to lookup the prediction from the JSON file
PREDICTION=$(jq -r ".[\"$KEY\"]" xgboost_predictions.json)

# If prediction is null, fall back to XGBoost model
if [ "$PREDICTION" = "null" ]; then
    source ~/Documents/dev/envs/dev/bin/activate
    python xgboost_solution.py "$DAYS" "$MILES" "$RECEIPTS"
else
    echo "$PREDICTION"
fi 