from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase
from database import get_db
from models.tenant import Tenant
from models.user import User
from bson import ObjectId
from typing import Optional, Dict
from pydantic import BaseModel
from util.auth import get_current_active_user

# Pydantic models for request/response
class TenantCreate(BaseModel):
    name: str
    domain: str
    owner_id: str
    contact_email: Optional[str] = None
    billing_address: Optional[str] = None
    metadata: Optional[Dict[str, str]] = None

class TenantUpdate(BaseModel):
    name: Optional[str] = None
    domain: Optional[str] = None
    is_active: Optional[bool] = None
    contact_email: Optional[str] = None
    billing_address: Optional[str] = None
    metadata: Optional[Dict[str, str]] = None

router = APIRouter(
    prefix="/tenants",
    tags=["tenants"],
    responses={404: {"description": "Not found"}},
)

@router.get("/")
async def get_tenants(
    db: AsyncIOMotorDatabase = Depends(get_db),
    owner_id: Optional[str] = None,
    is_active: Optional[bool] = None
):
    """Get all tenants with optional filtering"""
    query = {}
    if owner_id:
        query["owner_id"] = owner_id
    if is_active is not None:
        query["is_active"] = is_active

    tenants = await Tenant.find(db, query)
    return [
        {
            "id": tenant.id,
            "name": tenant.name,
            "domain": tenant.domain,
            "owner_id": tenant.owner_id,
            "is_active": tenant.is_active,
            "created_at": tenant.created_at
        }
        for tenant in tenants
    ]

@router.get("/{tenant_id}")
async def get_tenant(tenant_id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    """Get a specific tenant by ID"""
    tenant = await Tenant.find_one(db, {"_id": ObjectId(tenant_id)})
    if tenant is None:
        raise HTTPException(status_code=404, detail="Tenant not found")

    # Get subscriptions for this tenant
    subscriptions = await tenant.get_subscriptions(db)

    return {
        "id": tenant.id,
        "name": tenant.name,
        "domain": tenant.domain,
        "owner_id": tenant.owner_id,
        "is_active": tenant.is_active,
        "created_at": tenant.created_at,
        "updated_at": tenant.updated_at,
        "billing_address": tenant.billing_address,
        "contact_email": tenant.contact_email,
        "metadata": tenant.metadata,
        "subscription_count": len(subscriptions)
    }

@router.post("/")
async def create_tenant(tenant: TenantCreate, db: AsyncIOMotorDatabase = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    """Create a new tenant"""

    if tenant.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Unauthorized")

    # Verify owner exists
    owner = await User.find_one(db, {"_id": ObjectId(tenant.owner_id)})
    if owner is None:
        raise HTTPException(status_code=404, detail="Owner user not found")

    # Check if domain already exists
    existing = await Tenant.find_one(db, {"domain": tenant.domain})
    if existing is not None:
        raise HTTPException(status_code=400, detail="A tenant with this domain already exists")

    # Create tenant
    new_tenant = Tenant(
        name=tenant.name,
        domain=tenant.domain,
        owner_id=tenant.owner_id,
        contact_email=tenant.contact_email,
        billing_address=tenant.billing_address,
        metadata=tenant.metadata
    )

    await new_tenant.save(db)

    return {
        "id": new_tenant.id,
        "name": new_tenant.name,
        "domain": new_tenant.domain,
        "owner_id": new_tenant.owner_id,
        "created_at": new_tenant.created_at
    }

@router.put("/{tenant_id}")
async def update_tenant(
    tenant_id: str,
    tenant_update: TenantUpdate,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update an existing tenant"""
    existing_tenant = await Tenant.find_one(db, {"_id": ObjectId(tenant_id)})
    if existing_tenant is None:
        raise HTTPException(status_code=404, detail="Tenant not found")


    if existing_tenant.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this tenant")

    # Update fields
    if tenant_update.name is not None:
        existing_tenant.name = tenant_update.name
    if tenant_update.domain is not None:
        # Check if new domain is already in use by another tenant
        if tenant_update.domain != existing_tenant.domain:
            domain_check = await Tenant.find_one(db, {"domain": tenant_update.domain})
            if domain_check and str(domain_check._id) != tenant_id:
                raise HTTPException(status_code=400, detail="This domain is already in use")
        existing_tenant.domain = tenant_update.domain
    if tenant_update.is_active is not None:
        existing_tenant.is_active = tenant_update.is_active
    if tenant_update.contact_email is not None:
        existing_tenant.contact_email = tenant_update.contact_email
    if tenant_update.billing_address is not None:
        existing_tenant.billing_address = tenant_update.billing_address
    if tenant_update.metadata is not None:
        existing_tenant.metadata = tenant_update.metadata

    # Save changes
    await existing_tenant.save(db)

    return {
        "id": existing_tenant.id,
        "name": existing_tenant.name,
        "domain": existing_tenant.domain,
        "is_active": existing_tenant.is_active,
        "updated_at": existing_tenant.updated_at,
        "update_successful": True
    }

@router.get("/{tenant_id}/subscriptions")
async def get_tenant_subscriptions(tenant_id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    """Get all subscriptions for a tenant"""
    tenant = await Tenant.find_one(db, {"_id": ObjectId(tenant_id)})
    if tenant is None:
        raise HTTPException(status_code=404, detail="Tenant not found")

    subscriptions = await tenant.get_subscriptions(db)

    return [
        {
            "id": sub.id,
            "plan": sub.plan,
            "is_active": sub.is_active,
            "start_date": sub.start_date,
            "end_date": sub.end_date,
            "user_count": len(sub.subscribed_user_ids),
            "max_users": sub.max_users
        }
        for sub in subscriptions
    ]

@router.get("/{tenant_id}/users")
async def get_tenant_users(tenant_id: str, db: AsyncIOMotorDatabase = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    """Get all users subscribed to a tenant"""
    tenant = await Tenant.find_one(db, {"_id": ObjectId(tenant_id)})
    if tenant is None:
        raise HTTPException(status_code=404, detail="Tenant not found")

    if tenant.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this tenant")

    users = await tenant.get_subscribed_users(db)

    return [
        {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "is_active": user.is_active
        }
        for user in users
    ]
