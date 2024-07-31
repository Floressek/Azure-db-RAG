import os
import json
import dotenv
from typing import List, Dict, Any
from openai import OpenAI

# Load environment variables
dotenv.load_dotenv()

# Get the API key from the environment variable
OPENAI_API_KEY = os.getenv("OPEN_AI_KEY")
if not OPENAI_API_KEY:
    raise ValueError("No OpenAI API key found. Please set the OPEN_AI_KEY environment variable.")

# Initialize the OpenAI client with the API key
client = OpenAI(api_key=OPENAI_API_KEY)

FILE_PATH = os.getenv("INPUT_PATH_FILE")
if not FILE_PATH:
    raise ValueError("No input file path found. Please set the INPUT_PATH_FILE environment variable.")


def generate_embedding(text: str) -> List[float]:
    try:
        response = client.embeddings.create(
            model="text-embedding-ada-002",
            input=text
        )
        embedding = response.data[0].embedding
        return embedding
    except Exception as e:
        print(f"Error generating embedding: {e}")
        return []


def load_json(file_path: str) -> Dict[str, Any]:
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        return data
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return {"pages": []}
    except json.JSONDecodeError:
        print(f"Invalid JSON in file: {file_path}")
        return {"pages": []}


def save_json(data: Dict[str, Any], file_path: str) -> None:
    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


def add_embeddings_to_json(data: Dict[str, Any]) -> Dict[str, Any]:
    vectors = []
    for page in data.get("pages", []):
        for page_num, content in page.items():
            embedding = generate_embedding(content)
            vectors.append(embedding)

    data["vectors"] = vectors
    return data


if __name__ == "__main__":
    input_json_path = FILE_PATH
    output_json_path = 'output_with_embeddings.json'

    data = load_json(input_json_path)
    data_with_embeddings = add_embeddings_to_json(data)
    save_json(data_with_embeddings, output_json_path)

    print("Embeddings added and JSON file saved.")
