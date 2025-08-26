import requests
import sys
import json
from datetime import datetime

class MultiAgentAPITester:
    def __init__(self, base_url="https://fastapi-agents.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0

    def run_test(self, name, method, endpoint, expected_status, data=None, timeout=30):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}" if endpoint else f"{self.api_url}"
        headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=timeout)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=timeout)

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
            timeout=60
        )
        
        if success and 'project' in response:
            project = response['project']
            print(f"   Generated project: {project.get('name', 'Unknown')}")
            print(f"   Technologies: {len(project.get('technologies', []))} found")
            print(f"   Structure folders: {list(project.get('structure', {}).keys())}")
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
            timeout=60
        )
        
        if success and 'project' in response:
            project = response['project']
            print(f"   Generated project: {project.get('name', 'Unknown')}")
            
            # Check if AI-related technologies are included
            technologies = project.get('technologies', [])
            if 'Gemini API' in technologies:
                print(f"   ✅ AI integration detected in technologies")
            
            # Check if auth-related files are included
            structure = project.get('structure', {})
            frontend_files = structure.get('frontend', [])
            auth_files = [f for f in frontend_files if 'auth' in f.lower()]
            if auth_files:
                print(f"   ✅ Auth components detected: {auth_files}")
                
        return success, response

    def test_generate_empty_prompt(self):
        """Test app generation with empty prompt (should fail)"""
        prompt_data = {"prompt": ""}
        
        success, response = self.run_test(
            "Generate App - Empty Prompt", 
            "POST", 
            "generate", 
            400, 
            data=prompt_data
        )
        return success, response

    def test_get_projects(self):
        """Test getting all projects"""
        success, response = self.run_test("Get All Projects", "GET", "projects", 200)
        
        if success:
            if isinstance(response, list):
                print(f"   Found {len(response)} projects")
            else:
                print(f"   Response type: {type(response)}")
                
        return success, response

    def test_project_workflow(self):
        """Test complete project workflow: create -> retrieve -> export"""
        print(f"\n🔄 Testing Complete Project Workflow...")
        
        # Step 1: Create a project
        create_success, create_response = self.test_generate_app_simple()
        if not create_success:
            print("❌ Workflow failed at project creation")
            return False
            
        project_id = create_response.get('id')
        if not project_id:
            print("❌ No project ID returned")
            return False
            
        print(f"   Created project with ID: {project_id}")
        
        # Step 2: Retrieve the specific project
        get_success, get_response = self.run_test(
            f"Get Project {project_id}", 
            "GET", 
            f"projects/{project_id}", 
            200
        )
        
        if not get_success:
            print("❌ Workflow failed at project retrieval")
            return False
            
        # Step 3: Export the project
        export_success, export_response = self.run_test(
            f"Export Project {project_id}", 
            "POST", 
            f"export/{project_id}", 
            200
        )
        
        if export_success and 'export_data' in export_response:
            export_data = export_response['export_data']
            print(f"   ✅ Export includes: {list(export_data.keys())}")
            
        workflow_success = create_success and get_success and export_success
        print(f"   Workflow Result: {'✅ Success' if workflow_success else '❌ Failed'}")
        return workflow_success

def main():
    print("🚀 Starting Multi-Agent App Generator API Tests")
    print("=" * 60)
    
    tester = MultiAgentAPITester()
    
    # Basic API tests
    tester.test_root_endpoint()
    tester.test_get_agents()
    
    # Generation tests with different prompts
    tester.test_generate_app_simple()
    tester.test_generate_app_complex()
    tester.test_generate_empty_prompt()
    
    # Project management tests
    tester.test_get_projects()
    
    # Complete workflow test
    tester.test_project_workflow()
    
    # Print final results
    print("\n" + "=" * 60)
    print(f"📊 Final Results: {tester.tests_passed}/{tester.tests_run} tests passed")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All tests passed! Backend API is working correctly.")
        return 0
    else:
        failed_tests = tester.tests_run - tester.tests_passed
        print(f"⚠️  {failed_tests} test(s) failed. Check the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())