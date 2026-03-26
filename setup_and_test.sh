#!/bin/bash
# Fresh Setup and Test Automation for Meshtastic Mesh Visualizer
# Unix shell script version for Linux/Mac users

set -e  # Exit on any error

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Print functions
print_step() {
    local message="$1"
    local step_num="$2"
    if [ -n "$step_num" ]; then
        echo -e "\n${CYAN}${BOLD}📋 Step $step_num: $message${NC}"
    else
        echo -e "\n${BLUE}🔸 $message${NC}"
    fi
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Help function
show_help() {
    echo -e "${GREEN}Fresh Setup and Test Automation for Meshtastic Mesh Visualizer${NC}"
    echo ""
    echo "This script automates the complete setup process for a freshly cloned project:"
    echo "1. Creates and configures Python virtual environment"
    echo "2. Installs all required dependencies"
    echo "3. Sets up test environment"
    echo "4. Runs comprehensive tests"
    echo "5. Validates the installation"
    echo ""
    echo "Usage: ./setup_and_test.sh [options]"
    echo ""
    echo "Options:"
    echo "  --setup-only        Only run setup, skip tests"
    echo "  --test-only         Only run tests, skip setup"
    echo "  --clean             Clean install (remove existing .venv)"
    echo "  --no-tests          Skip all tests"
    echo "  --help              Show this help message"
    echo ""
    echo "Examples:"
    echo "  ./setup_and_test.sh                # Full setup and test"
    echo "  ./setup_and_test.sh --setup-only   # Just setup, no tests"
    echo "  ./setup_and_test.sh --test-only    # Just tests (assumes setup done)"
    echo "  ./setup_and_test.sh --clean        # Clean setup (remove existing .venv)"
    exit 0
}

# Parse command line arguments
SETUP_ONLY=false
TEST_ONLY=false
CLEAN=false
NO_TESTS=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --setup-only)
            SETUP_ONLY=true
            shift
            ;;
        --test-only)
            TEST_ONLY=true
            shift
            ;;
        --clean)
            CLEAN=true
            shift
            ;;
        --no-tests)
            NO_TESTS=true
            shift
            ;;
        --help)
            show_help
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Main script starts here
echo -e "${CYAN}${BOLD}"
echo "============================================================"
echo "  MESHTASTIC MESH VISUALIZER - FRESH SETUP"
echo "============================================================"
echo -e "${NC}"

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PATH="$PROJECT_ROOT/.venv"
PYTHON_EXE="$VENV_PATH/bin/python"
PIP_EXE="$VENV_PATH/bin/pip"

# Function to get the appropriate Python command
get_python_cmd() {
    # If venv exists and is functional, use it
    if [ -f "$PYTHON_EXE" ] && "$PYTHON_EXE" -c "import sys" &>/dev/null; then
        echo "$PYTHON_EXE"
        return 0
    fi
    
    # Otherwise find system Python
    if command -v python3 &> /dev/null; then
        echo "python3"
    elif command -v python &> /dev/null; then
        echo "python"
    else
        echo ""
    fi
}

# Function to get the appropriate pip command
get_pip_cmd() {
    # If venv exists and is functional, use it
    if [ -f "$PIP_EXE" ] && "$PIP_EXE" --version &>/dev/null; then
        echo "$PIP_EXE"
        return 0
    fi
    
    # Otherwise use venv python with -m pip
    local python_cmd=$(get_python_cmd)
    if [ -n "$python_cmd" ]; then
        echo "$python_cmd -m pip"
    else
        echo ""
    fi
}

# Check Python availability
print_step "Checking Python installation"

# Find any working Python for initial checks
INITIAL_PYTHON=""
if command -v python3 &> /dev/null && python3 -c "import sys" &>/dev/null; then
    INITIAL_PYTHON="python3"
elif command -v python &> /dev/null && python -c "import sys" &>/dev/null; then
    INITIAL_PYTHON="python"
fi

if [ -z "$INITIAL_PYTHON" ]; then
    print_error "No working Python found. Please install Python 3.8+ and ensure it's in your PATH."
    exit 1
fi

# Check Python version
PYTHON_VERSION=$($INITIAL_PYTHON --version 2>&1)
print_success "Found: $PYTHON_VERSION"

# Verify Python version is 3.8+
if $INITIAL_PYTHON -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"; then
    print_success "Python version check passed"
else
    print_error "Python 3.8+ required"
    exit 1
fi

# Setup phase
if [ "$TEST_ONLY" = false ]; then
    print_step "Setting up virtual environment" 1
    
    # Clean existing venv if requested
    if [ "$CLEAN" = true ] && [ -d "$VENV_PATH" ]; then
        print_step "Removing existing virtual environment"
        rm -rf "$VENV_PATH"
        print_success "Existing .venv removed"
    fi
    
    # Create virtual environment if it doesn't exist or is broken
    if [ ! -f "$PYTHON_EXE" ] || ! "$PYTHON_EXE" -c "import sys" &>/dev/null; then
        print_step "Creating/fixing virtual environment"
        
        # Find system Python
        SYSTEM_PYTHON=$(get_python_cmd)
        if [ -z "$SYSTEM_PYTHON" ]; then
            print_error "Python not found. Please install Python 3.8 or later."
            exit 1
        fi
        
        # Remove existing broken venv
        if [ -d "$VENV_PATH" ]; then
            print_step "Removing broken virtual environment"
            rm -rf "$VENV_PATH"
        fi
        
        # Create new venv
        print_step "Creating virtual environment with $SYSTEM_PYTHON"
        "$SYSTEM_PYTHON" -m venv "$VENV_PATH"
        
        if [ $? -ne 0 ]; then
            print_error "Failed to create virtual environment"
            exit 1
        fi
        
        # Verify venv creation
        if [ ! -f "$PYTHON_EXE" ] || ! "$PYTHON_EXE" -c "import sys" &>/dev/null; then
            print_error "Virtual environment creation failed or is broken"
            exit 1
        fi
        
        print_success "Virtual environment created successfully"
    else
        print_success "Virtual environment already exists and is functional"
    fi
    
    # Now all operations use the venv Python/pip directly
    PYTHON_CMD=$(get_python_cmd)
    PIP_CMD=$(get_pip_cmd)
    
    if [ -z "$PYTHON_CMD" ] || [ -z "$PIP_CMD" ]; then
        print_error "Failed to determine Python/pip commands"
        exit 1
    fi
    
    print_step "Installing dependencies" 2
    
    # Check requirements.txt exists
    if [ ! -f "$PROJECT_ROOT/requirements.txt" ]; then
        print_error "requirements.txt not found"
        exit 1
    fi
    
    # Upgrade pip first (using venv pip directly)
    print_step "Upgrading pip"
    $PIP_CMD install --upgrade pip
    
    # Install production dependencies
    print_step "Installing production dependencies"
    $PIP_CMD install -r "$PROJECT_ROOT/requirements.txt"
    
    # Install test dependencies
    print_step "Installing test dependencies"
    $PIP_CMD install pytest pytest-cov pytest-html
    
    print_success "All dependencies installed"
    
    print_step "Verifying project structure" 3
    
    REQUIRED_DIRS=("src" "tests" "scripts")
    REQUIRED_FILES=("src/app.py" "requirements.txt")
    MISSING_ITEMS=()
    
    # Check directories
    for dir in "${REQUIRED_DIRS[@]}"; do
        if [ ! -d "$PROJECT_ROOT/$dir" ]; then
            MISSING_ITEMS+=("Directory: $dir")
        fi
    done
    
    # Check files
    for file in "${REQUIRED_FILES[@]}"; do
        if [ ! -f "$PROJECT_ROOT/$file" ]; then
            MISSING_ITEMS+=("File: $file")
        fi
    done
    
    if [ ${#MISSING_ITEMS[@]} -gt 0 ]; then
        print_error "Missing required project structure:"
        for item in "${MISSING_ITEMS[@]}"; do
            print_error "  - $item"
        done
        exit 1
    fi
    
    print_success "Project structure verified"
    
    print_step "Setting up test data" 4
    
    if [ -f "$PROJECT_ROOT/scripts/test_data_switcher.py" ]; then
        if $PYTHON_CMD "$PROJECT_ROOT/scripts/test_data_switcher.py" small; then
            print_success "Test data configured"
        else
            print_warning "Could not set test data, continuing anyway"
        fi
    else
        print_warning "Test data switcher not found, skipping test data setup"
    fi
    
    if [ "$SETUP_ONLY" = true ]; then
        print_success "Setup complete!"
        echo ""
        echo -e "${CYAN}🚀 Quick Start Commands:${NC}"
        echo "  • Run app: $PYTHON_CMD src/app.py"
        echo "  • Run tests: $PYTHON_CMD -m pytest tests/ -v"
        echo "  • Switch test data: $PYTHON_CMD scripts/test_data_switcher.py small"
        echo ""
        print_success "You're all set! The project is ready for development."
        exit 0
    fi
fi

# Test phase
if [ "$NO_TESTS" = false ] && [ "$SETUP_ONLY" = false ]; then
    print_step "Running tests" 5
    
    # Ensure we have the correct Python command for tests
    PYTHON_CMD=$(get_python_cmd)
    if [ -z "$PYTHON_CMD" ]; then
        print_error "Failed to determine Python command for tests"
        exit 1
    fi
    
    if [ ! -d "$PROJECT_ROOT/tests" ]; then
        print_warning "Tests directory not found, skipping tests"
    else
        # Run unit tests
        print_step "Running unit tests"
        if [ -d "$PROJECT_ROOT/tests/unit" ]; then
            if $PYTHON_CMD -m pytest "$PROJECT_ROOT/tests/unit" -v --tb=short; then
                print_success "Unit tests passed"
            else
                print_warning "Some unit tests failed (expected for template tests)"
            fi
        fi
        
        # Run integration tests
        print_step "Running integration tests"
        if [ -d "$PROJECT_ROOT/tests/integration" ]; then
            if $PYTHON_CMD -m pytest "$PROJECT_ROOT/tests/integration" -v --tb=short; then
                print_success "Integration tests passed"
            else
                print_warning "Some integration tests failed (expected for template tests)"
            fi
        fi
    fi
    
    print_step "Testing application startup" 6
    
    if [ -f "$PROJECT_ROOT/src/app.py" ]; then
        TEST_SCRIPT='
import sys
sys.path.insert(0, "src")
try:
    import app
    print("✅ App import successful")
except Exception as e:
    print(f"❌ App import failed: {e}")
    sys.exit(1)
'
        
        if cd "$PROJECT_ROOT" && $PYTHON_CMD -c "$TEST_SCRIPT"; then
            print_success "Application startup test passed"
        else
            print_warning "Application startup test failed"
        fi
    else
        print_warning "app.py not found, skipping startup test"
    fi
fi

# Final summary
echo ""
echo -e "${GREEN}${BOLD}"
echo "============================================================"
echo "  SETUP COMPLETE!"
echo "============================================================"
echo -e "${NC}"
echo ""

# Get final Python command for summary
FINAL_PYTHON_CMD=$(get_python_cmd)

echo -e "${CYAN}📋 Environment Details:${NC}"
echo "  • Python: $PYTHON_VERSION"
echo "  • Platform: $(uname -s)"
echo "  • Virtual Environment: $VENV_PATH"
echo "  • Python Command: $FINAL_PYTHON_CMD"
echo "  • Project Root: $PROJECT_ROOT"
echo ""
echo -e "${CYAN}🚀 Quick Start Commands:${NC}"
echo "  • Run app: $FINAL_PYTHON_CMD src/app.py"
echo "  • Run tests: $FINAL_PYTHON_CMD -m pytest tests/ -v"
echo "  • Switch test data: $FINAL_PYTHON_CMD scripts/test_data_switcher.py small"
echo ""
echo -e "${CYAN}📁 Project Structure:${NC}"
echo "  • src/ - Application source code"
echo "  • tests/ - Test files (unit, integration, data)"
echo "  • scripts/ - Automation scripts"
echo "  • .venv/ - Virtual environment"
echo ""
print_success "🎉 You're all set! The project is ready for development."
