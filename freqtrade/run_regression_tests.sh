#!/bin/bash

# Regression Test Script for Freqtrade (Linux)
# Goal: Verify that CombinedStrategy performance has not degraded below baseline.

BASELINE_PROFIT="-0.04"  # Improved from -6.0% to ~ -3.0%
BASELINE_DRAWDOWN="0.04" # Improved from 8.5% to ~ 3.0%
STRATEGY="CombinedStrategy"
TIMERANGE="20251120-"
CONFIG="user_data/config_backtest.json"

echo "----------------------------------------------------------------"
echo "Running Regression Test for $STRATEGY"
echo "Baseline Profit Floor: $(echo "$BASELINE_PROFIT * 100" | bc -l)%"
echo "Baseline Max Drawdown: $(echo "$BASELINE_DRAWDOWN * 100" | bc -l)%"
echo "----------------------------------------------------------------"

# 1. Run Backtest
echo "Executing Freqtrade Backtest..."
podman-compose run --rm freqtrade backtesting --config $CONFIG --strategy $STRATEGY --timerange $TIMERANGE

# 2. Find the latest backtest result
# Assuming user_data is mapped to the standard location in the compose file
LATEST_ZIP=$(ls -t user_data/backtest_results/backtest-result-*.zip 2>/dev/null | grep -v ".meta.json" | head -n 1)

if [ -z "$LATEST_ZIP" ]; then
    echo "ERROR: Regression test failed: No backtest result file found in 'user_data/backtest_results/'." >&2
    exit 1
fi

echo "Found latest result: $LATEST_ZIP"

# 3. Parse JSON Results from Zip
TEMP_DIR=$(mktemp -d)

# Extract
unzip -q -o "$LATEST_ZIP" -d "$TEMP_DIR"

# Find JSON file inside
JSON_FILE=$(ls "$TEMP_DIR"/*.json | grep -v "_config.json" | grep -v "\.meta\.json" | head -n 1)

if [ -z "$JSON_FILE" ]; then
    echo "ERROR: No JSON string found in zip archive" >&2
    rm -r "$TEMP_DIR"
    exit 1
fi

echo "Parsing JSON: $(basename "$JSON_FILE")"

# Use jq to parse total_profit and max_drawdown
ACTUAL_PROFIT=$(jq -r ".strategy.$STRATEGY.profit_total" "$JSON_FILE")
ACTUAL_DRAWDOWN=$(jq -r ".strategy.$STRATEGY.max_drawdown_account" "$JSON_FILE")

# Cleanup
rm -r "$TEMP_DIR"

if [ "$ACTUAL_PROFIT" == "null" ] || [ -z "$ACTUAL_PROFIT" ]; then
    echo "ERROR: Could not find metrics for $STRATEGY in JSON output." >&2
    exit 1
fi

echo -e "\nRESULTS:"
echo "Actual Profit:     $(echo "$ACTUAL_PROFIT * 100" | bc -l)%"
echo "Actual Drawdown:   $(echo "$ACTUAL_DRAWDOWN * 100" | bc -l)%"

# 4. Compare (using bc for floating point comparison)
FAILED=0

# if actual_profit < baseline_profit
if [ $(echo "$ACTUAL_PROFIT < $BASELINE_PROFIT" | bc -l) -eq 1 ]; then
    echo -e "\e[31mFAILED: Profit ($(echo "$ACTUAL_PROFIT * 100" | bc -l)%) is below baseline ($(echo "$BASELINE_PROFIT * 100" | bc -l)%)\e[0m"
    FAILED=1
else
    echo -e "\e[32mPASS: Profit is within acceptable range.\e[0m"
fi

# if actual_drawdown > baseline_drawdown
if [ $(echo "$ACTUAL_DRAWDOWN > $BASELINE_DRAWDOWN" | bc -l) -eq 1 ]; then
    echo -e "\e[31mFAILED: Drawdown ($(echo "$ACTUAL_DRAWDOWN * 100" | bc -l)%) is higher than baseline ($(echo "$BASELINE_DRAWDOWN * 100" | bc -l)%)\e[0m"
    FAILED=1
else
    echo -e "\e[32mPASS: Drawdown is within acceptable range.\e[0m"
fi

if [ $FAILED -eq 1 ]; then
    echo -e "\n\e[31mREGRESSION DETECTED!\e[0m"
    exit 1
else
    echo -e "\n\e[32mRegression Test Passed Successfully.\e[0m"
    exit 0
fi
