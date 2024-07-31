import json
import os
import time
from pymongo import MongoClient, UpdateOne
from pymongo.errors import ConnectionFailure
from dotenv import load_dotenv
from openai import AzureOpenAI
from tenacity import retry, wait_random_exponential, stop_after_attempt

# Load environment variables
load_dotenv()

# MongoDB connection details
CONNECTION_STRING = os.environ.get("COSMOSDB_CONNECTION_STRING")
DB_NAME = os.environ.get("DB_NAME")
COLLECTION_NAME = os.environ.get("COSMOS_COLLECTION_NAME")

# Azure OpenAI API details
AOAI_ENDPOINT = os.environ.get("AOAI_ENDPOINT")
AOAI_KEY = os.environ.get("AOAI_KEY")
EMBEDDINGS_DEPLOYMENT_NAME = "embeddings"
COMPLETIONS_DEPLOYMENT_NAME = "completions"
AOAI_API_VERSION = "2023-05-15"


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


# Generate embeddings
@retry(wait=wait_random_exponential(min=1, max=20), stop=stop_after_attempt(3))
def generate_embeddings(text: str):
    response = ai_client.embeddings.create(input=text, model=EMBEDDINGS_DEPLOYMENT_NAME)
    embeddings = response.data[0].embedding
    time.sleep(0.5)  # rest period to avoid rate limiting on AOAI
    return embeddings


# Vectorize and update documents
def add_collection_content_vector_field(collection_name: str):
    collection = db[collection_name]
    bulk_operations = []
    for doc in collection.find():
        if "contentVector" in doc:
            del doc["contentVector"]
        content = json.dumps(doc, default=str)
        content_vector = generate_embeddings(content)
        bulk_operations.append(UpdateOne(
            {"_id": doc["_id"]},
            {"$set": {"contentVector": content_vector}},
            upsert=True
        ))
    collection.bulk_write(bulk_operations)


# Create vector indexes
def create_vector_index(collection_name: str):
    db.command({
        'createIndexes': collection_name,
        'indexes': [
            {
                'name': 'VectorSearchIndex',
                'key': {
                    "contentVector": "cosmosSearch"
                },
                'cosmosSearchOptions': {
                    'kind': 'vector-ivf',
                    'numLists': 1,
                    'similarity': 'COS',
                    'dimensions': 1536
                }
            }
        ]
    })


# Perform vector search
def vector_search(collection_name, query, num_results=3):
    collection = db[collection_name]
    query_embedding = generate_embeddings(query)
    pipeline = [
        {
            '$search': {
                "cosmosSearch": {
                    "vector": query_embedding,
                    "path": "contentVector",
                    "k": num_results
                },
                "returnStoredSource": True}},
        {'$project': {'similarityScore': {'$meta': 'searchScore'}, 'document': '$$ROOT'}}
    ]
    results = collection.aggregate(pipeline)
    return results


def print_product_search_result(result):
    print(f"Similarity Score: {result['similarityScore']}")
    print(f"Name: {result['document']['name']}")
    print(f"Category: {result['document']['categoryName']}")
    print(f"SKU: {result['document']['categoryName']}")
    print(f"_id: {result['document']['_id']}\n")


# Retrieve and Generate (RAG) results
system_prompt = """
You are a helpful, fun and friendly sales assistant for Cosmic Works, a bicycle and bicycle accessories store. 
Your name is Cosmo.
You are designed to answer questions about the products that Cosmic Works sells.

Only answer questions related to the information provided in the list of products below that are represented
in JSON format.

If you are asked a question that is not in the list, respond with "I don't know."

List of products:
"""


def rag_with_vector_search(question: str, num_results: int = 3):
    results = vector_search("products", question, num_results=num_results)
    product_list = ""
    for result in results:
        if "contentVector" in result["document"]:
            del result["document"]["contentVector"]
        product_list += json.dumps(result["document"], indent=4, default=str) + "\n\n"

    formatted_prompt = system_prompt + product_list

    messages = [
        {"role": "system", "content": formatted_prompt},
        {"role": "user", "content": question}
    ]

    completion = ai_client.chat.completions.create(messages=messages, model=COMPLETIONS_DEPLOYMENT_NAME)
    return completion.choices[0].message.content


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
            print(f"Inserted: {result.upserted_count}, Matched: {result.matched_count}, Modified: {result.modified_count}")
        else:
            print("No valid products to insert or update.")

        # Establish Azure OpenAI connectivity
        ai_client = AzureOpenAI(
            azure_endpoint=AOAI_ENDPOINT,
            api_version=AOAI_API_VERSION,
            api_key=AOAI_KEY
        )

        # Add vector fields to collections
        add_collection_content_vector_field("products")
        add_collection_content_vector_field("customers")
        add_collection_content_vector_field("sales")

        # Create vector indexes for collections
        create_vector_index("products")
        create_vector_index("customers")
        create_vector_index("sales")

        # Example queries
        query = "What bikes do you have?"
        results = vector_search("products", query, num_results=4)
        for result in results:
            print_product_search_result(result)

        query = "What do you have that is yellow?"
        results = vector_search("products", query, num_results=4)
        for result in results:
            print_product_search_result(result)

        # Example RAG usage
        print(rag_with_vector_search("What bikes do you have?", 5))
        print(rag_with_vector_search("What are the names and skus of yellow products?", 5))

        # Closing the MongoDB connection
        client_org.close()
    else:
        print("Failed to connect to MongoDB. Exiting...")
