#!/usr/bin/env python3
"""
Quick verification script for the Execution Sandbox implementation.
"""

import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_basic_imports():
    """Test that we can at least import the modules."""
    print("Testing basic imports...")

    try:
        from apps.api.app.services import sandbox_executor, test_executor
        print("✓ Services imported successfully")
        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False

def test_class_availability():
    """Test that key classes are available."""
    print("\nTesting class availability...")

    try:
        from apps.api.app.services.sandbox_executor import (
            SandboxConfig, SecurityLevel, NetworkPolicy, ResourceLimits
        )
        from apps.api.app.services.test_executor import TestExecutor, TestFramework

        # Test creating instances
        config = SandboxConfig()
        assert config.security_level == SecurityLevel.STANDARD

        executor = TestExecutor()
        assert hasattr(executor, 'sandbox')

        print("✓ Classes available and instantiable")
        return True
    except Exception as e:
        print(f"✗ Class test failed: {e}")
        return False

def main():
    print("Execution Sandbox Implementation - Basic Verification")
    print("=" * 52)

    tests = [
        test_basic_imports,
        test_class_availability,
    ]

    passed = 0
    for test in tests:
        if test():
            passed += 1

    print(f"\nResults: {passed}/{len(tests)} tests passed")

    if passed == len(tests):
        print("✅ Basic verification passed!")
        return 0
    else:
        print("❌ Basic verification failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())