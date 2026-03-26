"""
Test runner script for Meshtastic Mesh Visualizer
"""
import unittest
import sys
from pathlib import Path

# Add src to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))


def run_unit_tests():
    """Run all unit tests"""
    print("Running Unit Tests...")
    print("=" * 50)
    
    # Discover and run unit tests
    loader = unittest.TestLoader()
    start_dir = Path(__file__).parent / "unit"
    suite = loader.discover(str(start_dir), pattern='test_*.py')
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


def run_integration_tests():
    """Run all integration tests"""
    print("\nRunning Integration Tests...")
    print("=" * 50)
    
    # Discover and run integration tests
    loader = unittest.TestLoader()
    start_dir = Path(__file__).parent / "integration"
    suite = loader.discover(str(start_dir), pattern='test_*.py')
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


def run_all_tests():
    """Run all tests"""
    print("Meshtastic Mesh Visualizer Test Suite")
    print("=" * 50)
    
    unit_success = run_unit_tests()
    integration_success = run_integration_tests()
    
    print("\n" + "=" * 50)
    if unit_success and integration_success:
        print("✅ All tests passed!")
        return True
    else:
        print("❌ Some tests failed!")
        return False


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Run tests for Meshtastic Mesh Visualizer')
    parser.add_argument('--unit', action='store_true', help='Run only unit tests')
    parser.add_argument('--integration', action='store_true', help='Run only integration tests')
    
    args = parser.parse_args()
    
    if args.unit:
        success = run_unit_tests()
    elif args.integration:
        success = run_integration_tests()
    else:
        success = run_all_tests()
    
    sys.exit(0 if success else 1)
