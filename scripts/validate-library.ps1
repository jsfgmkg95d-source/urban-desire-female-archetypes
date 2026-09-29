[CmdletBinding()]
param(
    [switch]$Json,
    [string]$PythonExe
)

$ErrorActionPreference = 'Stop'
$scriptPath = Join-Path $PSScriptRoot 'validate-library.py'
$pythonArguments = @()

if ($PythonExe) {
    $pythonCommand = Get-Command -Name $PythonExe -ErrorAction Stop
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
    $pythonCommand = Get-Command py
    $pythonArguments += '-3'
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $pythonCommand = Get-Command python
} elseif (Get-Command python3 -ErrorAction SilentlyContinue) {
    $pythonCommand = Get-Command python3
} else {
    throw 'Python 3.11 or newer is required. Install Python or pass -PythonExe with its executable path.'
}

$pythonArguments += @('-X', 'utf8', $scriptPath)
if ($Json) { $pythonArguments += '--json' }
& $pythonCommand.Source @pythonArguments
exit $LASTEXITCODE
