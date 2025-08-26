import os
import time
import logging
from typing import Dict, Any, List
from dotenv import load_dotenv
from emergentintegrations.llm.chat import LlmChat, UserMessage
from models import AIAnalysisRequest, AIAnalysisResponse

load_dotenv()

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        self.api_key = os.getenv("EMERGENT_LLM_KEY")
        if not self.api_key:
            raise ValueError("EMERGENT_LLM_KEY not found in environment variables")
        
    async def analyze_project_requirements(self, prompt: str, analysis_type: str = "comprehensive") -> Dict[str, Any]:
        """Analyze project requirements using AI and return structured data."""
        start_time = time.time()
        
        try:
            # Create AI chat instance with Gemini
            chat = LlmChat(
                api_key=self.api_key,
                session_id=f"project_analysis_{int(time.time())}",
                system_message=self._get_system_message(analysis_type)
            ).with_model("gemini", "gemini-2.0-flash")
            
            # Create analysis prompt
            analysis_prompt = self._create_analysis_prompt(prompt, analysis_type)
            user_message = UserMessage(text=analysis_prompt)
            
            # Get AI response
            response = await chat.send_message(user_message)
            
            # Parse and structure the response
            structured_result = self._parse_ai_response(response, analysis_type)
            
            processing_time = time.time() - start_time
            
            return {
                "success": True,
                "result": structured_result,
                "processing_time": processing_time,
                "model_used": "gemini-2.0-flash",
                "confidence_score": 0.85  # This would be calculated based on response quality
            }
            
        except Exception as e:
            logger.error(f"AI analysis failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "processing_time": time.time() - start_time
            }
    
    def _get_system_message(self, analysis_type: str) -> str:
        """Get appropriate system message based on analysis type."""
        system_messages = {
            "comprehensive": """You are an expert software architect and project analyst. 
                               Analyze user requirements and provide detailed technical specifications 
                               for web application development.""",
            
            "project_structure": """You are a senior software architect specializing in project structure design. 
                                   Analyze requirements and design optimal file/folder structures for web applications.""",
            
            "technology_stack": """You are a technology consultant with expertise in modern web development stacks. 
                                  Recommend appropriate technologies, frameworks, and tools based on project requirements.""",
            
            "agent_tasks": """You are a project manager expert in breaking down complex projects into manageable tasks. 
                             Analyze requirements and define specific tasks for different development agents."""
        }
        
        return system_messages.get(analysis_type, system_messages["comprehensive"])
    
    def _create_analysis_prompt(self, user_prompt: str, analysis_type: str) -> str:
        """Create specific analysis prompt for AI."""
        base_prompt = f"User wants to build: {user_prompt}\n\n"
        
        prompts = {
            "comprehensive": f"""{base_prompt}
Provide a comprehensive analysis including:
1. Project overview and key features
2. Recommended technology stack
3. Database schema design
4. API endpoints structure
5. Frontend component architecture
6. Security considerations
7. Deployment recommendations

Format your response as structured JSON with clear sections.""",

            "project_structure": f"""{base_prompt}
Design an optimal project structure including:
1. Frontend folder structure with React components
2. Backend folder structure with FastAPI organization
3. Database schema files
4. Configuration files
5. Testing structure
6. Documentation structure

Provide specific file and folder names with their purposes.""",

            "technology_stack": f"""{base_prompt}
Recommend the best technology stack including:
1. Frontend technologies (React, Next.js, Vue, etc.)
2. Backend technologies (FastAPI, Express, Django, etc.)
3. Database options (MongoDB, PostgreSQL, etc.)
4. Authentication methods
5. Deployment platforms
6. Additional tools and libraries

Explain why each technology is recommended for this specific project.""",

            "agent_tasks": f"""{base_prompt}
Break down this project into specific tasks for these agents:
1. Designer Agent - UI/UX and styling tasks
2. Frontend Agent - React/JavaScript development tasks
3. Backend Agent - API and server-side logic tasks
4. Database Agent - Schema design and data management tasks
5. AI Service Agent - AI integration and intelligent features tasks
6. Testing Agent - Quality assurance and testing tasks

Provide detailed task descriptions for each agent."""
        }
        
        return prompts.get(analysis_type, prompts["comprehensive"])
    
    def _parse_ai_response(self, response: str, analysis_type: str) -> Dict[str, Any]:
        """Parse AI response into structured format."""
        try:
            # Try to parse as JSON first
            import json
            return json.loads(response)
        except:
            # If not JSON, structure the text response
            return {
                "raw_analysis": response,
                "analysis_type": analysis_type,
                "structured_data": self._extract_structured_data(response, analysis_type)
            }
    
    def _extract_structured_data(self, response: str, analysis_type: str) -> Dict[str, Any]:
        """Extract structured data from text response."""
        # Basic text parsing to extract key information
        lines = response.split('\n')
        structured = {
            "sections": [],
            "technologies": [],
            "files": [],
            "tasks": []
        }
        
        current_section = ""
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Detect section headers
            if any(keyword in line.lower() for keyword in ['overview', 'stack', 'structure', 'tasks', 'requirements']):
                current_section = line
                structured["sections"].append(line)
            
            # Extract technologies mentioned
            tech_keywords = ['react', 'fastapi', 'mongodb', 'tailwind', 'jwt', 'websocket', 'stripe', 'gemini']
            for tech in tech_keywords:
                if tech.lower() in line.lower() and tech not in structured["technologies"]:
                    structured["technologies"].append(tech)
            
            # Extract file mentions
            if any(ext in line.lower() for ext in ['.js', '.py', '.json', '.css', '.html']):
                structured["files"].append(line)
        
        return structured

    async def generate_agent_response(self, agent_name: str, prompt: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate specific response for an individual agent."""
        start_time = time.time()
        
        try:
            chat = LlmChat(
                api_key=self.api_key,
                session_id=f"{agent_name}_{int(time.time())}",
                system_message=self._get_agent_system_message(agent_name)
            ).with_model("gemini", "gemini-2.0-flash")
            
            agent_prompt = self._create_agent_prompt(agent_name, prompt, context)
            user_message = UserMessage(text=agent_prompt)
            
            response = await chat.send_message(user_message)
            
            # Parse agent-specific response
            structured_result = self._parse_agent_response(response, agent_name)
            
            return {
                "success": True,
                "agent": agent_name,
                "result": structured_result,
                "processing_time": time.time() - start_time,
                "model_used": "gemini-2.0-flash"
            }
            
        except Exception as e:
            logger.error(f"Agent {agent_name} response generation failed: {str(e)}")
            return {
                "success": False,
                "agent": agent_name,
                "error": str(e),
                "processing_time": time.time() - start_time
            }
    
    def _get_agent_system_message(self, agent_name: str) -> str:
        """Get system message for specific agent."""
        messages = {
            "designer": "You are a senior UI/UX designer specializing in modern web interfaces and responsive design.",
            "frontend": "You are a senior React developer with expertise in modern frontend development and component architecture.",
            "backend": "You are a senior backend developer specializing in FastAPI, Python, and scalable API design.",
            "database": "You are a database architect expert in MongoDB, PostgreSQL, and optimal database design patterns.",
            "ai": "You are an AI integration specialist with expertise in LLM APIs, machine learning, and intelligent features.",
            "tester": "You are a senior QA engineer specializing in automated testing, test strategies, and quality assurance."
        }
        return messages.get(agent_name, "You are an expert software developer.")
    
    def _create_agent_prompt(self, agent_name: str, prompt: str, context: Dict[str, Any] = None) -> str:
        """Create agent-specific prompt."""
        base = f"Project: {prompt}\n\n"
        if context:
            base += f"Context: {context}\n\n"
        
        agent_prompts = {
            "designer": f"{base}As a UI/UX designer, provide:\n1. Design system and color palette\n2. Component wireframes\n3. Responsive design strategy\n4. User experience flow",
            "frontend": f"{base}As a frontend developer, provide:\n1. React component structure\n2. State management approach\n3. Routing strategy\n4. API integration plan",
            "backend": f"{base}As a backend developer, provide:\n1. API endpoints design\n2. Authentication strategy\n3. Database integration\n4. Business logic structure",
            "database": f"{base}As a database architect, provide:\n1. Schema design\n2. Data relationships\n3. Indexing strategy\n4. Query optimization",
            "ai": f"{base}As an AI specialist, provide:\n1. AI service integration\n2. Model selection\n3. API endpoints for AI features\n4. Intelligent feature recommendations",
            "tester": f"{base}As a QA engineer, provide:\n1. Testing strategy\n2. Test cases\n3. Quality metrics\n4. Automated testing approach"
        }
        
        return agent_prompts.get(agent_name, f"{base}Provide expert analysis for this project.")
    
    def _parse_agent_response(self, response: str, agent_name: str) -> Dict[str, Any]:
        """Parse agent-specific response."""
        # This would contain agent-specific parsing logic
        return {
            "agent_type": agent_name,
            "analysis": response,
            "recommendations": self._extract_recommendations(response),
            "technical_details": self._extract_technical_details(response, agent_name)
        }
    
    def _extract_recommendations(self, response: str) -> List[str]:
        """Extract recommendations from response."""
        recommendations = []
        lines = response.split('\n')
        for line in lines:
            if any(word in line.lower() for word in ['recommend', 'suggest', 'should', 'use', 'implement']):
                recommendations.append(line.strip())
        return recommendations[:5]  # Limit to top 5
    
    def _extract_technical_details(self, response: str, agent_name: str) -> Dict[str, Any]:
        """Extract technical details specific to agent type."""
        details = {"agent": agent_name}
        
        # Agent-specific extraction logic
        if agent_name == "frontend":
            details["components"] = [line.strip() for line in response.split('\n') if '.js' in line.lower()]
            details["libraries"] = [word for word in response.split() if word.lower() in ['react', 'redux', 'axios', 'tailwind']]
        
        elif agent_name == "backend":
            details["endpoints"] = [line.strip() for line in response.split('\n') if '/api/' in line.lower()]
            details["technologies"] = [word for word in response.split() if word.lower() in ['fastapi', 'mongodb', 'jwt', 'redis']]
        
        elif agent_name == "database":
            details["collections"] = [line.strip() for line in response.split('\n') if any(word in line.lower() for word in ['collection', 'table', 'schema'])]
            details["indexes"] = [line.strip() for line in response.split('\n') if 'index' in line.lower()]
        
        return details