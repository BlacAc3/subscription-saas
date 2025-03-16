from datetime import datetime
from typing import List, Optional, Dict
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ASCENDING
from bson.objectid import ObjectId

class User:
    collection = None  # Will be set during initialization

    @classmethod
    async def set_collection(cls, db: AsyncIOMotorDatabase):
        """Set the collection for the User class"""
        cls.collection = db.users
        # Create indexes
        # Drop existing index if it exists
        try:
            await cls.collection.drop_index("email_1")
        except Exception:
            # Index may not exist, continue
            pass

        # Create new index
        await cls.collection.create_index([("email", ASCENDING)], unique=True)

    def __init__(self,
                name: str,
                email: str,
                password: str,
                _id: Optional[str] = None,
                is_active: bool = True,
                created_at: Optional[datetime] = None,
                updated_at: Optional[datetime] = None,
                roles: List[str] = None,
                metadata: Optional[Dict[str, str]] = None):

        self._id = ObjectId(_id) if _id else ObjectId()
        self.name = name
        self.email = email
        self.password = password  # Hashed password
        self.is_active = is_active
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
        self.roles = roles or ["user"]  # Global roles (system-wide)
        self.metadata = metadata

    @property
    def id(self):
        return str(self._id)

    def to_dict(self):
        """Convert the user object to a dictionary for MongoDB"""
        return {
            "_id": self._id,
            "name": self.name,
            "email": self.email,
            "password": self.password,
            "is_active": self.is_active,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "roles": self.roles,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data):
        """Create a User instance from a MongoDB document"""
        if not data:
            return None

        return cls(
            _id=str(data.get("_id")),
            name=data.get("name"),
            email=data.get("email"),
            password=data.get("password"),
            is_active=data.get("is_active", True),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
            roles=data.get("roles", ["user"]),
            metadata=data.get("metadata")
        )

    @classmethod
    async def find_one(cls, db, query):
        """Find a single user by query"""
        if cls.collection is None:
            await cls.set_collection(db)

        result = await cls.collection.find_one(query)
        if result:
            return cls.from_dict(result)
        return None

    @classmethod
    async def find(cls, db, query):
        """Find users matching the query"""
        if cls.collection is None:
            await cls.set_collection(db)

        cursor = cls.collection.find(query)
        results = await cursor.to_list(length=None)
        return [cls.from_dict(doc) for doc in results]

    async def save(self, db, session=None):
        """Save the user to the database"""
        if self.__class__.collection is None:
            await self.__class__.set_collection(db)

        self.updated_at = datetime.utcnow()
        data = self.to_dict()

        if session:
            result = await self.__class__.collection.replace_one(
                {"_id": self._id},
                data,
                upsert=True,
                session=session
            )
        else:
            result = await self.__class__.collection.replace_one(
                {"_id": self._id},
                data,
                upsert=True
            )

        return result

    async def get_tenants(self, db):
        """Get all tenants this user belongs to"""
        from .subscription import Subscription
        from .tenant import Tenant

        if Subscription.collection is None:
            await Subscription.set_collection(db)

        # Find subscriptions where this user is subscribed
        subscriptions = await Subscription.find({
            "subscribed_user_ids": self.id,
            "is_active": True
        })

        # Extract the tenant IDs from those subscriptions
        tenant_ids = [sub.tenant_id for sub in subscriptions]

        if not tenant_ids:
            return []

        if Tenant.collection is None:
            await Tenant.set_collection(db)

        # Convert to ObjectId if they are strings
        object_ids = [ObjectId(tid) if isinstance(tid, str) else tid for tid in tenant_ids]

        # Find and return the tenant objects
        return await Tenant.find(db, {"_id": {"$in": object_ids}})

    async def get_subscriptions(self, db):
        """Get all subscriptions for this user"""
        from .subscription import Subscription

        if Subscription.collection is None:
            await Subscription.set_collection(db)

        # Find all subscriptions where this user is subscribed
        return await Subscription.find({
            "subscribed_user_ids": self.id
        })

    async def get_owned_tenants(self, db):
        """Get all tenants owned by this user"""
        from .tenant import Tenant

        if Tenant.collection is None:
            await Tenant.set_collection(db)

        return await Tenant.find(db, {"owner_id": self.id})
