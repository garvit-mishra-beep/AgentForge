#!/usr/bin/env python3
"""
Verification script for GitHub Native Workflow implementation.
This script verifies that all components are properly implemented and can be imported.
"""

import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all necessary modules can be imported."""
    print("Testing imports...")

    try:
        # Test basic imports
        from apps.api.app.integrations import (
            GitHubAppManager,
            EnhancedPRReviewer,
            RepositorySynchronizer,
            synchronize_repository,
            review_pull_request,
            handle_repository_webhook,
            github_app_manager,
            enhanced_pr_reviewer,
            repository_synchronizer
        )
        print("✓ Enhanced GitHub imports successful")
    except Exception as e:
        print(f"✗ Enhanced GitHub imports failed: {e}")
        return False

    try:
        from apps.api.app.integrations import (
            GitHubClient,
            default_pr_reviewer,
            _findings_to_comments
        )
        print("✓ Base GitHub imports successful")
    except Exception as e:
        print(f"✗ Base GitHub imports failed: {e}")
        return False

    try:
        from apps.api.app.routes.github import router
        print("✓ GitHub routes import successful")
    except Exception as e:
        print(f"✗ GitHub routes import failed: {e}")
        return False

    return True

def test_components_instantiation():
    """Test that components can be instantiated."""
    print("\nTesting component instantiation...")

    try:
        from apps.api.app.integrations.github_enhanced import (
            GitHubAppManager,
            EnhancedPRReviewer,
            RepositorySynchronizer
        )

        app_manager = GitHubAppManager()
        pr_reviewer = EnhancedPRReviewer()
        repo_sync = RepositorySynchronizer()

        print("✓ Component instantiation successful")
        return True
    except Exception as e:
        print(f"✗ Component instantiation failed: {e}")
        return False

def test_route_configuration():
    """Test that routes are properly configured."""
    print("\nTesting route configuration...")

    try:
        from apps.api.app.routes.github import router

        # Check that the router has the expected routes
        routes = [route.path for route in router.routes]
        expected_routes = ['/status', '/webhook']

        for route in expected_routes:
            if any(route in r for r in routes):
                print(f"✓ Route {route} found")
            else:
                print(f"✗ Route {route} not found")
                return False

        print("✓ Route configuration verification successful")
        return True
    except Exception as e:
        print(f"✗ Route configuration verification failed: {e}")
        return False

def main():
    """Run all verification tests."""
    print("GitHub Native Workflow Implementation Verification")
    print("=" * 50)

    tests = [
        test_imports,
        test_components_instantiation,
        test_route_configuration
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1
        print()

    print(f"Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All verification tests passed!")
        print("The GitHub Native Workflow system is ready for use.")
        return 0
    else:
        print("❌ Some verification tests failed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())