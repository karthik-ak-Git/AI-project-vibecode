import requests
import sys
import json
from datetime import datetime
import time

class QuickAPITester:
    def __init__(self, base_url="https://admin-agent-portal.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.auth_token = None
        self.test_user_email = f"quicktest_{int(time.time())}@example.com"
        self.test_user_password = "TestPassword123!"

    def run_test(self, name, method, endpoint, expected_status, data=None, timeout=15, auth_required=False):
        """Run a single API test with shorter timeout"""
        url = f"{self.api_url}/{endpoint}" if endpoint else f"{self.api_url}"
        headers = {'Content-Type': 'application/json'}
        
        if auth_required and self.auth_token:
            headers['Authorization'] = f'Bearer {self.auth_token}'

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=timeout)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=timeout)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")

            return success, response.json() if response.text else {}

        except requests.exceptions.Timeout:
            print(f"❌ Failed - Request timed out after {timeout} seconds")
            return False, {}
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_system_health(self):
        """Test system health endpoints"""
        print("📊 System Health Tests")
        print("-" * 30)
        
        # Test system status
        success1, _ = self.run_test("System Status", "GET", "system/status", 200, timeout=10)
        
        # Test root endpoint
        success2, _ = self.run_test("Root Endpoint", "GET", "", 200)
        
        # Test agents endpoint
        success3, response = self.run_test("Get Agents", "GET", "agents", 200)
        if success3 and 'agents' in response:
            print(f"   Found {len(response['agents'])} agents")
        
        return success1 and success2 and success3

    def test_authentication(self):
        """Test authentication system"""
        print("\n🔐 Authentication Tests")
        print("-" * 30)
        
        # Test user registration
        user_data = {
            "email": self.test_user_email,
            "username": f"quicktest_{int(time.time())}",
            "full_name": "Quick Test User",
            "password": self.test_user_password
        }
        
        success1, response = self.run_test("User Registration", "POST", "auth/register", 200, data=user_data)
        if success1 and response.get('success'):
            print(f"   User registered: {response.get('data', {}).get('user_id')}")
        
        # Test user login
        login_data = {
            "email": self.test_user_email,
            "password": self.test_user_password
        }
        
        success2, response = self.run_test("User Login", "POST", "auth/login", 200, data=login_data)
        if success2 and 'access_token' in response:
            self.auth_token = response['access_token']
            print(f"   Token obtained successfully")
        
        # Test protected endpoint
        success3, response = self.run_test("Protected Endpoint", "GET", "auth/me", 200, auth_required=True)
        if success3:
            print(f"   User info retrieved: {response.get('email')}")
        
        return success1 and success2 and success3

    def test_ai_service(self):
        """Test AI service integration"""
        print("\n🤖 AI Service Tests")
        print("-" * 30)
        
        # Test simple AI analysis
        analysis_data = {
            "prompt": "Create a simple todo app",
            "analysis_type": "simple"
        }
        
        success, response = self.run_test(
            "AI Analysis", 
            "POST", 
            "ai/analyze", 
            200, 
            data=analysis_data,
            auth_required=True,
            timeout=30
        )
        
        if success and response.get('success'):
            data = response.get('data', {})
            print(f"   Processing time: {data.get('processing_time', 'N/A')}s")
            print(f"   Model used: {data.get('model_used', 'N/A')}")
        
        return success

    def test_project_management(self):
        """Test project management endpoints"""
        print("\n📁 Project Management Tests")
        print("-" * 30)
        
        # Test get projects
        success1, response = self.run_test("Get Projects", "GET", "projects", 200, auth_required=True)
        if success1:
            print(f"   Found {len(response) if isinstance(response, list) else 0} projects")
        
        # Test invalid project access
        success2, _ = self.run_test("Get Invalid Project", "GET", "projects/invalid_id", 404, auth_required=True)
        
        return success1 and success2

def main():
    print("🚀 Quick Multi-Agent Platform API Test")
    print("=" * 50)
    
    tester = QuickAPITester()
    
    # Run core tests
    health_ok = tester.test_system_health()
    auth_ok = tester.test_authentication()
    ai_ok = tester.test_ai_service()
    project_ok = tester.test_project_management()
    
    # Print results
    print("\n" + "=" * 50)
    print(f"📊 Results: {tester.tests_passed}/{tester.tests_run} tests passed")
    
    core_systems = [
        ("System Health", health_ok),
        ("Authentication", auth_ok),
        ("AI Service", ai_ok),
        ("Project Management", project_ok)
    ]
    
    print("\n🎯 Core System Status:")
    for system, status in core_systems:
        print(f"   {system}: {'✅ Working' if status else '❌ Issues'}")
    
    working_systems = sum(1 for _, status in core_systems if status)
    print(f"\n📈 Core Systems: {working_systems}/4 working")
    
    if working_systems >= 3:
        print("✅ Multi-Agent Platform is functional!")
        return 0
    else:
        print("❌ Platform has significant issues.")
        return 1

if __name__ == "__main__":
    sys.exit(main())