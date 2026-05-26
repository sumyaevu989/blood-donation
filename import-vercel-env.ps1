<#
Imports variables from a local .env file into Vercel for a given project.
USAGE:
  # set env vars in your shell (do NOT commit these values)
  $env:VERCEL_TOKEN = "your_token_here"
  $env:VERCEL_PROJECT_ID = "your_project_id_here"
  .\import-vercel-env.ps1 -EnvFile ".env" -Target production
#>
param(
    [string]$EnvFile = ".env",
    [ValidateSet("production","preview","development")]
    [string]$Target = "production"
)

if (-not $env:VERCEL_TOKEN) {
    Write-Error "VERCEL_TOKEN environment variable is not set. Export it first and re-run the script."
    exit 1
}
if (-not $env:VERCEL_PROJECT_ID) {
    Write-Error "VERCEL_PROJECT_ID environment variable is not set. Export it first and re-run the script."
    exit 1
}

if (-not (Test-Path $EnvFile)) {
    Write-Error ".env file not found at path: $EnvFile"
    exit 1
}

Get-Content $EnvFile | ForEach-Object {
    $line = $_.Trim()
    if (-not $line -or $line.StartsWith("#")) { return }
    if ($line -notmatch "^[A-Za-z_][A-Za-z0-9_]*=") { return }

    $parts = $line -split "=", 2
    $key = $parts[0].Trim()
    $value = $parts[1].Trim()

    if (($value.StartsWith('"') -and $value.EndsWith('"')) -or ($value.StartsWith("'") -and $value.EndsWith("'"))) {
        $value = $value.Substring(1, $value.Length - 2)
    }

    $body = @{ key = $key; value = $value; target = @($Target); type = "encrypted" } | ConvertTo-Json -Depth 5

    try {
        Invoke-RestMethod -Method Post -Uri "https://api.vercel.com/v9/projects/$($env:VERCEL_PROJECT_ID)/env" -Headers @{ Authorization = "Bearer $($env:VERCEL_TOKEN)" } -ContentType "application/json" -Body $body
        Write-Host "Imported $key"
    }
    catch {
        Write-Warning "Failed to import $key: $($_.Exception.Message)"
    }
}
