#!/bin/bash

# Generate Reporting Script
# Goal: Create HTML plots for the results

STRATEGY="CombinedStrategy"
CONFIG="user_data/config_backtest.json"
TIMERANGE="20251120-"

echo "Generating HTML Report for $STRATEGY..."

# 1. Plot Dataframe
# Plotting requires 'plotly' which is not in the standard image.
# We chain the install and plot command in one container session.

PLOT_CMD="pip install plotly && freqtrade plot-dataframe --config $CONFIG --strategy $STRATEGY --timerange $TIMERANGE"

podman-compose run --rm --entrypoint /bin/sh freqtrade -c "$PLOT_CMD"

echo "Report generation complete."
echo "Check 'user_data/plot/' for the HTML files."
