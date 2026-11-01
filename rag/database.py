from pathlib import Path
import chromadb
from dotenv import load_dotenv

from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

ROOT = Path(__file__).resolve().parents[1]
DATABASE_PATH = ROOT / "data" / "chroma"
MODEL_NAME = "all-MiniLM-L6-v2"

def get_collection():
    DATABASE_PATH.mkdir(parents=True, exist_ok=True)
    
    client = chromadb.PersistentClient(
        path=str(DATABASE_PATH)
    )
    
    embedding_function = SentenceTransformerEmbeddingFunction(
        model_name=MODEL_NAME,
        device="cpu",
        normalize_embeddings=True
    )
    
    collection = client.get_or_create_collection(
        name="godot_source",
        embedding_function=embedding_function,
        metadata={"hnsw:space": "cosine"}
    )
    
    return collection