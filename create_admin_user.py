#!/usr/bin/env python3
"""
Script to create or update the admin user in the database
"""
import asyncio
import os
from datetime import datetime, timezone
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext

# Load environment variables
load_dotenv('/app/backend/.env')

# Password context for hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Admin credentials
ADMIN_EMAIL = "kartik986340@gmail.com"
ADMIN_PASSWORD = "ak-047-ak"
ADMIN_USERNAME = "admin"
ADMIN_FULL_NAME = "Admin User"

def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)

async def create_admin_user():
    """Create or update admin user in database."""
    
    # Get MongoDB connection details
    mongo_url = os.getenv("MONGO_URL", "mongodb://localhost:27017")
    db_name = os.getenv("DB_NAME", "test_database")
    
    print(f"Connecting to MongoDB: {mongo_url}")
    print(f"Database: {db_name}")
    
    try:
        # Connect to MongoDB
        client = AsyncIOMotorClient(mongo_url)
        db = client[db_name]
        
        # Test connection
        await client.admin.command('ping')
        print("✅ Connected to MongoDB successfully")
        
        # Check if admin user already exists
        existing_user = await db.users.find_one({"email": ADMIN_EMAIL})
        
        # Hash the password
        hashed_password = get_password_hash(ADMIN_PASSWORD)
        
        current_time = datetime.now(timezone.utc)
        
        if existing_user:
            print(f"👤 Admin user already exists: {ADMIN_EMAIL}")
            print("🔄 Updating password...")
            
            # Update existing user with new password
            result = await db.users.update_one(
                {"email": ADMIN_EMAIL},
                {
                    "$set": {
                        "hashed_password": hashed_password,
                        "role": "admin",
                        "is_active": True,
                        "updated_at": current_time,
                        "username": ADMIN_USERNAME,
                        "full_name": ADMIN_FULL_NAME
                    }
                }
            )
            
            if result.modified_count > 0:
                print("✅ Admin user password updated successfully!")
            else:
                print("⚠️ No changes made to admin user")
                
        else:
            print(f"➕ Creating new admin user: {ADMIN_EMAIL}")
            
            # Create new admin user
            admin_user = {
                "email": ADMIN_EMAIL,
                "username": ADMIN_USERNAME,
                "full_name": ADMIN_FULL_NAME,
                "hashed_password": hashed_password,
                "role": "admin",
                "is_active": True,
                "profile_picture": None,
                "session_token": None,
                "session_expires": None,
                "emergent_auth_id": None,
                "created_at": current_time,
                "updated_at": current_time
            }
            
            result = await db.users.insert_one(admin_user)
            print(f"✅ Admin user created successfully with ID: {result.inserted_id}")
        
        # Verify the user was created/updated
        updated_user = await db.users.find_one({"email": ADMIN_EMAIL})
        if updated_user:
            print(f"\n📋 Admin User Details:")
            print(f"   Email: {updated_user['email']}")
            print(f"   Username: {updated_user['username']}")
            print(f"   Full Name: {updated_user['full_name']}")
            print(f"   Role: {updated_user['role']}")
            print(f"   Active: {updated_user['is_active']}")
            print(f"   Created: {updated_user['created_at']}")
            print(f"   Password Hash: {updated_user['hashed_password'][:20]}...")
            
        print(f"\n🎉 Admin can now login with:")
        print(f"   Email: {ADMIN_EMAIL}")
        print(f"   Password: {ADMIN_PASSWORD}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        raise
    finally:
        # Close connection
        client.close()
        print("\n🔌 Database connection closed")

if __name__ == "__main__":
    asyncio.run(create_admin_user())