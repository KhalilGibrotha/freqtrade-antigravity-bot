
# Regression Test Script for Freqtrade
# Goal: Verify that CombinedStrategy performance has not degraded below baseline.

$baseline_profit = -0.06  # Allow down to -6% (Actual was -5.18%)
$baseline_drawdown = 0.085 # Allow up to 8.5% (Actual was 7.60%)
$strategy = "CombinedStrategy"
$timerange = "20251120-"
$config = "user_data/config_backtest.json"


Write-Host "----------------------------------------------------------------"
Write-Host "Running Regression Test for $strategy"
Write-Host "Baseline Profit Floor: $($baseline_profit * 100)%"
Write-Host "Baseline Max Drawdown: $($baseline_drawdown * 100)%"
Write-Host "----------------------------------------------------------------"

# 1. Run Backtest
Write-Host "Executing Freqtrade Backtest..."
podman-compose run --rm freqtrade backtesting --config $config --strategy $strategy --timerange $timerange

# 2. Find the latest backtest result
# Check the Documents folder for results
$latest_file = Get-ChildItem "C:\Users\alexg\Documents\Freqtrade\user_data\backtest_results\backtest-result-*.json" | Sort-Object LastWriteTime -Descending | Select-Object -First 1

if (-not $latest_file) {
    Write-Error "Regression test failed: No backtest result file found in 'freqtrade/user_data/backtest_results/'."
    exit 1
}

Write-Host "Parsing output file: $($latest_file.Name)"

# 3. Parse JSON Results
try {
    $json = Get-Content $latest_file.FullName | ConvertFrom-Json
    
    # Structure is usually: $json.strategy.CombinedStrategy ...
    # API might return a list or dict. Let's inspect the first strategy found if key matches.
    $strat_metrics = $json.strategy.$strategy
    
    if (-not $strat_metrics) {
        Write-Error "Could not find metrics for $strategy in JSON output."
        exit 1
    }

    $actual_profit = $strat_metrics.total_profit
    $actual_drawdown = $strat_metrics.max_drawdown

    Write-Host "`nRESULTS:"
    Write-Host "Actual Profit:     $($actual_profit * 100)%"
    Write-Host "Actual Drawdown:   $($actual_drawdown * 100)%"

    # 4. Compare
    $failed = $false
    
    if ($actual_profit -lt $baseline_profit) {
        Write-Host "FAILED: Profit ($($actual_profit * 100)%) is below baseline ($($baseline_profit * 100)%)" -ForegroundColor Red
        $failed = $true
    }
    else {
        Write-Host "PASS: Profit is within acceptable range." -ForegroundColor Green
    }

    if ($actual_drawdown -gt $baseline_drawdown) {
        Write-Host "FAILED: Drawdown ($($actual_drawdown * 100)%) is higher than baseline ($($baseline_drawdown * 100)%)" -ForegroundColor Red
        $failed = $true
    }
    else {
        Write-Host "PASS: Drawdown is within acceptable range." -ForegroundColor Green
    }

    if ($failed) {
        Write-Host "`nREGRESSION DETECTED!" -ForegroundColor Red
        exit 1
    }
    else {
        Write-Host "`nRegression Test Passed Successfully." -ForegroundColor Green
        exit 0
    }

}
catch {
    Write-Error "Failed to parse regression results: $_"
    exit 1
}
