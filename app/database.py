from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
import os
from models.user import User
from models.tenant import Tenant
from models.subscription import Subscription
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")

async def init_db():
    client = AsyncIOMotorClient(MONGO_URI)
    database = client.saas_db
    print("Databases: ", client.list_database_names())
    print("Initializing database connection...")
    try:
        # Wait for the database to be initialized
        await init_beanie(database, document_models=[User, Tenant, Subscription])
        # Get all collection names
        collections = await database.list_collection_names()
        print(f"Database name: {database.name}")
        print(f"Collections in the database: {collections}")

        # Get document counts for each collection
        for collection in collections:
            count = await database[collection].count_documents({})
            print(f"{collection}: {count} documents")

    except Exception as e:
        print(f"Error initializing database: {e}")
