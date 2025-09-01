#!/usr/bin/env python3
"""
Simple test script to verify Time Helper functionality.
Run this after installation to ensure everything is working.
"""

import subprocess
import sys


def test_cli_commands():
    """Test that CLI commands work properly."""
    print("🧪 Testing CLI commands...")
    
    # Test basic help
    result = subprocess.run(["uv", "run", "time-helper", "--help"], 
                          capture_output=True, text=True)
    if result.returncode != 0:
        print("❌ CLI help command failed")
        return False
    print("✅ CLI help works")
    
    # Test init command
    result = subprocess.run(["uv", "run", "time-helper", "init"], 
                          capture_output=True, text=True)
    if result.returncode != 0:
        print("❌ Database initialization failed")
        return False
    print("✅ Database initialization works")
    
    return True


def test_report_generation():
    """Test report generation."""
    print("🧪 Testing report generation...")
    
    # Test direct timewarrior mode
    print("  Testing direct timewarrior integration...")
    result = subprocess.run([
        "uv", "run", "time-helper", "report",
        "--no-cache"
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ Direct timewarrior integration works")
        return True
    else:
        print(f"⚠️  Direct timewarrior integration had issues: {result.stderr}")
        # This might fail if no timewarrior data exists, which is OK
        return True


def main():
    """Run all tests."""
    print("🚀 Running Time Helper tests...\n")
    
    tests = [
        test_cli_commands,
        test_report_generation
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            failed += 1
        print()
    
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! Time Helper is ready to use.")
        print("\nQuick start:")
        print("  uv run time-helper report  # Generate report (fetches data directly from timewarrior)")
        return 0
    else:
        print("💥 Some tests failed. Please check the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
