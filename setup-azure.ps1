# KISS Studio - one-command Azure setup (student-account friendly)
# Run:  powershell -ExecutionPolicy Bypass -File setup-azure.ps1
$ErrorActionPreference = "Continue"
$rg = "kiss-hackathon"
$name = "kiss-foundry-" + (Get-Random -Maximum 9999)
$regions = @("eastus2", "eastus", "westus", "swedencentral")
$acct = $null

Write-Host "`n== KISS Azure setup (Azure for Students compatible) ==" -ForegroundColor Yellow

foreach ($loc in $regions) {
    Write-Host "Trying region $loc ..." -ForegroundColor Cyan
    az group create -n $rg -l $loc --only-show-errors | Out-Null
    $r = az cognitiveservices account create -n $name -g $rg --kind AIServices --sku S0 -l $loc --yes --only-show-errors 2>&1
    if ($LASTEXITCODE -eq 0) { $acct = $loc; Write-Host "  resource created in $loc" -ForegroundColor Green; break }
    Write-Host "  $loc refused: $($r | Select-Object -Last 1)" -ForegroundColor DarkYellow
}
if (-not $acct) { Write-Host "No region accepted the account. Paste this output to Claude." -ForegroundColor Red; exit 1 }

$models = @(
    @{n="gpt-4o-mini"; v="2024-07-18"},
    @{n="gpt-4o";      v="2024-11-20"},
    @{n="gpt-4o";      v="2024-08-06"},
    @{n="gpt-35-turbo";v="0125"}
)
$deployed = $null
foreach ($m in $models) {
    foreach ($sku in @("GlobalStandard", "Standard")) {
        Write-Host "Trying model $($m.n) $($m.v) ($sku) ..." -ForegroundColor Cyan
        az cognitiveservices account deployment create -g $rg -n $name `
            --deployment-name $m.n --model-name $m.n --model-version $m.v `
            --model-format OpenAI --sku-name $sku --sku-capacity 8 --only-show-errors 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) { $deployed = $m.n; Write-Host "  deployed $($m.n)!" -ForegroundColor Green; break }
    }
    if ($deployed) { break }
}
if (-not $deployed) { Write-Host "No chat model deployable - paste this output to Claude." -ForegroundColor Red; exit 1 }

# optional image model (fine if it fails)
az cognitiveservices account deployment create -g $rg -n $name `
    --deployment-name dall-e-3 --model-name dall-e-3 --model-version "3.0" `
    --model-format OpenAI --sku-name Standard --sku-capacity 1 --only-show-errors 2>&1 | Out-Null
$img = if ($LASTEXITCODE -eq 0) { "dall-e-3" } else { "" }
Write-Host ("Image model: " + ($(if ($img) {"dall-e-3 deployed"} else {"not available (fine - SVG tier keeps working)"})))

$endpoint = az cognitiveservices account show -n $name -g $rg --query properties.endpoint -o tsv
$key = az cognitiveservices account keys list -n $name -g $rg --query key1 -o tsv

$envPath = Join-Path $PSScriptRoot "foundry-track2\.env"
@"
AZURE_OPENAI_ENDPOINT=$endpoint
AZURE_OPENAI_KEY=$key
AZURE_AI_MODEL_DEPLOYMENT=$deployed
AZURE_AI_IMAGE_DEPLOYMENT=$img
"@ | Out-File -Encoding ascii $envPath

Write-Host "`n== DONE ==" -ForegroundColor Green
Write-Host "Region:     $acct"
Write-Host "Chat model: $deployed"
Write-Host "Image:      $(if ($img) {$img} else {'none'})"
Write-Host ".env written to $envPath"
Write-Host "`nNow: pip install -r foundry-track2\requirements.txt  (once)"
Write-Host "Then restart the dashboard (start.bat) - badge should read FOUNDRY:$($deployed.ToUpper())" -ForegroundColor Yellow
