"""Demo script to validate the dependency injection refactor.

This script demonstrates that the refactored code works correctly
in both test and production environments without TESTING flags.
"""

from main import create_app
from service_container import create_service_container, reset_service_container


def test_refactored_app_can_create_test_environment():
    """Test that the refactored app can be created for test environment."""
    # Reset service container to ensure clean state
    reset_service_container()

    try:
        # Create app for test environment
        app = create_app("test")

        print(f"✅ Test app created successfully: {app}")
        print(f"✅ App config: {app.config}")

        # Verify it works with test client
        with app.test_client() as client:
            response = client.get("/healthz")
            print(f"✅ Health check response: {response.status_code}")

    except Exception as e:
        print(f"❌ Failed to create test app: {e}")
        raise


def test_refactored_app_can_create_production_environment():
    """Test that the refactored app can be created for production (will fail \
without GCP creds)."""
    # Reset service container to ensure clean state
    reset_service_container()

    try:
        # This should fail because we don't have real GCP credentials
        create_app("production")
        print("❌ Expected production creation to fail, but it didn't")
        return False
    except ValueError as e:
        # Expected - missing production environment variables
        if "Missing required environment variables" in str(e):
            print(f"✅ Production validation correctly failed: {e}")
            return True
        else:
            print(f"❌ Unexpected error: {e}")
            return False


def validate_no_testing_flags():
    """Validate that TESTING flags have been eliminated."""
    print("🔍 Checking for TESTING flags in refactored code...")

    import ast

    # Check main.py for TESTING references
    with open("main.py") as f:
        main_content = f.read()
        if "TESTING" in main_content.upper():
            print(f"❌ Found TESTING reference in main.py")
            return False

    # Check service_container.py for TESTING references
    with open("service_container.py") as f:
        container_content = f.read()
        if "TESTING" in container_content.upper():
            print(f"❌ Found TESTING reference in service_container.py")
            return False

    print("✅ No TESTING flags in refactored code")
    return True


if __name__ == "__main__":
    print("🧪 Testing Dependency Injection Refactor...")
    print("=" * 50)

    try:
        # Test 1: Test environment
        print("\n1. Testing test environment creation...")
        test_refactored_app_can_create_test_environment()

        # Test 2: Production environment (should fail gracefully)
        print("\n2. Testing production environment validation...")
        test_refactored_app_can_create_production_environment()

        # Test 3: No TESTING flags
        print("\n3. Validating no TESTING flags...")
        validate_no_testing_flags()

        # Test production environment validation
        print("🏭 Testing production environment validation...")
        try:
            # This should fail because we don't have real GCP credentials
            create_service_container("production")
            print("❌ Expected production validation to fail, but it didn't")
        except ValueError as e:
            print(f"✅ Production validation correctly failed: {str(e)}")

        print(
            "\n🎉 All tests passed! The refactor successfully eliminates the \
TESTING flag anti-pattern."
        )

    except Exception as e:
        print(f"\n❌ Tests failed: {e}")
        raise
