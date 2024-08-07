import os
import time
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from dotenv import load_dotenv
from openai import OpenAI
from tenacity import retry, wait_random_exponential, stop_after_attempt
from flask import Flask, render_template, request, jsonify
import logging

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'

# Load environment variables
load_dotenv()

# MongoDB connection details
CONNECTION_STRING = os.environ.get("COSMOSDB_CONNECTION_STRING")
DB_NAME = os.environ.get("DB_NAME")
COLLECTION_NAME = os.environ.get("COSMOS_COLLECTION_NAME")

# Get the API key from the environment variable
OPENAI_API_KEY = os.getenv("OPEN_AI_KEY")
if not OPENAI_API_KEY:
    raise ValueError("No OpenAI API key found. Please set the OPEN_AI_KEY environment variable.")

# Initialize the OpenAI client with the API key
client = OpenAI(api_key=OPENAI_API_KEY)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def connect_to_cosmosdb(connection_string):
    try:
        client = MongoClient(connection_string)
        client.admin.command("ismaster")
        logging.info("MongoDB connection established successfully.")
        return client
    except ConnectionFailure as e:
        logging.error(f"Could not connect to MongoDB due to: {e}")
        return None


@retry(wait=wait_random_exponential(min=1, max=20), stop=stop_after_attempt(3))
def generate_embeddings(text: str):
    try:
        response = client.embeddings.create(
            model="text-embedding-ada-002",
            input=text
        )
        embeddings = response.data[0].embedding
        return embeddings
    except Exception as e:
        logging.error(f"Error generating embeddings: {e}")
        raise


def vector_search(collection, query, num_results=2):
    query_embedding = generate_embeddings(query)
    pipeline = [
        {
            '$search': {
                "cosmosSearch": {
                    "vector": query_embedding,
                    "path": "contentVector",
                    "k": num_results
                },
                "returnStoredSource": True
            }
        },
        {'$project': {'similarityScore': {'$meta': 'searchScore'}, 'document': '$$ROOT'}}
    ]
    results = collection.aggregate(pipeline)
    return results


def print_page_search_result(result):
    logging.info(f"Similarity Score: {result['similarityScore']}")
    page_number = result['document']['page_number']
    logging.info(f"Page: {page_number}")
    logging.info(f"Content: {result['document']['content']}")
    logging.info(f"_id: {result['document']['_id']}\n")


# Creative prompt for the RAG-like model
system_prompt = """
You are a helpful assistant designed to provide information about the Euvic Services presentation.
Try to answer questions based on the information provided in the presentation content below.
If you are asked a question that isn't covered in the presentation, respond based on the given information and your best judgment.

Presentation content:
"""


def rag_with_vector_search(collection, question: str, num_results: int = 2):
    results = vector_search(collection, question, num_results=num_results)
    presentation_content = ""
    for result in results:
        if "contentVector" in result["document"]:
            del result["document"]["contentVector"]
        page_number = result["document"]["page_number"]
        presentation_content += f"Page {page_number}: {result['document']['content']}\n\n"

    formatted_prompt = system_prompt + presentation_content

    messages = [
        {"role": "system", "content": formatted_prompt},
        {"role": "user", "content": question}
    ]

    try:
        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=messages
        )
        return completion.choices[0].message.content
    except Exception as e:
        logging.error(f"Error with OpenAI ChatCompletion: {e}")
        return "An error occurred while generating the response."



@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        logging.info("POST request received")
        question = request.form['question']
        num_results = int(request.form['num_results'])
        logging.info(f"Received question: {question} with num_results: {num_results}")

        start_time = time.time()
        logging.info("=" * 50)
        logging.info(f"Processing query: {question}")

        client_org = connect_to_cosmosdb(CONNECTION_STRING)
        if client_org is not None:
            db = client_org[DB_NAME]
            collection = db[COLLECTION_NAME]
            try:
                response = rag_with_vector_search(collection, question, num_results)
            except Exception as e:
                logging.error(f"Error processing query: {e}")
                response = "An error occurred during processing."
            finally:
                client_org.close()
        else:
            response = "Failed to connect to MongoDB."

        end_time = time.time()
        logging.info(f"Query processed in {end_time - start_time:.2f} seconds")
        logging.info("=" * 50)
        return jsonify({'response': response}), 200
    logging.info("GET request received")
    return render_template('index.html')


if __name__ == "__main__":
    app.run(debug=True, port=8080)
