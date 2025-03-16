from pymongo import ASCENDING
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from datetime import datetime
from typing import Optional, Dict, List, Any

class Tenant:
    collection = None  # Will be set during initialization

    @classmethod
    async def set_collection(cls, db: AsyncIOMotorDatabase):
        """Set the collection for the Tenant class"""
        cls.collection = db.tenants
        # Create indexes
        await cls.collection.create_index([("domain", ASCENDING)], unique=True)
        await cls.collection.create_index("owner_id")

    def __init__(
        self,
        name: str,
        domain: str,
        owner_id: str,
        _id: Optional[str] = None,
        created_at: datetime = None,
        updated_at: datetime = None,
        is_active: bool = True,
        billing_address: Optional[str] = None,
        contact_email: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None
    ):
        self._id = ObjectId(_id) if _id else ObjectId()
        self.name = name
        self.domain = domain
        self.owner_id = owner_id
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
        self.is_active = is_active
        self.billing_address = billing_address
        self.contact_email = contact_email
        self.metadata = metadata

    @property
    def id(self):
        return str(self._id)

    def to_dict(self) -> Dict[str, Any]:
        """Convert tenant object to dictionary for MongoDB storage"""
        return {
            "_id": self._id,
            "name": self.name,
            "domain": self.domain,
            "owner_id": self.owner_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "is_active": self.is_active,
            "billing_address": self.billing_address,
            "contact_email": self.contact_email,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Tenant':
        """Create a Tenant object from dictionary data"""
        if not data:
            return None

        return cls(
            _id=str(data.get("_id")),
            name=data.get("name"),
            domain=data.get("domain"),
            owner_id=data.get("owner_id"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
            is_active=data.get("is_active", True),
            billing_address=data.get("billing_address"),
            contact_email=data.get("contact_email"),
            metadata=data.get("metadata")
        )

    @classmethod
    async def find_one(cls, db, query: Dict[str, Any]) -> Optional['Tenant']:
        """Find a single tenant by query"""
        if cls.collection is None:
            await cls.set_collection(db)

        tenant_data = await cls.collection.find_one(query)
        if tenant_data:
            return cls.from_dict(tenant_data)
        return None

    @classmethod
    async def find(cls, db, query: Dict[str, Any]) -> List['Tenant']:
        """Find tenants by query"""
        if cls.collection is None:
            await cls.set_collection(db)

        cursor = cls.collection.find(query)
        results = await cursor.to_list(length=None)
        return [cls.from_dict(result) for result in results]

    async def save(self, db, session=None) -> 'Tenant':
        """Save the tenant to the database"""
        if self.__class__.collection is None:
            await self.__class__.set_collection(db)

        self.updated_at = datetime.utcnow()
        tenant_dict = self.to_dict()

        if session:
            result = await self.__class__.collection.replace_one(
                {"_id": self._id},
                tenant_dict,
                upsert=True,
                session=session
            )
        else:
            result = await self.__class__.collection.replace_one(
                {"_id": self._id},
                tenant_dict,
                upsert=True
            )

        return self

    async def get_subscribed_users(self, db) -> List:
        """Get all users subscribed with this tenant"""
        from .subscription import Subscription
        from .user import User

        if Subscription.collection is None:
            await Subscription.set_collection(db)

        # Find all subscriptions for this tenant
        subscriptions = await Subscription.find({"tenant_id": self.id})

        # Collect all user IDs from subscriptions
        all_user_ids = []
        for subscription in subscriptions:
            if subscription.subscribed_user_ids:
                all_user_ids.extend(subscription.subscribed_user_ids)

        # Remove duplicates
        unique_user_ids = list(set(all_user_ids))

        if not unique_user_ids:
            return []

        # Get actual user objects
        if User.collection is None:
            await User.set_collection(db)

        object_ids = [ObjectId(uid) if isinstance(uid, str) else uid for uid in unique_user_ids]
        return await User.find(db, {"_id": {"$in": object_ids}})

    async def get_subscriptions(self, db) -> List:
        """Get all subscriptions owned by this tenant"""
        from .subscription import Subscription

        if Subscription.collection is None:
            await Subscription.set_collection(db)

        return await Subscription.find({"tenant_id": self.id})

    async def is_user_subscribed(self, db, user_id: str) -> bool:
        """Check if a specific user is subscribed to this tenant"""
        from .subscription import Subscription

        if Subscription.collection is None:
            await Subscription.set_collection(db)

        # Find active subscriptions for this tenant
        subscriptions = await Subscription.find({
            "tenant_id": self.id,
            "is_active": True
        })

        # Check if user is in any of the subscriptions
        for subscription in subscriptions:
            if user_id in subscription.subscribed_user_ids:
                return True

        return False
