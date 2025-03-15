from beanie import Document, Indexed
from pydantic import Field
from datetime import datetime
from typing import Optional, Dict, List

class Subscription(Document):
    tenant_id: str = Indexed()
    subscribed_user_ids: List[str] = []  # List of user IDs who are using this subscription
    plan: str  # ID or name of the subscription plan
    is_active: bool = True
    start_date: datetime = Field(default_factory=datetime.utcnow)
    end_date: Optional[datetime] = None
    renewal_date: Optional[datetime] = None
    billing_cycle: str = "monthly"
    max_users: Optional[int] = None  # Maximum number of users allowed (None = unlimited)
    payment_method_id: Optional[str] = None  # Reference to payment method
    metadata: Optional[Dict[str, str]] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "subscriptions"
        indexes = [
            "tenant_id",
            "created_by_user_id",
            "subscribed_user_ids",
            [("tenant_id", "is_active"), {"unique": False}]
        ]

    async def save(self, *args, **kwargs):
        self.updated_at = datetime.utcnow()
        return await super().save(*args, **kwargs)

    async def get_tenant(self):
        """Get the tenant associated with this subscription"""
        from tenant import Tenant
        return await Tenant.find_one(Tenant.id == self.tenant_id)

    async def get_subscribed_users(self):
        """Get all users subscribed to this subscription"""
        from user import User
        if not self.subscribed_user_ids:
            return []
        return await User.find({"_id": {"$in": self.subscribed_user_ids}}).to_list()

    async def add_user(self, user_id: str) -> bool:
        """
        Add a user to this subscription.

        Returns:
            bool: True if user was added, False if subscription is at capacity
        """
        # Check if we're at max capacity if max_users is set
        if self.max_users is not None and len(self.subscribed_user_ids) >= self.max_users:
            return False

        # Check if user is already subscribed
        if user_id in self.subscribed_user_ids:
            return True

        # Add user to subscription
        self.subscribed_user_ids.append(user_id)
        await self.save()
        return True

    async def remove_user(self, user_id: str) -> bool:
        """
        Remove a user from this subscription.

        Returns:
            bool: True if user was removed, False if user wasn't in the subscription
        """
        if user_id in self.subscribed_user_ids:
            self.subscribed_user_ids.remove(user_id)
            await self.save()
            return True
        return False

    def is_user_subscribed(self, user_id: str) -> bool:
        """Check if a user is subscribed to this subscription"""
        return user_id in self.subscribed_user_ids

    def has_available_seats(self) -> bool:
        """Check if subscription has available seats"""
        if self.max_users is None:
            return True
        return len(self.subscribed_user_ids) < self.max_users
