from motor.motor_asyncio import AsyncIOMotorClient
from core.config import settings
from typing import Optional


class DataBase:
    """Manages the MongoDB Atlas connection."""
    client: Optional[AsyncIOMotorClient] = None
    db_name: str = settings.MONGO_DB_NAME


db = DataBase()


async def connect_to_mongo():
    """Establishes the MongoDB Atlas connection using the URI."""
    try:
        # Use the URI directly from settings, which contains cluster details and credentials
        db.client = AsyncIOMotorClient(
            settings.MONGO_DB_URI,
            serverSelectionTimeoutMS=5000,
            uuidRepresentation="standard"
        )

        # Test the connection to Atlas
        await db.client.admin.command('ping')
        print(f"MongoDB Atlas connection established to database: {db.db_name}")

    except Exception as e:
        print(f"❌ ERROR: Could not connect to MongoDB Atlas. Check URI and Network Access.")
        print(f"Details: {e}")
        # In a production environment, you might stop the application here
        # or implement retry logic.


async def close_mongo_connection():
    """Closes the MongoDB Atlas connection."""
    if db.client:
        db.client.close()
        print("MongoDB Atlas connection closed.")


def get_database():
    """Dependency injection function to get the specific database instance."""
    # The database name is appended to the client connection
    if not db.client:
        # Should not happen if startup hook is correct, but safe check
        raise ConnectionError("MongoDB client is not initialized.")
    return db.client[db.db_name]


# Global access point for collections
def get_user_collection():
    return get_database()["users"]


def get_application_collection():
    return get_database()["applications"]