from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime
from database import get_db
from models.user import User
from util.auth import get_current_active_user, hash_password
from bson import ObjectId
from typing import List, Optional, Dict
from pydantic import BaseModel

# Pydantic models for request/response
class UserCreate(BaseModel):
    name: str
    email: str
    password: str
    roles: Optional[List[str]] = None
    metadata: Optional[Dict[str, str]] = None

# Example request body for testing
"""
{
  "name": "John Doe",
  "email": "john.doe@example.com",
  "password": "securePassword123",
  "roles": ["user", "admin"],
  "metadata": {
    "department": "Engineering",
    "location": "Remote"
  }
}
"""

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None
    roles: Optional[List[str]] = None
    metadata: Optional[Dict[str, str]] = None

class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    is_active: bool
    roles: List[str]
    created_at: datetime
    metadata: Optional[Dict[str, str]] = None

router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={404: {"description": "Not found"}},
)


@router.get("/")
async def get_users(
    db: AsyncIOMotorDatabase = Depends(get_db),
    is_active: Optional[bool] = None,
    current_user: User = Depends(get_current_active_user)
):
    """Get all users with optional filtering"""
    query = {}
    if "admin" not in current_user.roles:
        query["_id"] = ObjectId(current_user.id)

    if is_active is not None:
        query["is_active"] = is_active

    users = await User.find(db, query)
    print(users)
    return [
        {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "is_active": user.is_active,
            "roles": user.roles,
            "created_at": user.created_at
        }
        for user in users
    ]

@router.get("/{user_id}")
async def get_user(user_id: str, db: AsyncIOMotorDatabase = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    """Get a specific user by ID"""

    # Check if the user is requesting their own data or is an admin
    if user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this user data")

    user = await User.find_one(db, {"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "is_active": user.is_active,
        "roles": user.roles,
        "created_at": user.created_at,
        "updated_at": user.updated_at,
        "metadata": user.metadata
    }

@router.post("/")
async def create_user(user: UserCreate, db: AsyncIOMotorDatabase = Depends(get_db)):
    """Create a new user"""
    # Check if email already exists
    existing = await User.find_one(db, {"email": user.email})
    if existing:
        raise HTTPException(status_code=400, detail="A user with this email already exists")
        return

    # Hash the password
    hashed_password = hash_password(user.password)

    # Create user
    new_user = User(
        name=user.name,
        email=user.email,
        password=hashed_password,
        roles=user.roles,
        metadata=user.metadata
    )

    await new_user.save(db)

    return {
        "id": new_user.id,
        "name": new_user.name,
        "email": new_user.email,
        "is_active": new_user.is_active,
        "roles": new_user.roles,
        "created_at": new_user.created_at
    }

@router.put("/{user_id}")
async def update_user(
    user_id: str,
    user_update: UserUpdate,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update an existing user"""

    if user_id != current_user.id or "admin" not in current_user.roles:
        raise HTTPException(status_code=403, detail="Not authorized to update this user")

    existing_user = await User.find_one(db, {"_id": ObjectId(user_id)})
    if not existing_user:
        raise HTTPException(status_code=404, detail="User not found")

    # Update fields
    if user_update.name is not None:
        existing_user.name = user_update.name
    if user_update.email is not None:
        # Check if new email is already in use by another user
        if user_update.email != existing_user.email:
            email_check = await User.find_one(db, {"email": user_update.email})
            if email_check and str(email_check._id) != user_id:
                raise HTTPException(status_code=400, detail="This email is already in use")
        existing_user.email = user_update.email
    if user_update.password is not None:
        existing_user.password = hash_password(user_update.password)
    if user_update.is_active is not None:
        existing_user.is_active = user_update.is_active
    if user_update.roles is not None:
        existing_user.roles = user_update.roles
    if user_update.metadata is not None:
        existing_user.metadata = user_update.metadata

    # Save changes
    await existing_user.save(db)

    return {
        "id": existing_user.id,
        "name": existing_user.name,
        "email": existing_user.email,
        "is_active": existing_user.is_active,
        "roles": existing_user.roles,
        "updated_at": existing_user.updated_at,
        "update_successful": True
    }

@router.get("/{user_id}/tenants")
async def get_user_tenants(user_id: str, db: AsyncIOMotorDatabase = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    """Get all tenants a user belongs to"""

    if user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this information")

    user = await User.find_one(db, {"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    tenants = await user.get_tenants(db)

    return [
        {
            "id": tenant.id,
            "name": tenant.name,
            "domain": tenant.domain,
            "is_active": tenant.is_active
        }
        for tenant in tenants
    ]

@router.get("/{user_id}/owned-tenants")
async def get_user_owned_tenants(user_id: str, db: AsyncIOMotorDatabase = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    """Get all tenants owned by a user"""

    if user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this information")

    user = await User.find_one(db, {"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    tenants = await user.get_owned_tenants(db)

    return [
        {
            "id": tenant.id,
            "name": tenant.name,
            "domain": tenant.domain,
            "is_active": tenant.is_active,
            "created_at": tenant.created_at
        }
        for tenant in tenants
    ]

@router.get("/{user_id}/subscriptions")
async def get_user_subscriptions(user_id: str, db: AsyncIOMotorDatabase = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    """Get all subscriptions a user has"""
    if user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this information")

    user = await User.find_one(db, {"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    subscriptions = await user.get_subscriptions(db)

    return [
        {
            "id": sub.id,
            "tenant_id": sub.tenant_id,
            "plan": sub.plan,
            "is_active": sub.is_active,
            "start_date": sub.start_date,
            "end_date": sub.end_date
        }
        for sub in subscriptions
    ]
