#!/usr/bin/env python3
"""Local Development Runner for TelegramGroupie

This script provides a local development environment for the TelegramGroupie
application with hot-reload capabilities and integrated testing support.
"""

import os
import sys


def load_env_file(env_file_path):
    """Load environment variables from a file."""
    if not os.path.exists(env_file_path):
        print(f"⚠️  Environment file not found: {env_file_path}")
        return False

    with open(env_file_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ[key] = value

    print(f"✅ Loaded environment from: {env_file_path}")
    return True


def setup_development_environment():
    """Setup the development environment."""
    print("🔧 Setting up local development environment...")

    # Try to load .env file first, then fallback to config/local.env
    env_files = [".env", "config/local.env"]
    env_loaded = False

    for env_file in env_files:
        if load_env_file(env_file):
            env_loaded = True
            break

    if not env_loaded:
        print("⚠️  No environment file found. Using default values for testing.")
        # Set default test values
        os.environ.setdefault("FLASK_ENV", "development")
        os.environ.setdefault("FLASK_DEBUG", "True")
        os.environ.setdefault("PORT", "8080")
        os.environ.setdefault("WEBHOOK_SECRET", "test_secret_123")
        os.environ.setdefault("INTEGRATION_TEST_MODE", "true")

    # Set Flask to development mode
    os.environ["FLASK_APP"] = "main.py"
    os.environ["FLASK_ENV"] = "development"

    print("🌟 Environment configured for local development")
    return True


def check_dependencies():
    """Check if required dependencies are installed."""
    print("📦 Checking dependencies...")

    try:
        import flask
        import google.cloud.firestore
        import google.cloud.kms

        print("✅ All dependencies are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Please run: pip install -r requirements.txt")
        return False


def start_firestore_emulator():
    """Start Firestore emulator if available."""
    print("🔥 Checking for Firestore emulator...")

    # Check if gcloud is available
    if os.system("which gcloud > /dev/null 2>&1") == 0:
        print("✅ gcloud CLI found")

        # Check if emulators are available
        if os.system("gcloud beta emulators firestore --help > /dev/null 2>&1") == 0:
            print("🚀 Starting Firestore emulator...")
            print("Run this in a separate terminal:")
            print("gcloud beta emulators firestore start --host-port=localhost:8081")
            print("Then set: export FIRESTORE_EMULATOR_HOST=localhost:8081")
        else:
            print("⚠️  Firestore emulator not available. Install with:")
            print("gcloud components install cloud-firestore-emulator")
    else:
        print(
            "⚠️  gcloud CLI not found. For local Firestore testing, install gcloud SDK"
        )


def run_integration_tests():
    """Run integration tests."""
    print("🧪 Running integration tests...")

    # Set test environment
    os.environ["TESTING"] = "true"
    os.environ["INTEGRATION_TEST_MODE"] = "true"

    # Run pytest with integration test markers, excluding Docker tests
    exit_code = os.system(
        'python -m pytest tests/ -v -m "not requires_auth and not docker" --tb=short'
    )

    if exit_code == 0:
        print("✅ Integration tests passed!")
    else:
        print("❌ Some integration tests failed")

    return exit_code == 0


def start_local_server():
    """Start the local Flask development server."""
    print("🚀 Starting local development server...")
    print(
        f"Server will be available at: http://localhost:{os.environ.get('PORT', '8080')}"
    )
    print("Press Ctrl+C to stop the server")

    # Import and run the Flask app
    try:
        from main import app

        port = int(os.environ.get("PORT", 8080))
        app.run(host="0.0.0.0", port=port, debug=True)
    except KeyboardInterrupt:
        print("\n👋 Server stopped")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        return False

    return True


def main():
    """Main function."""
    print("🚀 TelegramGroupie Local Development Setup")
    print("=" * 50)

    # Parse command line arguments
    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "test":
            setup_development_environment()
            if check_dependencies():
                run_integration_tests()
            return

        if command == "emulator":
            start_firestore_emulator()
            return

        if command == "help":
            print("Available commands:")
            print("  python run_local.py        - Start development server")
            print("  python run_local.py test   - Run integration tests")
            print("  python run_local.py emulator - Show emulator setup instructions")
            print("  python run_local.py help   - Show this help")
            return

    # Default: setup and start server
    if not setup_development_environment():
        sys.exit(1)

    if not check_dependencies():
        sys.exit(1)

    start_firestore_emulator()

    print("\n" + "=" * 50)
    print("🎯 Ready for integration testing!")
    print("💡 Tip: Set up your .env file with real credentials for full testing")
    print("=" * 50 + "\n")

    start_local_server()


if __name__ == "__main__":
    main()
