#!/usr/bin/env python3
"""
Debug script to help identify issues in GitHub Actions CI environment.
"""

import os
import sys
import traceback

print("🔍 CI Environment Debug Information")
print("=" * 50)

# Check Python version
print(f"Python version: {sys.version}")
print(f"Python executable: {sys.executable}")

# Check environment variables
print(f"\nTESTING env var: {os.environ.get('TESTING', 'NOT SET')}")
print(f"PYTHONPATH: {os.environ.get('PYTHONPATH', 'NOT SET')}")
print(f"Current working directory: {os.getcwd()}")

# Check Python path
print(f"\nPython sys.path:")
for i, path in enumerate(sys.path):
    print(f"  {i}: {path}")

# Try to import main modules
print(f"\n🧪 Testing imports...")

try:
    print("Importing sys modules mock...")
    sys.modules["telegram"] = None
    sys.modules["telegram.ext"] = None
    print("✅ Telegram mocks set")
except Exception as e:
    print(f"❌ Error setting telegram mocks: {e}")

try:
    print("Testing main.py import...")
    import main
    print("✅ main.py imported successfully")
except Exception as e:
    print(f"❌ Error importing main.py: {e}")
    traceback.print_exc()

try:
    print("Testing pytest import...")
    import pytest
    print(f"✅ pytest version: {pytest.__version__}")
except Exception as e:
    print(f"❌ Error importing pytest: {e}")

# Check if we can run a simple pytest command
try:
    print("\n🧪 Testing pytest execution...")
    import subprocess
    result = subprocess.run([
        sys.executable, "-m", "pytest", "--version"
    ], capture_output=True, text=True, timeout=10)
    
    if result.returncode == 0:
        print(f"✅ pytest --version: {result.stdout.strip()}")
    else:
        print(f"❌ pytest --version failed: {result.stderr}")
        
except Exception as e:
    print(f"❌ Error running pytest --version: {e}")

# Test pytest markers
try:
    print("\n🏷️ Testing pytest markers...")
    result = subprocess.run([
        sys.executable, "-m", "pytest", "--markers"
    ], capture_output=True, text=True, timeout=10)
    
    if result.returncode == 0:
        print("✅ pytest markers command succeeded")
        markers_output = result.stdout
        if "unit:" in markers_output:
            print("✅ 'unit' marker found")
        else:
            print("❌ 'unit' marker NOT found")
            print(f"Markers output: {markers_output}")
    else:
        print(f"❌ pytest --markers failed: {result.stderr}")
        
except Exception as e:
    print(f"❌ Error running pytest --markers: {e}")

print("\n🎯 Debug complete!") 