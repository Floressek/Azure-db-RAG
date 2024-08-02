import pymongo
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from dotenv import load_dotenv
import os

load_dotenv()
# Replace with your actual connection string
CONNECTION_STRING = os.environ.get("COSMOS_CONNECTION_STRING")
DB_NAME = os.environ.get("COSMOS_DB_NAME")


# COLLECTION_NAME = os.environ.get("COSMOS_COLLECTION_NAME")


def connect_to_cosmosdb(connection_string):
    try:
        client = pymongo.MongoClient(connection_string)
        client.admin.command("ismaster")
        print("MongoDB connection established successfully.")
        return client
    except ConnectionFailure as e:
        print(f"Could not connect to MongoDB due to: {e}")
        return None


if __name__ == "__main__":
    client_org = connect_to_cosmosdb(CONNECTION_STRING)
    print(client_org)
