# PowerShell shim for task command - calls Taskfile.yml in the same directory as this script
param(
    [Parameter(ValueFromRemainingArguments=$true)]
    [string[]]$TaskArgs
)

# Get the directory where this script is located
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Get the Taskfile.yml path in the same directory
$TaskfilePath = Join-Path $ScriptDir "Taskfile.yml"

# Get the current working directory (where the command was executed from)
$ExecutionDir = Get-Location

# Verify the Taskfile exists
if (-not (Test-Path $TaskfilePath)) {
    Write-Error "Taskfile.yml not found at: $TaskfilePath"
    exit 1
}

# Call task with the Taskfile location, working directory, and pass through any arguments
$TaskArgs += @("--taskfile", $TaskfilePath, "--dir", $ExecutionDir)
& task $TaskArgs