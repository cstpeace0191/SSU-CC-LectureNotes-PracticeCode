# PowerShell wrapper for katenary.exe
$repoRoot = $PSScriptRoot
$katenaryExe = Join-Path $repoRoot "katenary.exe"

if (-not (Test-Path $katenaryExe)) {
    Write-Error "katenary.exe not found at $katenaryExe"
    exit 1
}

$rawArgs = $args

# Check if this is a 'convert' command with -c / --compose-file
$isConvert = $false
$composeFile = $null
$outputDir = $null

for ($i = 0; $i -lt $rawArgs.Length; $i++) {
    $arg = $rawArgs[$i]
    if ($arg -eq "convert") {
        $isConvert = $true
    }
    elseif (($arg -eq "-c" -or $arg -eq "--compose-file") -and ($i + 1 -lt $rawArgs.Length)) {
        $composeFile = $rawArgs[$i + 1]
    }
    elseif ($arg.StartsWith("--compose-file=")) {
        $composeFile = $arg.Substring(15)
    }
    elseif (($arg -eq "-o" -or $arg -eq "--output-dir") -and ($i + 1 -lt $rawArgs.Length)) {
        $outputDir = $rawArgs[$i + 1]
    }
    elseif ($arg.StartsWith("--output-dir=")) {
        $outputDir = $arg.Substring(13)
    }
    elseif ($arg.StartsWith("-o=")) {
        $outputDir = $arg.Substring(3)
    }
}

if ($isConvert -and $composeFile -and (-not (Test-Path (Join-Path $repoRoot "compose.yaml")))) {
    $resolvedCompose = Resolve-Path (Join-Path $repoRoot $composeFile) -ErrorAction SilentlyContinue
    if (-not $resolvedCompose) {
        $resolvedCompose = Resolve-Path $composeFile -ErrorAction SilentlyContinue
    }
    
    if ($resolvedCompose -and (Test-Path $resolvedCompose)) {
        $tempDir = [System.IO.Path]::Combine([System.IO.Path]::GetTempPath(), [System.Guid]::NewGuid().ToString(), "getting-started-todo-app")
        New-Item -ItemType Directory -Path $tempDir -Force | Out-Null
        try {
            Copy-Item $resolvedCompose (Join-Path $tempDir "compose.yaml")
            
            $forwardArgs = @()
            $skipNext = $false
            for ($j = 0; $j -lt $rawArgs.Length; $j++) {
                if ($skipNext) {
                    $skipNext = $false
                    continue
                }
                $a = $rawArgs[$j]
                if ($a -eq "-c" -or $a -eq "--compose-file") {
                    $skipNext = $true
                    continue
                }
                if ($a.StartsWith("--compose-file=")) {
                    continue
                }
                if ($a -eq "-o" -or $a -eq "--output-dir") {
                    $forwardArgs += $a
                    $targetOut = $rawArgs[$j + 1]
                    if (-not [System.IO.Path]::IsPathRooted($targetOut)) {
                        $targetOut = [System.IO.Path]::GetFullPath((Join-Path $repoRoot $targetOut))
                    }
                    $forwardArgs += $targetOut
                    $skipNext = $true
                    continue
                }
                $forwardArgs += $a
            }

            # Add default icon if not specified
            if (-not ($rawArgs -contains "-i") -and -not ($rawArgs -contains "--icon")) {
                $forwardArgs += "-i"
                $forwardArgs += "https://raw.githubusercontent.com/docker/getting-started-todo-app/master/client/public/favicon.ico"
            }
            
            Push-Location $tempDir
            try {
                & $katenaryExe @forwardArgs
                $exitCode = $LASTEXITCODE
            } finally {
                Pop-Location
            }
            
            # Run patch-service-type if outputDir was specified
            if ($exitCode -eq 0 -and $outputDir) {
                $targetOut = if ([System.IO.Path]::IsPathRooted($outputDir)) { $outputDir } else { Join-Path $repoRoot $outputDir }
                $patchScript = Join-Path $repoRoot "scripts\patch-service-type.py"
                if (Test-Path $patchScript) {
                    python $patchScript $targetOut
                }
            }
            exit $exitCode
        } finally {
            $parentTemp = Split-Path $tempDir -Parent
            if (Test-Path $parentTemp) {
                Remove-Item -Recurse -Force $parentTemp -ErrorAction SilentlyContinue
            }
        }
    }
}

# Default pass-through
& $katenaryExe @rawArgs
exit $LASTEXITCODE
