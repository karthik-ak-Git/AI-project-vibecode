from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import uuid
from datetime import datetime, timezone
import asyncio
import json

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Define Models
class StatusCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class StatusCheckCreate(BaseModel):
    client_name: str

class AppGenerationRequest(BaseModel):
    prompt: str
    user_preferences: Optional[Dict[str, Any]] = None

class AgentResponse(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    agent_name: str
    status: str  # waiting, running, completed, error
    progress: int = 0
    result: Optional[Dict[str, Any]] = None
    logs: List[str] = []
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class GeneratedProject(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    prompt: str
    structure: Dict[str, List[str]]
    technologies: List[str]
    agents_results: Dict[str, Dict[str, Any]]
    status: str = "completed"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Agent definitions
AGENTS = [
    {
        "id": "designer",
        "name": "Designer Agent",
        "description": "Creates responsive UI layouts with Tailwind CSS",
        "capabilities": ["UI/UX Design", "Responsive Layout", "Tailwind CSS", "Component Design"]
    },
    {
        "id": "frontend", 
        "name": "Frontend Agent",
        "description": "Generates React/Next.js components and logic",
        "capabilities": ["React Development", "Component Architecture", "State Management", "API Integration"]
    },
    {
        "id": "backend",
        "name": "Backend Agent", 
        "description": "Sets up FastAPI/Express.js API endpoints",
        "capabilities": ["API Development", "Database Integration", "Authentication", "Business Logic"]
    },
    {
        "id": "database",
        "name": "Database Agent",
        "description": "Designs MongoDB/PostgreSQL schemas",
        "capabilities": ["Schema Design", "Data Modeling", "Query Optimization", "Migrations"]
    },
    {
        "id": "ai",
        "name": "AI Service Agent",
        "description": "Integrates AI capabilities and endpoints", 
        "capabilities": ["AI Integration", "Model Selection", "API Configuration", "Prompt Engineering"]
    },
    {
        "id": "tester",
        "name": "Prompt Tester Agent",
        "description": "Validates and tests generated code",
        "capabilities": ["Code Validation", "Testing Strategy", "Quality Assurance", "Performance Testing"]
    }
]

def generate_mock_project_structure(prompt: str) -> Dict[str, List[str]]:
    """Generate a realistic project structure based on the prompt"""
    base_structure = {
        "frontend": [
            "src/App.js",
            "src/components/",
            "src/components/ui/",
            "src/pages/",
            "src/hooks/",
            "src/utils/",
            "src/styles/",
            "public/index.html",
            "package.json",
            "tailwind.config.js"
        ],
        "backend": [
            "server.py",
            "models/",
            "routes/",
            "middleware/",
            "utils/",
            "requirements.txt",
            ".env.example"
        ],
        "database": [
            "schemas/",
            "migrations/",
            "seeds/",
            "indexes.js"
        ],
        "config": [
            ".env",
            ".gitignore",
            "README.md",
            "docker-compose.yml"
        ],
        "tests": [
            "tests/unit/",
            "tests/integration/",
            "tests/e2e/",
            "pytest.ini"
        ]
    }
    
    # Add specific files based on prompt content
    prompt_lower = prompt.lower()
    
    if "auth" in prompt_lower or "login" in prompt_lower:
        base_structure["frontend"].extend([
            "src/components/auth/Login.js",
            "src/components/auth/Register.js",
            "src/contexts/AuthContext.js"
        ])
        base_structure["backend"].extend([
            "routes/auth.py",
            "middleware/auth.py"
        ])
    
    if "dashboard" in prompt_lower:
        base_structure["frontend"].extend([
            "src/pages/Dashboard.js",
            "src/components/dashboard/"
        ])
        
    if "api" in prompt_lower or "endpoint" in prompt_lower:
        base_structure["backend"].extend([
            "routes/api.py",
            "models/user.py"
        ])
    
    return base_structure

def generate_agent_result(agent_id: str, prompt: str) -> Dict[str, Any]:
    """Generate realistic results for each agent based on the prompt"""
    results = {
        "designer": {
            "components": ["Header", "Navigation", "Hero Section", "Main Content", "Footer"],
            "color_palette": "Modern blue and gray with accent colors",
            "layout_type": "Responsive grid-based design",
            "design_system": "Tailwind CSS with custom components",
            "wireframes": ["Desktop layout", "Mobile layout", "Tablet layout"],
            "ui_patterns": ["Cards", "Forms", "Buttons", "Navigation", "Modals"]
        },
        "frontend": {
            "framework": "React 18 with TypeScript",
            "components": ["App.js", "Header.js", "MainContent.js", "Sidebar.js"],
            "state_management": "React hooks and Context API",
            "routing": "React Router v6",
            "styling": "Tailwind CSS with styled-components",
            "api_integration": "Axios with custom hooks",
            "features": ["Responsive design", "Dark mode support", "Form validation"]
        },
        "backend": {
            "framework": "FastAPI with Python 3.11",
            "endpoints": ["/api/users", "/api/auth", "/api/data"],
            "authentication": "JWT with refresh tokens",
            "database_orm": "SQLAlchemy with async support",
            "validation": "Pydantic models",
            "middleware": ["CORS", "Rate limiting", "Request logging"],
            "features": ["Auto-generated docs", "Input validation", "Error handling"]
        },
        "database": {
            "type": "MongoDB with Motor (async)",
            "collections": ["users", "projects", "sessions"],
            "schema_validation": "Pydantic models",
            "indexes": ["User email (unique)", "Project name", "Session expiry"],
            "relationships": "Embedded and referenced documents",
            "backup_strategy": "Automated daily backups",
            "optimization": "Query performance tuning"
        },
        "ai": {
            "provider": "Gemini API",
            "services": ["Text generation", "Content analysis", "Smart suggestions"],
            "endpoints": ["/api/ai/generate", "/api/ai/analyze", "/api/ai/suggest"],
            "models": ["gemini-pro", "gemini-pro-vision"],
            "features": ["Prompt optimization", "Response caching", "Rate limiting"],
            "integration": "Async request handling"
        },
        "tester": {
            "test_types": ["Unit tests", "Integration tests", "E2E tests"],
            "frameworks": ["pytest", "React Testing Library", "Playwright"],
            "coverage": "95% code coverage achieved",
            "ci_cd": "GitHub Actions pipeline",
            "quality_gates": ["ESLint", "Black formatter", "Type checking"],
            "performance": "Lighthouse score 95+",
            "security": "OWASP security testing"
        }
    }
    
    # Customize results based on prompt
    prompt_lower = prompt.lower()
    
    if "ecommerce" in prompt_lower or "shop" in prompt_lower:
        results["frontend"]["components"].extend(["ProductCard.js", "Cart.js", "Checkout.js"])
        results["backend"]["endpoints"].extend(["/api/products", "/api/orders", "/api/payments"])
        results["database"]["collections"].extend(["products", "orders", "payments"])
        
    if "blog" in prompt_lower:
        results["frontend"]["components"].extend(["BlogPost.js", "BlogList.js", "Editor.js"])
        results["backend"]["endpoints"].extend(["/api/posts", "/api/comments"])
        results["database"]["collections"].extend(["posts", "comments", "categories"])
        
    return results.get(agent_id, {})

def extract_project_name(prompt: str) -> str:
    """Extract a project name from the prompt"""
    words = prompt.lower().split()
    
    # Remove common words
    filtered_words = [word for word in words if word not in [
        'a', 'an', 'the', 'for', 'to', 'build', 'create', 'make', 'app', 'application',
        'web', 'website', 'system', 'platform', 'tool', 'service'
    ]]
    
    # Take first 2-3 meaningful words
    name_words = filtered_words[:3] if len(filtered_words) >= 3 else filtered_words[:2]
    
    if not name_words:
        return "generated-app"
        
    return "-".join(name_words) + "-app"

# Routes
@api_router.get("/")
async def root():
    return {"message": "Multi-Agent App Generator API"}

@api_router.get("/agents")
async def get_agents():
    """Get list of available agents"""
    return {"agents": AGENTS}

@api_router.post("/generate", response_model=Dict[str, Any])
async def generate_app(request: AppGenerationRequest):
    """Main endpoint to generate an app from a prompt"""
    
    if not request.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt cannot be empty")
    
    try:
        # Generate project structure
        project_structure = generate_mock_project_structure(request.prompt)
        
        # Generate agent results
        agents_results = {}
        for agent in AGENTS:
            agents_results[agent["id"]] = generate_agent_result(agent["id"], request.prompt)
        
        # Extract technologies used
        technologies = ["React", "FastAPI", "MongoDB", "Tailwind CSS"]
        
        # Add specific technologies based on prompt
        prompt_lower = request.prompt.lower()
        if "ai" in prompt_lower or "ml" in prompt_lower:
            technologies.append("Gemini API")
        if "auth" in prompt_lower:
            technologies.append("JWT Authentication")
        if "real-time" in prompt_lower or "websocket" in prompt_lower:
            technologies.append("WebSockets")
        if "payment" in prompt_lower:
            technologies.append("Stripe API")
            
        # Create generated project
        project = GeneratedProject(
            name=extract_project_name(request.prompt),
            description=request.prompt,
            prompt=request.prompt,
            structure=project_structure,
            technologies=technologies,
            agents_results=agents_results
        )
        
        # Store in database
        project_dict = project.dict()
        project_dict['created_at'] = project_dict['created_at'].isoformat()
        await db.generated_projects.insert_one(project_dict)
        
        return {
            "success": True,
            "project": project.dict(),
            "message": "App generated successfully"
        }
        
    except Exception as e:
        logging.error(f"App generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"App generation failed: {str(e)}")

@api_router.get("/projects", response_model=List[Dict[str, Any]])
async def get_projects():
    """Get all generated projects"""
    try:
        projects = await db.generated_projects.find().to_list(100)
        # Convert ObjectId to string for JSON serialization
        for project in projects:
            if '_id' in project:
                project['_id'] = str(project['_id'])
        return projects
    except Exception as e:
        logging.error(f"Failed to fetch projects: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch projects")

@api_router.get("/projects/{project_id}")
async def get_project(project_id: str):
    """Get a specific project by ID"""
    try:
        project = await db.generated_projects.find_one({"id": project_id})
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        return project
    except Exception as e:
        logging.error(f"Failed to fetch project: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch project")

@api_router.post("/export/{project_id}")
async def export_project(project_id: str):
    """Export project as downloadable code structure"""
    try:
        project = await db.generated_projects.find_one({"id": project_id})
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
            
        # In a real implementation, this would generate actual code files
        # For now, return the project structure and guidelines
        export_data = {
            "project_name": project["name"],
            "description": project["description"],
            "structure": project["structure"],
            "technologies": project["technologies"],
            "setup_instructions": [
                "1. Create a new directory for your project",
                "2. Set up the frontend with 'npx create-react-app frontend'",
                "3. Set up the backend with FastAPI",
                "4. Install dependencies from package.json and requirements.txt",
                "5. Configure environment variables",
                "6. Run the development servers"
            ],
            "agents_output": project["agents_results"]
        }
        
        return {
            "success": True,
            "export_data": export_data,
            "message": "Project exported successfully"
        }
        
    except Exception as e:
        logging.error(f"Project export failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Project export failed")

# Legacy routes for compatibility
@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.dict()
    status_obj = StatusCheck(**status_dict)
    status_dict = status_obj.dict()
    status_dict['timestamp'] = status_dict['timestamp'].isoformat()
    _ = await db.status_checks.insert_one(status_dict)
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find().to_list(1000)
    return [StatusCheck(**status_check) for status_check in status_checks]

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()