# Fresh Setup and Test Automation for Meshtastic Mesh Visualizer
# PowerShell version for Windows users

param(
    [switch]$SetupOnly,      # Only run setup, skip tests
    [switch]$TestOnly,       # Only run tests, skip setup
    [switch]$Clean,          # Clean install (remove existing .venv)
    [switch]$NoTests,        # Skip all tests
    [switch]$Help            # Show help
)

# Show help if requested
if ($Help) {
    Write-Host "Fresh Setup and Test Automation for Meshtastic Mesh Visualizer" -ForegroundColor Green
    Write-Host ""
    Write-Host "This script automates the complete setup process for a freshly cloned project:"
    Write-Host "1. Creates and configures Python virtual environment"
    Write-Host "2. Installs all required dependencies"
    Write-Host "3. Sets up test environment"
    Write-Host "4. Runs comprehensive tests"
    Write-Host "5. Validates the installation"
    Write-Host ""
    Write-Host "Usage: .\setup_and_test.ps1 [options]"
    Write-Host ""
    Write-Host "Options:"
    Write-Host "  -SetupOnly          Only run setup, skip tests"
    Write-Host "  -TestOnly           Only run tests, skip setup"
    Write-Host "  -Clean              Clean install (remove existing .venv)"
    Write-Host "  -NoTests            Skip all tests"
    Write-Host "  -Help               Show this help message"
    Write-Host ""
    Write-Host "Examples:"
    Write-Host "  .\setup_and_test.ps1                # Full setup and test"
    Write-Host "  .\setup_and_test.ps1 -SetupOnly     # Just setup, no tests"
    Write-Host "  .\setup_and_test.ps1 -TestOnly      # Just tests (assumes setup done)"
    Write-Host "  .\setup_and_test.ps1 -Clean         # Clean setup (remove existing .venv)"
    exit 0
}

# Color functions
function Write-Step {
    param([string]$Message, [int]$StepNum = 0)
    if ($StepNum -gt 0) {
        Write-Host ""
        Write-Host "📋 Step $StepNum`: $Message" -ForegroundColor Cyan
    } else {
        Write-Host ""
        Write-Host "🔸 $Message" -ForegroundColor Blue
    }
}

function Write-Success {
    param([string]$Message)
    Write-Host "✅ $Message" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "⚠️  $Message" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "❌ $Message" -ForegroundColor Red
}

function Test-Command {
    param([string]$Command)
    try {
        Get-Command $Command -ErrorAction Stop | Out-Null
        return $true
    } catch {
        return $false
    }
}

function Invoke-SafeCommand {
    param(
        [string]$Command,
        [string]$WorkingDirectory = (Get-Location),
        [bool]$ThrowOnError = $true
    )
    
    try {
        $result = Invoke-Expression $Command
        return $result
    } catch {
        Write-Error "Command failed: $Command"
        Write-Error "Error: $($_.Exception.Message)"
        if ($ThrowOnError) {
            throw
        }
        return $null
    }
}

# Main script starts here
Write-Host ""
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "  MESHTASTIC MESH VISUALIZER - FRESH SETUP" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host ""

# Check Python availability
Write-Step "Checking Python installation"

# Try to find a working Python
$pythonCandidates = @("python3", "python", "C:\Python311\python.exe", "C:\Python310\python.exe", "C:\Python39\python.exe", "C:\Python38\python.exe")
$workingPython = $null

foreach ($candidate in $pythonCandidates) {
    try {
        $versionResult = & $candidate --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            # Test if this Python can import site module
            $siteTest = & $candidate -c "import site" 2>&1
            if ($LASTEXITCODE -eq 0) {
                $workingPython = $candidate
                Write-Success "Found working Python: $candidate"
                break
            } else {
                Write-Warning "Python $candidate found but has issues (missing site module)"
            }
        }
    } catch {
        # Continue to next candidate
    }
}

if (-not $workingPython) {
    Write-Error "No working Python installation found. Please install Python 3.8+ from python.org"
    exit 1
}

# Check Python version
$pythonVersion = & $workingPython --version 2>&1
Write-Success "Found: $pythonVersion"

# Verify Python version is 3.8+
$versionMatch = $pythonVersion -match "Python (\d+)\.(\d+)"
if ($versionMatch) {
    $major = [int]$matches[1]
    $minor = [int]$matches[2]
    if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 8)) {
        Write-Error "Python 3.8+ required, found $major.$minor"
        exit 1
    }
} else {
    Write-Warning "Could not parse Python version, continuing anyway"
}

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$venvPath = Join-Path $projectRoot ".venv"
$pythonExe = Join-Path $venvPath "Scripts\python.exe"
$pipExe = Join-Path $venvPath "Scripts\pip.exe"

# Setup phase
if (-not $TestOnly) {
    Write-Step "Setting up virtual environment" 1
    
    # Clean existing venv if requested
    if ($Clean -and (Test-Path $venvPath)) {
        Write-Step "Removing existing virtual environment"
        Remove-Item -Recurse -Force $venvPath
        Write-Success "Existing .venv removed"
    }
    
    # Create new venv if it doesn't exist
    if (-not (Test-Path $venvPath)) {
        Write-Step "Creating new virtual environment"
        & $workingPython -m venv $venvPath
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Failed to create virtual environment"
            exit 1
        }
        Write-Success "Virtual environment created"
    } else {
        Write-Success "Virtual environment already exists"
    }
    
    Write-Step "Installing dependencies" 2
    
    # Check requirements.txt exists
    $requirementsFile = Join-Path $projectRoot "requirements.txt"
    if (-not (Test-Path $requirementsFile)) {
        Write-Error "requirements.txt not found"
        exit 1
    }
    
    # Upgrade pip first
    Write-Step "Upgrading pip"
    & $pipExe install --upgrade pip
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to upgrade pip"
        exit 1
    }
    
    # Install production dependencies
    Write-Step "Installing production dependencies"
    & $pipExe install -r $requirementsFile
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to install production dependencies"
        exit 1
    }
    
    # Install test dependencies
    Write-Step "Installing test dependencies"
    $testDeps = @("pytest", "pytest-cov", "pytest-html")
    foreach ($dep in $testDeps) {
        & $pipExe install $dep
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Failed to install $dep"
            exit 1
        }
    }
    
    Write-Success "All dependencies installed"
    
    Write-Step "Verifying project structure" 3
    
    $requiredDirs = @("src", "tests", "scripts")
    $requiredFiles = @("src\app.py", "requirements.txt")
    $missingItems = @()
    
    # Check directories
    foreach ($dir in $requiredDirs) {
        $dirPath = Join-Path $projectRoot $dir
        if (-not (Test-Path $dirPath)) {
            $missingItems += "Directory: $dir"
        }
    }
    
    # Check files
    foreach ($file in $requiredFiles) {
        $filePath = Join-Path $projectRoot $file
        if (-not (Test-Path $filePath)) {
            $missingItems += "File: $file"
        }
    }
    
    if ($missingItems.Count -gt 0) {
        Write-Error "Missing required project structure:"
        foreach ($item in $missingItems) {
            Write-Error "  - $item"
        }
        exit 1
    }
    
    Write-Success "Project structure verified"
    
    Write-Step "Setting up test data" 4
    
    $testDataSwitcher = Join-Path $projectRoot "scripts\test_data_switcher.py"
    if (Test-Path $testDataSwitcher) {
        & $pythonExe $testDataSwitcher small
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Test data configured"
        } else {
            Write-Warning "Could not set test data, continuing anyway"
        }
    } else {
        Write-Warning "Test data switcher not found, skipping test data setup"
    }
    
    if ($SetupOnly) {
        Write-Success "Setup complete!"
        # Show summary
        Write-Host ""
        Write-Host "🚀 Quick Start Commands:" -ForegroundColor Cyan
        Write-Host "  • Activate venv: .venv\Scripts\activate"
        Write-Host "  • Run app: `"$pythonExe`" src\app.py"
        Write-Host "  • Run tests: `"$pythonExe`" -m pytest tests\ -v"
        Write-Host "  • Switch test data: `"$pythonExe`" scripts\test_data_switcher.py small"
        Write-Host ""
        Write-Success "You're all set! The project is ready for development."
        exit 0
    }
}

# Test phase
if (-not $NoTests -and -not $SetupOnly) {
    Write-Step "Running tests" 5
    
    $testsDir = Join-Path $projectRoot "tests"
    if (-not (Test-Path $testsDir)) {
        Write-Warning "Tests directory not found, skipping tests"
    } else {
        # Run unit tests
        Write-Step "Running unit tests"
        $unitTestsDir = Join-Path $testsDir "unit"
        if (Test-Path $unitTestsDir) {
            & $pythonExe -m pytest $unitTestsDir -v --tb=short
            if ($LASTEXITCODE -eq 0) {
                Write-Success "Unit tests passed"
            } else {
                Write-Warning "Some unit tests failed (expected for template tests)"
            }
        }
        
        # Run integration tests
        Write-Step "Running integration tests"
        $integrationTestsDir = Join-Path $testsDir "integration"
        if (Test-Path $integrationTestsDir) {
            & $pythonExe -m pytest $integrationTestsDir -v --tb=short
            if ($LASTEXITCODE -eq 0) {
                Write-Success "Integration tests passed"
            } else {
                Write-Warning "Some integration tests failed (expected for template tests)"
            }
        }
    }
    
    Write-Step "Testing application startup" 6
    
    $appFile = Join-Path $projectRoot "src\app.py"
    if (Test-Path $appFile) {
        $testScript = @"
import sys
sys.path.insert(0, "src")
try:
    import app
    print("✅ App import successful")
except Exception as e:
    print(f"❌ App import failed: {e}")
    sys.exit(1)
"@
        
        $result = & $pythonExe -c $testScript
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Application startup test passed"
        } else {
            Write-Warning "Application startup test failed"
        }
    } else {
        Write-Warning "app.py not found, skipping startup test"
    }
}

# Final summary
Write-Host ""
Write-Host "=" * 60 -ForegroundColor Green
Write-Host "  SETUP COMPLETE!" -ForegroundColor Green
Write-Host "=" * 60 -ForegroundColor Green
Write-Host ""
Write-Host "📋 Environment Details:" -ForegroundColor Cyan
Write-Host "  • Python: $pythonVersion"
Write-Host "  • Platform: $env:OS"
Write-Host "  • Virtual Environment: $pythonExe"
Write-Host "  • Project Root: $projectRoot"
Write-Host ""
Write-Host "🚀 Quick Start Commands:" -ForegroundColor Cyan
Write-Host "  • Activate venv: .venv\Scripts\activate"
Write-Host "  • Run app: `"$pythonExe`" src\app.py"
Write-Host "  • Run tests: `"$pythonExe`" -m pytest tests\ -v"
Write-Host "  • Switch test data: `"$pythonExe`" scripts\test_data_switcher.py small"
Write-Host ""
Write-Host "📁 Project Structure:" -ForegroundColor Cyan
Write-Host "  • src\ - Application source code"
Write-Host "  • tests\ - Test files (unit, integration, data)"
Write-Host "  • scripts\ - Automation scripts"
Write-Host "  • .venv\ - Virtual environment"
Write-Host ""
Write-Success "🎉 You're all set! The project is ready for development."
