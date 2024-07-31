import json
from pymongo import MongoClient, UpdateOne
from pymongo.errors import ConnectionFailure
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Replace with your actual connection string
CONNECTION_STRING = os.environ.get("COSMOSDB_CONNECTION_STRING")
DB_NAME = os.environ.get("DB_NAME")
COLLECTION_NAME = os.environ.get("COSMOS_COLLECTION_NAME")


# Function to connect to MongoDB
def connect_to_cosmosdb(connection_string):
    try:
        client = MongoClient(connection_string)
        client.admin.command("ismaster")
        print("MongoDB connection established successfully.")
        return client
    except ConnectionFailure as e:
        print(f"Could not connect to MongoDB due to: {e}")
        return None


if __name__ == "__main__":
    # Debugging output for environment variables
    print("COSMOS_CONNECTION_STRING:", CONNECTION_STRING)
    print("COSMOS_DB_NAME:", DB_NAME)
    print("COSMOS_COLLECTION_NAME:", COLLECTION_NAME)

    # Connect to MongoDB
    client_org = connect_to_cosmosdb(CONNECTION_STRING)

    if client_org is not None:
        db = client_org[DB_NAME]
        collection = db[COLLECTION_NAME]

        # Load product data from the local JSON file
        file_path = r'C:\Users\szyme\PycharmProjects\Azure-db-test2\json_embeddings_azure\test.json'
        with open(file_path, 'r') as f:
            raw_data = json.load(f)

        bulk_operations = [
            UpdateOne(
                {"_id": data["id"]},
                {"$set": data},
                upsert=True
            ) for data in raw_data
        ]

        if bulk_operations:
            result = collection.bulk_write(bulk_operations)
            print(
                f"Inserted: {result.upserted_count}, Matched: {result.matched_count}, Modified: {result.modified_count}")
        else:
            print("No valid products to insert or update.")

        # Closing the MongoDB connection
        client_org.close()
    else:
        print("Failed to connect to MongoDB. Exiting...")
