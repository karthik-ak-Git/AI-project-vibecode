#!/usr/bin/env python3
"""
Script to create admin user for testing
"""
import asyncio
import sys
import os
sys.path.append('/app/backend')

from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
from datetime import datetime, timezone
import uuid

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def create_admin_user():
    """Create admin user with specific credentials"""
    try:
        # Connect to MongoDB
        mongo_url = "mongodb://localhost:27017"
        client = AsyncIOMotorClient(mongo_url)
        db = client["test_database"]
        
        # Test connection
        await db.command("ping")
        print("✅ Connected to MongoDB")
        
        # Admin user details
        admin_email = "kartik986340@gmail.com"
        admin_password = "ak-047-ak"
        
        # Check if admin user already exists
        existing_user = await db.users.find_one({"email": admin_email})
        
        if existing_user:
            print(f"⚠️ Admin user {admin_email} already exists")
            # Update password
            hashed_password = pwd_context.hash(admin_password)
            await db.users.update_one(
                {"email": admin_email},
                {
                    "$set": {
                        "hashed_password": hashed_password,
                        "role": "admin",
                        "updated_at": datetime.now(timezone.utc).isoformat()
                    }
                }
            )
            print(f"✅ Updated admin user password and role")
        else:
            # Create new admin user
            hashed_password = pwd_context.hash(admin_password)
            admin_user = {
                "id": str(uuid.uuid4()),
                "email": admin_email,
                "username": "kartik986340",
                "full_name": "Kartik Admin",
                "role": "admin",
                "hashed_password": hashed_password,
                "profile_picture": None,
                "is_active": True,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            
            await db.users.insert_one(admin_user)
            print(f"✅ Created admin user: {admin_email}")
        
        # Verify the user was created/updated
        user = await db.users.find_one({"email": admin_email})
        if user:
            print(f"✅ Admin user verified:")
            print(f"   Email: {user['email']}")
            print(f"   Role: {user['role']}")
            print(f"   Username: {user['username']}")
            print(f"   Active: {user['is_active']}")
        
        client.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🔧 Creating admin user...")
    success = asyncio.run(create_admin_user())
    if success:
        print("✅ Admin user setup completed!")
    else:
        print("❌ Admin user setup failed!")
        sys.exit(1)