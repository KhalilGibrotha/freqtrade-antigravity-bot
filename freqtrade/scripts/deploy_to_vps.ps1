<#
.SYNOPSIS
Deploys Freqtrade configurations, strategies, and FreqAI models to a remote Cloud VPS.

.DESCRIPTION
This script is designed for "Option A" architecture (Inference-Only VPS). 
It securely copies the necessary files from the local Windows machine to the remote Linux VPS via SCP (SSH).
It does NOT copy the massive historical databases (tradesv3.sqlite), as those are only needed locally for training/backtesting.

.PARAMETER VpsIp
The IP Address of the remote Cloud VPS.

.PARAMETER SshUser
The SSH username (default: root).

.PARAMETER RemoteDir
The destination directory on the remote VPS where Freqtrade is installed.

.EXAMPLE
.\deploy_to_vps.ps1 -VpsIp "192.168.1.100" -SshUser "ubuntu" -RemoteDir "/home/ubuntu/freqtrade"
#>

param (
    [Parameter(Mandatory = $true)]
    [string]$VpsIp,

    [string]$SshUser = "root",

    [string]$RemoteDir = "/root/freqtrade"
)

# 1. Ensure the remote directory structure exists
Write-Host "Creating remote directory structure on $VpsIp..." -ForegroundColor Cyan
ssh "${SshUser}@${VpsIp}" "mkdir -p ${RemoteDir}/user_data/strategies"
ssh "${SshUser}@${VpsIp}" "mkdir -p ${RemoteDir}/user_data/models"

# 2. Copy docker-compose.yml
Write-Host "Copying docker-compose.yml..." -ForegroundColor Cyan
scp .\docker-compose.yml "${SshUser}@${VpsIp}:${RemoteDir}/docker-compose.yml"

# 3. Copy JSON configurations
Write-Host "Copying JSON configurations..." -ForegroundColor Cyan
scp .\user_data\config.json "${SshUser}@${VpsIp}:${RemoteDir}/user_data/config.json"
scp .\user_data\config_experimental.json "${SshUser}@${VpsIp}:${RemoteDir}/user_data/config_experimental.json"
scp .\user_data\config_freqai.json "${SshUser}@${VpsIp}:${RemoteDir}/user_data/config_freqai.json"

# 4. Copy Python Strategies
Write-Host "Copying Python Strategies..." -ForegroundColor Cyan
scp .\user_data\strategies\*.py "${SshUser}@${VpsIp}:${RemoteDir}/user_data/strategies/"

# 5. Copy Trained FreqAI Models (Only the model folders, not the giant DBs)
# Note: Ensure we don't accidentally copy massive historical SQlite files!
if (Test-Path ".\user_data\models\") {
    Write-Host "Syncing Trained FreqAI Models (*.feather / Metadata)..." -ForegroundColor Cyan
    # Powershell native SCP for entire directories can be tricky, using recursive copy
    scp -r .\user_data\models\* "${SshUser}@${VpsIp}:${RemoteDir}/user_data/models/"
}
else {
    Write-Host "No FreqAI models found to sync." -ForegroundColor Yellow
}

Write-Host "`nDeployment synchronization complete!" -ForegroundColor Green
Write-Host "Next steps: SSH into the VPS and run 'docker-compose up -d' inside ${RemoteDir}" -ForegroundColor Yellow
