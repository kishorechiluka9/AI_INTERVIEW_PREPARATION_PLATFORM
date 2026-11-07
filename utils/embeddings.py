
import os
from pathlib import Path
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings

# Project root .env location
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = PROJECT_ROOT / ".env"

# Load environment variables
load_dotenv(dotenv_path=ENV_PATH, override=False)


def get_embedding_model():
    api_key = os.getenv("GOOGLE_API_KEY")

    if not api_key or not api_key.strip():
        raise ValueError(
            "GOOGLE_API_KEY missing. Check your .env configuration."
        )

    embeddings = GoogleGenerativeAIEmbeddings(
        model="gemini-embedding-001",
        google_api_key=api_key.strip()
    )

    return embeddings
