
from pathlib import Path
from dotenv import load_dotenv
import os

from langchain_google_genai import ChatGoogleGenerativeAI

# Load project .env
load_dotenv(Path(__file__).resolve().parent / ".env")

api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    raise ValueError("GOOGLE_API_KEY missing")

print("Testing Gemini connection...")

llm = ChatGoogleGenerativeAI(
    model="gemini-3.8-flash",
    google_api_key=api_key,
    temperature=0
)

response = llm.invoke(
    "Reply with exactly: Gemini connection successful"
)

print("Gemini response:")
print(response.content)
