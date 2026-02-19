<#
.SYNOPSIS
Runs a comparative backtest for multiple Freqtrade strategies.

.DESCRIPTION
This script uses Podman to run Freqtrade backtesting on a list of strategies
and outputs a comparative performance report.

.EXAMPLE
.\compare_strategies.ps1
#>

$strategies = "SimpleStrategy", "RSIStrategy", "CombinedStrategy", "TrailingStrategy", "SniperStrategy"
$timerange = "20251120-"
$timeframe = "5m"
$config = "user_data/config_backtest.json"

Write-Host "Starting Comparative Backtest for: $strategies" -ForegroundColor Cyan
Write-Host "Timeframe: $timeframe"
Write-Host "Timerange: $timerange"
Write-Host "Config: $config"
Write-Host "------------------------------------------------------"

# Build the argument list for podman-compose
# Note: We use Invoke-Expression or direct command execution depending on complexity.
# Here we construct the command string for clarity.

$cmd = "podman-compose run --rm freqtrade backtesting --config $config --strategy-list $strategies --timerange $timerange --timeframe $timeframe"

Write-Host "Executing: $cmd" -ForegroundColor Gray

# Execute the command
Invoke-Expression $cmd

Write-Host "------------------------------------------------------"
Write-Host "Comparison Complete." -ForegroundColor Green
