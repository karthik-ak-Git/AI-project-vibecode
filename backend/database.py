from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from typing import Optional
import os
from dotenv import load_dotenv
import logging
from datetime import datetime, timezone

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

# MCP Task Management Functions
async def create_mcp_task(task_data: dict):
    """Create a new MCP task"""
    db = await get_database()
    
    # Convert datetime objects to ISO strings for MongoDB storage
    if 'created_at' in task_data and hasattr(task_data['created_at'], 'isoformat'):
        task_data['created_at'] = task_data['created_at'].isoformat()
    if 'updated_at' in task_data and hasattr(task_data['updated_at'], 'isoformat'):
        task_data['updated_at'] = task_data['updated_at'].isoformat()
    
    result = await db.mcp_tasks.insert_one(task_data)
    return str(result.inserted_id)

async def get_mcp_tasks(created_by: str = None, status: str = None, limit: int = 50, skip: int = 0):
    """Get MCP tasks with optional filtering"""
    db = await get_database()
    
    query = {}
    if created_by:
        query["created_by"] = created_by
    if status:
        query["status"] = status
    
    cursor = db.mcp_tasks.find(query)
    cursor = cursor.sort("created_at", -1).skip(skip).limit(limit)
    
    tasks = await cursor.to_list(length=limit)
    for task in tasks:
        if '_id' in task:
            task['_id'] = str(task['_id'])
    
    return tasks

async def get_mcp_task_by_id(task_id: str, created_by: str = None):
    """Get MCP task by ID with optional user validation"""
    db = await get_database()
    
    query = {"id": task_id}
    if created_by:
        query["created_by"] = created_by
    
    task = await db.mcp_tasks.find_one(query)
    if task and '_id' in task:
        task['_id'] = str(task['_id'])
    
    return task

async def update_mcp_task(task_id: str, update_data: dict, created_by: str = None):
    """Update MCP task"""
    db = await get_database()
    
    # Add updated timestamp
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    query = {"id": task_id}
    if created_by:
        query["created_by"] = created_by
    
    result = await db.mcp_tasks.update_one(query, {"$set": update_data})
    return result.modified_count > 0

async def delete_mcp_task(task_id: str, created_by: str = None):
    """Delete MCP task"""
    db = await get_database()
    
    query = {"id": task_id}
    if created_by:
        query["created_by"] = created_by
    
    result = await db.mcp_tasks.delete_one(query)
    return result.deleted_count > 0

# LinkedIn Post Management Functions
async def create_linkedin_post(post_data: dict):
    """Create a LinkedIn post"""
    db = await get_database()
    
    if 'created_at' in post_data and hasattr(post_data['created_at'], 'isoformat'):
        post_data['created_at'] = post_data['created_at'].isoformat()
    if 'scheduled_for' in post_data and hasattr(post_data['scheduled_for'], 'isoformat'):
        post_data['scheduled_for'] = post_data['scheduled_for'].isoformat()
    
    result = await db.linkedin_posts.insert_one(post_data)
    return str(result.inserted_id)

async def get_linkedin_posts(mcp_task_id: str = None, status: str = None, limit: int = 50):
    """Get LinkedIn posts with optional filtering"""
    db = await get_database()
    
    query = {}
    if mcp_task_id:
        query["mcp_task_id"] = mcp_task_id
    if status:
        query["status"] = status
    
    cursor = db.linkedin_posts.find(query)
    cursor = cursor.sort("created_at", -1).limit(limit)
    
    posts = await cursor.to_list(length=limit)
    for post in posts:
        if '_id' in post:
            post['_id'] = str(post['_id'])
    
    return posts

async def update_linkedin_post(post_id: str, update_data: dict):
    """Update LinkedIn post"""
    db = await get_database()
    
    if 'posted_at' in update_data and hasattr(update_data['posted_at'], 'isoformat'):
        update_data['posted_at'] = update_data['posted_at'].isoformat()
    
    result = await db.linkedin_posts.update_one(
        {"id": post_id}, 
        {"$set": update_data}
    )
    return result.modified_count > 0

# Admin Statistics Functions
async def get_admin_stats():
    """Get admin dashboard statistics"""
    db = await get_database()
    
    # Count totals
    total_users = await db.users.count_documents({})
    total_projects = await db.generated_projects.count_documents({})
    total_mcp_tasks = await db.mcp_tasks.count_documents({})
    active_mcp_tasks = await db.mcp_tasks.count_documents({"status": "active"})
    
    # Get recent activity (last 10 projects and tasks)
    recent_projects = await db.generated_projects.find({}).sort("created_at", -1).limit(5).to_list(5)
    recent_tasks = await db.mcp_tasks.find({}).sort("created_at", -1).limit(5).to_list(5)
    
    recent_activity = []
    
    for project in recent_projects:
        recent_activity.append({
            "type": "project",
            "title": f"Project '{project.get('name')}' created",
            "timestamp": project.get('created_at'),
            "user_id": project.get('user_id')
        })
    
    for task in recent_tasks:
        recent_activity.append({
            "type": "mcp_task",
            "title": f"MCP Task '{task.get('name')}' created",
            "timestamp": task.get('created_at'),
            "user_id": task.get('created_by')
        })
    
    # Sort by timestamp
    recent_activity.sort(key=lambda x: x['timestamp'], reverse=True)
    
    return {
        "total_users": total_users,
        "total_projects": total_projects,
        "total_mcp_tasks": total_mcp_tasks,
        "active_mcp_tasks": active_mcp_tasks,
        "recent_activity": recent_activity[:10]
    }

async def get_all_users(limit: int = 50, skip: int = 0):
    """Get all users for admin management"""
    db = await get_database()
    
    cursor = db.users.find({})
    cursor = cursor.sort("created_at", -1).skip(skip).limit(limit)
    
    users = await cursor.to_list(length=limit)
    total_count = await db.users.count_documents({})
    
    for user in users:
        if '_id' in user:
            user['_id'] = str(user['_id'])
        # Don't include sensitive data
        user.pop('hashed_password', None)
        user.pop('session_token', None)
    
    return {
        "users": users,
        "total_count": total_count
    }