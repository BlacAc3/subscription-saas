from beanie import Document, Indexed
from pydantic import Field
from datetime import datetime
from typing import Optional, Dict

class Tenant(Document):
    name: str
    domain:str = Indexed(unique=True) #Using Indexed for efficient lookups
    owner_id: str  # ID of the user who created the tenant
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True
    billing_address: Optional[str] = None
    contact_email: Optional[str] = None  # Separate contact email for the tenant
    metadata: Optional[Dict[str, str]] = None  # For storing additional tenant-specific data

    class Settings:
        name = "tenants"

    async def save(self, *args, **kwargs):
        self.updated_at = datetime.utcnow()
        return await super().save(*args, **kwargs)

    async def get_subscribed_users(self):
        """Get all users subscribed with this tenant"""
        from subscription import Subscription

        subscriptions = await Subscription.find(Subscription.tenant_id == str(self.id)).to_list()
        all_user_ids = []
        for subscription in subscriptions:
            if hasattr(subscription, 'subscribed_users'):
                all_user_ids.extend(subscription.subscribed_users)

        return len(all_user_ids)
        # return await User.find({"_id": {"$in": all_user_ids}}).to_list()


    async def get_subscriptions(self):
        """Get all subscriptions owned by this tenant"""
        from subscription import Subscription
        return await Subscription.find(Subscription.tenant_id == str(self.id)).to_list()

    async def is_user_subscribed(self, user_id: str) -> bool:
        """Check if a specific user is subscribed to this tenant

        Args:
            user_id: The ID of the user to check

        Returns:
            bool: True if the user is subscribed, False otherwise
        """
        from subscription import Subscription

        subscriptions = await Subscription.find(Subscription.tenant_id == str(self.id)).to_list()

        for subscription in subscriptions:
            if hasattr(subscription, 'subscribed_users') and user_id in subscription.subscribed_users and subscription.is_active:
                return True

        return False
