#!/usr/bin/env python3
"""
Verification script for the Execution Sandbox Hardening implementation.
This script verifies that all components are properly implemented and can be imported.
"""

import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_imports():
    """Test that all necessary modules can be imported."""
    print("Testing imports...")

    try:
        # Test sandbox executor imports
        from apps.api.app.services.sandbox_executor import (
            SandboxExecutor, SandboxConfig, SecurityLevel,
            NetworkPolicy, ResourceLimits, ExecutionResult
        )
        print("âœ“ Sandbox executor imports successful")
    except Exception as e:
        print(f"âœ— Sandbox executor imports failed: {e}")
        return False

    try:
        # Test test executor imports
        from apps.api.app.services.test_executor import TestExecutor, TestFramework
        print("âœ“ Test executor imports successful")
    except Exception as e:
        print(f"âœ— Test executor imports failed: {e}")
        return False

    try:
        # Test that we can instantiate the main classes
        from apps.api.app.services.sandbox_executor import sandbox_executor
        from apps.api.app.services.test_executor import test_executor
        print("âœ“ Global instances accessible")
    except Exception as e:
        print(f"âœ— Global instances inaccessible: {e}")
        return False

    return True

def test_config_creation():
    """Test that we can create valid configurations."""
    print("\nTesting configuration creation...")

    try:
        from apps.api.app.services.sandbox_executor import (
            SandboxConfig, SecurityLevel, NetworkPolicy, ResourceLimits
        )

        # Test default config
        config = SandboxConfig()
        assert config.security_level == SecurityLevel.STANDARD
        assert config.network_policy == NetworkPolicy.NONE
        print("âœ“ Default configuration creation successful")

        # Test custom config
        custom_config = SandboxConfig(
            security_level=SecurityLevel.MAXIMUM,
            network_policy=NetworkPolicy.RESTRICTED,
            resource_limits=ResourceLimits(
                cpu_cpus=1.5,
                memory_mb=1024,
                max_processes=20
            ),
            max_execution_time=60
        )
        assert custom_config.security_level == SecurityLevel.MAXIMUM
        assert custom_config.network_policy == NetworkPolicy.RESTRICTED
        assert custom_config.resource_limits.cpu_cpus == 1.5
        print("âœ“ Custom configuration creation successful")

        return True
    except Exception as e:
        print(f"âœ— Configuration creation failed: {e}")
        return False

def test_integration_points():
    """Test that integration points are in place."""
    print("\nTesting integration points...")

    try:
        # Check that test_executor uses sandbox_executor
        from apps.api.app.services.test_executor import test_executor
        from apps.api.app.services.sandbox_executor import SandboxExecutor

        assert hasattr(test_executor, 'sandbox')
        assert isinstance(test_executor.sandbox, SandboxExecutor)
        print("âœ“ Test executor properly integrates with sandbox executor")

        return True
    except Exception as e:
        print(f"âœ— Integration point test failed: {e}")
        return False

def main():
    """Run all verification tests."""
    print("Execution Sandbox Hardening Implementation Verification")
    print("=" * 55)

    tests = [
        test_imports,
        test_config_creation,
        test_integration_points,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1
        print()

    print(f"Results: {passed}/{total} test groups passed")

    if passed == total:
        print("ðŸŽ‰ All verification tests passed!")
        print("The Execution Sandbox Hardening system is ready for use.")
        return 0
    else:
        print("âŒ Some verification tests failed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
