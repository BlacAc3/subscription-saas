from beanie import Document, Indexed
from pydantic import Field
from datetime import datetime
from typing import List, Optional, Dict

class User(Document):
    name: str
    email: str = Indexed(unique=True)
    password: str  # Hashed password
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    roles: List[str] = ["user"]  # Global roles (system-wide)
    metadata: Optional[Dict[str, str]] = None

    class Settings:
        name = "users"
        indexes = [
            "email",
            [("name", "created_at"), -1],
        ]

    async def save(self, *args, **kwargs):
        self.updated_at = datetime.utcnow()
        return await super().save(*args, **kwargs)

    async def get_tenants(self):
        """Get all tenants this user belongs to"""
        from subscription import Subscription
        from tenant import Tenant

        # Find subscriptions where this user is a subscribed user
        subscriptions = await Subscription.find({"subscribed_users": str(self.id)}).to_list()

        # Extract the tenant IDs from those subscriptions
        tenant_ids = [sub.tenant_id for sub in subscriptions]

        # Return the tenant objects
        return await Tenant.find({"_id": {"$in": tenant_ids}}).to_list()


    async def get_subscriptions(self):
        """Get all subscriptions for this user"""
        from subscription import Subscription

        # Find all subscriptions where this user is a subscribed user
        return await Subscription.find({"subscribed_users": str(self.id)}).to_list()

    async def get_active_subscription(self):
        """Get the active subscription for this tenant

        An active subscription (is_active=True) implies:
        1. The tenant has paid for the subscription
        2. The subscription is within its valid period (not expired)
        3. Users can access the tenant's services and features
        4. Billing is ongoing according to the billing cycle
        5. The tenant is considered in good standing
        """
        from subscription import Subscription
        return await Subscription.find_one({
            "tenant_id": str(self.id),
            "is_active": True
        })
