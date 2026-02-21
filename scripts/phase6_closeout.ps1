$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$timestamp = Get-Date -Format o
$reportPath = Join-Path $root "PHASE6_CLOSEOUT_REPORT.md"

$pythonExe = Join-Path $root ".venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    throw "Python virtual environment not found at .venv/Scripts/python.exe"
}

$requiredFiles = @(
    "README.md",
    "DEMO.md",
    "SCHEMA.md",
    "EXECUTION_LOG.md",
    "demo/signature_change.diff",
    "demo/trivial.diff"
)

$missing = @()
foreach ($f in $requiredFiles) {
    if (-not (Test-Path (Join-Path $root $f))) {
        $missing += $f
    }
}

$testOutput = & $pythonExe -m pytest -q 2>&1
$testExit = $LASTEXITCODE

& $pythonExe -m impact_tracer.cli.main --project demo/payments_service --diff-file demo/signature_change.diff --format markdown --output impact_report.md --graph-output graph.html --no-llm | Out-Null
$demoExit = $LASTEXITCODE

$branch = (git branch --show-current).Trim()
$head = (git rev-parse --short HEAD).Trim()
$tag = (git tag --list "v0.1.0").Trim()
$status = (git status --short)

$report = @()
$report += "# Phase 6 Closeout Report"
$report += ""
$report += "- Generated At: $timestamp"
$report += "- Branch: $branch"
$report += "- HEAD: $head"
$report += "- v0.1.0 Tag Present: $([string]::IsNullOrWhiteSpace($tag) -eq $false)"
$report += ""
$report += "## Automated Checks"
$report += "- Required files present: $($missing.Count -eq 0)"
if ($missing.Count -gt 0) {
    $report += "- Missing files: $($missing -join ", ")"
}
$report += "- Pytest exit code: $testExit"
$report += "- Demo markdown+graph run exit code: $demoExit"
$report += ""
$report += "## Git Working Tree"
if ([string]::IsNullOrWhiteSpace(($status -join "").Trim())) {
    $report += "- Clean"
} else {
    $report += "- Status lines:"
    $report += $status
}
$report += ""
$report += "## Manual Steps Remaining"
$report += "1. Run one rehearsal on presentation machine (Task 6.8)."
$report += "2. Complete hackathon submission confirmation (Task 6.9)."

Set-Content -Path $reportPath -Value ($report -join "`n") -Encoding UTF8
Write-Output "Report generated: $reportPath"
