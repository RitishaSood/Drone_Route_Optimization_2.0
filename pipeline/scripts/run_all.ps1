Write-Host "====================================="
Write-Host " UAV Python + C++ Full Pipeline"
Write-Host "====================================="

# Move to repo root
Set-Location $PSScriptRoot\..\..

$env:MPLBACKEND = "Agg"
$RootDir = Get-Location
$PythonDir = Join-Path $RootDir "pipeline\env_generator"
$CppDir = Join-Path $RootDir "pipeline\cpp_engine"

if ($env:RUN_DIR) {
    if ([System.IO.Path]::IsPathRooted($env:RUN_DIR)) {
        $ActiveRunDir = $env:RUN_DIR
    }
    else {
        $ActiveRunDir = Join-Path $RootDir $env:RUN_DIR
    }

    $DataRootDir = Join-Path $ActiveRunDir "data"
    $LogsDir = Join-Path $ActiveRunDir "logs"
}
else {
    $DataRootDir = Join-Path $RootDir "data"
    $LogsDir = $null
}

$CsvDir = Join-Path $DataRootDir "csv"
$PlotsDir = Join-Path $DataRootDir "plots"
$OutputsDir = Join-Path $DataRootDir "outputs"

Write-Host ""
Write-Host "[INFO] Root directory: $RootDir"
if ($env:RUN_DIR) {
    Write-Host "[INFO] Run directory: $ActiveRunDir"
}

# -------------------------------
# Step 1: Clean generated files
# -------------------------------

Write-Host ""
Write-Host "[1] Cleaning old generated files"

New-Item -ItemType Directory -Force -Path $DataRootDir | Out-Null
New-Item -ItemType Directory -Force -Path $CsvDir | Out-Null
New-Item -ItemType Directory -Force -Path $PlotsDir | Out-Null
New-Item -ItemType Directory -Force -Path $OutputsDir | Out-Null
if ($LogsDir) {
    New-Item -ItemType Directory -Force -Path $LogsDir | Out-Null
}

# Clean data folder but keep .gitkeep
Get-ChildItem -Path $CsvDir -Force |
Where-Object { $_.Name -ne ".gitkeep" } |
Remove-Item -Recurse -Force

# Clean plots folder but keep .gitkeep
Get-ChildItem -Path $PlotsDir -Force |
Where-Object { $_.Name -ne ".gitkeep" } |
Remove-Item -Recurse -Force

# Clean outputs folder but keep .gitkeep
Get-ChildItem -Path $OutputsDir -Force |
Where-Object { $_.Name -ne ".gitkeep" } |
Remove-Item -Recurse -Force

if ($LogsDir) {
    Get-ChildItem -Path $LogsDir -Force |
    Where-Object { $_.Name -ne ".gitkeep" -and $_.Name -ne "pipeline.log" } |
    Remove-Item -Recurse -Force
}

# Recreate .gitkeep if missing
New-Item -ItemType File -Force -Path (Join-Path $DataRootDir ".gitkeep") | Out-Null
New-Item -ItemType File -Force -Path (Join-Path $CsvDir ".gitkeep") | Out-Null
New-Item -ItemType File -Force -Path (Join-Path $PlotsDir ".gitkeep") | Out-Null
New-Item -ItemType File -Force -Path (Join-Path $OutputsDir ".gitkeep") | Out-Null
if ($LogsDir) {
    New-Item -ItemType File -Force -Path (Join-Path $LogsDir ".gitkeep") | Out-Null
}

Write-Host "[OK] Cleaned active data, plots, outputs, and logs folders while keeping .gitkeep and pipeline.log"

# -------------------------------
# Step 2: Setup Python venv and run generator
# -------------------------------

Write-Host ""
Write-Host "[2] Setting up Python venv and running generator"

Set-Location $PythonDir

$PythonExe = Join-Path $PythonDir "venv\Scripts\python.exe"
$PipExe = Join-Path $PythonDir "venv\Scripts\pip.exe"
$RequirementsFile = Join-Path $PythonDir "requirements.txt"

if (!(Test-Path $PythonExe)) {
    Write-Host "[INFO] Python venv not found. Creating pipeline\env_generator\venv..."

    py -3.11 -m venv venv

    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Failed to create Python venv"
        exit 1
    }

    Write-Host "[OK] Created pipeline\env_generator\venv"
}
else {
    Write-Host "[OK] Found existing pipeline\env_generator\venv"
}

if (!(Test-Path $PipExe)) {
    Write-Host "[ERROR] pip not found inside venv:"
    Write-Host $PipExe
    exit 1
}

if (Test-Path $RequirementsFile) {
    Write-Host "[INFO] Installing Python requirements..."

    & $PipExe install -r $RequirementsFile

    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Failed to install Python requirements"
        exit 1
    }

    Write-Host "[OK] Python requirements installed"
}
else {
    Write-Host "[WARN] requirements.txt not found. Skipping pip install."
}

Write-Host "[INFO] Using Python:"
Write-Host $PythonExe

& $PythonExe main.py

if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Python generator failed"
    exit 1
}

Write-Host "[OK] Python generator completed"

# -------------------------------
# Step 3: Validate generated CSVs
# -------------------------------

Write-Host ""
Write-Host "[3] Validating generated CSV files"

Set-Location $RootDir

$RequiredFiles = @(
    (Join-Path $CsvDir "terrain_height.csv"),
    (Join-Path $CsvDir "terrain_type.csv"),
    (Join-Path $CsvDir "sensor.csv"),
    (Join-Path $CsvDir "nfz.csv"),
    (Join-Path $CsvDir "env.csv")
)

foreach ($file in $RequiredFiles) {
    if (!(Test-Path $file)) {
        Write-Host "[ERROR] Missing required file: $file"
        exit 1
    }
    else {
        Write-Host "[OK] Found $file"
    }
}

# -------------------------------
# Step 4: Build C++ engine
# -------------------------------

Write-Host ""
Write-Host "[4] Building C++ engine"

Set-Location $CppDir

cmake -S . -B build

if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] CMake configuration failed"
    exit 1
}

cmake --build build --config Release

if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] C++ build failed"
    exit 1
}

Write-Host "[OK] C++ build completed"

# -------------------------------
# Step 5: Run C++ executable
# -------------------------------

Write-Host ""
Write-Host "[5] Running C++ engine"

Set-Location $RootDir

$CppExe = Join-Path $RootDir "pipeline\cpp_engine\build\Release\uav_pipeline.exe"

if (!(Test-Path $CppExe)) {
    Write-Host "[ERROR] C++ executable not found:"
    Write-Host $CppExe
    exit 1
}

if (Get-Command Unblock-File -ErrorAction SilentlyContinue) {
    Unblock-File -LiteralPath $CppExe -ErrorAction SilentlyContinue
}

$PreviousErrorActionPreference = $ErrorActionPreference
$ErrorActionPreference = "Stop"

try {
    & $CppExe

    if ((-not $?) -or ($LASTEXITCODE -ne 0)) {
        Write-Host "[ERROR] C++ pipeline failed"
        if ($LASTEXITCODE -ne $null) {
            Write-Host "Exit code: $LASTEXITCODE"
        }
        exit 1
    }
}
catch {
    Write-Host "[ERROR] C++ executable could not be launched:"
    Write-Host $_.Exception.Message
    Write-Host ""
    Write-Host "This is usually a Windows Application Control / antivirus policy blocking the built exe."
    Write-Host "Executable:"
    Write-Host $CppExe
    exit 1
}
finally {
    $ErrorActionPreference = $PreviousErrorActionPreference
}

Write-Host "[OK] C++ pipeline completed"

# -------------------------------
# Step 6: Validate C++ output
# -------------------------------

Write-Host ""
Write-Host "[6] Validating C++ output files"

$FinalCostCandidates = @(
    (Join-Path $OutputsDir "final_cost.csv"),
    (Join-Path $OutputsDir "finalcost.csv")
)

$FinalCostFile = $FinalCostCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1

if (!$FinalCostFile) {
    Write-Host "[ERROR] Missing output file. Checked:"
    $FinalCostCandidates | ForEach-Object { Write-Host $_ }
    exit 1
}
else {
    Write-Host "[OK] Found final cost file:"
    Write-Host $FinalCostFile
}

# -------------------------------
# Step 7: Generate final cost plots
# Optional: only runs if pipeline\env_generator\visualization\finalcsv.py exists
# -------------------------------

Write-Host ""
Write-Host "[7] Checking final cost plot script"

$FinalCostPlotScript = Join-Path $PythonDir "visualization\finalcsv.py"

if (Test-Path $FinalCostPlotScript) {
    Write-Host "[INFO] Generating final cost plots..."

    & $PythonExe $FinalCostPlotScript

    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Final cost plot generation failed"
        exit 1
    }

    Write-Host "[OK] Final cost plots generated"
}
else {
    Write-Host "[WARN] pipeline\env_generator\visualization\finalcsv.py not found. Skipping final cost plots."
}

# -------------------------------
# Step 8: Run path planner
# -------------------------------

Write-Host ""
Write-Host "[8] Checking path planner"

$PathPlannerMain = Join-Path $RootDir "pipeline\path_planner\main.py"

if (!(Test-Path $PathPlannerMain)) {
    Write-Host "[WARN] pipeline\path_planner\main.py not found. Skipping path planner."
}
else {
    if (!(Test-Path (Join-Path $OutputsDir "final_cost.csv")) -and !(Test-Path (Join-Path $OutputsDir "finalcost.csv"))) {
        Write-Host "[ERROR] final_cost.csv is required before running the path planner"
        exit 1
    }

    Write-Host "[INFO] Running path planner..."
    & $PythonExe $PathPlannerMain

    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Path planner failed"
        exit 1
    }

    Write-Host "[OK] Path planner completed"
}

# -------------------------------
# Done
# -------------------------------

Write-Host ""
Write-Host "====================================="
Write-Host " FULL PIPELINE COMPLETED SUCCESSFULLY"
Write-Host "====================================="

Write-Host ""
Write-Host "CSV input files:"
Write-Host $CsvDir

Write-Host ""
Write-Host "Plot files:"
Write-Host $PlotsDir

Write-Host ""
Write-Host "C++ output files:"
Write-Host $OutputsDir
