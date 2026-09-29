param(
    [string]$PrivateCsv = "local_station_private.csv",
    [string]$TemplateCsv = "japan_iptv_local_station_m3u_private_template.csv",
    [string]$OutputM3u = "local_station_private.m3u",
    [switch]$CreateOnly,
    [switch]$IncludeMissing
)

$ErrorActionPreference = "Stop"

function Write-Step($Message) {
    Write-Host "==> $Message"
}

if (-not (Test-Path $TemplateCsv)) {
    throw "Template CSV not found: $TemplateCsv"
}

if (-not (Test-Path "scripts/build_local_station_m3u_from_private_csv.py")) {
    throw "Builder script not found: scripts/build_local_station_m3u_from_private_csv.py"
}

if (-not (Test-Path $PrivateCsv)) {
    Write-Step "Creating private CSV from template: $PrivateCsv"
    Copy-Item $TemplateCsv $PrivateCsv
    Write-Host "Created: $PrivateCsv"
    Write-Host "Next: open $PrivateCsv and fill only the stream_url column."
    if ($CreateOnly) {
        exit 0
    }
}

$privateContent = Get-Content $PrivateCsv -Raw -Encoding UTF8
$hasFilledUrl = $privateContent -match "https?://"

if (-not $hasFilledUrl) {
    Write-Host "No stream_url values found yet."
    Write-Host "Open $PrivateCsv and fill only the stream_url column, then run this script again."
    exit 0
}

Write-Step "Building private local-station M3U: $OutputM3u"
$includeMissingArg = @()
if ($IncludeMissing) {
    $includeMissingArg += "--include-missing"
}

python scripts/build_local_station_m3u_from_private_csv.py `
    --csv $PrivateCsv `
    --out $OutputM3u `
    @includeMissingArg

if (-not (Test-Path $OutputM3u)) {
    throw "M3U was not created: $OutputM3u"
}

$extinfCount = (Select-String -Path $OutputM3u -Pattern '^#EXTINF' -Encoding UTF8).Count
Write-Host "Created: $OutputM3u"
Write-Host "#EXTINF entries: $extinfCount"
Write-Host "Done. Keep $PrivateCsv and $OutputM3u local only; .gitignore protects them."
