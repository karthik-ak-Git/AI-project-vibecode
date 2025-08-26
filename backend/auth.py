from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import Depends, HTTPException, status, Request, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from motor.motor_asyncio import AsyncIOMotorDatabase
import os
import requests
import secrets
from dotenv import load_dotenv
from models import User, UserInDB, EmergentAuthResponse
from database import get_database

load_dotenv()

# Security configuration
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer(auto_error=False)

SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# Admin email configuration
ADMIN_EMAIL = "kartik986340@gmail.com"

# Emergent OAuth Configuration
EMERGENT_AUTH_API = "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data"

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def generate_session_token() -> str:
    """Generate a secure session token."""
    return secrets.token_urlsafe(32)

def is_admin_email(email: str) -> bool:
    """Check if email belongs to admin."""
    return email.lower() == ADMIN_EMAIL.lower()

async def get_user(db: AsyncIOMotorDatabase, email: str) -> Optional[UserInDB]:
    """Get user by email from database."""
    user_data = await db.users.find_one({"email": email})
    if user_data:
        # Convert ObjectId to string
        if '_id' in user_data:
            user_data['_id'] = str(user_data['_id'])
        return UserInDB(**user_data)
    return None

async def get_user_by_session_token(db: AsyncIOMotorDatabase, session_token: str) -> Optional[UserInDB]:
    """Get user by session token from database."""
    user_data = await db.users.find_one({
        "session_token": session_token,
        "session_expires": {"$gt": datetime.now(timezone.utc)}
    })
    if user_data:
        if '_id' in user_data:
            user_data['_id'] = str(user_data['_id'])
        return UserInDB(**user_data)
    return None

async def authenticate_user(db: AsyncIOMotorDatabase, email: str, password: str) -> Optional[UserInDB]:
    """Authenticate user with email and password."""
    user = await get_user(db, email)
    if not user or not user.hashed_password:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

async def authenticate_with_emergent_oauth(session_id: str) -> Optional[EmergentAuthResponse]:
    """Authenticate user with Emergent OAuth."""
    try:
        headers = {"X-Session-ID": session_id}
        response = requests.get(EMERGENT_AUTH_API, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            return EmergentAuthResponse(**data)
        else:
            return None
    except Exception as e:
        print(f"Emergent OAuth error: {e}")
        return None

async def create_or_update_oauth_user(db: AsyncIOMotorDatabase, oauth_data: EmergentAuthResponse) -> UserInDB:
    """Create or update user from OAuth data."""
    existing_user = await get_user(db, oauth_data.email)
    
    # Generate session token and expiry
    session_token = generate_session_token()
    session_expires = datetime.now(timezone.utc) + timedelta(days=7)
    
    # Determine role based on email
    role = "admin" if is_admin_email(oauth_data.email) else "user"
    
    if existing_user:
        # Update existing user with new session token
        await db.users.update_one(
            {"email": oauth_data.email},
            {
                "$set": {
                    "session_token": session_token,
                    "session_expires": session_expires,
                    "emergent_auth_id": oauth_data.id,
                    "profile_picture": oauth_data.picture,
                    "updated_at": datetime.now(timezone.utc),
                    "role": role  # Update role in case it changed
                }
            }
        )
        
        # Fetch updated user
        updated_user = await get_user(db, oauth_data.email)
        return updated_user
    else:
        # Create new user
        username = oauth_data.email.split('@')[0]  # Use email prefix as username
        new_user = UserInDB(
            email=oauth_data.email,
            username=username,
            full_name=oauth_data.name,
            role=role,
            profile_picture=oauth_data.picture,
            session_token=session_token,
            session_expires=session_expires,
            emergent_auth_id=oauth_data.id,
            hashed_password=None  # OAuth users don't have passwords
        )
        
        # Store in database
        user_dict = new_user.dict()
        # Convert datetime objects to ISO strings
        for key, value in user_dict.items():
            if isinstance(value, datetime):
                user_dict[key] = value.isoformat()
        
        await db.users.insert_one(user_dict)
        return new_user

async def get_current_user_from_cookie_or_header(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncIOMotorDatabase = None
) -> User:
    """Get current authenticated user from session cookie or JWT token."""
    user = None
    
    # First, try to get user from session cookie (Emergent OAuth)
    session_token = request.cookies.get("session_token")
    if session_token:
        user_in_db = await get_user_by_session_token(db, session_token)
        if user_in_db:
            user = User(
                id=user_in_db.id,
                email=user_in_db.email,
                username=user_in_db.username,
                full_name=user_in_db.full_name,
                role=user_in_db.role,
                profile_picture=user_in_db.profile_picture,
                is_active=user_in_db.is_active,
                created_at=user_in_db.created_at,
                updated_at=user_in_db.updated_at
            )
    
    # Fallback to JWT token authentication
    if not user and credentials:
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
        try:
            payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
            email: str = payload.get("sub")
            if email is None:
                raise credentials_exception
        except JWTError:
            raise credentials_exception
        
        user_in_db = await get_user(db, email=email)
        if user_in_db is None:
            raise credentials_exception
        
        user = User(
            id=user_in_db.id,
            email=user_in_db.email,
            username=user_in_db.username,
            full_name=user_in_db.full_name,
            role=user_in_db.role,
            profile_picture=user_in_db.profile_picture,
            is_active=user_in_db.is_active,
            created_at=user_in_db.created_at,
            updated_at=user_in_db.updated_at
        )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user

# Legacy JWT-only authentication (for backwards compatibility)
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncIOMotorDatabase = None
) -> User:
    """Get current authenticated user from JWT token only."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = await get_user(db, email=email)
    if user is None:
        raise credentials_exception
    
    return User(
        id=user.id,
        email=user.email,
        username=user.username,
        full_name=user.full_name,
        role=user.role,
        profile_picture=user.profile_picture,
        is_active=user.is_active,
        created_at=user.created_at,
        updated_at=user.updated_at
    )

async def get_current_active_user(
    request: Request,
    db: AsyncIOMotorDatabase = Depends(get_database)
) -> User:
    """Get current active user."""
    current_user = await get_current_user_from_cookie_or_header(request, None, db)
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

async def require_admin(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """Require admin role."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user

def set_session_cookie(response: Response, session_token: str):
    """Set secure session cookie."""
    response.set_cookie(
        key="session_token",
        value=session_token,
        max_age=7 * 24 * 60 * 60,  # 7 days
        httponly=True,
        secure=True,
        samesite="none",
        path="/"
    )

def clear_session_cookie(response: Response):
    """Clear session cookie."""
    response.delete_cookie(
        key="session_token",
        path="/",
        httponly=True,
        secure=True,
        samesite="none"
    )