from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, Request, Response
from fastapi.security import HTTPBearer
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
import os
import logging
from pathlib import Path
from datetime import timedelta, datetime, timezone
from typing import List, Dict, Any, Optional
import asyncio
import time

# Import our custom modules
from models import *
from auth import *
from ai_service import AIService
from database import (
    connect_to_mongo, close_mongo_connection, get_database, get_user_projects, get_project_by_id,
    create_mcp_task, get_mcp_tasks, get_mcp_task_by_id, update_mcp_task, delete_mcp_task,
    create_linkedin_post, get_linkedin_posts, update_linkedin_post,
    get_admin_stats, get_all_users
)
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
    title="Multi-Agent App Generator API with Admin Features",
    description="Advanced multi-agent platform for generating web applications with AI and admin MCP management",
    version="3.0.0"
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

# MCP Task Types
MCP_TASK_TYPES = [
    {
        "id": "linkedin_post",
        "name": "LinkedIn Post Automation",
        "description": "Create and schedule LinkedIn posts with content generation",
        "parameters_schema": {
            "content": {"type": "string", "required": True},
            "schedule": {"type": "object", "required": False},
            "media_urls": {"type": "array", "required": False},
            "hashtags": {"type": "array", "required": False}
        }
    },
    {
        "id": "email_campaign",
        "name": "Email Campaign",
        "description": "Create and manage email marketing campaigns",
        "parameters_schema": {
            "subject": {"type": "string", "required": True},
            "content": {"type": "string", "required": True},
            "recipients": {"type": "array", "required": True},
            "schedule": {"type": "object", "required": False}
        }
    },
    {
        "id": "social_media_post",
        "name": "Social Media Post",
        "description": "Cross-platform social media posting automation",
        "parameters_schema": {
            "platforms": {"type": "array", "required": True},
            "content": {"type": "string", "required": True},
            "media_urls": {"type": "array", "required": False},
            "schedule": {"type": "object", "required": False}
        }
    }
]

# Dependencies
async def get_db() -> AsyncIOMotorDatabase:
    """Get database dependency"""
    return await get_database()

async def get_current_user_with_db(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncIOMotorDatabase = Depends(get_db)
) -> User:
    """Get current user with database dependency"""
    return await get_current_user_from_cookie_or_header(request, credentials, db)

# Enhanced Authentication Routes
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
        
        # Determine role based on email
        role = "admin" if is_admin_email(user_data.email) else "user"
        
        # Create new user
        hashed_password = get_password_hash(user_data.password)
        user_in_db = UserInDB(
            email=user_data.email,
            username=user_data.username,
            full_name=user_data.full_name,
            role=role,
            hashed_password=hashed_password
        )
        
        # Store in database
        user_dict = prepare_for_mongo(user_in_db.dict())
        await db.users.insert_one(user_dict)
        
        logger.info(f"New user registered: {user_data.email} as {role}")
        
        return APIResponse(
            success=True,
            message="User registered successfully",
            data={
                "user_id": user_in_db.id, 
                "email": user_in_db.email,
                "role": role
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"User registration failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Registration failed")

@api_router.post("/auth/login", response_model=Token)
async def login_user(
    user_credentials: UserLogin,
    response: Response,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Authenticate user and return JWT token + session cookie"""
    try:
        user = await authenticate_user(db, user_credentials.email, user_credentials.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Create session token for cookie-based auth
        session_token = generate_session_token()
        session_expires = datetime.now(timezone.utc) + timedelta(days=7)
        
        # Update user with session token
        await db.users.update_one(
            {"email": user.email},
            {
                "$set": {
                    "session_token": session_token,
                    "session_expires": session_expires.isoformat()
                }
            }
        )
        
        # Set secure session cookie
        set_session_cookie(response, session_token)
        
        # Create JWT access token (for backward compatibility)
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.email}, expires_delta=access_token_expires
        )
        
        logger.info(f"User logged in: {user.email} (Role: {user.role})")
        
        return Token(access_token=access_token, token_type="bearer")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Login failed")

@api_router.post("/auth/oauth/callback", response_model=APIResponse)
async def oauth_callback(
    request: Request,
    response: Response,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Handle Emergent OAuth callback"""
    try:
        # Get session ID from request
        data = await request.json()
        session_id = data.get("session_id")
        
        if not session_id:
            raise HTTPException(status_code=400, detail="Session ID required")
        
        # Authenticate with Emergent OAuth
        oauth_data = await authenticate_with_emergent_oauth(session_id)
        if not oauth_data:
            raise HTTPException(status_code=401, detail="OAuth authentication failed")
        
        # Create or update user
        user = await create_or_update_oauth_user(db, oauth_data)
        
        # Set secure session cookie
        set_session_cookie(response, user.session_token)
        
        logger.info(f"OAuth login successful: {user.email} (Role: {user.role})")
        
        return APIResponse(
            success=True,
            message="OAuth authentication successful",
            data={
                "user_id": user.id,
                "email": user.email,
                "role": user.role,
                "username": user.username,
                "full_name": user.full_name,
                "profile_picture": user.profile_picture
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OAuth callback failed: {str(e)}")
        raise HTTPException(status_code=500, detail="OAuth authentication failed")

@api_router.post("/auth/logout", response_model=APIResponse)
async def logout_user(
    request: Request,
    response: Response,
    current_user: User = Depends(get_current_user_with_db),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Logout user and clear session"""
    try:
        # Clear session token from database
        await db.users.update_one(
            {"id": current_user.id},
            {
                "$unset": {
                    "session_token": "",
                    "session_expires": ""
                }
            }
        )
        
        # Clear session cookie
        clear_session_cookie(response)
        
        logger.info(f"User logged out: {current_user.email}")
        
        return APIResponse(
            success=True,
            message="Logged out successfully"
        )
        
    except Exception as e:
        logger.error(f"Logout failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Logout failed")

@api_router.get("/auth/me", response_model=APIResponse)
async def read_users_me(current_user: User = Depends(get_current_user_with_db)):
    """Get current user information"""
    return APIResponse(
        success=True,
        message="User information retrieved",
        data={
            "id": current_user.id,
            "email": current_user.email,
            "username": current_user.username,
            "full_name": current_user.full_name,
            "role": current_user.role,
            "profile_picture": current_user.profile_picture,
            "is_active": current_user.is_active,
            "created_at": current_user.created_at.isoformat() if current_user.created_at else None
        }
    )

# Enhanced Project Generation Routes
@api_router.post("/generate", response_model=APIResponse)
async def generate_app(
    request: AppGenerationRequest,
    current_user: User = Depends(get_current_user_with_db),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Enhanced app generation with role-based priority"""
    if not request.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt cannot be empty")
    
    try:
        start_time = time.time()
        
        # Set priority based on user role
        priority = request.priority if current_user.role == "admin" else "normal"
        
        # Step 1: AI-powered analysis of the prompt
        logger.info(f"Starting AI analysis for user {current_user.id} (Role: {current_user.role})")
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
                    "ai_analysis": ai_analysis["result"],
                    "user_role": current_user.role,
                    "priority": priority
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
            priority=priority,
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
        
        logger.info(f"Project generated successfully for user {current_user.id} in {total_time:.2f}s (Priority: {priority})")
        
        return APIResponse(
            success=True,
            message="App generated successfully",
            data={
                "project": project.dict(),
                "generation_time": total_time,
                "ai_powered": True,
                "priority": priority
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
@api_router.get("/projects", response_model=APIResponse)
async def get_user_projects_endpoint(
    current_user: User = Depends(get_current_user_with_db),
    limit: int = 50,
    skip: int = 0
):
    """Get user's projects with pagination"""
    try:
        projects = await get_user_projects(current_user.id, limit, skip)
        return APIResponse(
            success=True,
            message="Projects retrieved successfully",
            data={"projects": projects}
        )
    except Exception as e:
        logger.error(f"Failed to fetch user projects: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch projects")

@api_router.get("/projects/{project_id}", response_model=APIResponse)
async def get_project_endpoint(
    project_id: str,
    current_user: User = Depends(get_current_user_with_db)
):
    """Get a specific project by ID (user must own the project)"""
    try:
        project = await get_project_by_id(project_id, current_user.id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        return APIResponse(
            success=True,
            message="Project retrieved successfully",
            data={"project": project}
        )
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
        
        # Admin can set higher priorities
        update_dict = {k: v for k, v in update_data.dict().items() if v is not None}
        if "priority" in update_dict and current_user.role != "admin":
            if update_dict["priority"] in ["high", "urgent"]:
                update_dict["priority"] = "normal"  # Non-admin users limited to normal priority
        
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
                "estimated_time": project.get("ai_analysis", {}).get("time_estimates", {}),
                "priority": project.get("priority", "normal")
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

# ADMIN-ONLY ROUTES
@api_router.get("/admin/stats", response_model=APIResponse)
async def get_admin_dashboard_stats(
    current_user: User = Depends(require_admin)
):
    """Get admin dashboard statistics"""
    try:
        stats = await get_admin_stats()
        return APIResponse(
            success=True,
            message="Admin stats retrieved successfully",
            data=stats
        )
    except Exception as e:
        logger.error(f"Failed to get admin stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get admin stats")

@api_router.get("/admin/users", response_model=APIResponse)
async def get_all_users_admin(
    current_user: User = Depends(require_admin),
    limit: int = 50,
    skip: int = 0
):
    """Get all users for admin management"""
    try:
        result = await get_all_users(limit, skip)
        return APIResponse(
            success=True,
            message="Users retrieved successfully",
            data=result
        )
    except Exception as e:
        logger.error(f"Failed to get users: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get users")

# MCP Task Management Routes (Admin Only)
@api_router.post("/admin/mcp/tasks", response_model=APIResponse)
async def create_mcp_task_endpoint(
    task_data: MCPTaskCreate,
    current_user: User = Depends(require_admin),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Create a new MCP task (Admin only)"""
    try:
        mcp_task = MCPTask(
            created_by=current_user.id,
            task_type=task_data.task_type,
            name=task_data.name,
            description=task_data.description,
            parameters=task_data.parameters,
            schedule=task_data.schedule
        )
        
        task_dict = prepare_for_mongo(mcp_task.dict())
        task_id = await create_mcp_task(task_dict)
        
        logger.info(f"MCP task created by admin {current_user.email}: {task_data.name}")
        
        return APIResponse(
            success=True,
            message="MCP task created successfully",
            data={"task_id": mcp_task.id, "task": mcp_task.dict()}
        )
        
    except Exception as e:
        logger.error(f"Failed to create MCP task: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create MCP task")

@api_router.get("/admin/mcp/tasks", response_model=APIResponse)
async def get_mcp_tasks_endpoint(
    current_user: User = Depends(require_admin),
    status: Optional[str] = None,
    limit: int = 50,
    skip: int = 0
):
    """Get MCP tasks (Admin only)"""
    try:
        tasks = await get_mcp_tasks(current_user.id, status, limit, skip)
        return APIResponse(
            success=True,
            message="MCP tasks retrieved successfully",
            data={"tasks": tasks}
        )
    except Exception as e:
        logger.error(f"Failed to get MCP tasks: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get MCP tasks")

@api_router.get("/admin/mcp/tasks/{task_id}", response_model=APIResponse)
async def get_mcp_task_endpoint(
    task_id: str,
    current_user: User = Depends(require_admin)
):
    """Get specific MCP task (Admin only)"""
    try:
        task = await get_mcp_task_by_id(task_id, current_user.id)
        if not task:
            raise HTTPException(status_code=404, detail="MCP task not found")
        
        return APIResponse(
            success=True,
            message="MCP task retrieved successfully",
            data={"task": task}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get MCP task: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get MCP task")

@api_router.put("/admin/mcp/tasks/{task_id}", response_model=APIResponse)
async def update_mcp_task_endpoint(
    task_id: str,
    update_data: MCPTaskUpdate,
    current_user: User = Depends(require_admin)
):
    """Update MCP task (Admin only)"""
    try:
        update_dict = {k: v for k, v in update_data.dict().items() if v is not None}
        
        success = await update_mcp_task(task_id, update_dict, current_user.id)
        if not success:
            raise HTTPException(status_code=404, detail="MCP task not found")
        
        return APIResponse(
            success=True,
            message="MCP task updated successfully",
            data={"task_id": task_id, "updated_fields": list(update_dict.keys())}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update MCP task: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update MCP task")

@api_router.delete("/admin/mcp/tasks/{task_id}", response_model=APIResponse)
async def delete_mcp_task_endpoint(
    task_id: str,
    current_user: User = Depends(require_admin)
):
    """Delete MCP task (Admin only)"""
    try:
        success = await delete_mcp_task(task_id, current_user.id)
        if not success:
            raise HTTPException(status_code=404, detail="MCP task not found")
        
        return APIResponse(
            success=True,
            message="MCP task deleted successfully",
            data={"task_id": task_id}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete MCP task: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete MCP task")

@api_router.get("/admin/mcp/task-types", response_model=APIResponse)
async def get_mcp_task_types(
    current_user: User = Depends(require_admin)
):
    """Get available MCP task types (Admin only)"""
    return APIResponse(
        success=True,
        message="MCP task types retrieved successfully",
        data={"task_types": MCP_TASK_TYPES}
    )

# LinkedIn Post Management Routes (Admin Only)
@api_router.post("/admin/linkedin/posts", response_model=APIResponse)
async def create_linkedin_post_endpoint(
    mcp_task_id: str,
    post_data: LinkedInPostCreate,
    current_user: User = Depends(require_admin)
):
    """Create LinkedIn post for MCP task (Admin only)"""
    try:
        # Verify MCP task exists and belongs to admin
        task = await get_mcp_task_by_id(mcp_task_id, current_user.id)
        if not task:
            raise HTTPException(status_code=404, detail="MCP task not found")
        
        linkedin_post = LinkedInPost(
            mcp_task_id=mcp_task_id,
            content=post_data.content,
            media_urls=post_data.media_urls,
            scheduled_for=post_data.scheduled_for
        )
        
        post_dict = prepare_for_mongo(linkedin_post.dict())
        post_id = await create_linkedin_post(post_dict)
        
        logger.info(f"LinkedIn post created by admin {current_user.email} for task {mcp_task_id}")
        
        return APIResponse(
            success=True,
            message="LinkedIn post created successfully",
            data={"post_id": linkedin_post.id, "post": linkedin_post.dict()}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create LinkedIn post: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create LinkedIn post")

@api_router.get("/admin/linkedin/posts", response_model=APIResponse)
async def get_linkedin_posts_endpoint(
    current_user: User = Depends(require_admin),
    mcp_task_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50
):
    """Get LinkedIn posts (Admin only)"""
    try:
        posts = await get_linkedin_posts(mcp_task_id, status, limit)
        return APIResponse(
            success=True,
            message="LinkedIn posts retrieved successfully",
            data={"posts": posts}
        )
    except Exception as e:
        logger.error(f"Failed to get LinkedIn posts: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get LinkedIn posts")

# System and Agent Information Routes
@api_router.get("/agents")
async def get_agents():
    """Get list of available agents with enhanced information"""
    return APIResponse(
        success=True,
        message="Agents retrieved successfully",
        data={"agents": AGENTS}
    )

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
    
    return APIResponse(
        success=True,
        message="System status retrieved",
        data={
            "status": "healthy",
            "database": db_status,
            "ai_service": ai_status,
            "version": "3.0.0",
            "features": ["multi_agent_generation", "admin_mcp_management", "oauth_auth"],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    )

# Legacy routes for compatibility
@api_router.get("/")
async def root():
    return APIResponse(
        success=True,
        message="Multi-Agent App Generator API v3.0 with Admin Features",
        data={"status": "operational", "version": "3.0.0"}
    )

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
    logger.info("Multi-Agent App Generator API v3.0 with Admin Features started successfully")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources"""
    await close_mongo_connection()
    logger.info("API shutdown completed")