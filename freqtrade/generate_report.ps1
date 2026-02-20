
# Generate Reporting Script
# Goal: Create HTML plots for the results

$strategy = "CombinedStrategy"
$config = "user_data/config_backtest.json"
$timerange = "20251120-"

Write-Host "Generating HTML Report for $strategy..."

# 1. Plot Dataframe
# Plotting requires 'plotly' which is not in the standard image.
# We chain the install and plot command in one container session.

$plot_cmd = "pip install plotly && freqtrade plot-dataframe --config $config --strategy $strategy --timerange $timerange"

podman-compose run --rm --entrypoint /bin/sh freqtrade -c "$plot_cmd"

Write-Host "Report generation complete."
Write-Host "Check 'C:\Users\alexg\Documents\Freqtrade\user_data\plot\' for the HTML files."
