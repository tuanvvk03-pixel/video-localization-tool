param(
    [switch]$IncludeWorkspace,
    [switch]$Quiet
)

$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $repoRoot

function Remove-IfExists {
    param(
        [Parameter(Mandatory = $true)][string]$LiteralPath,
        [switch]$Recurse
    )
    if (-not (Test-Path -LiteralPath $LiteralPath)) {
        return
    }
    if (-not $Quiet) {
        Write-Host "[clean_runtime] removing $LiteralPath"
    }
    if ($Recurse) {
        Remove-Item -LiteralPath $LiteralPath -Recurse -Force -ErrorAction SilentlyContinue
    } else {
        Remove-Item -LiteralPath $LiteralPath -Force -ErrorAction SilentlyContinue
    }
}

$dirNames = @("__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", ".locks", "htmlcov")
Get-ChildItem -Path $repoRoot -Recurse -Directory -Force -ErrorAction SilentlyContinue |
    Where-Object { $dirNames -contains $_.Name } |
    ForEach-Object { Remove-IfExists -LiteralPath $_.FullName -Recurse }

Get-ChildItem -Path $repoRoot -Recurse -File -Force -ErrorAction SilentlyContinue |
    Where-Object {
        $_.Name -in @(".coverage", "coverage.xml", "run.log") -or
        $_.Extension -in @(".pyc", ".pyo")
    } |
    ForEach-Object { Remove-IfExists -LiteralPath $_.FullName }

if ($IncludeWorkspace) {
    $workspacePath = Join-Path $repoRoot "workspace"
    if (Test-Path -LiteralPath $workspacePath) {
        Get-ChildItem -Path $workspacePath -Force -ErrorAction SilentlyContinue |
            ForEach-Object { Remove-IfExists -LiteralPath $_.FullName -Recurse }
    }
}

if (-not $Quiet) {
    Write-Host "[clean_runtime] complete"
}
