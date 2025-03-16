from datetime import datetime
from typing import Optional, Dict, List
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

class Subscription:
    collection = None  # This will be set during initialization

    @classmethod
    async def set_collection(cls, db: AsyncIOMotorDatabase):
        """Set the collection for the Subscription class"""
        cls.collection = db.subscriptions
        # Create indexes
        await cls.collection.create_index("tenant_id")
        await cls.collection.create_index([("tenant_id", 1), ("is_active", 1)])

    def __init__(self,
                 tenant_id: str,
                 plan: str,
                 _id: Optional[str] = None,
                 subscribed_user_ids: List[str] = None,
                 is_active: bool = True,
                 start_date: datetime = None,
                 end_date: Optional[datetime] = None,
                 renewal_date: Optional[datetime] = None,
                 billing_cycle: str = "monthly",
                 max_users: Optional[int] = None,
                 payment_method_id: Optional[str] = None,
                 metadata: Optional[Dict[str, str]] = None,
                 updated_at: datetime = None
                 ):

        self._id = ObjectId(_id) if _id else ObjectId()
        self.tenant_id = tenant_id
        self.subscribed_user_ids = subscribed_user_ids or []
        self.plan = plan
        self.is_active = is_active
        self.start_date = start_date or datetime.utcnow()
        self.end_date = end_date
        self.renewal_date = renewal_date
        self.billing_cycle = billing_cycle
        self.max_users = max_users
        self.payment_method_id = payment_method_id
        self.metadata = metadata
        self.updated_at = updated_at or datetime.utcnow()

    @property
    def id(self):
        return str(self._id)

    @classmethod
    def from_db_dict(cls, data: dict) -> Optional['Subscription']:
        """Create a Subscription instance from a database dictionary"""
        if data is None:
            return None
        return cls(
            _id=str(data.get("_id")),
            tenant_id=data.get("tenant_id"),
            subscribed_user_ids=data.get("subscribed_user_ids", []),
            plan=data.get("plan"),
            is_active=data.get("is_active", True),
            start_date=data.get("start_date"),
            end_date=data.get("end_date"),
            renewal_date=data.get("renewal_date"),
            billing_cycle=data.get("billing_cycle", "monthly"),
            max_users=data.get("max_users"),
            payment_method_id=data.get("payment_method_id"),
            metadata=data.get("metadata"),
            updated_at=data.get("updated_at", datetime.utcnow())
        )

    def to_db_dict(self) -> dict:
        """Convert the subscription to a dictionary for database storage"""
        return {
            "_id": self._id,
            "tenant_id": self.tenant_id,
            "subscribed_user_ids": self.subscribed_user_ids,
            "plan": self.plan,
            "is_active": self.is_active,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "renewal_date": self.renewal_date,
            "billing_cycle": self.billing_cycle,
            "max_users": self.max_users,
            "payment_method_id": self.payment_method_id,
            "metadata": self.metadata,
            "updated_at": self.updated_at
        }

    @classmethod
    async def find_one(cls, query: dict) -> Optional['Subscription']:
        """Find a single subscription by query"""
        if cls.collection is None:
            raise ValueError("Collection not set. Call set_collection first.")
        result = await cls.collection.find_one(query)
        return cls.from_db_dict(result)

    @classmethod
    async def find(cls, query: dict) -> List['Subscription']:
        """Find subscriptions by query"""
        if cls.collection is None:
            raise ValueError("Collection not set. Call set_collection first.")
        cursor = cls.collection.find(query)
        results = await cursor.to_list(length=None)
        return [cls.from_db_dict(result) for result in results]

    async def save(self, session=None) -> bool:
        """Save the subscription to the database"""
        if self.__class__.collection is None:
            raise ValueError("Collection not set. Call set_collection first.")

        self.updated_at = datetime.utcnow()
        data = self.to_db_dict()

        if session:
            result = await self.__class__.collection.replace_one(
                {"_id": data["_id"]},
                data,
                upsert=True,
                session=session
            )
        else:
            result = await self.__class__.collection.replace_one(
                {"_id": data["_id"]},
                data,
                upsert=True
            )

        return result.acknowledged

    async def get_tenant(self, db):
        """Get the tenant associated with this subscription"""
        from .tenant import Tenant
        return await Tenant.find_one(db, {"_id": ObjectId(self.tenant_id)})

    async def get_subscribed_users(self, db):
        """Get all users subscribed to this subscription"""
        from .user import User
        if not self.subscribed_user_ids:
            return []

        # Convert user IDs to ObjectId if they're strings
        object_ids = [ObjectId(uid) if isinstance(uid, str) else uid for uid in self.subscribed_user_ids]
        return await User.find(db, {"_id": {"$in": object_ids}})

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
