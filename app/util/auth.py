from datetime import datetime, timedelta
from typing import Optional, Dict, List
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorDatabase
import hashlib
import os
from database import get_db
from models.user import User
from models.tenant import Tenant
from bson import ObjectId

# JWT Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    user_id: Optional[str] = None
    roles: List[str] = []

def hash_password(password: str) -> str:
    """Hash a password for storing"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a stored password against a provided password"""
    return hash_password(plain_password) == hashed_password

async def authenticate_user(db: AsyncIOMotorDatabase, email: str, password: str) -> Optional[User]:
    """Authenticate a user by email and password"""
    user = await User.find_one(db, {"email": email})
    if not user:
        return None
    if not verify_password(password, user.password):
        return None
    return user

def create_access_token(data: Dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a new JWT token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncIOMotorDatabase = Depends(get_db)) -> User:
    """Get the current user from the JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        token_data = TokenData(user_id=user_id, roles=payload.get("roles", []))
    except JWTError:
        raise credentials_exception

    user = await User.find_one(db, {"_id": ObjectId(token_data.user_id)})
    if user is None:
        raise credentials_exception

    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Ensure the user is active"""
    # if not current_user.is_active:
        # raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

async def is_admin(current_user: User = Depends(get_current_active_user)) -> User:
    """Check if the user has admin role"""
    if "admin" not in current_user.roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user

async def is_tenant_owner(tenant_id: str, current_user: User = Depends(get_current_active_user),
                         db: AsyncIOMotorDatabase = Depends(get_db)) -> bool:
    """Check if the user is the owner of a specific tenant"""
    tenant = await Tenant.find_one(db, {"_id": ObjectId(tenant_id)})
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    if tenant.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this tenant"
        )

    return current_user

async def can_access_subscription(subscription_id: str, current_user: User = Depends(get_current_active_user),
                                db: AsyncIOMotorDatabase = Depends(get_db)) -> bool:
    """Check if the user can access a specific subscription"""
    from models.subscription import Subscription

    if Subscription.collection is None:
        await Subscription.set_collection(db)

    subscription = await Subscription.find_one({"_id": ObjectId(subscription_id)})
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")

    # Tenant owners can access all subscriptions for their tenants
    tenant = await Tenant.find_one(db, {"_id": ObjectId(subscription.tenant_id)})
    if tenant and tenant.owner_id == current_user.id:
        return current_user

    # Users who are part of the subscription can access it
    if current_user.id in subscription.subscribed_user_ids:
        return current_user

    # Admins can access all subscriptions
    if "admin" in current_user.roles:
        return current_user

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Not authorized to access this subscription"
    )
