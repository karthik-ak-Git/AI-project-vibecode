from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
import os
import logging
from pathlib import Path
from datetime import timedelta
from typing import List, Dict, Any, Optional
import asyncio
import time

# Import our custom modules
from models import *
from auth import *
from ai_service import AIService
from database import connect_to_mongo, close_mongo_connection, get_database, get_user_projects, get_project_by_id
from utils import *

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create the main app
app = FastAPI(
    title="Multi-Agent App Generator API",
    description="Advanced multi-agent platform for generating web applications with AI",
    version="2.0.0"
)

# Create API router
api_router = APIRouter(prefix="/api")

# Initialize AI service
ai_service = AIService()

# Agent definitions with enhanced capabilities
AGENTS = [
    {
        "id": "designer",
        "name": "Designer Agent",
        "description": "Creates responsive UI layouts with Tailwind CSS and modern design systems",
        "capabilities": ["UI/UX Design", "Responsive Layout", "Tailwind CSS", "Component Design", "Design Systems"],
        "expertise_level": "senior"
    },
    {
        "id": "frontend", 
        "name": "Frontend Agent",
        "description": "Generates React/Next.js components with modern architecture patterns",
        "capabilities": ["React Development", "Component Architecture", "State Management", "API Integration", "Performance Optimization"],
        "expertise_level": "senior"
    },
    {
        "id": "backend",
        "name": "Backend Agent", 
        "description": "Sets up FastAPI/Express.js with scalable architecture and best practices",
        "capabilities": ["API Development", "Database Integration", "Authentication", "Business Logic", "Performance Optimization"],
        "expertise_level": "senior"
    },
    {
        "id": "database",
        "name": "Database Agent",
        "description": "Designs optimized MongoDB/PostgreSQL schemas with proper indexing",
        "capabilities": ["Schema Design", "Data Modeling", "Query Optimization", "Migrations", "Performance Tuning"],
        "expertise_level": "senior"
    },
    {
        "id": "ai",
        "name": "AI Service Agent",
        "description": "Integrates advanced AI capabilities using Gemini and other LLM APIs", 
        "capabilities": ["AI Integration", "Model Selection", "API Configuration", "Prompt Engineering", "ML Optimization"],
        "expertise_level": "expert"
    },
    {
        "id": "tester",
        "name": "Prompt Tester Agent",
        "description": "Implements comprehensive testing strategies and quality assurance",
        "capabilities": ["Test Strategy", "Automated Testing", "Quality Assurance", "Performance Testing", "Security Testing"],
        "expertise_level": "senior"
    }
]

# Dependencies
async def get_db() -> AsyncIOMotorDatabase:
    """Get database dependency"""
    return await get_database()

async def get_current_user_with_db(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncIOMotorDatabase = Depends(get_db)
) -> User:
    """Get current user with database dependency"""
    return await get_current_user(credentials, db)

# Authentication Routes
@api_router.post("/auth/register", response_model=APIResponse)
async def register_user(
    user_data: UserCreate,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Register a new user"""
    try:
        # Validate email format
        if not validate_email(user_data.email):
            raise HTTPException(
                status_code=400,
                detail="Invalid email format"
            )
        
        # Validate password strength
        password_validation = validate_password(user_data.password)
        if not password_validation["valid"]:
            raise HTTPException(
                status_code=400,
                detail=f"Password validation failed: {', '.join(password_validation['errors'])}"
            )
        
        # Check if user already exists
        existing_user = await get_user(db, user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="Email already registered"
            )
        
        # Check username uniqueness
        existing_username = await db.users.find_one({"username": user_data.username})
        if existing_username:
            raise HTTPException(
                status_code=400,
                detail="Username already taken"
            )
        
        # Create new user
        hashed_password = get_password_hash(user_data.password)
        user_in_db = UserInDB(
            email=user_data.email,
            username=user_data.username,
            full_name=user_data.full_name,
            hashed_password=hashed_password
        )
        
        # Store in database
        user_dict = prepare_for_mongo(user_in_db.dict())
        await db.users.insert_one(user_dict)
        
        logger.info(f"New user registered: {user_data.email}")
        
        return APIResponse(
            success=True,
            message="User registered successfully",
            data={"user_id": user_in_db.id, "email": user_in_db.email}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"User registration failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Registration failed")

@api_router.post("/auth/login", response_model=Token)
async def login_user(
    user_credentials: UserLogin,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Authenticate user and return JWT token"""
    try:
        user = await authenticate_user(db, user_credentials.email, user_credentials.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Create access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.email}, expires_delta=access_token_expires
        )
        
        logger.info(f"User logged in: {user.email}")
        
        return Token(access_token=access_token, token_type="bearer")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Login failed")

@api_router.get("/auth/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user_with_db)):
    """Get current user information"""
    return current_user

# Enhanced Project Generation Routes
@api_router.post("/generate", response_model=APIResponse)
async def generate_app(
    request: AppGenerationRequest,
    current_user: User = Depends(get_current_user_with_db),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Enhanced app generation with real AI analysis"""
    if not request.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt cannot be empty")
    
    try:
        start_time = time.time()
        
        # Step 1: AI-powered analysis of the prompt
        logger.info(f"Starting AI analysis for user {current_user.id}")
        ai_analysis = await ai_service.analyze_project_requirements(request.prompt, "comprehensive")
        
        if not ai_analysis["success"]:
            raise HTTPException(status_code=500, detail=f"AI analysis failed: {ai_analysis.get('error')}")
        
        # Step 2: Generate project metadata
        project_name = generate_project_name(request.prompt)
        technologies = extract_technologies_from_prompt(request.prompt)
        project_structure = generate_project_structure(request.prompt, technologies)
        complexity = calculate_project_complexity(request.prompt)
        time_estimates = estimate_development_time(complexity, technologies)
        
        # Step 3: Generate individual agent responses using AI
        agents_results = {}
        for agent in AGENTS:
            logger.info(f"Generating response for {agent['name']}")
            agent_response = await ai_service.generate_agent_response(
                agent["id"], 
                request.prompt,
                context={
                    "technologies": technologies,
                    "complexity": complexity,
                    "ai_analysis": ai_analysis["result"]
                }
            )
            
            if agent_response["success"]:
                agents_results[agent["id"]] = agent_response["result"]
            else:
                # Fallback to basic response if AI fails
                agents_results[agent["id"]] = generate_fallback_agent_response(agent["id"], request.prompt)
        
        # Step 4: Create the generated project
        project = GeneratedProject(
            user_id=current_user.id,
            name=project_name,
            description=request.prompt,
            prompt=request.prompt,
            structure=project_structure,
            technologies=technologies,
            agents_results=agents_results,
            ai_analysis={
                "complexity": complexity,
                "time_estimates": time_estimates,
                "ai_insights": ai_analysis["result"],
                "processing_time": ai_analysis["processing_time"]
            }
        )
        
        # Step 5: Store in database
        project_dict = prepare_for_mongo(project.dict())
        await db.generated_projects.insert_one(project_dict)
        
        total_time = time.time() - start_time
        
        logger.info(f"Project generated successfully for user {current_user.id} in {total_time:.2f}s")
        
        return APIResponse(
            success=True,
            message="App generated successfully",
            data={
                "project": project.dict(),
                "generation_time": total_time,
                "ai_powered": True
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"App generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"App generation failed: {str(e)}")

def generate_fallback_agent_response(agent_id: str, prompt: str) -> Dict[str, Any]:
    """Generate fallback response if AI service fails"""
    fallback_responses = {
        "designer": {
            "analysis": "Professional UI/UX design with modern Tailwind CSS components",
            "recommendations": ["Use consistent color palette", "Implement responsive design", "Focus on user experience"],
            "technical_details": {"components": ["Header", "Navigation", "Main Content", "Footer"], "styling": "Tailwind CSS"}
        },
        "frontend": {
            "analysis": "React-based frontend with modern hooks and component architecture",
            "recommendations": ["Use functional components", "Implement proper state management", "Add error boundaries"],
            "technical_details": {"framework": "React 18", "components": ["App.js", "components/"], "libraries": ["React Router", "Axios"]}
        },
        "backend": {
            "analysis": "FastAPI backend with robust API design and authentication",
            "recommendations": ["Implement JWT authentication", "Use proper validation", "Add comprehensive logging"],
            "technical_details": {"endpoints": ["/api/auth", "/api/users"], "technologies": ["FastAPI", "MongoDB"]}
        },
        "database": {
            "analysis": "MongoDB schema design with proper indexing and relationships",
            "recommendations": ["Create proper indexes", "Design normalized schema", "Implement data validation"],
            "technical_details": {"collections": ["users", "projects"], "indexes": ["email", "created_at"]}
        },
        "ai": {
            "analysis": "AI integration using Gemini API for intelligent features",
            "recommendations": ["Use appropriate model selection", "Implement proper error handling", "Cache responses"],
            "technical_details": {"services": ["Text generation"], "provider": "Gemini API"}
        },
        "tester": {
            "analysis": "Comprehensive testing strategy with automated test suites",
            "recommendations": ["Implement unit tests", "Add integration tests", "Use CI/CD pipeline"],
            "technical_details": {"frameworks": ["pytest", "Jest"], "coverage": "90%+"}
        }
    }
    
    return fallback_responses.get(agent_id, {"analysis": "Expert analysis provided", "recommendations": [], "technical_details": {}})

# AI Service Routes
@api_router.post("/ai/analyze", response_model=APIResponse)
async def analyze_with_ai(
    request: AIAnalysisRequest,
    current_user: User = Depends(get_current_user_with_db),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Perform specific AI analysis on user request"""
    try:
        analysis_result = await ai_service.analyze_project_requirements(
            request.prompt, 
            request.analysis_type
        )
        
        if analysis_result["success"]:
            # Store analysis in database
            analysis_data = {
                "user_id": current_user.id,
                "analysis_type": request.analysis_type,
                "prompt": request.prompt,
                "result": analysis_result["result"],
                "processing_time": analysis_result["processing_time"],
                "model_used": analysis_result["model_used"],
                "timestamp": datetime.now(timezone.utc)
            }
            
            await db.ai_analyses.insert_one(prepare_for_mongo(analysis_data))
            
            return APIResponse(
                success=True,
                message="AI analysis completed",
                data=analysis_result
            )
        else:
            raise HTTPException(status_code=500, detail=analysis_result.get("error"))
            
    except Exception as e:
        logger.error(f"AI analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"AI analysis failed: {str(e)}")

# Enhanced Project Management Routes
@api_router.get("/projects", response_model=List[Dict[str, Any]])
async def get_user_projects_endpoint(
    current_user: User = Depends(get_current_user_with_db),
    limit: int = 50,
    skip: int = 0
):
    """Get user's projects with pagination"""
    try:
        projects = await get_user_projects(current_user.id, limit, skip)
        return projects
    except Exception as e:
        logger.error(f"Failed to fetch user projects: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch projects")

@api_router.get("/projects/{project_id}")
async def get_project_endpoint(
    project_id: str,
    current_user: User = Depends(get_current_user_with_db)
):
    """Get a specific project by ID (user must own the project)"""
    try:
        project = await get_project_by_id(project_id, current_user.id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        return project
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch project: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch project")

@api_router.put("/projects/{project_id}", response_model=APIResponse)
async def update_project(
    project_id: str,
    update_data: ProjectUpdate,
    current_user: User = Depends(get_current_user_with_db),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Update project details"""
    try:
        # Verify project ownership
        project = await get_project_by_id(project_id, current_user.id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Prepare update data
        update_dict = {k: v for k, v in update_data.dict().items() if v is not None}
        update_dict["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        # Update in database
        result = await db.generated_projects.update_one(
            {"id": project_id, "user_id": current_user.id},
            {"$set": update_dict}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Project not found or no changes made")
        
        return APIResponse(
            success=True,
            message="Project updated successfully",
            data={"project_id": project_id, "updated_fields": list(update_dict.keys())}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update project: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update project")

@api_router.delete("/projects/{project_id}", response_model=APIResponse)
async def delete_project(
    project_id: str,
    current_user: User = Depends(get_current_user_with_db),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Delete a project"""
    try:
        result = await db.generated_projects.delete_one(
            {"id": project_id, "user_id": current_user.id}
        )
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Project not found")
        
        return APIResponse(
            success=True,
            message="Project deleted successfully",
            data={"project_id": project_id}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete project: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete project")

# Enhanced Export Routes
@api_router.post("/export/{project_id}", response_model=APIResponse)
async def export_project(
    project_id: str,
    current_user: User = Depends(get_current_user_with_db)
):
    """Export project with enhanced documentation and setup instructions"""
    try:
        project = await get_project_by_id(project_id, current_user.id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Enhanced export data with documentation
        export_data = {
            "project_info": {
                "name": project["name"],
                "description": project["description"],
                "created_at": project["created_at"],
                "complexity": project.get("ai_analysis", {}).get("complexity", "medium"),
                "estimated_time": project.get("ai_analysis", {}).get("time_estimates", {})
            },
            "structure": project["structure"],
            "technologies": project["technologies"],
            "setup_instructions": generate_setup_instructions(project),
            "deployment_guide": generate_deployment_guide(project),
            "agents_output": project["agents_results"],
            "ai_insights": project.get("ai_analysis", {}),
            "development_roadmap": generate_development_roadmap(project),
            "best_practices": generate_best_practices(project["technologies"]),
            "environment_setup": generate_environment_config(project)
        }
        
        return APIResponse(
            success=True,
            message="Project exported successfully",
            data={"export_data": export_data}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Project export failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Project export failed")

def generate_setup_instructions(project: Dict[str, Any]) -> List[str]:
    """Generate detailed setup instructions"""
    instructions = [
        "# Project Setup Instructions",
        "",
        "## Prerequisites",
        "- Node.js 18+ and npm/yarn",
        "- Python 3.11+",
        "- MongoDB 5.0+",
        "",
        "## Backend Setup",
        "1. Navigate to the backend directory",
        "2. Create a virtual environment: `python -m venv venv`",
        "3. Activate virtual environment:",
        "   - Windows: `venv\\Scripts\\activate`",
        "   - macOS/Linux: `source venv/bin/activate`",
        "4. Install dependencies: `pip install -r requirements.txt`",
        "5. Copy `.env.example` to `.env` and configure variables",
        "6. Start the server: `uvicorn main:app --reload`",
        "",
        "## Frontend Setup",
        "1. Navigate to the frontend directory",
        "2. Install dependencies: `npm install`",
        "3. Copy `.env.example` to `.env` and configure variables",
        "4. Start development server: `npm run dev`",
        "",
        "## Database Setup",
        "1. Install MongoDB locally or use MongoDB Atlas",
        "2. Create database and configure connection string",
        "3. Run database migrations if applicable",
        "",
        "## Environment Variables",
        "Configure the following environment variables:",
    ]
    
    # Add technology-specific instructions
    technologies = project.get("technologies", [])
    
    if "JWT Authentication" in technologies:
        instructions.extend([
            "- JWT_SECRET_KEY: Generate a secure secret key",
            "- JWT_ALGORITHM: HS256 (recommended)",
            "- JWT_ACCESS_TOKEN_EXPIRE_MINUTES: 30 (or desired duration)"
        ])
    
    if "Gemini API" in technologies:
        instructions.extend([
            "- GEMINI_API_KEY: Your Google Gemini API key",
            "- AI_MODEL: gemini-2.0-flash (or preferred model)"
        ])
    
    if "Stripe API" in technologies:
        instructions.extend([
            "- STRIPE_PUBLIC_KEY: Your Stripe publishable key",
            "- STRIPE_SECRET_KEY: Your Stripe secret key"
        ])
    
    instructions.extend([
        "",
        "## Running the Application",
        "1. Start MongoDB service",
        "2. Start the backend server (port 8000)",
        "3. Start the frontend development server (port 3000)",
        "4. Access the application at http://localhost:3000"
    ])
    
    return instructions

def generate_deployment_guide(project: Dict[str, Any]) -> List[str]:
    """Generate deployment guide"""
    return [
        "# Deployment Guide",
        "",
        "## Production Deployment Options",
        "",
        "### Option 1: Docker Deployment",
        "1. Build Docker images: `docker-compose build`",
        "2. Start services: `docker-compose up -d`",
        "3. Configure reverse proxy (nginx)",
        "",
        "### Option 2: Cloud Deployment",
        "- **Frontend**: Deploy to Vercel, Netlify, or AWS S3+CloudFront",
        "- **Backend**: Deploy to AWS EC2, Google Cloud Run, or Railway",
        "- **Database**: Use MongoDB Atlas or AWS DocumentDB",
        "",
        "### Option 3: VPS Deployment",
        "1. Set up Ubuntu 20.04+ VPS",
        "2. Install Node.js, Python, MongoDB",
        "3. Configure nginx as reverse proxy",
        "4. Set up SSL certificates with Let's Encrypt",
        "5. Configure PM2 for process management",
        "",
        "## Environment Configuration",
        "- Set NODE_ENV=production",
        "- Configure production database URLs",
        "- Set secure JWT secrets",
        "- Enable HTTPS in production",
        "",
        "## Security Considerations",
        "- Use environment variables for all secrets",
        "- Enable CORS for specific domains only",
        "- Implement rate limiting",
        "- Regular security updates"
    ]

def generate_development_roadmap(project: Dict[str, Any]) -> Dict[str, List[str]]:
    """Generate development roadmap"""
    complexity = project.get("ai_analysis", {}).get("complexity", "medium")
    
    roadmaps = {
        "simple": {
            "Phase 1 (Week 1-2)": [
                "Set up project structure",
                "Implement basic authentication",
                "Create core components",
                "Set up database schema"
            ],
            "Phase 2 (Week 3-4)": [
                "Implement main features",
                "Add basic testing",
                "Style with Tailwind CSS",
                "Deploy to staging"
            ],
            "Phase 3 (Week 5-6)": [
                "Add advanced features",
                "Comprehensive testing",
                "Performance optimization",
                "Production deployment"
            ]
        },
        "medium": {
            "Phase 1 (Week 1-3)": [
                "Project setup and architecture",
                "Authentication system",
                "Database design and setup",
                "Core API endpoints"
            ],
            "Phase 2 (Week 4-6)": [
                "Frontend components development",
                "State management implementation",
                "API integration",
                "Basic testing setup"
            ],
            "Phase 3 (Week 7-9)": [
                "Advanced features implementation",
                "Real-time functionality",
                "Comprehensive testing",
                "Security hardening"
            ],
            "Phase 4 (Week 10-12)": [
                "Performance optimization",
                "Documentation completion",
                "Deployment pipeline",
                "Production launch"
            ]
        },
        "complex": {
            "Phase 1 (Week 1-4)": [
                "Architecture design and setup",
                "Core infrastructure",
                "Authentication and authorization",
                "Database architecture"
            ],
            "Phase 2 (Week 5-8)": [
                "Core feature development",
                "API development",
                "Frontend architecture",
                "Integration testing"
            ],
            "Phase 3 (Week 9-12)": [
                "Advanced features",
                "AI integration",
                "Real-time features",
                "Performance optimization"
            ],
            "Phase 4 (Week 13-16)": [
                "Security implementation",
                "Comprehensive testing",
                "Documentation",
                "Deployment and monitoring"
            ]
        }
    }
    
    return roadmaps.get(complexity, roadmaps["medium"])

def generate_best_practices(technologies: List[str]) -> Dict[str, List[str]]:
    """Generate best practices for the technology stack"""
    practices = {
        "General": [
            "Follow consistent coding standards",
            "Use version control effectively (Git)",
            "Write comprehensive documentation",
            "Implement proper error handling",
            "Use environment variables for configuration"
        ],
        "React": [
            "Use functional components with hooks",
            "Implement proper state management",
            "Optimize component re-renders",
            "Use React.memo for expensive components",
            "Follow component composition patterns"
        ],
        "FastAPI": [
            "Use Pydantic models for validation",
            "Implement proper dependency injection",
            "Use async/await for database operations",
            "Add comprehensive API documentation",
            "Implement proper logging"
        ],
        "MongoDB": [
            "Design schema with proper relationships",
            "Create appropriate indexes",
            "Use aggregation pipelines efficiently",
            "Implement proper data validation",
            "Regular backup and monitoring"
        ]
    }
    
    # Add technology-specific practices
    if "JWT Authentication" in technologies:
        practices["Security"] = [
            "Use secure JWT secret keys",
            "Implement token refresh mechanism",
            "Add proper token validation",
            "Use HTTPS in production",
            "Implement rate limiting"
        ]
    
    return practices

def generate_environment_config(project: Dict[str, Any]) -> Dict[str, Dict[str, str]]:
    """Generate environment configuration templates"""
    return {
        "backend": {
            "MONGO_URL": "mongodb://localhost:27017",
            "DB_NAME": "your_app_db",
            "JWT_SECRET_KEY": "your-super-secret-jwt-key-here",
            "JWT_ALGORITHM": "HS256",
            "JWT_ACCESS_TOKEN_EXPIRE_MINUTES": "30",
            "CORS_ORIGINS": "http://localhost:3000",
            "LOG_LEVEL": "INFO"
        },
        "frontend": {
            "REACT_APP_API_URL": "http://localhost:8000/api",
            "REACT_APP_APP_NAME": project.get("name", "My App"),
            "REACT_APP_ENVIRONMENT": "development"
        }
    }

# System and Agent Information Routes
@api_router.get("/agents")
async def get_agents():
    """Get list of available agents with enhanced information"""
    return {"agents": AGENTS}

@api_router.get("/system/status")
async def system_status():
    """Get system status and health check"""
    try:
        # Test database connection
        db = await get_database()
        await db.command("ping")
        db_status = "healthy"
    except:
        db_status = "unhealthy"
    
    try:
        # Test AI service
        test_analysis = await ai_service.analyze_project_requirements("test", "simple")
        ai_status = "healthy" if test_analysis.get("success") else "unhealthy"
    except:
        ai_status = "unhealthy"
    
    return {
        "status": "healthy",
        "database": db_status,
        "ai_service": ai_status,
        "version": "2.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

# Legacy routes for compatibility
@api_router.get("/")
async def root():
    return {"message": "Multi-Agent App Generator API v2.0", "status": "operational"}

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_obj = StatusCheck(**input.dict())
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    return []  # Legacy endpoint, return empty list

# Include the router in the main app
app.include_router(api_router)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Event handlers
@app.on_event("startup")
async def startup_event():
    """Initialize database connection and services"""
    await connect_to_mongo()
    logger.info("Multi-Agent App Generator API v2.0 started successfully")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources"""
    await close_mongo_connection()
    logger.info("API shutdown completed")