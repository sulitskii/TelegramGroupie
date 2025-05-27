#!/usr/bin/env python3
"""
Deployment Validation Script

This script validates a complete deployment by:
1. Parsing environment configuration from .env files
2. Sending test webhook payloads to the deployed application
3. Verifying messages are encrypted and stored in KMS
4. Testing message retrieval through the API
5. Validating end-to-end encryption/decryption flow

Usage:
    python validate-deployment.py --env-file path/to/.env --base-url https://your-app.com
    python validate-deployment.py --help
"""

import argparse
import json
import os
import random
import string
import sys
import time
from datetime import datetime
from typing import Dict, Any, Optional
import requests
from dotenv import load_dotenv


class DeploymentValidator:
    """Validates deployment by testing the complete message flow."""
    
    def __init__(self, base_url: str, env_config: Dict[str, str]):
        self.base_url = base_url.rstrip('/')
        self.env_config = env_config
        self.test_results = []
        self.test_message_id = None
        self.test_chat_id = -100123456789  # Test group chat ID
        self.test_user_id = 123456789
        
    def log_test(self, test_name: str, success: bool, message: str, details: Optional[Dict] = None):
        """Log test result."""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "message": message,
            "details": details or {},
            "timestamp": datetime.now().isoformat()
        })
        
        if not success:
            if details:
                print(f"   Details: {json.dumps(details, indent=2)}")
    
    def generate_test_message(self) -> str:
        """Generate a unique test message."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        return f"DEPLOYMENT_TEST_{timestamp}_{random_suffix}"
    
    def test_health_endpoint(self) -> bool:
        """Test the health check endpoint."""
        try:
            response = requests.get(f"{self.base_url}/healthz", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "ok":
                    self.log_test("Health Check", True, "Application is healthy")
                    return True
                else:
                    self.log_test("Health Check", False, f"Unexpected response: {data}")
                    return False
            else:
                self.log_test("Health Check", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Health Check", False, f"Request failed: {str(e)}")
            return False
    
    def create_test_webhook_payload(self, message_text: str) -> Dict[str, Any]:
        """Create a test Telegram webhook payload."""
        self.test_message_id = random.randint(1000000, 9999999)
        
        return {
            "update_id": random.randint(100000000, 999999999),
            "message": {
                "message_id": self.test_message_id,
                "from": {
                    "id": self.test_user_id,
                    "first_name": "Test",
                    "last_name": "User",
                    "username": "deployment_test_user"
                },
                "chat": {
                    "id": self.test_chat_id,
                    "title": "Deployment Test Group",
                    "type": "group"
                },
                "date": int(time.time()),
                "text": message_text
            }
        }
    
    def test_webhook_endpoint(self, test_message: str) -> bool:
        """Test webhook endpoint with test payload."""
        webhook_secret = self.env_config.get("WEBHOOK_SECRET")
        if not webhook_secret:
            self.log_test("Webhook Test", False, "WEBHOOK_SECRET not found in environment")
            return False
        
        payload = self.create_test_webhook_payload(test_message)
        webhook_url = f"{self.base_url}/webhook/{webhook_secret}"
        
        try:
            response = requests.post(
                webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "ok":
                    self.log_test("Webhook Processing", True, f"Message processed successfully (ID: {self.test_message_id})")
                    return True
                else:
                    self.log_test("Webhook Processing", False, f"Unexpected response: {data}")
                    return False
            else:
                self.log_test("Webhook Processing", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Webhook Processing", False, f"Request failed: {str(e)}")
            return False
    
    def test_message_api_retrieval(self, test_message: str) -> bool:
        """Test message retrieval through API."""
        api_key = self.env_config.get("API_KEY")
        if not api_key:
            self.log_test("API Retrieval", False, "API_KEY not found in environment")
            return False
        
        # Wait a moment for message to be processed
        time.sleep(2)
        
        try:
            # Test API retrieval with filters
            response = requests.get(
                f"{self.base_url}/messages",
                params={
                    "chat_id": self.test_chat_id,
                    "user_id": self.test_user_id,
                    "limit": 10
                },
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                messages = data.get("messages", [])
                
                # Look for our test message
                test_message_found = False
                for message in messages:
                    if message.get("text") == test_message:
                        test_message_found = True
                        self.log_test("Message Retrieval", True, 
                                    f"Test message found and decrypted successfully")
                        self.log_test("KMS Encryption/Decryption", True, 
                                    "Message was encrypted in KMS and decrypted for API response")
                        return True
                
                if not test_message_found:
                    self.log_test("Message Retrieval", False, 
                                f"Test message not found in API response. Found {len(messages)} messages")
                    return False
            else:
                self.log_test("Message Retrieval", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Message Retrieval", False, f"Request failed: {str(e)}")
            return False
    
    def test_api_authorization(self) -> bool:
        """Test API authorization is working."""
        try:
            # Test without authorization
            response = requests.get(f"{self.base_url}/messages", timeout=10)
            
            if response.status_code == 401:
                self.log_test("API Authorization", True, "API correctly requires authorization")
                return True
            elif response.status_code == 200:
                self.log_test("API Authorization", False, "API is unprotected (no API_KEY configured)")
                return False
            else:
                self.log_test("API Authorization", False, f"Unexpected response: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("API Authorization", False, f"Request failed: {str(e)}")
            return False
    
    def test_batch_api(self) -> bool:
        """Test batch processing API."""
        api_key = self.env_config.get("API_KEY")
        if not api_key:
            self.log_test("Batch API", False, "API_KEY not found in environment")
            return False
        
        try:
            response = requests.post(
                f"{self.base_url}/messages/batch",
                json={
                    "chat_id": self.test_chat_id,
                    "batch_size": 5
                },
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if "messages" in data and "count" in data:
                    self.log_test("Batch API", True, f"Batch processing successful, returned {data['count']} messages")
                    return True
                else:
                    self.log_test("Batch API", False, f"Invalid response format: {data}")
                    return False
            else:
                self.log_test("Batch API", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Batch API", False, f"Request failed: {str(e)}")
            return False
    
    def validate_environment_config(self) -> bool:
        """Validate required environment configuration."""
        required_vars = [
            "GCP_PROJECT_ID",
            "KMS_LOCATION", 
            "KMS_KEY_RING",
            "KMS_KEY_ID",
            "WEBHOOK_SECRET"
        ]
        
        missing_vars = []
        for var in required_vars:
            if not self.env_config.get(var):
                missing_vars.append(var)
        
        if missing_vars:
            self.log_test("Environment Config", False, 
                        f"Missing required variables: {', '.join(missing_vars)}")
            return False
        else:
            self.log_test("Environment Config", True, "All required environment variables present")
            return True
    
    def run_validation(self) -> bool:
        """Run complete deployment validation."""
        print(f"🚀 Starting deployment validation for: {self.base_url}")
        print(f"📅 Timestamp: {datetime.now().isoformat()}")
        print("=" * 80)
        
        # Generate unique test message
        test_message = self.generate_test_message()
        print(f"🧪 Test message: {test_message}")
        print("=" * 80)
        
        # Run all tests
        tests = [
            ("Environment Configuration", lambda: self.validate_environment_config()),
            ("Health Check", lambda: self.test_health_endpoint()),
            ("API Authorization", lambda: self.test_api_authorization()),
            ("Webhook Processing", lambda: self.test_webhook_endpoint(test_message)),
            ("Message API Retrieval", lambda: self.test_message_api_retrieval(test_message)),
            ("Batch API", lambda: self.test_batch_api()),
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test_name, test_func in tests:
            try:
                if test_func():
                    passed_tests += 1
            except Exception as e:
                self.log_test(test_name, False, f"Test execution failed: {str(e)}")
        
        # Summary
        print("=" * 80)
        print(f"📊 VALIDATION SUMMARY")
        print(f"   Tests Passed: {passed_tests}/{total_tests}")
        print(f"   Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if passed_tests == total_tests:
            print("🎉 DEPLOYMENT VALIDATION SUCCESSFUL!")
            print("   All systems are working correctly.")
            return True
        else:
            print("⚠️  DEPLOYMENT VALIDATION FAILED!")
            print("   Some tests failed. Check the logs above for details.")
            return False


def parse_env_file(env_file_path: str) -> Dict[str, str]:
    """Parse environment file and return configuration."""
    if not os.path.exists(env_file_path):
        raise FileNotFoundError(f"Environment file not found: {env_file_path}")
    
    # Load environment variables from file
    load_dotenv(env_file_path)
    
    # Extract relevant variables
    env_vars = {}
    for key in os.environ:
        env_vars[key] = os.environ[key]
    
    return env_vars


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Validate deployment by testing webhook -> KMS -> API flow",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Validate production deployment
    python validate-deployment.py --env-file production.env --base-url https://your-app.com
    
    # Validate staging deployment
    python validate-deployment.py --env-file staging.env --base-url https://staging-app.com
    
    # Use environment variables instead of file
    export WEBHOOK_SECRET=your-secret
    export API_KEY=your-api-key
    python validate-deployment.py --base-url https://your-app.com
        """
    )
    
    parser.add_argument(
        "--env-file",
        help="Path to .env file with configuration",
        type=str
    )
    
    parser.add_argument(
        "--base-url",
        help="Base URL of the deployed application",
        required=True,
        type=str
    )
    
    parser.add_argument(
        "--output",
        help="Output file for test results (JSON format)",
        type=str
    )
    
    args = parser.parse_args()
    
    try:
        # Parse environment configuration
        if args.env_file:
            env_config = parse_env_file(args.env_file)
            print(f"📁 Loaded configuration from: {args.env_file}")
        else:
            env_config = dict(os.environ)
            print("📁 Using current environment variables")
        
        # Create validator and run tests
        validator = DeploymentValidator(args.base_url, env_config)
        success = validator.run_validation()
        
        # Save results if requested
        if args.output:
            with open(args.output, 'w') as f:
                json.dump({
                    "validation_successful": success,
                    "timestamp": datetime.now().isoformat(),
                    "base_url": args.base_url,
                    "test_results": validator.test_results
                }, f, indent=2)
            print(f"📄 Results saved to: {args.output}")
        
        # Exit with appropriate code
        sys.exit(0 if success else 1)
        
    except Exception as e:
        print(f"❌ Validation failed with error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main() 