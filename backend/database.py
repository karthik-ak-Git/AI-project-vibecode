from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from typing import Optional
import os
from dotenv import load_dotenv
import logging

load_dotenv()

logger = logging.getLogger(__name__)

class Database:
    client: Optional[AsyncIOMotorClient] = None
    database: Optional[AsyncIOMotorDatabase] = None

database = Database()

async def connect_to_mongo():
    """Create database connection"""
    try:
        mongo_url = os.environ['MONGO_URL']
        database.client = AsyncIOMotorClient(mongo_url)
        database.database = database.client[os.environ['DB_NAME']]
        
        # Test the connection
        await database.database.command("ping")
        logger.info("Successfully connected to MongoDB")
        
        # Create indexes for better performance
        await create_indexes()
        
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise

async def close_mongo_connection():
    """Close database connection"""
    if database.client:
        database.client.close()
        logger.info("Disconnected from MongoDB")

async def get_database() -> AsyncIOMotorDatabase:
    """Get database instance"""
    if database.database is None:
        await connect_to_mongo()
    return database.database

async def create_indexes():
    """Create database indexes for better performance"""
    try:
        db = database.database
        
        # User indexes
        await db.users.create_index("email", unique=True)
        await db.users.create_index("username", unique=True)
        await db.users.create_index("created_at")
        await db.users.create_index("session_token")
        await db.users.create_index("role")
        await db.users.create_index("emergent_auth_id")
        
        # Project indexes  
        await db.generated_projects.create_index("user_id")
        await db.generated_projects.create_index("created_at")
        await db.generated_projects.create_index("name")
        await db.generated_projects.create_index("priority")
        await db.generated_projects.create_index([("user_id", 1), ("created_at", -1)])
        
        # AI Analysis indexes
        await db.ai_analyses.create_index("user_id")
        await db.ai_analyses.create_index("analysis_type")
        await db.ai_analyses.create_index("timestamp")
        
        # Chat indexes
        await db.chat_sessions.create_index("user_id")
        await db.chat_sessions.create_index("created_at")
        await db.chat_messages.create_index("session_id")
        await db.chat_messages.create_index("timestamp")
        
        # MCP Task indexes
        await db.mcp_tasks.create_index("created_by")
        await db.mcp_tasks.create_index("task_type")
        await db.mcp_tasks.create_index("status")
        await db.mcp_tasks.create_index("created_at")
        await db.mcp_tasks.create_index([("created_by", 1), ("status", 1)])
        
        # LinkedIn Post indexes
        await db.linkedin_posts.create_index("mcp_task_id")
        await db.linkedin_posts.create_index("status")
        await db.linkedin_posts.create_index("scheduled_for")
        await db.linkedin_posts.create_index("posted_at")
        
        logger.info("Database indexes created successfully")
        
    except Exception as e:
        logger.error(f"Failed to create indexes: {e}")

# Utility functions for common database operations
async def get_user_projects(user_id: str, limit: int = 50, skip: int = 0):
    """Get user's projects with pagination"""
    db = await get_database()
    cursor = db.generated_projects.find({"user_id": user_id})
    cursor = cursor.sort("created_at", -1).skip(skip).limit(limit)
    
    projects = await cursor.to_list(length=limit)
    for project in projects:
        if '_id' in project:
            project['_id'] = str(project['_id'])
    
    return projects

async def get_project_by_id(project_id: str, user_id: str = None):
    """Get project by ID with optional user validation"""
    db = await get_database()
    
    query = {"id": project_id}
    if user_id:
        query["user_id"] = user_id
    
    project = await db.generated_projects.find_one(query)
    if project and '_id' in project:
        project['_id'] = str(project['_id'])
    
    return project

async def store_ai_analysis(analysis_data: dict):
    """Store AI analysis results"""
    db = await get_database()
    
    # Convert datetime objects to ISO strings for MongoDB storage
    if 'timestamp' in analysis_data and hasattr(analysis_data['timestamp'], 'isoformat'):
        analysis_data['timestamp'] = analysis_data['timestamp'].isoformat()
    
    result = await db.ai_analyses.insert_one(analysis_data)
    return str(result.inserted_id)

async def get_user_ai_analyses(user_id: str, analysis_type: str = None, limit: int = 20):
    """Get user's AI analysis history"""
    db = await get_database()
    
    query = {"user_id": user_id}
    if analysis_type:
        query["analysis_type"] = analysis_type
    
    cursor = db.ai_analyses.find(query).sort("timestamp", -1).limit(limit)
    analyses = await cursor.to_list(length=limit)
    
    for analysis in analyses:
        if '_id' in analysis:
            analysis['_id'] = str(analysis['_id'])
    
    return analyses

async def store_chat_message(message_data: dict):
    """Store chat message"""
    db = await get_database()
    
    if 'timestamp' in message_data and hasattr(message_data['timestamp'], 'isoformat'):
        message_data['timestamp'] = message_data['timestamp'].isoformat()
    
    result = await db.chat_messages.insert_one(message_data)
    return str(result.inserted_id)

async def get_chat_history(session_id: str, limit: int = 50):
    """Get chat history for a session"""
    db = await get_database()
    
    cursor = db.chat_messages.find({"session_id": session_id})
    cursor = cursor.sort("timestamp", 1).limit(limit)
    
    messages = await cursor.to_list(length=limit)
    for message in messages:
        if '_id' in message:
            message['_id'] = str(message['_id'])
    
    return messages