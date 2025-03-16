from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase
from database import get_db
from models.subscription import Subscription
from models.tenant import Tenant
from models.user import User
from bson import ObjectId
from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from util.auth import get_current_active_user

# Pydantic models for request/response
class SubscriptionCreate(BaseModel):
    tenant_id: str
    plan: str
    max_users: Optional[int] = None
    billing_cycle: str = "monthly"
    payment_method_id: Optional[str] = None

class SubscriptionUpdate(BaseModel):
    plan: Optional[str] = None
    is_active: Optional[bool] = None
    end_date: Optional[datetime] = None
    renewal_date: Optional[datetime] = None
    billing_cycle: Optional[str] = None
    max_users: Optional[int] = None
    payment_method_id: Optional[str] = None

class SubscriptionUser(BaseModel):
    user_id: str

router = APIRouter(
    prefix="/subscriptions",
    tags=["subscriptions"],
    responses={404: {"description": "Not found"}},
)

@router.get("/")
async def get_subscriptions(
    db: AsyncIOMotorDatabase = Depends(get_db),
    tenant_id: Optional[str] = None,
    is_active: Optional[bool] = True
):
    """Get all subscriptions with optional filtering"""
    if Subscription.collection is None:
        await Subscription.set_collection(db)

    # Build the query
    query = {}
    if tenant_id:
        query["tenant_id"] = tenant_id
    if is_active is not None:
        query["is_active"] = is_active

    subscriptions = await Subscription.find(query)
    return [
        {
            "id": sub.id,
            "tenant_id": sub.tenant_id,
            "plan": sub.plan,
            "is_active": sub.is_active,
            "user_count": len(sub.subscribed_user_ids),
            "max_users": sub.max_users,
            "start_date": sub.start_date,
            "end_date": sub.end_date,
            "renewal_date": sub.renewal_date,
            "billing_cycle": sub.billing_cycle
        }
        for sub in subscriptions
    ]

@router.get("/{subscription_id}")
async def get_subscription(subscription_id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    """Get a specific subscription by ID"""
    if Subscription.collection is None:
        await Subscription.set_collection(db)

    subscription = await Subscription.find_one({"_id": ObjectId(subscription_id)})
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")

    return {
        "id": subscription.id,
        "tenant_id": subscription.tenant_id,
        "plan": subscription.plan,
        "is_active": subscription.is_active,
        "start_date": subscription.start_date,
        "end_date": subscription.end_date,
        "renewal_date": subscription.renewal_date,
        "billing_cycle": subscription.billing_cycle,
        "user_count": len(subscription.subscribed_user_ids),
        "max_users": subscription.max_users,
        "subscribed_user_ids": subscription.subscribed_user_ids,
        "has_available_seats": subscription.has_available_seats()
    }

@router.post("/")
async def create_subscription(subscription: SubscriptionCreate, db: AsyncIOMotorDatabase = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    """Create a new subscription"""
    if Subscription.collection is None:
        await Subscription.set_collection(db)

    # Verify tenant exists
    tenant = await Tenant.find_one(db, {"_id": ObjectId(subscription.tenant_id)})
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    if tenant.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the tenant owner can create subscriptions")

    # Create subscription
    new_subscription = Subscription(
        tenant_id=subscription.tenant_id,
        plan=subscription.plan,
        max_users=subscription.max_users,
        billing_cycle=subscription.billing_cycle,
        payment_method_id=subscription.payment_method_id
    )

    await new_subscription.save()

    return {
        "id": new_subscription.id,
        "tenant_id": new_subscription.tenant_id,
        "plan": new_subscription.plan,
        "is_active": new_subscription.is_active,
        "start_date": new_subscription.start_date,
        "billing_cycle": new_subscription.billing_cycle,
        "max_users": new_subscription.max_users
    }

@router.put("/{subscription_id}")
async def update_subscription(
    subscription_id: str,
    subscription_update: SubscriptionUpdate,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update an existing subscription"""
    if Subscription.collection is None:
        await Subscription.set_collection(db)

    # Find existing subscription
    existing_subscription = await Subscription.find_one({"_id": ObjectId(subscription_id)})
    if not existing_subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")

    # Verify tenant exists
    tenant = await Tenant.find_one(db, {"_id": ObjectId(existing_subscription.tenant_id)})
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    if tenant.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the tenant owner can update this subscription")

    # Update fields
    if subscription_update.plan is not None:
        existing_subscription.plan = subscription_update.plan
    if subscription_update.is_active is not None:
        existing_subscription.is_active = subscription_update.is_active
    if subscription_update.end_date is not None:
        existing_subscription.end_date = subscription_update.end_date
    if subscription_update.renewal_date is not None:
        existing_subscription.renewal_date = subscription_update.renewal_date
    if subscription_update.billing_cycle is not None:
        existing_subscription.billing_cycle = subscription_update.billing_cycle
    if subscription_update.max_users is not None:
        existing_subscription.max_users = subscription_update.max_users
    if subscription_update.payment_method_id is not None:
        existing_subscription.payment_method_id = subscription_update.payment_method_id

    # Save changes
    await existing_subscription.save()

    return {
        "id": existing_subscription.id,
        "tenant_id": existing_subscription.tenant_id,
        "plan": existing_subscription.plan,
        "is_active": existing_subscription.is_active,
        "user_count": len(existing_subscription.subscribed_user_ids),
        "max_users": existing_subscription.max_users,
        "billing_cycle": existing_subscription.billing_cycle,
        "update_successful": True
    }

@router.post("/{subscription_id}/users")
async def add_user_to_subscription(
    subscription_id: str,
    user_data: SubscriptionUser,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Add a user to a subscription"""
    if Subscription.collection is None:
        await Subscription.set_collection(db)

    # Find existing subscription
    subscription = await Subscription.find_one({"_id": ObjectId(subscription_id)})
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")

    #verify if the user is a tenant owner
    tenant = await Tenant.find_one(db, {"_id": ObjectId(subscription.tenant_id)})
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    if tenant.owner_id != current_user.id and "admin" not in current_user.roles:
        raise HTTPException(status_code=403, detail="Only the tenant owner can add users to this subscription")

    # Verify user exists
    user = await User.find_one(db, {"_id": ObjectId(user_data.user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    already_subscribed = user_data.user_id in subscription.subscribed_user_ids
    if already_subscribed:
        raise HTTPException(status_code=400, detail="User is already subscribed")

    # Add user to subscription
    result = await subscription.add_user(user_data.user_id)
    if not result:
        raise HTTPException(status_code=400, detail="Subscription is at maximum capacity")

    return {
        "subscription_id": subscription.id,
        "user_id": user_data.user_id,
        "success": True,
        "user_count": len(subscription.subscribed_user_ids),
        "max_users": subscription.max_users
    }

@router.delete("/{subscription_id}/users/{user_id}")
async def remove_user_from_subscription(
    subscription_id: str,
    user_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Remove a user from a subscription"""
    if Subscription.collection is None:
        await Subscription.set_collection(db)

    # Find existing subscription
    subscription = await Subscription.find_one({"_id": ObjectId(subscription_id)})
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")

    #verify if the user is a tenant owner
    tenant = await Tenant.find_one(db, {"_id": ObjectId(subscription.tenant_id)})
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    if tenant.owner_id != current_user.id and "admin" not in current_user.roles:
        raise HTTPException(status_code=403, detail="Only the tenant owner can remove users from this subscription")

    # Remove user from subscription
    result = await subscription.remove_user(user_id)
    if not result:
        raise HTTPException(status_code=400, detail="User is not subscribed")

    return {
        "subscription_id": subscription.id,
        "user_id": user_id,
        "success": True,
        "user_count": len(subscription.subscribed_user_ids)
    }

@router.get("/{subscription_id}/users")
async def get_subscription_users(subscription_id: str, db: AsyncIOMotorDatabase = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    """Get all users for a subscription"""
    if Subscription.collection is None:
        await Subscription.set_collection(db)

    # Find existing subscription
    subscription = await Subscription.find_one({"_id": ObjectId(subscription_id)})
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")

    #verify if the user is a tenant owner
    tenant = await Tenant.find_one(db, {"_id": ObjectId(subscription.tenant_id)})
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    if tenant.owner_id != current_user.id and "admin" not in current_user.roles:
        raise HTTPException(status_code=403, detail="Only the tenant owner can retrieve subscribed users in this subscription.")

    # Get subscribed users
    users = await subscription.get_subscribed_users(db)

    return [
        {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "is_active": user.is_active
        }
        for user in users
    ]
