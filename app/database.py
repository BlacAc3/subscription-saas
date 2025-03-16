from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from models.user import User
from models.tenant import Tenant
from models.subscription import Subscription

# Load environment variables
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")

async def init_db():
    """Initialize the database connection and setup collections"""
    client = AsyncIOMotorClient(MONGO_URI)
    database = client.saas_db

    print("Initializing database connection...")
    try:
        # Initialize collections for each model
        await User.set_collection(database)
        await Tenant.set_collection(database)
        await Subscription.set_collection(database)

        print("Database connection initialized successfully")

        # Print database information for debugging
        databases = await client.list_database_names()
        print(f"Available databases: {databases}")

        # Get all collection names
        collections = await database.list_collection_names()
        print(f"Database name: {database.name}")
        print(f"Collections in the database: {collections}")

        # Get document counts for each collection
        for collection in collections:
            count = await database[collection].count_documents({})
            print(f"{collection}: {count} documents")

        return database

    except Exception as e:
        print(f"Error initializing database: {e}")
        raise

# Function to get database instance
async def get_db():
    """Get database instance"""
    client = AsyncIOMotorClient(MONGO_URI)
    return client.saas_db
