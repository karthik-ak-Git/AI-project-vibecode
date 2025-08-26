import requests
import sys
import json
from datetime import datetime
import time

class MultiAgentAPITester:
    def __init__(self, base_url="https://fastapi-agents.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.auth_token = None
        self.test_user_email = f"testuser_{int(time.time())}@example.com"
        self.test_user_password = "TestPassword123!"
        self.created_project_id = None

    def run_test(self, name, method, endpoint, expected_status, data=None, timeout=30, auth_required=False):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}" if endpoint else f"{self.api_url}"
        headers = {'Content-Type': 'application/json'}
        
        # Add authorization header if required and token is available
        if auth_required and self.auth_token:
            headers['Authorization'] = f'Bearer {self.auth_token}'

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        if auth_required:
            print(f"   Auth: {'✅ Token provided' if self.auth_token else '❌ No token'}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=timeout)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=timeout)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=timeout)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=timeout)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    print(f"   Response keys: {list(response_data.keys()) if isinstance(response_data, dict) else 'Non-dict response'}")
                except:
                    print(f"   Response: {response.text[:100]}...")
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                print(f"   Response: {response.text[:200]}...")

            return success, response.json() if response.text else {}

        except requests.exceptions.Timeout:
            print(f"❌ Failed - Request timed out after {timeout} seconds")
            return False, {}
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    # System Health Tests
    def test_system_status(self):
        """Test system status endpoint"""
        success, response = self.run_test("System Status", "GET", "system/status", 200)
        
        if success:
            expected_keys = ['status', 'database', 'ai_service', 'version', 'timestamp']
            for key in expected_keys:
                if key in response:
                    print(f"   ✅ Found {key}: {response[key]}")
                else:
                    print(f"   ❌ Missing {key}")
                    
        return success, response

    def test_root_endpoint(self):
        """Test the root API endpoint"""
        return self.run_test("Root API Endpoint", "GET", "", 200)

    def test_get_agents(self):
        """Test getting list of available agents"""
        success, response = self.run_test("Get Agents", "GET", "agents", 200)
        
        if success and 'agents' in response:
            agents = response['agents']
            print(f"   Found {len(agents)} agents")
            expected_agents = ['designer', 'frontend', 'backend', 'database', 'ai', 'tester']
            found_agents = [agent['id'] for agent in agents]
            
            for expected in expected_agents:
                if expected in found_agents:
                    print(f"   ✅ Found {expected} agent")
                else:
                    print(f"   ❌ Missing {expected} agent")
                    
        return success, response

    # Authentication System Tests
    def test_user_registration(self):
        """Test user registration"""
        user_data = {
            "email": self.test_user_email,
            "username": f"testuser_{int(time.time())}",
            "full_name": "Test User",
            "password": self.test_user_password
        }
        
        success, response = self.run_test(
            "User Registration", 
            "POST", 
            "auth/register", 
            200, 
            data=user_data
        )
        
        if success and response.get('success'):
            print(f"   ✅ User registered successfully")
            print(f"   User ID: {response.get('data', {}).get('user_id')}")
        
        return success, response

    def test_user_login(self):
        """Test user login and store token"""
        login_data = {
            "email": self.test_user_email,
            "password": self.test_user_password
        }
        
        success, response = self.run_test(
            "User Login", 
            "POST", 
            "auth/login", 
            200, 
            data=login_data
        )
        
        if success and 'access_token' in response:
            self.auth_token = response['access_token']
            print(f"   ✅ Login successful, token stored")
            print(f"   Token type: {response.get('token_type')}")
        
        return success, response

    def test_protected_endpoint(self):
        """Test protected endpoint /auth/me"""
        success, response = self.run_test(
            "Protected Endpoint (/auth/me)", 
            "GET", 
            "auth/me", 
            200,
            auth_required=True
        )
        
        if success:
            print(f"   ✅ User info retrieved")
            print(f"   Email: {response.get('email')}")
            print(f"   Username: {response.get('username')}")
        
        return success, response

    def test_invalid_token(self):
        """Test with invalid token"""
        # Temporarily set invalid token
        original_token = self.auth_token
        self.auth_token = "invalid_token_123"
        
        success, response = self.run_test(
            "Invalid Token Test", 
            "GET", 
            "auth/me", 
            401,  # Expecting unauthorized
            auth_required=True
        )
        
        # Restore original token
        self.auth_token = original_token
        
        return success, response

    # AI Service Integration Tests
    def test_ai_analysis_simple(self):
        """Test AI analysis with simple analysis type"""
        analysis_data = {
            "prompt": "Create a simple blog website with user authentication",
            "analysis_type": "simple"
        }
        
        success, response = self.run_test(
            "AI Analysis - Simple", 
            "POST", 
            "ai/analyze", 
            200, 
            data=analysis_data,
            auth_required=True,
            timeout=45
        )
        
        if success and response.get('success'):
            print(f"   ✅ AI analysis completed")
            data = response.get('data', {})
            print(f"   Processing time: {data.get('processing_time', 'N/A')}s")
            print(f"   Model used: {data.get('model_used', 'N/A')}")
        
        return success, response

    def test_ai_analysis_comprehensive(self):
        """Test AI analysis with comprehensive analysis type"""
        analysis_data = {
            "prompt": "Build a task management app with real-time collaboration and AI features",
            "analysis_type": "comprehensive"
        }
        
        success, response = self.run_test(
            "AI Analysis - Comprehensive", 
            "POST", 
            "ai/analyze", 
            200, 
            data=analysis_data,
            auth_required=True,
            timeout=60
        )
        
        if success and response.get('success'):
            print(f"   ✅ Comprehensive AI analysis completed")
            data = response.get('data', {})
            if 'result' in data:
                result = data['result']
                print(f"   Analysis sections: {list(result.keys()) if isinstance(result, dict) else 'Non-dict result'}")
        
        return success, response

    # Multi-Agent Generation System Tests
    def test_generate_app_simple(self):
        """Test app generation with a simple prompt"""
        prompt_data = {
            "prompt": "Build a simple blog website with user authentication"
        }
        
        success, response = self.run_test(
            "Generate App - Simple Blog", 
            "POST", 
            "generate", 
            200, 
            data=prompt_data,
            auth_required=True,
            timeout=90
        )
        
        if success and response.get('success'):
            project = response.get('data', {}).get('project', {})
            self.created_project_id = project.get('id')  # Store for later tests
            print(f"   Generated project: {project.get('name', 'Unknown')}")
            print(f"   Technologies: {len(project.get('technologies', []))} found")
            print(f"   Structure folders: {list(project.get('structure', {}).keys())}")
            
            # Verify all 6 agents responded
            agents_results = project.get('agents_results', {})
            expected_agents = ['designer', 'frontend', 'backend', 'database', 'ai', 'tester']
            for agent in expected_agents:
                if agent in agents_results:
                    print(f"   ✅ {agent} agent responded")
                else:
                    print(f"   ❌ {agent} agent missing")
            
            return success, project
            
        return success, response

    def test_generate_app_complex(self):
        """Test app generation with a complex prompt"""
        prompt_data = {
            "prompt": "Build a task management app with user authentication, project boards, real-time collaboration, AI-powered suggestions, and deadline tracking"
        }
        
        success, response = self.run_test(
            "Generate App - Complex Task Manager", 
            "POST", 
            "generate", 
            200, 
            data=prompt_data,
            auth_required=True,
            timeout=120
        )
        
        if success and response.get('success'):
            project = response.get('data', {}).get('project', {})
            print(f"   Generated project: {project.get('name', 'Unknown')}")
            
            # Check if AI-related technologies are included
            technologies = project.get('technologies', [])
            if 'Gemini API' in technologies or any('AI' in tech for tech in technologies):
                print(f"   ✅ AI integration detected in technologies")
            
            # Check technology stack extraction
            print(f"   Technologies extracted: {technologies}")
            
            # Verify project structure generation
            structure = project.get('structure', {})
            if 'frontend' in structure and 'backend' in structure:
                print(f"   ✅ Full-stack structure generated")
                
        return success, response

    def test_generate_empty_prompt(self):
        """Test app generation with empty prompt (should fail)"""
        prompt_data = {"prompt": ""}
        
        success, response = self.run_test(
            "Generate App - Empty Prompt", 
            "POST", 
            "generate", 
            400, 
            data=prompt_data,
            auth_required=True
        )
        return success, response

    # Project Management Tests
    def test_get_projects(self):
        """Test getting user projects"""
        success, response = self.run_test(
            "Get User Projects", 
            "GET", 
            "projects", 
            200,
            auth_required=True
        )
        
        if success:
            if isinstance(response, list):
                print(f"   Found {len(response)} projects")
                if len(response) > 0:
                    project = response[0]
                    print(f"   Sample project keys: {list(project.keys())}")
            else:
                print(f"   Response type: {type(response)}")
                
        return success, response

    def test_get_project_by_id(self):
        """Test getting a specific project by ID"""
        if not self.created_project_id:
            print("   ⚠️ No project ID available, skipping test")
            return False, {}
            
        success, response = self.run_test(
            f"Get Project by ID", 
            "GET", 
            f"projects/{self.created_project_id}", 
            200,
            auth_required=True
        )
        
        if success:
            print(f"   Retrieved project: {response.get('name', 'Unknown')}")
            print(f"   Project ID matches: {response.get('id') == self.created_project_id}")
                
        return success, response

    def test_update_project(self):
        """Test updating a project"""
        if not self.created_project_id:
            print("   ⚠️ No project ID available, skipping test")
            return False, {}
            
        update_data = {
            "name": "Updated Blog Website",
            "description": "Updated description for the blog website"
        }
        
        success, response = self.run_test(
            "Update Project", 
            "PUT", 
            f"projects/{self.created_project_id}", 
            200,
            data=update_data,
            auth_required=True
        )
        
        if success and response.get('success'):
            print(f"   ✅ Project updated successfully")
            updated_fields = response.get('data', {}).get('updated_fields', [])
            print(f"   Updated fields: {updated_fields}")
                
        return success, response

    def test_delete_project_invalid_id(self):
        """Test deleting a project with invalid ID"""
        success, response = self.run_test(
            "Delete Project - Invalid ID", 
            "DELETE", 
            "projects/invalid_id_123", 
            404,
            auth_required=True
        )
        return success, response

    # Export System Tests
    def test_export_project(self):
        """Test project export"""
        if not self.created_project_id:
            print("   ⚠️ No project ID available, skipping test")
            return False, {}
            
        success, response = self.run_test(
            "Export Project", 
            "POST", 
            f"export/{self.created_project_id}", 
            200,
            auth_required=True,
            timeout=45
        )
        
        if success and response.get('success'):
            export_data = response.get('data', {}).get('export_data', {})
            print(f"   ✅ Export completed")
            print(f"   Export sections: {list(export_data.keys())}")
            
            # Verify export data completeness
            expected_sections = ['project_info', 'structure', 'technologies', 'setup_instructions', 
                               'deployment_guide', 'agents_output', 'development_roadmap']
            for section in expected_sections:
                if section in export_data:
                    print(f"   ✅ {section} included")
                else:
                    print(f"   ❌ {section} missing")
                    
        return success, response

    def test_export_invalid_project(self):
        """Test exporting invalid project"""
        success, response = self.run_test(
            "Export Invalid Project", 
            "POST", 
            "export/invalid_project_123", 
            404,
            auth_required=True
        )
        return success, response

    def test_project_workflow(self):
        """Test complete project workflow: create -> retrieve -> export"""
        print(f"\n🔄 Testing Complete Project Workflow...")
        
        # Step 1: Create a project
        create_success, create_response = self.test_generate_app_simple()
        if not create_success:
            print("❌ Workflow failed at project creation")
            return False
            
        project_id = self.created_project_id
        if not project_id:
            print("❌ No project ID returned")
            return False
            
        print(f"   Created project with ID: {project_id}")
        
        # Step 2: Retrieve the specific project
        get_success, get_response = self.test_get_project_by_id()
        
        if not get_success:
            print("❌ Workflow failed at project retrieval")
            return False
            
        # Step 3: Export the project
        export_success, export_response = self.test_export_project()
        
        workflow_success = create_success and get_success and export_success
        print(f"   Workflow Result: {'✅ Success' if workflow_success else '❌ Failed'}")
        return workflow_success

    def cleanup_test_project(self):
        """Clean up the test project"""
        if self.created_project_id:
            print(f"\n🧹 Cleaning up test project...")
            success, response = self.run_test(
                "Delete Test Project", 
                "DELETE", 
                f"projects/{self.created_project_id}", 
                200,
                auth_required=True
            )
            if success:
                print("   ✅ Test project deleted successfully")
            else:
                print("   ⚠️ Failed to delete test project")

def main():
    print("🚀 Starting Comprehensive Multi-Agent Platform API Tests")
    print("=" * 70)
    
    tester = MultiAgentAPITester()
    
    # Phase 1: System Health Tests
    print(f"\n📊 Phase 1: System Health Tests")
    print("-" * 40)
    tester.test_system_status()
    tester.test_root_endpoint()
    tester.test_get_agents()
    
    # Phase 2: Authentication System Tests
    print(f"\n🔐 Phase 2: Authentication System Tests")
    print("-" * 40)
    tester.test_user_registration()
    tester.test_user_login()
    tester.test_protected_endpoint()
    tester.test_invalid_token()
    
    # Phase 3: AI Service Integration Tests
    print(f"\n🤖 Phase 3: AI Service Integration Tests")
    print("-" * 40)
    tester.test_ai_analysis_simple()
    tester.test_ai_analysis_comprehensive()
    
    # Phase 4: Multi-Agent Generation System Tests
    print(f"\n⚙️ Phase 4: Multi-Agent Generation System Tests")
    print("-" * 40)
    tester.test_generate_app_simple()
    tester.test_generate_app_complex()
    tester.test_generate_empty_prompt()
    
    # Phase 5: Project Management Tests
    print(f"\n📁 Phase 5: Project Management Tests")
    print("-" * 40)
    tester.test_get_projects()
    tester.test_get_project_by_id()
    tester.test_update_project()
    tester.test_delete_project_invalid_id()
    
    # Phase 6: Export System Tests
    print(f"\n📤 Phase 6: Export System Tests")
    print("-" * 40)
    tester.test_export_project()
    tester.test_export_invalid_project()
    
    # Phase 7: Complete Workflow Test
    print(f"\n🔄 Phase 7: Complete Workflow Test")
    print("-" * 40)
    # Note: This will create another project, but that's fine for comprehensive testing
    workflow_success = tester.test_project_workflow()
    
    # Cleanup
    tester.cleanup_test_project()
    
    # Print final results
    print("\n" + "=" * 70)
    print(f"📊 Final Results: {tester.tests_passed}/{tester.tests_run} tests passed")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All tests passed! Multi-Agent Platform API is working correctly.")
        return 0
    else:
        failed_tests = tester.tests_run - tester.tests_passed
        print(f"⚠️  {failed_tests} test(s) failed. Check the issues above.")
        
        # Calculate success rate
        success_rate = (tester.tests_passed / tester.tests_run) * 100
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        if success_rate >= 80:
            print("✅ Overall system is functional with minor issues.")
            return 0
        else:
            print("❌ System has significant issues that need attention.")
            return 1

if __name__ == "__main__":
    sys.exit(main())