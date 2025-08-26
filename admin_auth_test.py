#!/usr/bin/env python3
"""
Focused Admin Authentication System Tests
"""
import requests
import json
import sys

class AdminAuthTester:
    def __init__(self, base_url="https://admin-agent-portal.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.admin_token = None
        self.regular_token = None

    def run_test(self, name, method, endpoint, expected_status, data=None, auth_required=False, token_type="admin"):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}" if endpoint else f"{self.api_url}"
        headers = {'Content-Type': 'application/json'}
        
        # Add authorization header if required
        if auth_required:
            if token_type == "admin" and self.admin_token:
                headers['Authorization'] = f'Bearer {self.admin_token}'
            elif token_type == "regular" and self.regular_token:
                headers['Authorization'] = f'Bearer {self.regular_token}'

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        if auth_required:
            token_status = "✅ Token provided" if (token_type == "admin" and self.admin_token) or (token_type == "regular" and self.regular_token) else "❌ No token"
            print(f"   Auth ({token_type}): {token_status}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=30)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    if isinstance(response_data, dict):
                        print(f"   Response keys: {list(response_data.keys())}")
                    return True, response_data
                except:
                    return True, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                print(f"   Response: {response.text[:200]}...")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_admin_login(self):
        """Test admin user login"""
        admin_login_data = {
            "email": "kartik986340@gmail.com",
            "password": "ak-047-ak"
        }
        
        success, response = self.run_test(
            "Admin User Login", 
            "POST", 
            "auth/login", 
            200, 
            data=admin_login_data
        )
        
        if success and 'access_token' in response:
            self.admin_token = response['access_token']
            print(f"   ✅ Admin login successful, token stored")
            print(f"   Token type: {response.get('token_type')}")
        
        return success, response

    def test_admin_user_info(self):
        """Test admin user info retrieval"""
        success, response = self.run_test(
            "Admin User Info (/auth/me)", 
            "GET", 
            "auth/me", 
            200,
            auth_required=True,
            token_type="admin"
        )
        
        if success and response.get('success'):
            user_data = response.get('data', {})
            user_role = user_data.get('role')
            user_email = user_data.get('email')
            
            print(f"   ✅ Admin user info retrieved")
            print(f"   Email: {user_email}")
            print(f"   Role: {user_role}")
            
            if user_role == "admin":
                print(f"   ✅ Admin role verified")
            else:
                print(f"   ❌ Expected admin role, got: {user_role}")
                return False, response
        
        return success, response

    def test_admin_stats(self):
        """Test admin stats endpoint"""
        success, response = self.run_test(
            "Admin Stats Endpoint", 
            "GET", 
            "admin/stats", 
            200,
            auth_required=True,
            token_type="admin"
        )
        
        if success and response.get('success'):
            stats_data = response.get('data', {})
            print(f"   ✅ Admin stats retrieved")
            print(f"   Total users: {stats_data.get('total_users')}")
            print(f"   Total projects: {stats_data.get('total_projects')}")
            print(f"   Total MCP tasks: {stats_data.get('total_mcp_tasks')}")
        
        return success, response

    def test_admin_users(self):
        """Test admin users endpoint"""
        success, response = self.run_test(
            "Admin Users Endpoint", 
            "GET", 
            "admin/users", 
            200,
            auth_required=True,
            token_type="admin"
        )
        
        if success and response.get('success'):
            users_data = response.get('data', {})
            users_list = users_data.get('users', [])
            print(f"   ✅ Admin users list retrieved")
            print(f"   Found {len(users_list)} users")
            
            # Check if admin user is in the list
            admin_found = any(user.get('email') == 'kartik986340@gmail.com' for user in users_list)
            if admin_found:
                print(f"   ✅ Admin user found in users list")
            else:
                print(f"   ⚠️ Admin user not found in users list")
        
        return success, response

    def test_admin_mcp_tasks(self):
        """Test admin MCP tasks endpoint"""
        success, response = self.run_test(
            "Admin MCP Tasks Endpoint", 
            "GET", 
            "admin/mcp/tasks", 
            200,
            auth_required=True,
            token_type="admin"
        )
        
        if success and response.get('success'):
            tasks_data = response.get('data', {})
            tasks_list = tasks_data.get('tasks', [])
            print(f"   ✅ Admin MCP tasks retrieved")
            print(f"   Found {len(tasks_list)} MCP tasks")
        
        return success, response

    def test_admin_mcp_task_types(self):
        """Test admin MCP task types endpoint"""
        success, response = self.run_test(
            "Admin MCP Task Types Endpoint", 
            "GET", 
            "admin/mcp/task-types", 
            200,
            auth_required=True,
            token_type="admin"
        )
        
        if success and response.get('success'):
            task_types_data = response.get('data', {})
            task_types_list = task_types_data.get('task_types', [])
            print(f"   ✅ Admin MCP task types retrieved")
            print(f"   Found {len(task_types_list)} task types")
            
            # Check for expected task types
            expected_types = ['linkedin_post', 'email_campaign', 'social_media_post']
            found_types = [task_type.get('id') for task_type in task_types_list]
            
            for expected_type in expected_types:
                if expected_type in found_types:
                    print(f"   ✅ Found {expected_type} task type")
                else:
                    print(f"   ⚠️ Missing {expected_type} task type")
        
        return success, response

    def test_regular_user_restrictions(self):
        """Test that regular users cannot access admin endpoints"""
        # First create a regular user and get token
        regular_user_data = {
            "email": f"regular_user_test@example.com",
            "username": "regular_test",
            "full_name": "Regular Test User",
            "password": "TestPassword123!"
        }
        
        # Register regular user
        reg_success, reg_response = self.run_test(
            "Regular User Registration", 
            "POST", 
            "auth/register", 
            200, 
            data=regular_user_data
        )
        
        if not reg_success:
            print("   ⚠️ Could not create regular user for testing")
            return False, {}
        
        # Login regular user
        login_data = {
            "email": regular_user_data["email"],
            "password": regular_user_data["password"]
        }
        
        login_success, login_response = self.run_test(
            "Regular User Login", 
            "POST", 
            "auth/login", 
            200, 
            data=login_data
        )
        
        if login_success and 'access_token' in login_response:
            self.regular_token = login_response['access_token']
            print(f"   ✅ Regular user token obtained")
        else:
            print("   ⚠️ Could not get regular user token")
            return False, {}
        
        # Test admin endpoints with regular user token (should fail)
        print(f"\n🔒 Testing Regular User Admin Access Restrictions...")
        
        # Test admin stats with regular user token (should fail)
        stats_success, _ = self.run_test(
            "Regular User -> Admin Stats (Should Fail)", 
            "GET", 
            "admin/stats", 
            403,  # Expecting forbidden
            auth_required=True,
            token_type="regular"
        )
        
        # Test admin users with regular user token (should fail)
        users_success, _ = self.run_test(
            "Regular User -> Admin Users (Should Fail)", 
            "GET", 
            "admin/users", 
            403,  # Expecting forbidden
            auth_required=True,
            token_type="regular"
        )
        
        return stats_success and users_success, {}

    def run_all_tests(self):
        """Run all admin authentication tests"""
        print("👑 Admin Authentication System Tests")
        print("=" * 50)
        
        # Test 1: Admin Login
        login_success, _ = self.test_admin_login()
        if not login_success:
            print("❌ Admin login failed - cannot continue with other tests")
            return False
        
        # Test 2: Admin User Info
        info_success, _ = self.test_admin_user_info()
        
        # Test 3: Admin Endpoints
        stats_success, _ = self.test_admin_stats()
        users_success, _ = self.test_admin_users()
        tasks_success, _ = self.test_admin_mcp_tasks()
        task_types_success, _ = self.test_admin_mcp_task_types()
        
        # Test 4: Regular User Restrictions
        restrictions_success, _ = self.test_regular_user_restrictions()
        
        # Summary
        print("\n" + "=" * 50)
        print(f"📊 Admin Auth Tests Results: {self.tests_passed}/{self.tests_run} tests passed")
        
        all_critical_tests_passed = (
            login_success and 
            info_success and 
            stats_success and 
            users_success and 
            tasks_success and 
            task_types_success
        )
        
        if all_critical_tests_passed:
            print("🎉 All critical admin authentication tests passed!")
            print("✅ Admin user can login with kartik986340@gmail.com / ak-047-ak")
            print("✅ Admin user has 'admin' role")
            print("✅ Admin user can access all admin endpoints")
            print("✅ JWT token validation works correctly")
            return True
        else:
            print("❌ Some critical admin authentication tests failed")
            return False

def main():
    tester = AdminAuthTester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())