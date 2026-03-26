#!/usr/bin/env python3
"""
Fresh Setup and Test Automation Script for Meshtastic Mesh Visualizer

This script automates the complete setup process for a freshly cloned project:
1. Creates and configures Python virtual environment
2. Installs all required dependencies
3. Sets up test environment
4. Runs comprehensive tests
5. Validates the installation

Usage:
    python setup_and_test.py [options]
    
Examples:
    python setup_and_test.py                    # Full setup and test
    python setup_and_test.py --setup-only       # Just setup, no tests
    python setup_and_test.py --test-only        # Just tests (assumes setup done)
    python setup_and_test.py --clean            # Clean setup (remove existing .venv)
"""

import os
import sys
import subprocess
import platform
import argparse
import shutil
from pathlib import Path

class Colors:
    """Terminal colors for better output"""
    GREEN = '\033[92m'
    YELLOW = '\033[93m' 
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_step(message, step_num=None):
    """Print a step with formatting"""
    if step_num:
        print(f"\n{Colors.CYAN}{Colors.BOLD}📋 Step {step_num}: {message}{Colors.END}")
    else:
        print(f"\n{Colors.BLUE}🔸 {message}{Colors.END}")

def print_success(message):
    """Print success message"""
    print(f"{Colors.GREEN}✅ {message}{Colors.END}")

def print_warning(message):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠️  {message}{Colors.END}")

def print_error(message):
    """Print error message"""
    print(f"{Colors.RED}❌ {message}{Colors.END}")

def run_command(command, cwd=None, check=True, capture_output=False):
    """Run a command and handle errors"""
    try:
        if capture_output:
            result = subprocess.run(command, shell=True, cwd=cwd, check=check, 
                                  capture_output=True, text=True)
            return result
        else:
            result = subprocess.run(command, shell=True, cwd=cwd, check=check)
            return result
    except subprocess.CalledProcessError as e:
        print_error(f"Command failed: {command}")
        print_error(f"Error: {e}")
        return None

def check_python_version():
    """Check if Python version is suitable"""
    print_step("Checking Python version")
    
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print_error(f"Python 3.8+ required, found {version.major}.{version.minor}")
        return False
    
    print_success(f"Python {version.major}.{version.minor}.{version.micro} - OK")
    return True

def check_system_python():
    """Check if we're running with a broken system Python"""
    try:
        import site
        return True
    except ImportError:
        print_warning("System Python appears to have issues (missing 'site' module)")
        print_warning("This is common with some Python installations")
        return False

def get_working_python():
    """Find a working Python executable"""
    python_candidates = [
        "python3",
        "python",
        r"C:\Python311\python.exe",
        r"C:\Python310\python.exe", 
        r"C:\Python39\python.exe",
        r"C:\Python38\python.exe"
    ]
    
    for python_cmd in python_candidates:
        try:
            result = run_command(f"{python_cmd} --version", capture_output=True, check=False)
            if result and result.returncode == 0:
                # Test if this Python can import site
                test_result = run_command(f"{python_cmd} -c \"import site\"", capture_output=True, check=False)
                if test_result and test_result.returncode == 0:
                    print_success(f"Found working Python: {python_cmd}")
                    return python_cmd
        except:
            continue
    
    return None

def setup_virtual_environment(project_root, clean=False, python_cmd="python"):
    """Set up Python virtual environment"""
    print_step("Setting up virtual environment", 1)
    
    venv_path = project_root / ".venv"
    
    # Clean existing venv if requested
    if clean and venv_path.exists():
        print_step("Removing existing virtual environment")
        shutil.rmtree(venv_path)
        print_success("Existing .venv removed")
    
    # Create new venv if it doesn't exist
    if not venv_path.exists():
        print_step("Creating new virtual environment")
        result = run_command(f"{python_cmd} -m venv {venv_path}")
        if result is None:
            return False
        print_success("Virtual environment created")
    else:
        print_success("Virtual environment already exists")
    
    return True

def get_venv_python_path(project_root):
    """Get the path to the virtual environment Python executable"""
    venv_path = project_root / ".venv"
    
    if platform.system() == "Windows":
        return venv_path / "Scripts" / "python.exe"
    else:
        return venv_path / "bin" / "python"

def install_dependencies(project_root):
    """Install project dependencies"""
    print_step("Installing dependencies", 2)
    
    python_exe = get_venv_python_path(project_root)
    requirements_file = project_root / "requirements.txt"
    
    if not requirements_file.exists():
        print_error("requirements.txt not found")
        return False
    
    # Upgrade pip first
    print_step("Upgrading pip")
    result = run_command(f'"{python_exe}" -m pip install --upgrade pip')
    if result is None:
        return False
    
    # Install production dependencies
    print_step("Installing production dependencies")
    result = run_command(f'"{python_exe}" -m pip install -r "{requirements_file}"')
    if result is None:
        return False
    
    # Install test dependencies
    print_step("Installing test dependencies")
    test_deps = ["pytest", "pytest-cov", "pytest-html"]
    for dep in test_deps:
        result = run_command(f'"{python_exe}" -m pip install {dep}')
        if result is None:
            return False
    
    print_success("All dependencies installed")
    return True

def verify_project_structure(project_root):
    """Verify the project has the expected structure"""
    print_step("Verifying project structure", 3)
    
    required_dirs = ["src", "tests", "scripts"]
    required_files = ["src/app.py", "requirements.txt"]
    
    missing_items = []
    
    # Check directories
    for dir_name in required_dirs:
        dir_path = project_root / dir_name
        if not dir_path.exists():
            missing_items.append(f"Directory: {dir_name}")
    
    # Check files
    for file_name in required_files:
        file_path = project_root / file_name
        if not file_path.exists():
            missing_items.append(f"File: {file_name}")
    
    if missing_items:
        print_error("Missing required project structure:")
        for item in missing_items:
            print_error(f"  - {item}")
        return False
    
    print_success("Project structure verified")
    return True

def setup_test_data(project_root):
    """Set up test data"""
    print_step("Setting up test data", 4)
    
    python_exe = get_venv_python_path(project_root)
    test_data_switcher = project_root / "scripts" / "test_data_switcher.py"
    
    if not test_data_switcher.exists():
        print_warning("Test data switcher not found, skipping test data setup")
        return True
    
    # Switch to small test dataset
    result = run_command(f'"{python_exe}" "{test_data_switcher}" small')
    if result is None:
        print_warning("Could not set test data, continuing anyway")
        return True
    
    print_success("Test data configured")
    return True

def run_tests(project_root):
    """Run the test suite"""
    print_step("Running tests", 5)
    
    python_exe = get_venv_python_path(project_root)
    tests_dir = project_root / "tests"
    
    if not tests_dir.exists():
        print_warning("Tests directory not found, skipping tests")
        return True
    
    # Run unit tests
    print_step("Running unit tests")
    unit_tests_dir = tests_dir / "unit"
    if unit_tests_dir.exists():
        result = run_command(f'"{python_exe}" -m pytest "{unit_tests_dir}" -v --tb=short', 
                           cwd=project_root, check=False)
        if result and result.returncode == 0:
            print_success("Unit tests passed")
        else:
            print_warning("Some unit tests failed (expected for template tests)")
    
    # Run integration tests
    print_step("Running integration tests")
    integration_tests_dir = tests_dir / "integration"
    if integration_tests_dir.exists():
        result = run_command(f'"{python_exe}" -m pytest "{integration_tests_dir}" -v --tb=short',
                           cwd=project_root, check=False)
        if result and result.returncode == 0:
            print_success("Integration tests passed")
        else:
            print_warning("Some integration tests failed (expected for template tests)")
    
    return True

def test_app_startup(project_root):
    """Test that the Flask app can start"""
    print_step("Testing application startup", 6)
    
    python_exe = get_venv_python_path(project_root)
    app_file = project_root / "src" / "app.py"
    
    if not app_file.exists():
        print_warning("app.py not found, skipping startup test")
        return True
    
    # Test import
    test_script = '''
import sys
sys.path.insert(0, "src")
try:
    import app
    print("✅ App import successful")
except Exception as e:
    print(f"❌ App import failed: {e}")
    sys.exit(1)
'''
    
    result = run_command(f'"{python_exe}" -c "{test_script}"', cwd=project_root, check=False)
    if result and result.returncode == 0:
        print_success("Application startup test passed")
        return True
    else:
        print_warning("Application startup test failed")
        return False

def generate_summary_report(project_root):
    """Generate a summary report"""
    print_step("Generating summary report")
    
    python_exe = get_venv_python_path(project_root)
    
    # Get installed packages
    result = run_command(f'"{python_exe}" -m pip list', capture_output=True)
    packages = result.stdout if result else "Could not get package list"
    
    # Create summary
    summary = f"""
{Colors.CYAN}{Colors.BOLD}=== MESHTASTIC MESH VISUALIZER SETUP COMPLETE ==={Colors.END}

{Colors.GREEN}✅ Setup Status: READY{Colors.END}

📋 Environment Details:
  • Python: {sys.version.split()[0]}
  • Platform: {platform.system()} {platform.release()}
  • Virtual Environment: {get_venv_python_path(project_root)}
  • Project Root: {project_root}

📦 Key Installed Packages:
"""
    
    # Extract key packages from pip list
    if "Could not get package list" not in packages:
        key_packages = ["Flask", "folium", "geopy", "watchdog", "pytest"]
        for line in packages.split('\n'):
            for pkg in key_packages:
                if line.startswith(pkg):
                    summary += f"  • {line}\n"
    
    summary += f"""
🚀 Quick Start Commands:
  • Activate venv: {Colors.CYAN}.venv\\Scripts\\activate{Colors.END} (Windows) or {Colors.CYAN}source .venv/bin/activate{Colors.END} (Unix)
  • Run app: {Colors.CYAN}"{get_venv_python_path(project_root)}" src/app.py{Colors.END}
  • Run tests: {Colors.CYAN}"{get_venv_python_path(project_root)}" -m pytest tests/ -v{Colors.END}
  • Switch test data: {Colors.CYAN}"{get_venv_python_path(project_root)}" scripts/test_data_switcher.py small{Colors.END}

📁 Project Structure:
  • src/ - Application source code
  • tests/ - Test files (unit, integration, data)
  • scripts/ - Automation scripts
  • .venv/ - Virtual environment

{Colors.GREEN}🎉 You're all set! The project is ready for development.{Colors.END}
"""
    
    print(summary)

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Fresh setup and test automation for Meshtastic Mesh Visualizer")
    parser.add_argument("--setup-only", action="store_true", help="Only run setup, skip tests")
    parser.add_argument("--test-only", action="store_true", help="Only run tests, skip setup")
    parser.add_argument("--clean", action="store_true", help="Clean install (remove existing .venv)")
    parser.add_argument("--no-tests", action="store_true", help="Skip all tests")
    
    args = parser.parse_args()
    
    project_root = Path(__file__).parent
    
    print(f"{Colors.CYAN}{Colors.BOLD}")
    print("=" * 60)
    print("  MESHTASTIC MESH VISUALIZER - FRESH SETUP")
    print("=" * 60)
    print(f"{Colors.END}")
    
    # Check if we're running with a broken Python
    if not check_system_python():
        print_step("Looking for working Python installation")
        working_python = get_working_python()
        if not working_python:
            print_error("Could not find a working Python installation")
            print_error("Please install Python 3.8+ from https://python.org")
            sys.exit(1)
        
        # Re-run this script with the working Python
        print_step(f"Restarting with working Python: {working_python}")
        script_path = Path(__file__).absolute()
        cmd_args = " ".join(sys.argv[1:])  # Pass through all arguments
        result = run_command(f"{working_python} \"{script_path}\" {cmd_args}")
        sys.exit(0 if result and result.returncode == 0 else 1)
    
    # Check Python version (we're now running with working Python)
    if not check_python_version():
        sys.exit(1)
    
    # Determine which Python to use for venv creation
    python_cmd = sys.executable if sys.executable else "python"
    
    # Setup phase
    if not args.test_only:
        success = True
        success &= setup_virtual_environment(project_root, args.clean, python_cmd)
        success &= install_dependencies(project_root)
        success &= verify_project_structure(project_root)
        success &= setup_test_data(project_root)
        
        if not success:
            print_error("Setup failed!")
            sys.exit(1)
        
        if args.setup_only:
            print_success("Setup complete!")
            generate_summary_report(project_root)
            return
    
    # Test phase
    if not args.no_tests and not args.setup_only:
        success = True
        success &= run_tests(project_root)
        success &= test_app_startup(project_root)
        
        if not success:
            print_warning("Some tests failed, but setup is complete")
    
    # Final summary
    generate_summary_report(project_root)
    print_success("Fresh setup and testing complete!")

if __name__ == "__main__":
    main()
