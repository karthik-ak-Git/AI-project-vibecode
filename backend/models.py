from pydantic import BaseModel, Field, EmailStr
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import uuid

# User Models with Role System
class UserRole(BaseModel):
    name: str  # "admin" or "user"
    permissions: List[str] = []

class UserBase(BaseModel):
    email: EmailStr
    username: str
    full_name: Optional[str] = None
    role: str = "user"  # "admin" or "user"
    profile_picture: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserInDB(UserBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    hashed_password: Optional[str] = None  # Optional for OAuth users
    session_token: Optional[str] = None
    session_expires: Optional[datetime] = None
    emergent_auth_id: Optional[str] = None  # For Emergent OAuth
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class User(UserBase):
    id: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class SessionToken(BaseModel):
    session_token: str
    expires_at: datetime

# OAuth Models
class EmergentAuthResponse(BaseModel):
    id: str
    email: str
    name: str
    picture: str
    session_token: str

# MCP (Automation Tasks) Models
class MCPTaskType(BaseModel):
    id: str
    name: str  # "linkedin_post", "email_campaign", "social_media", etc.
    description: str
    parameters_schema: Dict[str, Any]  # JSON schema for task parameters

class MCPTask(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_by: str  # Admin user ID
    task_type: str  # Type of automation
    name: str
    description: str
    parameters: Dict[str, Any]  # Task-specific parameters
    status: str = "draft"  # "draft", "active", "paused", "completed", "failed"
    schedule: Optional[Dict[str, Any]] = None  # Scheduling information
    execution_count: int = 0
    last_executed: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class MCPTaskCreate(BaseModel):
    task_type: str
    name: str
    description: str
    parameters: Dict[str, Any]
    schedule: Optional[Dict[str, Any]] = None

class MCPTaskUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    status: Optional[str] = None
    schedule: Optional[Dict[str, Any]] = None

# LinkedIn Post Automation Models
class LinkedInPost(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    mcp_task_id: str
    content: str
    media_urls: List[str] = []
    scheduled_for: Optional[datetime] = None
    posted_at: Optional[datetime] = None
    engagement_metrics: Dict[str, int] = {}  # likes, comments, shares, etc.
    status: str = "draft"  # "draft", "scheduled", "posted", "failed"
    linkedin_post_id: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class LinkedInPostCreate(BaseModel):
    content: str
    media_urls: List[str] = []
    scheduled_for: Optional[datetime] = None

# Project Models (Enhanced)
class AppGenerationRequest(BaseModel):
    prompt: str
    user_preferences: Optional[Dict[str, Any]] = None
    ai_model: Optional[str] = "gemini-2.0-flash"  # Default to Gemini
    priority: str = "normal"  # "low", "normal", "high", "urgent" (admin can set higher priorities)

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
    user_id: str
    name: str
    description: str
    prompt: str
    structure: Dict[str, List[str]]
    technologies: List[str]
    agents_results: Dict[str, Dict[str, Any]]
    ai_analysis: Optional[Dict[str, Any]] = None
    status: str = "completed"
    priority: str = "normal"  # Admin projects can have higher priority
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None

# AI Service Models
class AIAnalysisRequest(BaseModel):
    prompt: str
    analysis_type: str  # "project_structure", "technology_stack", "agent_tasks"
    context: Optional[Dict[str, Any]] = None

class AIAnalysisResponse(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    analysis_type: str
    result: Dict[str, Any]
    confidence_score: float
    processing_time: float
    model_used: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# System Models
class StatusCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class StatusCheckCreate(BaseModel):
    client_name: str

class APIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

# Chat/Session Models for AI persistence
class ChatMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    user_id: str
    message_type: str  # "user", "assistant", "system"
    content: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ChatSession(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    project_id: Optional[str] = None
    session_name: str
    model_used: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_active: bool = True

# Admin Dashboard Models
class AdminStats(BaseModel):
    total_users: int
    total_projects: int
    total_mcp_tasks: int
    active_mcp_tasks: int
    recent_activity: List[Dict[str, Any]]

class UserManagement(BaseModel):
    users: List[User]
    total_count: int
    page: int
    per_page: int