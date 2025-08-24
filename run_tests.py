#!/usr/bin/env python3
"""
Simple test runner for Chess Analysis AI.

This script runs the unit tests and provides a summary.
"""

import sys
import subprocess
import os
from pathlib import Path

def run_tests():
    """Run the test suite."""
    
    print("Chess Analysis AI - Test Runner")
    print("=" * 50)
    
    # Check if pytest is available
    try:
        import pytest
        print(f"✓ pytest {pytest.__version__} found")
    except ImportError:
        print("✗ pytest not found. Installing...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pytest"])
            print("✓ pytest installed successfully")
        except subprocess.CalledProcessError:
            print("✗ Failed to install pytest")
            return False
    
    # Run tests
    print("\nRunning tests...")
    print("-" * 50)
    
    try:
        # Run tests with coverage
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "tests/", 
            "-v", 
            "--tb=short"
        ], capture_output=True, text=True)
        
        # Print test output
        if result.stdout:
            print(result.stdout)
        
        if result.stderr:
            print("Errors/Warnings:")
            print(result.stderr)
        
        # Check result
        if result.returncode == 0:
            print("\n" + "=" * 50)
            print("✓ All tests passed!")
            return True
        else:
            print("\n" + "=" * 50)
            print("✗ Some tests failed!")
            return False
            
    except Exception as e:
        print(f"✗ Error running tests: {e}")
        return False


def check_imports():
    """Check if all required modules can be imported."""
    
    print("\nChecking imports...")
    print("-" * 50)
    
    required_modules = [
        "chess_analyzer.models",
        "chess_analyzer.engine", 
        "chess_analyzer.evaluator",
        "chess_analyzer.annotator",
        "chess_analyzer.api"
    ]
    
    all_imports_ok = True
    
    for module in required_modules:
        try:
            __import__(module)
            print(f"✓ {module}")
        except ImportError as e:
            print(f"✗ {module}: {e}")
            all_imports_ok = False
    
    return all_imports_ok


def main():
    """Main test runner function."""
    
    # Check imports first
    imports_ok = check_imports()
    
    if not imports_ok:
        print("\n✗ Some modules failed to import. Please check your installation.")
        return False
    
    # Run tests
    tests_ok = run_tests()
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    
    if imports_ok and tests_ok:
        print("✓ All checks passed!")
        print("✓ Ready to use Chess Analysis AI!")
        return True
    else:
        print("✗ Some checks failed!")
        if not imports_ok:
            print("  - Module import issues detected")
        if not tests_ok:
            print("  - Test failures detected")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
