#!/bin/bash

# SYNOPSIS
# Runs a comparative backtest for multiple Freqtrade strategies.
#
# DESCRIPTION
# This script uses Podman to run Freqtrade backtesting on a list of strategies
# and outputs a comparative performance report.

STRATEGIES="SimpleStrategy RSIStrategy CombinedStrategy TrailingStrategy SniperStrategy"
TIMERANGE="20251120-"
TIMEFRAME="5m"
CONFIG="user_data/config_backtest.json"

echo -e "\e[36mStarting Comparative Backtest for: $STRATEGIES\e[0m"
echo "Timeframe: $TIMEFRAME"
echo "Timerange: $TIMERANGE"
echo "Config: $CONFIG"
echo "------------------------------------------------------"

# Build and execute the command
CMD="podman-compose run --rm freqtrade backtesting --config $CONFIG --strategy-list $STRATEGIES --timerange $TIMERANGE --timeframe $TIMEFRAME"

echo -e "\e[90mExecuting: $CMD\e[0m"
eval $CMD

echo "------------------------------------------------------"
echo -e "\e[32mComparison Complete.\e[0m"
